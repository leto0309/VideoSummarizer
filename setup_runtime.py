from pathlib import Path
import shutil
import subprocess
import sys
import traceback
import zipfile
from config import ROOT, TOOLS
from install_support import download_file, fetch
from network_check import explain
from setup_text import t

NODE_VERSION = '24.19.0'
OLLAMA_VERSION = '0.40.2'


def progress(message):
    print(message, flush=True)


def setup_node():
    target = TOOLS / 'node'
    if (target / 'node.exe').is_file():
        return
    # Portable official LTS package: no system PATH changes.
    base = f'https://nodejs.org/dist/v{NODE_VERSION}/'
    sums = fetch(base + 'SHASUMS256.txt', progress=progress)
    expected, filename = next(line.split() for line in sums.text.splitlines() if line.endswith('-win-x64.zip'))
    archive = TOOLS / filename
    target.mkdir(parents=True, exist_ok=True)
    progress(t('node_download', version=NODE_VERSION))
    download_file(base + filename, archive, sha256=expected, progress=progress)
    with zipfile.ZipFile(archive) as package:
        for name in ('node.exe', 'LICENSE'):
            entry = next(e for e in package.infolist() if e.filename.endswith('/' + name))
            with package.open(entry) as source, (target / name).open('wb') as destination:
                shutil.copyfileobj(source, destination)
    archive.unlink()


def setup_ollama():
    release = fetch(f'https://api.github.com/repos/ollama/ollama/releases/tags/v{OLLAMA_VERSION}', progress=progress)
    assets = {a['name']: a for a in release.json()['assets']}
    asset = assets['ollama-windows-amd64.zip']
    archive = TOOLS / asset['name']
    TOOLS.mkdir(exist_ok=True)
    if shutil.disk_usage(ROOT).free < asset['size'] * 4 + 4 * 1024**3:
        raise RuntimeError(t('low_disk'))
    sums = fetch(assets['sha256sum.txt']['browser_download_url'], progress=progress)
    expected = next(line.split()[0] for line in sums.text.splitlines()
                    if Path(line.split()[-1].lstrip('*')).name == archive.name)
    progress(t('ollama_download', version=OLLAMA_VERSION, gb=asset['size'] / 1024**3))
    download_file(asset['browser_download_url'], archive, sha256=expected, size=asset['size'], progress=progress)
    destination = TOOLS / 'ollama'
    destination.mkdir(exist_ok=True)
    with zipfile.ZipFile(archive) as package:
        for entry in package.infolist():
            target = (destination / entry.filename).resolve()
            if not target.is_relative_to(destination.resolve()):
                raise RuntimeError(t('unsafe_archive'))
        package.extractall(destination)
    archive.unlink()  # exact project-owned installer only, never a model


def setup():
    TOOLS.mkdir(exist_ok=True)
    try:
        setup_node()
    except Exception as exc:
        explain(exc, 'node')
        raise
    if not (TOOLS / 'ollama' / 'ollama.exe').exists():
        try:
            setup_ollama()
        except Exception as exc:
            explain(exc, 'github')
            raise
    else:
        print(t('ollama_bundled'), flush=True)
    print(t('cuda_skipped'), flush=True)
    from launcher import pull
    try:
        pull()
    except subprocess.CalledProcessError as exc:
        explain(exc, 'ollama')
        raise
    # Subtitle-only use remains available if the speech model host is unreachable.
    from whisper_models import ensure_model, ModelUnavailableError
    try:
        ensure_model(progress=lambda message: print(message, flush=True))
    except ModelUnavailableError as exc:
        print(t('whisper_incomplete'), flush=True)
        print(str(exc), flush=True)


if __name__ == '__main__':
    try:
        setup()
    except Exception as exc:
        traceback.print_exc()
        if getattr(exc, 'download_source', None):
            from network_check import check
            check([exc.download_source])
        sys.exit(1)
