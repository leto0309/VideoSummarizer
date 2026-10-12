from contextlib import contextmanager
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch
import urllib.request

import requests

import desktop_launcher
import install_support
import launcher
import network_check
import setup_runtime

ROOT = Path(__file__).resolve().parents[1]
PAYLOAD = bytes(range(256)) * 4096


@contextmanager
def local_server(handler):
    server = ThreadingHTTPServer(('127.0.0.1', 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f'http://127.0.0.1:{server.server_address[1]}'
    finally:
        server.shutdown()
        server.server_close()


def closed_port_url():
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        return f'http://127.0.0.1:{sock.getsockname()[1]}/'


def offline_opener():
    return urllib.request.build_opener(urllib.request.ProxyHandler({}), network_check._NoRedirect())


def offline_session():
    session = requests.Session()
    session.trust_env = False
    return session


class Quiet(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass


def site_handler():
    class Site(Quiet):
        seen = []

        def do_HEAD(self):
            type(self).seen.append(self.command)
            self.send_response(302 if self.path == '/moved' else 404)
            if self.path == '/moved':
                self.send_header('Location', 'http://192.0.2.1/')  # unroutable: following would time out
            self.end_headers()
    return Site


def range_handler(honour_range=True, drop_first=False):
    class Ranges(Quiet):
        seen = []
        drop = drop_first

        def do_GET(self):
            cls = type(self)
            requested = self.headers.get('Range')
            cls.seen.append(requested)
            start = int(requested[len('bytes='):-1]) if requested and honour_range else 0
            body = PAYLOAD[start:]
            self.send_response(206 if start else 200)
            if start:
                self.send_header('Content-Range', f'bytes {start}-{len(PAYLOAD) - 1}/{len(PAYLOAD)}')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            if cls.drop:
                cls.drop = False
                self.wfile.write(body[:len(body) // 3])
                self.close_connection = True
                return
            self.wfile.write(body)
    return Ranges


class NetworkCheckTests(unittest.TestCase):
    def test_any_response_counts_as_reachable_and_redirects_are_not_followed(self):
        handler = site_handler()
        with local_server(handler) as base:
            missing = network_check.probe(base + '/missing', timeout=5, opener=offline_opener())
            moved = network_check.probe(base + '/moved', timeout=5, opener=offline_opener())
        self.assertEqual((missing['reachable'], missing['status']), (True, 404))
        self.assertEqual((moved['reachable'], moved['status']), (True, 302))
        self.assertEqual(handler.seen, ['HEAD', 'HEAD'])

    def test_refused_connection_is_reported_without_raising(self):
        result = network_check.probe(closed_port_url(), timeout=5, opener=offline_opener())
        self.assertFalse(result['reachable'])
        self.assertEqual(result['error'], '连接被拒绝')

    def test_summary_marks_needed_sites_and_writes_report(self):
        with local_server(site_handler()) as base, tempfile.TemporaryDirectory() as folder, \
             patch.dict(network_check.SOURCES, {'pypi': ('PyPI', 'Python 依赖', (base + '/',)),
                                                'node': ('Node.js 官网', 'Node.js', (closed_port_url(),))}, clear=True):
            lines = []
            network_check.check(['pypi', 'node'], needed=['node'], progress=lines.append,
                                timeout=5, opener=offline_opener(), root=folder)
            report = json.loads((Path(folder) / 'logs/network-check.json').read_text(encoding='utf-8'))
        text = '\n'.join(lines)
        self.assertRegex(text, r'- PyPI：可以连接（[\d.]+ 秒），用于下载 Python 依赖（本次不需要）')
        self.assertRegex(text, r'- Node\.js 官网：无法连接：127\.0\.0\.1 连接被拒绝，用于下载 Node\.js（本次配置需要）')
        self.assertEqual(report['needed'], ['node'])
        self.assertEqual([row['reachable'] for row in report['results']], [True, False])

    def test_check_needs_only_the_standard_library(self):
        result = subprocess.run([sys.executable, '-S', '-c', 'import network_check'], cwd=ROOT,
                                capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_failure_note_names_source_and_keeps_exception_type(self):
        error = subprocess.CalledProcessError(1, 'pip')
        network_check.explain(error, 'pypi')
        network_check.explain(error, 'pypi')
        self.assertIsInstance(error, subprocess.CalledProcessError)
        self.assertEqual(error.download_source, 'pypi')
        self.assertEqual(len(error.__notes__), 1)
        self.assertIn('PyPI', error.__notes__[0])
        self.assertIn('check-network.bat', error.__notes__[0])


class SetupFailureTests(unittest.TestCase):
    def test_dependency_failure_names_pypi_and_does_not_mark_ready(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            with patch.object(desktop_launcher, 'ROOT', root), \
                 patch.object(desktop_launcher, 'READY', root / 'ready.json'), \
                 patch.object(desktop_launcher, 'dependencies_ready', return_value=False), \
                 patch('install_support.install_requirements', side_effect=subprocess.CalledProcessError(1, 'pip')):
                with self.assertRaises(subprocess.CalledProcessError) as caught:
                    desktop_launcher.prepare()
            self.assertIn('PyPI', caught.exception.__notes__[0])
            self.assertFalse((root / 'ready.json').exists())

    def test_node_and_model_failures_name_their_sources(self):
        with tempfile.TemporaryDirectory() as folder:
            tools = Path(folder) / 'tools'
            (tools / 'ollama').mkdir(parents=True)
            (tools / 'ollama/ollama.exe').touch()
            with patch.object(setup_runtime, 'ROOT', Path(folder)), patch.object(setup_runtime, 'TOOLS', tools):
                with patch.object(setup_runtime, 'setup_node', side_effect=requests.ConnectionError('offline')):
                    with self.assertRaises(requests.ConnectionError) as node:
                        setup_runtime.setup()
                with patch.object(setup_runtime, 'setup_node'), \
                     patch('launcher.pull', side_effect=subprocess.CalledProcessError(1, 'ollama pull')):
                    with self.assertRaises(subprocess.CalledProcessError) as model:
                        setup_runtime.setup()
        self.assertIn('Node.js 官网', node.exception.__notes__[0])
        self.assertIn('Ollama 模型库', model.exception.__notes__[0])

    def test_needed_sources_skip_bundled_and_copied_files(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for name in ('tools/ollama/ollama.exe', 'models/whisper/small/model.bin'):
                (root / name).parent.mkdir(parents=True, exist_ok=True)
                (root / name).touch()
            with patch.object(desktop_launcher, 'ROOT', root), \
                 patch.object(desktop_launcher, 'dependencies_ready', return_value=True):
                self.assertEqual(desktop_launcher.needed_sources(), ['node', 'ollama'])
                (root / 'models/ollama/manifests/registry.ollama.ai/library/qwen3-vl').mkdir(parents=True)
                self.assertEqual(desktop_launcher.needed_sources(), ['node'])

    def test_model_already_present_is_not_pulled_again(self):
        for present, pulls in ((True, 0), (False, 1)):
            models = [{'name': 'qwen3-vl:2b-instruct'}] if present else []
            with self.subTest(present=present), patch.object(launcher, 'ensure_server'), \
                 patch.object(launcher.requests, 'Session') as session, \
                 patch.object(launcher.subprocess, 'run') as run:
                session.return_value.get.return_value.json.return_value = {'models': models}
                launcher.pull('qwen3-vl:2b-instruct')
                self.assertEqual(run.call_count, pulls)


class ResumableDownloadTests(unittest.TestCase):
    def download(self, handler, partial=None, sha256=hashlib.sha256(PAYLOAD).hexdigest()):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        target = Path(folder.name) / 'tool.zip'
        if partial is not None:
            target.with_name('tool.zip.part').write_bytes(partial)
        lines = []
        with local_server(handler) as base:
            install_support.download_file(base + '/tool.zip', target, sha256=sha256, session=offline_session(),
                                          sleep=lambda seconds: None, progress=lines.append)
        return target, lines

    def test_existing_partial_download_is_resumed_with_a_range_request(self):
        handler = range_handler()
        target, _ = self.download(handler, partial=PAYLOAD[:1000])
        self.assertEqual(target.read_bytes(), PAYLOAD)
        self.assertEqual(handler.seen, ['bytes=1000-'])
        self.assertFalse(target.with_name('tool.zip.part').exists())

    def test_dropped_connection_is_retried_until_complete(self):
        handler = range_handler(drop_first=True)
        target, lines = self.download(handler)
        self.assertEqual(target.read_bytes(), PAYLOAD)
        self.assertEqual(len(handler.seen), 2)
        self.assertTrue(any('下载中断' in line for line in lines), lines)

    def test_server_ignoring_range_restarts_instead_of_appending(self):
        handler = range_handler(honour_range=False)
        target, _ = self.download(handler, partial=b'stale bytes')
        self.assertEqual(target.read_bytes(), PAYLOAD)

    def test_checksum_mismatch_discards_the_download(self):
        with tempfile.TemporaryDirectory() as folder, local_server(range_handler()) as base:
            with self.assertRaisesRegex(RuntimeError, 'SHA256'):
                install_support.download_file(base + '/tool.zip', Path(folder) / 'tool.zip', sha256='0' * 64,
                                              session=offline_session(), sleep=lambda seconds: None,
                                              progress=lambda message: None)
            self.assertEqual(list(Path(folder).iterdir()), [])


if __name__ == '__main__':
    unittest.main()
