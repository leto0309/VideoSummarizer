"""Build Windows x64 bundle with pinned, checksum-verified standalone CPython."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tarfile
import urllib.request
import zipfile

PYTHON_RELEASE = '20261009'
PYTHON_FILE = 'cpython-3.11.17+20261009-x86_64-pc-windows-msvc-install_only.tar.gz'
PYTHON_SHA256 = '4d307648d2fe5f8d927e10380cc33eb7afd8a34a7efe0ed786b5860b5f2d3408'
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app_version import portable_record, validate_release_version


def build(version):
    if os.name != 'nt' or not re.fullmatch(r'v\d+\.\d+\.\d+(?:-[A-Za-z0-9.-]+)?', version):
        raise ValueError('Windows build and valid release version required')
    validate_release_version(version)
    cache = ROOT / 'build'
    cache.mkdir(exist_ok=True)
    archive = cache / PYTHON_FILE
    if not archive.exists():
        url = f'https://github.com/astral-sh/python-build-standalone/releases/download/{PYTHON_RELEASE}/' + PYTHON_FILE.replace('+', '%2B')
        partial = archive.with_suffix('.part')
        with urllib.request.urlopen(url, timeout=120) as response, partial.open('wb') as output:
            shutil.copyfileobj(response, output)
        partial.replace(archive)
    if hashlib.sha256(archive.read_bytes()).hexdigest() != PYTHON_SHA256:
        raise ValueError('Standalone Python checksum mismatch')
    package = cache / version / 'VideoSummarizer'
    if package.exists():
        raise ValueError('Build output already exists; use a new build directory or version')
    package.mkdir(parents=True)
    tracked = subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT).decode('utf-8').split('\0')
    blocked = {'.git', '.venv', 'runtime', 'models', 'tools', 'temp', 'outputs', 'logs', 'build', 'dist', '__pycache__'}
    for name in filter(None, tracked):
        source = ROOT / name
        if (any(part in blocked for part in Path(name).parts) or name.startswith('.env')
                or Path(name).name in {'bookmark-settings.json', 'language-settings.json'} or source.is_symlink()):
            raise ValueError(f'Unexpected tracked file: {name}')
        target = package / name
        target.parent.mkdir(parents=True, exist_ok=True)
        data = source.read_text(encoding='utf-8-sig').replace('\r\n', '\n')
        if name.endswith('.bat'):
            data = data.replace('\n', '\r\n')
        target.write_bytes(data.encode('utf-8'))
    with tarfile.open(archive, 'r:gz') as tar:
        for member in tar.getmembers():
            if not (member.name == 'python' or member.name.startswith('python/')):
                raise ValueError('Unexpected Python archive root')
            if not (member.isdir() or member.isfile()) or not (package / member.name).resolve().is_relative_to((package / 'python').resolve()):
                raise ValueError('Unsafe Python archive member')
        # Every member is a validated regular file/directory; no links or devices.
        tar.extractall(package)
    (package / 'python').rename(package / 'runtime')
    # srt is only published as a source archive. Build its MIT-licensed pure
    # Python wheel here so first-run setup needs no source extraction/build.
    subprocess.run([sys.executable, '-m', 'pip', 'wheel', '--no-cache-dir', '--no-deps',
                    '--wheel-dir', str(package / 'wheels'), 'srt==3.5.3'], check=True)
    compiler = Path(os.environ['WINDIR']) / 'Microsoft.NET' / 'Framework64' / 'v4.0.30319' / 'csc.exe'
    subprocess.run([str(compiler), '/nologo', '/target:winexe', '/platform:x64',
                    '/r:System.Windows.Forms.dll', '/r:System.Drawing.dll',
                    '/out:' + str(package / 'VideoSummarizer.exe'), str(ROOT / 'packaging' / 'Launcher.cs')], check=True)
    (package / 'PORTABLE_BUILD.json').write_text(json.dumps(portable_record({
        'version': version, 'python': '3.11.17', 'python_release': PYTHON_RELEASE,
        'python_archive_sha256': PYTHON_SHA256,
        'bootstrap': 'native .NET Framework launcher', 'dependencies': 'srt wheel bundled; others download on first consented launch'
    }, version, 'windows-x64'), indent=2), encoding='utf-8')
    destination = ROOT / 'dist'
    destination.mkdir(exist_ok=True)
    output = destination / f'VideoSummarizer-{version}-windows-x64.zip'
    with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_DEFLATED) as zip:
        for file in sorted(package.rglob('*')):
            if file.is_file():
                zip.write(file, file.relative_to(package.parent).as_posix())
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    (destination / 'WINDOWS_SHA256SUMS.txt').write_text(f'{digest}  {output.name}\n', encoding='utf-8')
    print(json.dumps({'package': str(package), 'zip': str(output), 'bytes': output.stat().st_size,
                      'sha256': digest}), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('version')
    build(parser.parse_args().version)
