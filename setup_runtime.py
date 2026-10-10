import hashlib
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile
import requests
from config import ROOT, TOOLS, node_runtime

NODE_VERSION = '24.19.0'
OLLAMA_VERSION = '0.40.2'


def setup_node():
    target = TOOLS / 'node'
    if (target / 'node.exe').is_file():
        return
    # Portable official LTS package: no system PATH changes.
    base = f'https://nodejs.org/dist/v{NODE_VERSION}/'
    sums = requests.get(base + 'SHASUMS256.txt', timeout=30)
    sums.raise_for_status()
    expected, filename = next(line.split() for line in sums.text.splitlines() if line.endswith('-win-x64.zip'))
    archive = TOOLS / filename
    target.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256()
    with requests.get(base + filename, stream=True, timeout=(30, 120)) as response:
        response.raise_for_status()
        with archive.open('wb') as handle:
            for chunk in response.iter_content(1024**2):
                digest.update(chunk)
                handle.write(chunk)
    if digest.hexdigest() != expected:
        raise RuntimeError('Node 官方 SHA256 不一致，拒絕安裝')
    with zipfile.ZipFile(archive) as package:
        for name in ('node.exe', 'LICENSE'):
            entry = next(e for e in package.infolist() if e.filename.endswith('/' + name))
            with package.open(entry) as source, (target / name).open('wb') as destination:
                shutil.copyfileobj(source, destination)
    archive.unlink()


def setup():
    TOOLS.mkdir(exist_ok=True)
    setup_node()
    executable = TOOLS / 'ollama' / 'ollama.exe'
    if not executable.exists():
        release = requests.get(f'https://api.github.com/repos/ollama/ollama/releases/tags/v{OLLAMA_VERSION}', timeout=30)
        release.raise_for_status()
        assets = {a['name']: a for a in release.json()['assets']}
        asset = assets['ollama-windows-amd64.zip']
        archive = TOOLS / asset['name']
        TOOLS.mkdir(exist_ok=True)
        if shutil.disk_usage(ROOT).free < asset['size'] * 4 + 4 * 1024**3:
            raise RuntimeError('可用空間不足，請至少保留約 10 GB 安裝空間')
        sums = requests.get(assets['sha256sum.txt']['browser_download_url'], timeout=30)
        sums.raise_for_status()
        expected = next(line.split()[0] for line in sums.text.splitlines()
                        if Path(line.split()[-1].lstrip('*')).name == archive.name)
        digest = hashlib.sha256()
        with requests.get(asset['browser_download_url'], stream=True, timeout=(30, 120)) as response:
            response.raise_for_status()
            with archive.open('wb') as handle:
                for chunk in response.iter_content(1024**2):
                    digest.update(chunk)
                    handle.write(chunk)
        if digest.hexdigest() != expected:
            raise RuntimeError('官方 SHA256 不一致，拒絕解壓縮')
        destination = TOOLS / 'ollama'
        destination.mkdir(exist_ok=True)
        with zipfile.ZipFile(archive) as package:
            for entry in package.infolist():
                target = (destination / entry.filename).resolve()
                if not target.is_relative_to(destination.resolve()):
                    raise RuntimeError('拒絕含越界路徑的壓縮檔')
            package.extractall(destination)
        archive.unlink()  # exact project-owned installer only, never a model
    else:
        print('已找到项目内 Ollama，跳过 Ollama 程序下载。', flush=True)
    print('首次配置默认跳过可选 CUDA 库。Whisper 可使用 CPU int8；GPU 加速可稍后双击 install-gpu.bat 安装。', flush=True)
    from launcher import pull
    pull()
    # Subtitle-only use remains available if the speech model host is unreachable.
    from whisper_models import ensure_model, ModelUnavailableError
    try:
        ensure_model(progress=lambda message: print(message, flush=True))
    except ModelUnavailableError as exc:
        print('警告：語音模型尚未完成；有字幕的影片仍可處理。', flush=True)
        print(str(exc), flush=True)


if __name__ == '__main__':
    setup()
