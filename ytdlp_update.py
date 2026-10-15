"""Update or restore the yt-dlp download component in this project's own Python."""
import argparse
import importlib.metadata
import os
from pathlib import Path
import subprocess
import sys

from setup_text import t

ROOT = Path(__file__).resolve().parent
LOCK = ROOT / '.pipeline.lock'


def installed():
    try:
        return importlib.metadata.version('yt-dlp')
    except importlib.metadata.PackageNotFoundError:
        return t('not_installed')


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
            progress(t('ytdlp_restoring') if restore else t('ytdlp_updating'))
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
            progress(t('ytdlp_restored' if restore else 'ytdlp_updated', before=before, after=installed()))
    except Timeout as exc:
        raise RuntimeError(t('ytdlp_busy')) from exc


def ask(read=input, show=print):
    """The menu update-ytdlp.bat shows, in the page language. Returns 'U', 'R' or 'C'."""
    for key in ('ytdlp_intro', 'ytdlp_choice_update', 'ytdlp_choice_restore'):
        show(t(key))
    show(t('ytdlp_current', version=installed()))
    while True:
        try:
            choice = read(t('ytdlp_prompt')).strip().upper()
        except EOFError:
            return 'C'
        if choice in ('U', 'R', 'C'):
            return choice


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--restore', action='store_true')
    parser.add_argument('--ask', action='store_true')
    args = parser.parse_args()
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    restore = args.restore
    if args.ask:
        choice = ask()
        if choice == 'C':
            print(t('ytdlp_cancelled'), flush=True)
            sys.exit(1)
        restore = choice == 'R'
    try:
        update(restore, progress=lambda message: print(message, flush=True))
    except Exception as exc:
        print(t('unfinished', error=exc), flush=True)
        for note in getattr(exc, '__notes__', []):
            print(note, flush=True)
        sys.exit(1)
