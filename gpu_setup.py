"""Explicit optional Whisper CUDA installation; never part of first startup."""
import os
from pathlib import Path
import subprocess
import sys

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
            progress('可选 Whisper GPU 加速：将下载 CUDA 运行库，可能超过 1 GB；总时限 20 分钟。')
            progress('可在窗口取消安装；取消或失败后，原有 CPU 模式仍可使用。')
            try:
                install_requirements(ROOT / 'requirements-gpu.txt', timeout=1200, root=ROOT,
                                     progress=progress)
            except (subprocess.CalledProcessError, TimeoutError, OSError) as exc:
                progress('GPU 加速库未安装完成，CPU int8 模式仍可使用。详情请查看 logs/install.log。')
                raise RuntimeError('可选 GPU 安装未完成；请先用 CPU，网络恢复后可再次运行 install-gpu.bat。') from exc
            progress('GPU 运行库安装完成。请在摘要任务结束后重启程序，再选择自动 CUDA → CPU。')
            progress('安装完成不代表显卡兼容性已验证；转录不兼容时仍会回退 CPU。')
    except Timeout as exc:
        raise RuntimeError('摘要任务正在运行，请等待完成后再安装 GPU 加速。') from exc


if __name__ == '__main__':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    from startup_lock import StartupMutex
    try:
        with StartupMutex():
            install_gpu()
    except KeyboardInterrupt:
        print('已取消 GPU 安装。CPU 模式仍可使用。', flush=True)
        sys.exit(1)
