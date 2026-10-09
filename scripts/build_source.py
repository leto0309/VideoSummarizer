"""Package only Git-tracked source; never include local runtime or outputs."""
import argparse
import hashlib
from pathlib import Path
import re
import subprocess
import zipfile


def build(version):
    if not re.fullmatch(r'v\d+\.\d+\.\d+(?:-[A-Za-z0-9.-]+)?', version):
        raise ValueError('Invalid release version')
    root = Path(__file__).resolve().parents[1]
    tracked = subprocess.check_output(['git', 'ls-files', '-z'], cwd=root).decode('utf-8').split('\0')
    blocked = {'.git', '.venv', 'runtime', 'models', 'tools', 'temp', 'outputs', 'logs', 'build', 'dist', '__pycache__'}
    destination = root / 'dist'
    destination.mkdir(exist_ok=True)
    archive = destination / f'VideoSummarizer-{version}-source.zip'
    count = 0
    with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED) as package:
        for name in sorted(filter(None, tracked)):
            path = root / name
            relative = Path(name)
            if (any(part in blocked for part in relative.parts) or name.startswith('.env')
                    or relative.name == 'bookmark-settings.json' or relative.name.startswith('cookies')
                    or path.is_symlink() or not path.is_file() or path.stat().st_size > 200000):
                raise ValueError(f'Unexpected tracked file: {name}')
            content = path.read_text(encoding='utf-8-sig').replace('\r\n', '\n')
            if name.endswith('.bat'):
                content = content.replace('\n', '\r\n')
            info = zipfile.ZipInfo('VideoSummarizer/' + relative.as_posix())
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            package.writestr(info, content.encode('utf-8'))
            count += 1
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    (destination / 'SHA256SUMS.txt').write_text(f'{digest}  {archive.name}\n', encoding='utf-8')
    print(f'Packaged {count} tracked files: {archive.name}; SHA256 {digest}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('version')
    build(parser.parse_args().version)
