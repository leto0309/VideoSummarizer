"""Update or restore the yt-dlp download component in this project's own Python."""
import argparse
import importlib.metadata
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
LOCK = ROOT / '.pipeline.lock'


def installed():
    try:
        return importlib.metadata.version('yt-dlp')
    except importlib.metadata.PackageNotFoundError:
        return '未安装'


def update(restore=False, progress=print):
    """Newest nightly by default (the project tracks nightly); restore reinstalls the locked, hashed set."""
    from filelock import FileLock, Timeout
    import install_support
    from network_check import explain
    command = [sys.executable, '-m', 'pip', 'install', '--only-binary=:all:', '--progress-bar', 'raw',
               '--no-warn-script-location', '--disable-pip-version-check', '--timeout', '30', '--retries', '2',
               '--cache-dir', str(ROOT / 'tools/pip-cache'), '--upgrade', '--pre', 'yt-dlp[default]']
    try:
        with FileLock(str(LOCK), timeout=0):
            before = installed()
            progress('恢复本版本测试过的 yt-dlp 及其依赖……' if restore else '从 PyPI 更新 yt-dlp 到最新版本……')
            try:
                if restore:
                    # Also returns any dependency the update changed to its locked version.
                    install_support.install_requirements(ROOT / 'requirements.lock', timeout=600, root=ROOT,
                                                         progress=progress)
                elif code := install_support.run_installer(command, timeout=600, root=ROOT, progress=progress):
                    raise subprocess.CalledProcessError(code, command)
            except subprocess.CalledProcessError as error:
                explain(error, 'pypi')
                raise
            # Closing the page leaves the background service running; restarting Windows stops it.
            progress(f'yt-dlp {"已恢复" if restore else "已更新"}：{before} → {installed()}。'
                     '正在运行的网页仍在使用更改前的版本，请重启电脑后再打开 VideoSummarizer，更改才会生效。')
    except Timeout as exc:
        raise RuntimeError('摘要任务正在运行，请等待完成后再更新下载组件。') from exc


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--restore', action='store_true')
    args = parser.parse_args()
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    try:
        update(args.restore, progress=lambda message: print(message, flush=True))
    except Exception as exc:
        print(f'未完成：{exc}', flush=True)
        for note in getattr(exc, '__notes__', []):
            print(note, flush=True)
        sys.exit(1)
