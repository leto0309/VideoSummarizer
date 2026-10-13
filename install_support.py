"""Visible, bounded project-local installers. No system PATH or global installs."""
import hashlib
import os
from pathlib import Path
import queue
import re
import subprocess
import sys
import threading
import time

from logfiles import rotate

ROOT = Path(__file__).resolve().parent


def stop_process(process):
    """Stop only the installer process created by this invocation and its tree."""
    if process.poll() is not None:
        return
    if os.name == 'nt':
        taskkill = Path(os.environ['SystemRoot']) / 'System32/taskkill.exe'
        try:
            subprocess.run([str(taskkill), '/PID', str(process.pid), '/T', '/F'],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                           timeout=15, check=True, creationflags=subprocess.CREATE_NO_WINDOW)
        except (OSError, subprocess.SubprocessError):
            process.kill()
    else:
        process.kill()
    process.wait(timeout=15)


def run_installer(command, *, timeout, root=None, progress=print):
    root = Path(root or ROOT)
    temporary = root / 'tools/install-temp'
    temporary.mkdir(parents=True, exist_ok=True)
    logs = root / 'logs'
    logs.mkdir(exist_ok=True)
    env = {**os.environ, 'TEMP': str(temporary), 'TMP': str(temporary),
           'PYTHONIOENCODING': 'utf-8', 'PYTHONUNBUFFERED': '1', 'PYTHONNOUSERSITE': '1'}
    process = subprocess.Popen(command, cwd=root, env=env, stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT, text=True, encoding='utf-8',
                               errors='replace', bufsize=1)
    lines = queue.Queue()

    def read_output():
        try:
            for line in process.stdout:
                lines.put(line.rstrip('\r\n'))
        finally:
            lines.put(None)

    reader = threading.Thread(target=read_output, daemon=True)
    reader.start()
    started = time.monotonic()
    notice = started
    output_done = False
    try:
        with rotate(logs / 'install.log').open('a', encoding='utf-8') as log:
            while not output_done or process.poll() is None:
                now = time.monotonic()
                if now - started >= timeout:
                    stop_process(process)
                    raise TimeoutError(f'安装超过 {timeout / 60:g} 分钟总时限，已停止本次安装；已有模型和摘要保留。')
                try:
                    line = lines.get(timeout=.25)
                except queue.Empty:
                    line = ''
                if line is None:
                    output_done = True
                elif line:
                    log.write(line + '\n')
                    log.flush()
                    match = re.fullmatch(r'Progress (\d+) of (\d+)', line)
                    if match:
                        current, total = map(int, match.groups())
                        percent = f' ({current / total:.1%})' if total else ''
                        line = f'下载进度：{current / 1024**2:.1f} / {total / 1024**2:.1f} MiB{percent}'
                    progress(line)
                    notice = time.monotonic()
                if now - notice >= 15:
                    progress(f'安装仍在运行，已等待 {now-started:.0f} 秒；总时限 {timeout/60:g} 分钟。')
                    notice = now
            return process.wait()
    except BaseException:
        stop_process(process)
        raise
    finally:
        reader.join(timeout=2)
        process.stdout.close()


def install_requirements(requirements, *, timeout=2700, root=None, progress=print):
    root = Path(root or ROOT)
    command = [sys.executable, '-m', 'pip', 'install', '--only-binary=:all:',
               '--progress-bar', 'raw', '--no-warn-script-location', '--disable-pip-version-check',
               '--timeout', '30', '--retries', '2', '--resume-retries', '2',
               '--cache-dir', str(root / 'tools/pip-cache'),
               '--find-links', str(root / 'wheels'), '-r', str(requirements)]
    code = run_installer(command, timeout=timeout, root=root, progress=progress)
    if code:
        raise subprocess.CalledProcessError(code, command)


def fetch(url, *, attempts=3, timeout=30, session=None, sleep=time.sleep, progress=print):
    """Small metadata request (checksum list, release information) with bounded retries."""
    import requests
    session = session or requests.Session()
    for attempt in range(1, attempts + 1):
        try:
            response = session.get(url, timeout=timeout)
            response.raise_for_status()
            return response
        except requests.RequestException:
            if attempt == attempts:
                raise
            progress(f'连接失败，{5 * attempt} 秒后重试（第 {attempt + 1}/{attempts} 次）：{url}')
            sleep(5 * attempt)


def download_file(url, target, *, sha256, size=None, attempts=4, session=None, sleep=time.sleep, progress=print):
    """Resume a project-owned .part file across attempts; publish only after the SHA256 matches."""
    import requests
    session = session or requests.Session()
    target = Path(target)
    partial = target.with_name(target.name + '.part')
    for attempt in range(1, attempts + 1):
        start = partial.stat().st_size if partial.is_file() else 0
        if size is not None and start >= size:
            break
        try:
            headers = {'Range': f'bytes={start}-'} if start else {}
            with session.get(url, stream=True, timeout=(30, 120), headers=headers) as response:
                if start and response.status_code == 416:
                    break  # Already complete from an earlier attempt; the checksum decides.
                if start and response.status_code == 206 and response.headers.get(
                        'Content-Range', '').startswith(f'bytes {start}-'):
                    mode = 'ab'
                else:
                    # The server ignored the range: start again rather than append the whole file.
                    response.raise_for_status()
                    mode, start = 'wb', 0
                with partial.open(mode) as handle:
                    noticed = start
                    for chunk in response.iter_content(1024**2):
                        handle.write(chunk)
                        if handle.tell() - noticed >= 50 * 1024**2:
                            noticed = handle.tell()
                            progress(f'已下载 {noticed / 1024**2:.0f} MiB：{target.name}')
            break
        except requests.RequestException:
            if attempt == attempts:
                raise
            done = partial.stat().st_size if partial.is_file() else 0
            progress(f'下载中断，{5 * attempt} 秒后从已下载的 {done / 1024**2:.1f} MiB 继续'
                     f'（第 {attempt + 1}/{attempts} 次）：{target.name}')
            sleep(5 * attempt)
    digest = hashlib.sha256()
    with partial.open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024**2), b''):
            digest.update(chunk)
    if digest.hexdigest() != sha256:
        partial.unlink()
        raise RuntimeError(f'{target.name} 的 SHA256 与官方记录不一致，已删除未完成的下载，请重试。')
    partial.replace(target)
    return target
