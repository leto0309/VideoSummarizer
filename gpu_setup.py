"""Explicit optional Whisper CUDA installation; never part of first startup."""
import os
from pathlib import Path
import subprocess
import sys

from setup_text import t

ROOT = Path(__file__).resolve().parent


def installed(root=None):
    """True when this Python has the pinned optional CUDA wheels from requirements-gpu.txt."""
    import importlib.metadata
    for line in (Path(root or ROOT) / 'requirements-gpu.txt').read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        package, version = line.split('==', 1)
        try:
            if importlib.metadata.version(package) != version:
                return False
        except importlib.metadata.PackageNotFoundError:
            return False
    return True


def install_gpu(progress=print):
    from filelock import FileLock, Timeout
    from install_support import install_requirements
    try:
        with FileLock(str(ROOT / '.pipeline.lock'), timeout=0):
            progress(t('gpu_intro'))
            progress(t('gpu_cancel_hint'))
            try:
                install_requirements(ROOT / 'requirements-gpu.lock', timeout=1200, root=ROOT,
                                     progress=progress)
            except (subprocess.CalledProcessError, TimeoutError, OSError) as exc:
                progress(t('gpu_incomplete'))
                raise RuntimeError(t('gpu_failed')) from exc
            progress(t('gpu_done'))
            progress(t('gpu_unverified'))
    except Timeout as exc:
        raise RuntimeError(t('gpu_busy')) from exc


def confirmed(read=input):
    """The source edition's install-gpu.bat asks here, in the page language."""
    try:
        return read(t('gpu_confirm')).strip().upper() == 'Y'
    except EOFError:
        return False


if __name__ == '__main__':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    from startup_lock import StartupMutex
    if '--ask' in sys.argv[1:] and not confirmed():
        print(t('gpu_cancelled'), flush=True)
        sys.exit(1)
    try:
        with StartupMutex():
            install_gpu()
    except KeyboardInterrupt:
        print(t('gpu_cancelled'), flush=True)
        sys.exit(1)
