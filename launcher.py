"""Project-owned Ollama service on a separate loopback port; cloud disabled."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback
from datetime import datetime
import requests
from config import ROOT, MODELS, TOOLS, OLLAMA_URL, default_model
from logfiles import rotate


def owned_process(pid, executable):
    if os.name != 'nt':
        return False
    import ctypes
    from ctypes import wintypes
    kernel = ctypes.windll.kernel32
    kernel.OpenProcess.restype = wintypes.HANDLE
    kernel.QueryFullProcessImageNameW.argtypes = [wintypes.HANDLE, wintypes.DWORD,
                                                wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)]
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    handle = kernel.OpenProcess(0x1000, False, int(pid))
    if not handle:
        return False
    try:
        buffer = ctypes.create_unicode_buffer(32768)
        length = wintypes.DWORD(len(buffer))
        return bool(kernel.QueryFullProcessImageNameW(handle, 0, buffer, ctypes.byref(length))) and (
            Path(buffer.value).resolve() == Path(executable).resolve())
    finally:
        kernel.CloseHandle(handle)


def server_env():
    return {**os.environ, 'OLLAMA_HOST': '127.0.0.1:11435', 'OLLAMA_NO_CLOUD': '1',
            'OLLAMA_MODELS': str(MODELS / 'ollama'), 'OLLAMA_CONTEXT_LENGTH': '4096',
            'OLLAMA_NUM_PARALLEL': '1', 'OLLAMA_MAX_LOADED_MODELS': '1',
            'OLLAMA_KEEP_ALIVE': '0', 'OLLAMA_NOPRUNE': '1',
            'USERPROFILE': str(TOOLS / 'profile')}


def ensure_server(progress=lambda message: None):
    logs = ROOT / 'logs'
    logs.mkdir(exist_ok=True)
    ownerfile = logs / 'ollama-owner.json'
    session = requests.Session()
    session.trust_env = False
    try:
        response = session.get(OLLAMA_URL + '/api/version', timeout=3)
        response.raise_for_status()
        running = True
    except requests.RequestException:
        running = False
    if running:
        owner = json.loads(ownerfile.read_text()) if ownerfile.is_file() else {}
        if owner.get('root') != str(ROOT) or not owned_process(owner.get('pid', 0), TOOLS / 'ollama' / 'ollama.exe'):
            raise RuntimeError('11435 端口已有其他服务，请先释放此端口；不使用未知 Ollama 服务。')
        progress('Ollama 已在运行，已确认属于本项目。')
        return
    executable = TOOLS / 'ollama' / 'ollama.exe'
    if not executable.is_file():
        raise RuntimeError('缺少便携式 Ollama，请运行 setup.bat')
    progress('正在启动本机 Ollama；GPU 初始化可能需要约 1–2 分钟，请保持窗口开启。')
    profile = TOOLS / 'profile' / '.ollama'
    profile.mkdir(parents=True, exist_ok=True)
    (profile / 'server.json').write_text('{"disable_ollama_cloud": true}', encoding='utf-8')
    with (logs / 'ollama.log').open('w', encoding='utf-8') as log:
        process = subprocess.Popen([str(executable), 'serve'], cwd=ROOT, env=server_env(),
                                    stdout=log, stderr=log, stdin=subprocess.DEVNULL,
                                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
    ownerfile.write_text(json.dumps({'root': str(ROOT), 'pid': process.pid, 'cloud_disabled': True}), encoding='utf-8')
    started = time.monotonic()
    last_notice = started
    for _ in range(120):
        if process.poll() is not None:
            raise RuntimeError('Ollama 启动失败，请检查 logs/ollama.log')
        try:
            response = session.get(OLLAMA_URL + '/api/version', timeout=2)
            if response.ok:
                progress(f'Ollama 已就绪，启动等待 {time.monotonic()-started:.0f} 秒。')
                return
        except requests.RequestException:
            pass
        if time.monotonic() - last_notice >= 15:
            progress(f'仍在等待 Ollama 初始化，已等待 {time.monotonic()-started:.0f} 秒。')
            last_notice = time.monotonic()
        time.sleep(.5)
    raise RuntimeError('Ollama 启动超时')


def pull(model=None):
    from config import ALLOWED_MODELS
    model = model or default_model()
    if model not in ALLOWED_MODELS:
        raise ValueError('只能下载核准的本机模型')
    ensure_server()
    # A model copied from another computer must not need the model registry again.
    session = requests.Session()
    session.trust_env = False
    response = session.get(OLLAMA_URL + '/api/tags', timeout=10)
    response.raise_for_status()
    if model in [item.get('name') for item in response.json().get('models', [])]:
        print(f'已找到本机摘要模型 {model}，跳过下载。', flush=True)
        return
    subprocess.run([str(TOOLS / 'ollama' / 'ollama.exe'), 'pull', model],
                   env=server_env(), check=True)


def startup_status(message):
    line = datetime.now().strftime('%Y-%m-%d %H:%M:%S') + ' ' + message
    print(line, flush=True)
    logs = ROOT / 'logs'
    logs.mkdir(exist_ok=True)
    with rotate(logs / 'startup.log').open('a', encoding='utf-8') as handle:
        handle.write(line + '\n')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--serve-only', action='store_true')
    parser.add_argument('--pull', action='store_true')
    parser.add_argument('--model')
    parser.add_argument('--headless', action='store_true', help='Start without automatically opening a browser')
    args = parser.parse_args()
    startup_status('正在检查 VideoSummarizer 启动环境。')
    ensure_server(progress=startup_status)
    if args.pull:
        pull(args.model)
    elif not args.serve_only:
        pidfile = ROOT / 'logs' / 'streamlit.pid'
        session = requests.Session()
        session.trust_env = False
        try:
            pid = int(pidfile.read_text().strip()) if pidfile.is_file() else 0
        except (OSError, ValueError):
            pid = 0
        try:
            response = session.get('http://127.0.0.1:8501/_stcore/health', timeout=3)
            if response.ok:
                if not owned_process(pid, sys.executable):
                    raise RuntimeError('8501 端口已有未知服务；不打开、不停止其他服务。')
                if not args.headless:
                    import webbrowser
                    webbrowser.open('http://127.0.0.1:8501')
                startup_status('网页已在运行：http://127.0.0.1:8501')
                sys.exit(0)
        except requests.RequestException:
            pass
        startup_status('正在启动本机网页服务。')
        with rotate(ROOT / 'logs' / 'streamlit.log').open('a', encoding='utf-8') as web_out, \
             rotate(ROOT / 'logs' / 'streamlit-error.log').open('a', encoding='utf-8') as web_err:
            process = subprocess.Popen([sys.executable, '-m', 'streamlit', 'run', str(ROOT / 'app.py'),
                        '--server.address=127.0.0.1', '--server.port=8501',
                        '--browser.gatherUsageStats=false',
                        '--server.showEmailPrompt=false',
                        '--server.headless=' + ('true' if args.headless else 'false')],
                        cwd=ROOT, stdout=web_out, stderr=web_err, stdin=subprocess.DEVNULL)
        pidfile.write_text(str(process.pid), encoding='utf-8')
        for _ in range(40):
            if process.poll() is not None:
                raise RuntimeError('网页进程退出；请查看 logs/streamlit-error.log。')
            try:
                response = session.get('http://127.0.0.1:8501/_stcore/health', timeout=2)
                if response.ok:
                    startup_status('启动成功：http://127.0.0.1:8501；保持此启动进程运行。')
                    break
            except requests.RequestException:
                pass
            time.sleep(.5)
        else:
            raise RuntimeError('网页健康检查超时；请查看 logs/streamlit-error.log。')
        sys.exit(process.wait())


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        startup_status('启动失败：' + str(exc))
        with rotate(ROOT / 'logs' / 'startup.log').open('a', encoding='utf-8') as handle:
            handle.write(traceback.format_exc() + '\n')
        sys.exit(1)
