"""Fixed-purpose URI launcher. No URL text is passed to a shell."""
import ctypes
from ctypes import wintypes
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback
from urllib.parse import urlsplit
import webbrowser

import requests
from launcher import owned_process
from config import PYTHON

ROOT = Path(__file__).resolve().parent
WEB_URL = 'http://127.0.0.1:8501/'
OLLAMA_URL = 'http://127.0.0.1:11435'
URI = 'videosummarizer://open'


def validate_uri(value):
    parsed = urlsplit(value)
    if (parsed.scheme != 'videosummarizer' or parsed.netloc != 'open'
            or parsed.path not in ('', '/') or parsed.query or parsed.fragment):
        raise ValueError('只接受 videosummarizer://open，不接受视频网址或其他指令。')


def log(message):
    folder = ROOT / 'logs'
    folder.mkdir(exist_ok=True)
    with (folder / 'bookmark.log').open('a', encoding='utf-8') as handle:
        handle.write(time.strftime('%Y-%m-%d %H:%M:%S ') + message + '\n')


def project_process(file, executable, json_file=False):
    try:
        data = file.read_text(encoding='utf-8')
        if json_file:
            data = json.loads(data)
            if data.get('root') != str(ROOT):
                return False
            pid = data['pid']
        else:
            pid = int(data.strip())
        return owned_process(pid, executable)
    except (OSError, ValueError, KeyError, TypeError):
        return False


def healthy(session, url):
    try:
        return session.get(url, timeout=2).status_code == 200
    except requests.RequestException:
        return False


def services_ready(session):
    web = healthy(session, WEB_URL + '_stcore/health')
    ollama = healthy(session, OLLAMA_URL + '/api/version')
    if web and not project_process(ROOT / 'logs' / 'streamlit.pid', PYTHON):
        raise RuntimeError('8501 端口的服务无法确认属于本项目；请查看现有进程。')
    if ollama and not project_process(ROOT / 'logs' / 'ollama-owner.json',
                                     ROOT / 'tools' / 'ollama' / 'ollama.exe', True):
        raise RuntimeError('11435 端口的服务无法确认属于本项目；不使用未知模型服务。')
    return web and ollama


class StartupMutex:
    """Serialize bookmark clicks in this user's Windows session."""
    def __enter__(self):
        kernel = ctypes.windll.kernel32
        kernel.CreateMutexW.argtypes = [wintypes.LPVOID, wintypes.BOOL, wintypes.LPCWSTR]
        kernel.CreateMutexW.restype = wintypes.HANDLE
        kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        kernel.WaitForSingleObject.restype = wintypes.DWORD
        kernel.ReleaseMutex.argtypes = [wintypes.HANDLE]
        kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        name = 'Local\\VideoSummarizerBookmark-' + hashlib.sha256(str(ROOT).encode()).hexdigest()[:16]
        self.kernel = kernel
        self.handle = kernel.CreateMutexW(None, False, name)
        if not self.handle:
            raise ctypes.WinError()
        status = kernel.WaitForSingleObject(self.handle, 300000)
        if status not in (0, 0x80):
            kernel.CloseHandle(self.handle)
            self.handle = None
            raise RuntimeError('另一个启动正在进行；等待超时，请查看 logs/bookmark.log。')
        return self

    def __exit__(self, *args):
        self.kernel.ReleaseMutex(self.handle)
        self.kernel.CloseHandle(self.handle)


def open_on_demand(session, launch, open_page, deadline_seconds=240):
    if services_ready(session):
        log('服务已在运行，直接打开网页。')
        open_page(WEB_URL)
        return
    owner = ROOT / 'logs' / 'bookmark-service.json'
    process = None
    if project_process(owner, PYTHON, True):
        log('先前的背景启动器仍在运行，等待服务就绪。')
    else:
        # A manual start.bat may already be starting; don't race it.
        pending_web = project_process(ROOT / 'logs' / 'streamlit.pid', PYTHON)
        if pending_web and not healthy(session, WEB_URL + '_stcore/health'):
            raise RuntimeError('已有网页进程未就绪。请关闭旧 start.bat 窗口后重试。')
        log('启动背景服务；初始化可能需要约两分钟。')
        process = launch()
        owner.write_text(json.dumps({'root': str(ROOT), 'pid': process.pid}), encoding='utf-8')
    deadline = time.monotonic() + deadline_seconds
    while time.monotonic() < deadline:
        if services_ready(session):
            log('服务已就绪，打开网页。')
            open_page(WEB_URL)
            return
        if process is not None and process.poll() is not None:
            raise RuntimeError('背景启动器已退出，请查看 logs/startup.log。')
        time.sleep(.5)
    raise RuntimeError('等待服务超时，请查看 logs/startup.log 和 logs/bookmark.log。')


def launch_service():
    with (ROOT / 'logs' / 'bookmark-service.log').open('a', encoding='utf-8') as output:
        return subprocess.Popen([str(PYTHON), '-u', str(ROOT / 'launcher.py'), '--headless'],
                                cwd=ROOT, stdin=subprocess.DEVNULL, stdout=output, stderr=output,
                                env={**os.environ, 'PYTHONIOENCODING': 'utf-8', 'OLLAMA_NO_CLOUD': '1'},
                                creationflags=subprocess.CREATE_NO_WINDOW)


def open_chrome(url):
    # Browser choice is fixed at installation; protocol text never becomes a command.
    settings = ROOT / 'bookmark-settings.json'
    if settings.is_file():
        chrome = Path(json.loads(settings.read_text(encoding='utf-8'))['chrome'])
        if chrome.is_file() and chrome.name.lower() == 'chrome.exe':
            subprocess.Popen([str(chrome), url], stdin=subprocess.DEVNULL,
                             creationflags=subprocess.CREATE_NO_WINDOW)
            return
    webbrowser.open(url)


def main():
    if len(sys.argv) != 2:
        raise ValueError('此启动器只接受一个固定协议链接。')
    validate_uri(sys.argv[1])
    log('收到启动链接，开始检查；若重复点击，等待前一次启动完成。')
    session = requests.Session()
    session.trust_env = False
    with StartupMutex():
        open_on_demand(session, launch_service, open_chrome)


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        log(traceback.format_exc())
        ctypes.windll.user32.MessageBoxW(None, str(exc), 'VideoSummarizer 启动失败', 0x10)
        sys.exit(1)
