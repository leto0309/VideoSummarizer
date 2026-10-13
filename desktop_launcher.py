"""Portable bootstrap. All commands use the bundled interpreter, never PATH Python."""
import argparse
import importlib.metadata
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import traceback

from logfiles import rotate

ROOT = Path(__file__).resolve().parent
READY = ROOT / 'portable-ready.json'
# update-ytdlp.bat may install a newer build than the tested pin when platforms change.
AT_LEAST = {'yt-dlp', 'yt-dlp-ejs'}


def version_key(text):
    return tuple(int(part) for part in re.findall(r'\d+', text))


def dependencies_ready():
    requirements = ROOT / 'requirements.txt'
    for line in requirements.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        package, version = line.split('==', 1)
        package = package.split('[', 1)[0]
        try:
            installed = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            return False
        if installed != version and not (package in AT_LEAST and version_key(installed) >= version_key(version)):
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


def needed_sources():
    """Download sites the coming first-run setup will contact, for the network summary."""
    needed = ['pypi'] if not dependencies_ready() else []
    if not (ROOT / 'tools/node/node.exe').is_file():
        needed.append('node')
    if not (ROOT / 'tools/ollama/ollama.exe').is_file():
        needed.append('github')
    if not (ROOT / 'models/ollama/manifests/registry.ollama.ai/library/qwen3-vl').is_dir():
        needed.append('ollama')
    if not (ROOT / 'models/whisper/small/model.bin').is_file():
        needed.append('huggingface')
    return needed


def prepare():
    print('首次配置：正在安装视频与 AI 依赖，可能需要数 GB 下载与空间。', flush=True)
    if not dependencies_ready():
        from install_support import install_requirements
        from network_check import explain
        try:
            install_requirements(ROOT / 'requirements.txt', root=ROOT,
                                 progress=lambda message: print(message, flush=True))
        except (subprocess.CalledProcessError, TimeoutError, OSError) as exc:
            explain(exc, 'pypi')
            raise
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
    from faster_whisper import WhisperModel  # noqa: F401 -- the self-test checks that Whisper imports
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
    # The native window appends its whole output to desktop.log on every start.
    rotate(ROOT / 'logs' / 'desktop.log')
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
                from network_check import check
                check(needed=needed_sources())
                prepare()
    if needs_setup():
        raise RuntimeError('需要首次配置，请重新打开 VideoSummarizer.exe 并同意下载。')
    from bookmark_launcher import StartupMutex, open_on_demand, launch_service, open_chrome
    import requests
    session = requests.Session()
    session.trust_env = False
    with StartupMutex():
        print('正在启动本机服务；初始化可能需要约两分钟。', flush=True)
        open_on_demand(session, launch_service, open_chrome)
    print('网页已打开。关闭进度窗口不会停止背景服务。', flush=True)


if __name__ == '__main__':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    os.environ['PYTHONNOUSERSITE'] = '1'
    os.environ['OLLAMA_NO_CLOUD'] = '1'
    try:
        install_temp = ROOT / 'tools' / 'install-temp'
        install_temp.mkdir(parents=True, exist_ok=True)
        os.environ['TEMP'] = os.environ['TMP'] = str(install_temp)
        main()
    except Exception as exc:
        # The traceback ends with the source-specific advice; then re-check that one site.
        traceback.print_exc()
        if getattr(exc, 'download_source', None):
            from network_check import check
            check([exc.download_source])
        sys.exit(1)
