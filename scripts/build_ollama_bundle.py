"""Combine a verified with-Whisper ZIP and the complete pinned official Ollama ZIP."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import stat
import sys
import sys
import time
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app_version import portable_record, validate_packaged_version, validate_release_version
sys.path.insert(0, str(ROOT))
from scripts.build_model_bundle import FILES, digest, verify
OLLAMA_VERSION = '0.40.2'
OLLAMA_FILE = 'ollama-windows-amd64.zip'
OLLAMA_SHA256 = 'e29ad1d5063dd4b54b2492d9b00adab2cff9621bfa654b6c92aa8d6f1fdfe7fc'
OLLAMA_BYTES = 1468085195
OLLAMA_URL = f'https://github.com/ollama/ollama/releases/download/v{OLLAMA_VERSION}/{OLLAMA_FILE}'
ASSET_LIMIT = 2 * 1024**3


def download_archive(url, target, expected_size):
    """Resume project-owned partial downloads, then let the caller verify SHA256."""
    partial = target.with_suffix(target.suffix + '.part')
    for attempt in range(4):
        start = partial.stat().st_size if partial.is_file() else 0
        if start == expected_size:
            partial.replace(target)
            return
        try:
            request = urllib.request.Request(url, headers={'Range': f'bytes={start}-'} if start else {})
            with urllib.request.urlopen(request, timeout=120) as response:
                if response.status == 206:
                    if response.headers.get('Content-Range') != f'bytes {start}-{expected_size-1}/{expected_size}':
                        raise ValueError('Unexpected download range')
                elif response.status == 200:
                    start = 0
                else:
                    raise ValueError('Unexpected download response')
                with partial.open('ab' if start else 'wb') as output:
                    while chunk := response.read(1024**2):
                        output.write(chunk)
            if partial.stat().st_size != expected_size:
                raise OSError('Incomplete upstream download')
            partial.replace(target)
            return
        except (OSError, TimeoutError):
            if attempt == 3:
                raise
            print(f'Retrying {target.name}, preserving partial download', flush=True)
            time.sleep(attempt + 1)


def safe_name(info):
    name = info.filename
    path = PurePosixPath(name)
    if (not name or '\\' in name or ':' in name or path.is_absolute()
            or '..' in path.parts or stat.S_ISLNK(info.external_attr >> 16)):
        raise ValueError('Unsafe archive entry')
    return path


def validate_base(package, version):
    seen = set()
    for info in package.infolist():
        path = safe_name(info)
        parts = path.parts
        if parts[0] != 'VideoSummarizer' or info.filename.casefold() in seen:
            raise ValueError('Unexpected portable archive root or duplicate')
        seen.add(info.filename.casefold())
        if len(parts) > 1 and parts[1] != 'runtime':
            if set(parts).intersection({'.git', '.venv', 'tools', 'logs', 'outputs', 'temp'}):
                raise ValueError('Unexpected private data in base archive')
            if parts[-1] in {'language-settings.json', 'bookmark-settings.json', 'portable-ready.json'}:
                raise ValueError('Unexpected user settings in base archive')
            if parts[1] == 'models' and str(path).removeprefix('VideoSummarizer/models/whisper/small/') not in FILES:
                raise ValueError('Unexpected model in base archive')
    portable = json.loads(package.read('VideoSummarizer/PORTABLE_BUILD.json'))
    whisper = json.loads(package.read('VideoSummarizer/WHISPER_BUNDLE.json'))
    if portable.get('version') != version or whisper.get('version') != version:
        raise ValueError('Base archive version mismatch')
    validate_packaged_version(package.read('VideoSummarizer/app_version.py').decode('utf-8'), version)
    for name, expected in FILES.items():
        with package.open('VideoSummarizer/models/whisper/small/' + name) as handle:
            if hashlib.file_digest(handle, 'sha256').hexdigest() != expected:
                raise ValueError('Unexpected Whisper model contents')


def validate_ollama(package):
    seen = set()
    files = set()
    for info in package.infolist():
        path = safe_name(info)
        if info.filename.casefold() in seen:
            raise ValueError('Duplicate upstream archive entry')
        seen.add(info.filename.casefold())
        if not info.is_dir():
            files.add(str(path))
    if 'ollama.exe' not in files or not any(name.startswith('lib/ollama/') for name in files):
        raise ValueError('Incomplete Ollama archive')
    if not any('LICENSE' in name.upper() for name in files):
        raise ValueError('Missing upstream component licenses')


def copy_entry(source, info, output, name):
    checksum = hashlib.sha256()
    target = zipfile.ZipInfo(name, date_time=info.date_time)
    target.compress_type = zipfile.ZIP_DEFLATED
    target.external_attr = 0o100644 << 16
    # Streaming avoids holding large CUDA DLLs or the complete ZIP in memory.
    with source.open(info) as reader, output.open(target, 'w', force_zip64=True) as writer:
        while chunk := reader.read(1024**2):
            writer.write(chunk)
            checksum.update(chunk)
    return checksum.hexdigest()


def build(version, base_sha256, whisper_zip=None, ollama_zip=None):
    if not re.fullmatch(r'v\d+\.\d+\.\d+(?:-[A-Za-z0-9.-]+)?', version):
        raise ValueError('Invalid release version')
    if not re.fullmatch(r'[0-9a-f]{64}', base_sha256 or ''):
        raise ValueError('Verified with-Whisper SHA256 required')
    validate_release_version(version)
    cache = ROOT / 'build' / 'ollama-cache'
    cache.mkdir(parents=True, exist_ok=True)
    base_name = f'VideoSummarizer-{version}-windows-x64-with-whisper.zip'
    base = Path(whisper_zip) if whisper_zip else cache / base_name
    if not base.is_file():
        if whisper_zip:
            raise FileNotFoundError(base)
        from scripts.build_model_bundle import download
        download(f'https://github.com/leto0309/VideoSummarizer/releases/download/{version}/{base_name}', base)
    verify(base, base_sha256)
    upstream = Path(ollama_zip) if ollama_zip else cache / OLLAMA_FILE
    if not upstream.is_file():
        if ollama_zip:
            raise FileNotFoundError(upstream)
        print('Downloading pinned official Ollama archive (about 1.47 GB)', flush=True)
        download_archive(OLLAMA_URL, upstream, OLLAMA_BYTES)
    verify(upstream, OLLAMA_SHA256)
    with urllib.request.urlopen(f'https://raw.githubusercontent.com/ollama/ollama/v{OLLAMA_VERSION}/LICENSE', timeout=30) as response:
        license_text = response.read()
    if b'MIT License' not in license_text or b'Ollama' not in license_text:
        raise ValueError('Invalid Ollama license')
    output_dir = ROOT / 'dist'
    output_dir.mkdir(exist_ok=True)
    output = output_dir / f'VideoSummarizer-{version}-windows-x64-with-whisper-ollama.zip'
    if output.exists():
        raise ValueError('Bundle already exists; preserve it and use a fresh checkout')
    partial = output.with_suffix('.zip.part')
    instructions = f'''# {version} Windows 内含 Whisper + Ollama 版

完整解压到可写入的 Windows 10 22H2 / Windows 11 x64 文件夹，双击 VideoSummarizer.exe。无需手动安装 Python。
已包含 Python、Whisper small 和完整官方 Ollama {OLLAMA_VERSION} Windows x64 程序及运行库。首次配置会跳过 Ollama 程序下载；Whisper 转录不必访问 Hugging Face。
首次配置默认跳过 CUDA 库，语音转录默认 CPU int8。GPU 加速可稍后双击 install-gpu.bat 单独安装，带下载进度、20 分钟总时限和取消按钮；失败不影响 CPU 模式。
仍需在首次同意后下载其他 Python 依赖、FFmpeg、Node.js 和 Qwen 摘要模型。本包不是完全离线包，也不保证所有网络均可完成这些剩余下载。
默认简体中文，页面和摘要可分别切换简体中文、繁體中文或 English。已有摘要可生成其他语言版本，保留原始 SRT、摘要和时间戳。
请至少预留 15 GB 可用空间，完整解压并保留 tools/ollama 下所有 DLL 和许可文件。旧程序仍在后台时，先正常停止旧版服务或重启 Windows，再打开新文件夹；共用端口 8501 / 11435。
原版 Ollama ZIP：{OLLAMA_URL}
Ollama ZIP SHA256：{OLLAMA_SHA256}
原始 Ollama MIT 许可在 vendor-notices/ollama/LICENSE.txt，其他组件许可保留在 tools/ollama 原始目录。OLLAMA_BUNDLE.json 记录上游来源、版本和每个文件的哈希。
本包不含用户媒体、摘要、日志、语言偏好、cookies、密钥或个人模型缓存；所有模型推理在本机进行，Ollama cloud 已禁用。
'''
    with zipfile.ZipFile(base) as baseline, zipfile.ZipFile(upstream) as vendor:
        validate_base(baseline, version)
        validate_ollama(vendor)
        file_hashes = {}
        with zipfile.ZipFile(partial, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as package:
            for info in baseline.infolist():
                if info.is_dir():
                    continue
                if info.filename == 'VideoSummarizer/README.md':
                    package.writestr(info.filename, instructions.encode('utf-8') + b'\n---\n\n' + baseline.read(info))
                elif info.filename == 'VideoSummarizer/WHISPER-EDITION.md':
                    package.writestr(info.filename, instructions)
                elif info.filename == 'VideoSummarizer/PORTABLE_BUILD.json':
                    package.writestr(info.filename, json.dumps(portable_record(
                        json.loads(baseline.read(info)), version, 'windows-x64-with-whisper-ollama'), indent=2))
                else:
                    copy_entry(baseline, info, package, info.filename)
            for info in vendor.infolist():
                if not info.is_dir():
                    file_hashes[info.filename] = copy_entry(vendor, info, package, 'VideoSummarizer/tools/ollama/' + info.filename)
            package.writestr('VideoSummarizer/OLLAMA-EDITION.md', instructions)
            package.writestr('VideoSummarizer/vendor-notices/ollama/LICENSE.txt', license_text)
            record = {'version': version, 'edition': 'windows-x64-with-whisper-ollama',
                      'base_with_whisper_sha256': base_sha256, 'ollama_version': OLLAMA_VERSION,
                      'ollama_archive_url': OLLAMA_URL, 'ollama_archive_sha256': OLLAMA_SHA256,
                      'files_sha256': file_hashes, 'other_dependencies': 'download after first-launch consent'}
            package.writestr('VideoSummarizer/OLLAMA_BUNDLE.json', json.dumps(record, indent=2))
    if partial.stat().st_size >= ASSET_LIMIT:
        raise ValueError('Release asset exceeds GitHub 2 GiB limit; preserve partial build')
    with zipfile.ZipFile(partial) as package:
        if package.testzip() is not None:
            raise ValueError('Final bundle ZIP CRC failed')
    partial.replace(output)
    sha256 = digest(output)
    (output_dir / 'WITH_WHISPER_OLLAMA_SHA256SUMS.txt').write_text(f'{sha256}  {output.name}\n', encoding='utf-8')
    print(json.dumps({'zip': str(output), 'bytes': output.stat().st_size, 'sha256': sha256,
                      'ollama_files': len(file_hashes), 'zip_crc': 'passed'}), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--version', required=True)
    parser.add_argument('--base-sha256', required=True)
    parser.add_argument('--whisper-zip', type=Path)
    parser.add_argument('--ollama-zip', type=Path)
    args = parser.parse_args()
    build(args.version, args.base_sha256, args.whisper_zip, args.ollama_zip)
