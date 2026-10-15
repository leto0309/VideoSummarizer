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
from setup_text import t

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
        raise ValueError(t('whisper_small_only'))
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
        progress(t('whisper_downloading'))
        try:
            from huggingface_hub import snapshot_download
            folder = Path(snapshot_download(
                REPO, cache_dir=str(base), endpoint='https://huggingface.co', token=False,
                allow_patterns=['config.json', 'preprocessor_config.json', 'model.bin',
                                'tokenizer.json', 'vocabulary.*'],
                max_workers=2, etag_timeout=30))
            if not complete(folder):
                raise RuntimeError(t('whisper_missing_files'))
            return folder
        except Exception as exc:
            logs = ROOT / 'logs'
            logs.mkdir(exist_ok=True)
            with rotate(logs / 'whisper-download.log').open('a', encoding='utf-8') as handle:
                traceback.print_exc(file=handle)
            raise ModelUnavailableError(t('whisper_unavailable')) from exc


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    if args.check:
        folder = cached_model()
        print(t('whisper_ready') if folder else t('whisper_not_ready'))
        return 0 if folder else 1
    try:
        folder = ensure_model(progress=lambda message: print(message, flush=True))
        print(t('whisper_ready_at', folder=folder), flush=True)
        return 0
    except ModelUnavailableError as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
