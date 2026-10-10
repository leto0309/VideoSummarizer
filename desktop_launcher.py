"""Portable bootstrap. All commands use the bundled interpreter, never PATH Python."""
import argparse
import importlib.metadata
import json
import os
from pathlib import Path
import subprocess
import sys
import traceback

ROOT = Path(__file__).resolve().parent
READY = ROOT / 'portable-ready.json'


def dependencies_ready():
    requirements = ROOT / 'requirements.txt'
    for line in requirements.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        package, version = line.split('==', 1)
        package = package.split('[', 1)[0]
        try:
            if importlib.metadata.version(package) != version:
                return False
        except importlib.metadata.PackageNotFoundError:
            return False
    return True


def needs_setup():
    if not dependencies_ready():
        return True
    try:
        data = json.loads(READY.read_text(encoding='utf-8'))
        return data.get('version') != 1 or not all((ROOT / path).is_file() for path in (
            'tools/ollama/ollama.exe', 'tools/node/node.exe'))
    except (OSError, ValueError):
        return True


def prepare():
    print('首次配置：正在安裝影片與 AI 依賴，可能需要數 GB 下載與空間。', flush=True)
    if not dependencies_ready():
        from install_support import install_requirements
        install_requirements(ROOT / 'requirements.txt', root=ROOT,
                             progress=lambda message: print(message, flush=True))
    from setup_runtime import setup
    setup()
    READY.write_text(json.dumps({'version': 1}), encoding='utf-8')
    print('首次配置完成。', flush=True)


def self_test():
    """Exercise the packaged interpreter and an actual local HTTP server, no models."""
    import socket
    import time
    import urllib.request
    from config import ffmpeg
    from faster_whisper import WhisperModel
    from streamlit.testing.v1 import AppTest
    app = AppTest.from_file(str(ROOT / 'app.py')).run(timeout=30)
    assert not app.exception, [item.message for item in app.exception]
    subprocess.run([ffmpeg(), '-version'], check=True, stdout=subprocess.DEVNULL)
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        port = sock.getsockname()[1]
    args = [sys.executable, '-m', 'streamlit', 'run', str(ROOT / 'app.py'),
            '--server.address=127.0.0.1', f'--server.port={port}', '--server.headless=true',
            '--server.showEmailPrompt=false', '--browser.gatherUsageStats=false']
    process = subprocess.Popen(args, cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        for _ in range(80):
            if process.poll() is not None:
                raise RuntimeError('Portable Streamlit process exited')
            try:
                opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
                with opener.open(f'http://127.0.0.1:{port}/_stcore/health', timeout=2) as response:
                    assert response.status == 200
                    break
            except OSError:
                time.sleep(.25)
        else:
            raise RuntimeError('Portable HTTP health check timed out')
    finally:
        process.terminate()
        process.wait(timeout=20)
    print(json.dumps({'portable_self_test': 'passed', 'python': sys.version.split()[0],
                      'executable': sys.executable, 'http_health': True, 'ffmpeg': True,
                      'whisper_import': True, 'app_load': True}), flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--setup', action='store_true')
    parser.add_argument('--self-test', action='store_true')
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--install-gpu', action='store_true')
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    if args.check:
        sys.exit(10 if needs_setup() else 0)
    if args.install_gpu:
        if needs_setup():
            raise RuntimeError('请先打开 VideoSummarizer.exe 完成首次配置，再安装可选 GPU 加速。')
        from startup_lock import StartupMutex
        from gpu_setup import install_gpu
        with StartupMutex():
            install_gpu(progress=lambda message: print(message, flush=True))
        return
    if args.setup:
        from startup_lock import StartupMutex
        with StartupMutex():
            if needs_setup():
                prepare()
    if needs_setup():
        raise RuntimeError('需要首次配置，請重新開啟 VideoSummarizer.exe 並同意下載。')
    from bookmark_launcher import StartupMutex, open_on_demand, launch_service, open_chrome
    import requests
    session = requests.Session()
    session.trust_env = False
    with StartupMutex():
        print('正在啟動本機服務；初始化可能需要約兩分鐘。', flush=True)
        open_on_demand(session, launch_service, open_chrome)
    print('網頁已開啟。關閉進度視窗不會停止背景服務。', flush=True)


if __name__ == '__main__':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    os.environ['PYTHONNOUSERSITE'] = '1'
    os.environ['OLLAMA_NO_CLOUD'] = '1'
    try:
        install_temp = ROOT / 'tools' / 'install-temp'
        install_temp.mkdir(parents=True, exist_ok=True)
        os.environ['TEMP'] = os.environ['TMP'] = str(install_temp)
        main()
    except Exception:
        traceback.print_exc()
        sys.exit(1)
