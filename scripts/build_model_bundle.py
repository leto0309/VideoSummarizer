"""Add pinned public Whisper weights to a checksum-verified portable release."""
import argparse
import hashlib
import json
import re
from pathlib import Path
import shutil
import stat
import sys
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app_version import RELEASE_TAG, portable_record, validate_packaged_version, validate_release_version
REVISION = '536b0662742c02347bc0e980a01041f333bce120'
FILES = {
    'config.json': 'b55496ac7940a7ae47d2c01eab40edfd8701feec1229d9cce3b40014383fb828',
    'model.bin': '3e305921506d8872816023e4c273e75d2419fb89b24da97b4fe7bce14170d671',
    'tokenizer.json': 'fb7b63191e9bb045082c79fd742a3106a12c99513ab30df4a0d47fa6cb6fd0ab',
    'vocabulary.txt': '34ce3fe1c5041027b3f8d42912270993f986dbc4bb34cf27f951e34a1e453913',
}
MODEL_BASE = f'https://huggingface.co/Systran/faster-whisper-small/resolve/{REVISION}/'


def digest(path):
    result = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024**2), b''):
            result.update(chunk)
    return result.hexdigest()


def verify(path, expected):
    if digest(path) != expected:
        raise ValueError(f'SHA256 mismatch: {Path(path).name}')


def download(url, target):
    target.parent.mkdir(parents=True, exist_ok=True)
    partial = target.with_suffix(target.suffix + '.part')
    print(f'Downloading {target.name}', flush=True)
    with urllib.request.urlopen(url, timeout=120) as response, partial.open('wb') as handle:
        shutil.copyfileobj(response, handle, length=1024**2)
    partial.replace(target)


def extract_base(archive, destination):
    with zipfile.ZipFile(archive) as package:
        for entry in package.infolist():
            parts = Path(entry.filename).parts
            if (not parts or parts[0] != 'VideoSummarizer'
                    or not (destination / entry.filename).resolve().is_relative_to(destination.resolve())
                    or stat.S_ISLNK(entry.external_attr >> 16)):
                raise ValueError('Unsafe portable archive path')
            if (len(parts) > 1 and parts[1] != 'runtime'
                    and (any(part in {'.git', '.venv', 'models', 'logs', 'outputs', 'temp'} for part in parts)
                         or parts[-1] in {'language-settings.json', 'bookmark-settings.json', 'portable-ready.json'})):
                raise ValueError('Unexpected private data in base archive')
        package.extractall(destination)


def build(portable_zip=None, model_dir=None, version=RELEASE_TAG, base_sha256=None):
    if not re.fullmatch(r'v\d+\.\d+\.\d+(?:-[A-Za-z0-9.-]+)?', version):
        raise ValueError('Invalid release version')
    # No built-in fallback: the caller supplies the digest of the portable ZIP it just verified.
    if not base_sha256 or not re.fullmatch(r'[0-9a-f]{64}', base_sha256):
        raise ValueError('A verified portable base SHA256 is required')
    validate_release_version(version)
    base_name = f'VideoSummarizer-{version}-windows-x64.zip'
    cache = ROOT / 'build' / 'with-whisper-cache'
    cache.mkdir(parents=True, exist_ok=True)
    base = Path(portable_zip) if portable_zip else cache / base_name
    if not base.exists():
        download(f'https://github.com/leto0309/VideoSummarizer/releases/download/{version}/' + base_name, base)
    verify(base, base_sha256)
    destination = ROOT / 'build' / ('with-whisper-' + version)
    if destination.exists():
        raise ValueError('Bundle staging already exists; preserve it and use a fresh checkout')
    destination.mkdir()
    extract_base(base, destination)
    bundle = destination / 'VideoSummarizer'
    record = json.loads((bundle / 'PORTABLE_BUILD.json').read_text(encoding='utf-8'))
    if record.get('version') != version:
        raise ValueError('Portable base version does not match requested release')
    validate_packaged_version((bundle / 'app_version.py').read_text(encoding='utf-8'), version)
    (bundle / 'PORTABLE_BUILD.json').write_text(json.dumps(
        portable_record(record, version, 'windows-x64-with-whisper'), indent=2), encoding='utf-8')
    model_target = bundle / 'models' / 'whisper' / 'small'
    model_target.mkdir(parents=True)
    for name, expected_file_hash in FILES.items():
        source = Path(model_dir) / name if model_dir else cache / name
        if not source.exists():
            if model_dir:
                raise FileNotFoundError(source)
            download(MODEL_BASE + name, source)
        verify(source, expected_file_hash)
        shutil.copyfile(source, model_target / name)
    notices = bundle / 'vendor-notices' / 'whisper'
    notices.mkdir(parents=True)
    for name, url in (
        ('MODEL-CARD.md', MODEL_BASE + 'README.md'),
        ('LICENSE.txt', 'https://raw.githubusercontent.com/openai/whisper/main/LICENSE'),
    ):
        download(url, notices / name)
    instructions = f'''# {version} Windows 内含 Whisper 版

完整解压到可写入的 Windows 10 22H2 / Windows 11 x64 文件夹，双击 VideoSummarizer.exe。无需安装系统 Python。
Whisper small 已包含在 models/whisper/small，转录无需访问 Hugging Face。首次仍需同意下载其他依赖、Ollama、Node.js 和摘要模型；这不是全部依赖预装的离线包。
首次配置默认跳过 CUDA 库，语音转录默认 CPU int8。GPU 加速可稍后双击 install-gpu.bat 单独安装，可查看下载进度或取消，20 分钟总时限，失败不影响 CPU 模式。
默认简体中文。页面和摘要可分别选择简体中文、繁體中文或 English。已有摘要可保留原版并生成其他语言版本；原始字幕和时间戳不改写。英文版本需要本机模型处理。
请使用独立文件夹。旧版仍在运行时，先正常关闭旧版服务或重启 Windows，再打开新版；两份程序共用 8501 / 11435 端口。
Whisper 来源：https://huggingface.co/Systran/faster-whisper-small
固定版本：{REVISION}。四个模型文件逐一校验 SHA256，见 WHISPER_BUNDLE.json。原始模型卡和 MIT 许可在 vendor-notices/whisper。
本包不含用户的媒体、摘要、日志、语言偏好、书签配置或凭证。其他依赖需要联网，GPU 兼容性与速度因电脑而异。
'''
    (bundle / 'WHISPER-EDITION.md').write_text(instructions, encoding='utf-8')
    readme = bundle / 'README.md'
    readme.write_text(instructions + '\n\n---\n\n' + readme.read_text(encoding='utf-8'), encoding='utf-8')
    third_party = bundle / 'THIRD_PARTY_NOTICES.md'
    third_party.write_text('This additional with-Whisper edition bundles the four public Whisper small files, '
                          'with their original MIT license and model card in vendor-notices/whisper. '
                          'The standard portable edition described below remains model-free.\n\n'
                          + third_party.read_text(encoding='utf-8'), encoding='utf-8')
    record = {'version': version, 'edition': 'windows-x64-with-whisper', 'base_sha256': base_sha256,
              'whisper_repository': 'Systran/faster-whisper-small', 'revision': REVISION,
              'files_sha256': FILES, 'other_dependencies': 'download after first-launch consent'}
    (bundle / 'WHISPER_BUNDLE.json').write_text(json.dumps(record, indent=2), encoding='utf-8')
    output_dir = ROOT / 'dist'
    output_dir.mkdir(exist_ok=True)
    output = output_dir / f'VideoSummarizer-{version}-windows-x64-with-whisper.zip'
    with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=1) as package:
        for file in sorted(bundle.rglob('*')):
            if file.is_file():
                package.write(file, file.relative_to(destination).as_posix())
    sha256 = digest(output)
    (output_dir / 'WITH_WHISPER_SHA256SUMS.txt').write_text(f'{sha256}  {output.name}\n', encoding='utf-8')
    print(json.dumps({'zip': str(output), 'bytes': output.stat().st_size, 'sha256': sha256}), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--portable-zip', type=Path)
    parser.add_argument('--model-dir', type=Path)
    parser.add_argument('--version', default=RELEASE_TAG)
    parser.add_argument('--base-sha256', required=True)
    args = parser.parse_args()
    build(args.portable_zip, args.model_dir, args.version, args.base_sha256)
