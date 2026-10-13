"""Prepare Whisper files once, before any CUDA/CPU inference attempts."""
import argparse
import json
import os
from pathlib import Path
import re
import sys
import traceback
from config import MODELS, ROOT
from logfiles import rotate

REPO = 'Systran/faster-whisper-small'


class ModelUnavailableError(RuntimeError):
    pass


def complete(folder):
    """Check required local files; native loading validates the actual weights."""
    try:
        for name in ('model.bin', 'config.json', 'tokenizer.json'):
            if not (folder / name).is_file() or (folder / name).stat().st_size == 0:
                return False
        if not any((folder / name).is_file() and (folder / name).stat().st_size
                   for name in ('vocabulary.txt', 'vocabulary.json')):
            return False
        for name in ('config.json', 'tokenizer.json'):
            if not isinstance(json.loads((folder / name).read_text(encoding='utf-8')), dict):
                return False
        return True
    except (OSError, ValueError):
        return False


def cached_model(model='small'):
    if model != 'small':
        raise ValueError('目前模型准备功能支持 Whisper small。')
    base = MODELS / 'whisper'
    # Flat folder supports offline transfer without cache symlinks or metadata.
    if complete(base / model):
        return base / model
    cache = base / ('models--' + REPO.replace('/', '--'))
    try:
        revision = (cache / 'refs' / 'main').read_text(encoding='utf-8').strip()
        if re.fullmatch(r'[0-9a-f]{40}', revision) and complete(cache / 'snapshots' / revision):
            return cache / 'snapshots' / revision
    except OSError:
        pass
    snapshots = cache / 'snapshots'
    if snapshots.is_dir():
        for folder in sorted(snapshots.iterdir(), reverse=True):
            if re.fullmatch(r'[0-9a-f]{40}', folder.name) and complete(folder):
                return folder
    return None


def ensure_model(model='small', progress=lambda message: None):
    existing = cached_model(model)
    if existing:
        return existing
    base = MODELS / 'whisper'
    base.mkdir(parents=True, exist_ok=True)
    from filelock import FileLock
    with FileLock(str(base / '.download.lock'), timeout=600):
        existing = cached_model(model)
        if existing:
            return existing
        # Hub reads environment variables at import time. No implicit account token.
        os.environ['HF_HOME'] = str(MODELS / 'huggingface')
        os.environ['HF_HUB_DISABLE_TELEMETRY'] = '1'
        os.environ['HF_HUB_DISABLE_IMPLICIT_TOKEN'] = '1'
        os.environ.setdefault('HF_HUB_ETAG_TIMEOUT', '30')
        os.environ.setdefault('HF_HUB_DOWNLOAD_TIMEOUT', '120')
        progress('下载 Whisper small（约 464 MiB）；来源：huggingface.co，完成后可离线转录。')
        try:
            from huggingface_hub import snapshot_download
            folder = Path(snapshot_download(
                REPO, cache_dir=str(base), endpoint='https://huggingface.co', token=False,
                allow_patterns=['config.json', 'preprocessor_config.json', 'model.bin',
                                'tokenizer.json', 'vocabulary.*'],
                max_workers=2, etag_timeout=30))
            if not complete(folder):
                raise RuntimeError('下载的模型缺少必要文件，请重试。')
            return folder
        except Exception as exc:
            logs = ROOT / 'logs'
            logs.mkdir(exist_ok=True)
            with rotate(logs / 'whisper-download.log').open('a', encoding='utf-8') as handle:
                traceback.print_exc(file=handle)
            raise ModelUnavailableError(
                'Whisper small 模型尚未准备完成：下载失败或 Hugging Face 连接超时。'
                '\n这不是 CUDA/CPU 运算错误，切换 CPU 不会修复模型下载。'
                '\n请检查能否开启 https://huggingface.co/Systran/faster-whisper-small，'
                '再执行 prepare-whisper.bat 重试。'
                '\n无法连接时，可从另一台已完成下载的电脑复制 models/whisper，'
                '或将官方模型必要文件放到 models/whisper/small。'
                '\n详细原因记录于 logs/whisper-download.log；已下载的文件会保留。'
            ) from exc


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    if args.check:
        folder = cached_model()
        print('Whisper small 已准备完成。' if folder else 'Whisper small 尚未准备完成。')
        return 0 if folder else 1
    try:
        folder = ensure_model(progress=lambda message: print(message, flush=True))
        print(f'Whisper small 已准备完成：{folder}', flush=True)
        return 0
    except ModelUnavailableError as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
