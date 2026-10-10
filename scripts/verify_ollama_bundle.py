"""Verify bundled files and start only this Ollama on an isolated loopback port."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import time
import urllib.request


def verify_bundle(root):
    record = json.loads((root / 'OLLAMA_BUNDLE.json').read_text(encoding='utf-8'))
    executable = root / 'tools/ollama/ollama.exe'
    if not executable.is_file() or not record['files_sha256']:
        raise ValueError('Missing bundled Ollama')
    for name, expected in record['files_sha256'].items():
        path = root / 'tools/ollama' / name
        if not path.resolve().is_relative_to((root / 'tools/ollama').resolve()):
            raise ValueError('Unexpected bundled path')
        with path.open('rb') as handle:
            if hashlib.file_digest(handle, 'sha256').hexdigest() != expected:
                raise ValueError('Bundled Ollama file hash mismatch: ' + name)
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        port = sock.getsockname()[1]
    # No existing project service, user profile, models or process is touched.
    profile = root / 'tools/ollama-self-test'
    profile.mkdir(parents=True, exist_ok=False)
    (profile / '.ollama').mkdir()
    (profile / '.ollama/server.json').write_text('{"disable_ollama_cloud":true}', encoding='utf-8')
    environment = {**os.environ, 'OLLAMA_HOST': f'127.0.0.1:{port}', 'OLLAMA_NO_CLOUD': '1',
                   'OLLAMA_MODELS': str(profile / 'models'), 'OLLAMA_NOPRUNE': '1',
                   'USERPROFILE': str(profile)}
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
    with (profile / 'serve.log').open('w', encoding='utf-8') as log:
        process = subprocess.Popen([str(executable), 'serve'], cwd=root, env=environment,
                                   stdout=log, stderr=log, stdin=subprocess.DEVNULL,
                                   creationflags=flags)
        try:
            for _ in range(180):
                if process.poll() is not None:
                    raise RuntimeError('Bundled Ollama exited; see isolated serve.log')
                try:
                    with opener.open(f'http://127.0.0.1:{port}/api/version', timeout=2) as response:
                        actual = json.load(response)['version']
                    if actual != record['ollama_version']:
                        raise ValueError('Unexpected running Ollama version')
                    with opener.open(f'http://127.0.0.1:{port}/api/tags', timeout=2) as response:
                        if json.load(response)['models']:
                            raise ValueError('Unexpected model in isolated self-test')
                    break
                except OSError:
                    time.sleep(.5)
            else:
                raise RuntimeError('Bundled Ollama health check timed out')
        finally:
            process.terminate()
            process.wait(timeout=30)
    print(json.dumps({'ollama_bundle_test': 'passed', 'version': actual,
                      'files_verified': len(record['files_sha256']), 'http_health': True,
                      'isolated_port': port, 'model_download': False}), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('bundle', type=Path)
    verify_bundle(parser.parse_args().bundle.resolve())
