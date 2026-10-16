from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import os
from pathlib import Path
import re
import socket
import tempfile
import threading
import unittest

import yt_dlp

import downloader
from i18n import LANGUAGES, friendly_error, tr

PAYLOAD = os.urandom(3 * 1024**2 + 12345)
# The error the user saw on v0.3.10 when a Bilibili audio transfer stopped part-way.
SEEN = 'ERROR: [download] Got error: 15372 bytes read, 995626 more expected. Giving up after 2 retries'


class FlakyFile(BaseHTTPRequestHandler):
    """Serves PAYLOAD with Range support; the first ranged GET (the download itself) is cut off after 100 KiB.

    The generic extractor first reads the URL without a Range header to inspect it; that probe is served whole.
    """
    requests = []

    def log_message(self, *args):
        pass

    def span(self):
        match = re.fullmatch(r'bytes=(\d+)-(\d*)', self.headers.get('Range', ''))
        if not match:
            return 0, len(PAYLOAD) - 1, False
        end = int(match.group(2)) if match.group(2) else len(PAYLOAD) - 1
        return int(match.group(1)), min(end, len(PAYLOAD) - 1), True

    def head(self, start, end, partial):
        self.send_response(206 if partial else 200)
        self.send_header('Content-Type', 'audio/mp4')
        self.send_header('Accept-Ranges', 'bytes')
        self.send_header('Content-Length', str(end - start + 1))
        if partial:
            self.send_header('Content-Range', f'bytes {start}-{end}/{len(PAYLOAD)}')
        self.end_headers()

    def do_HEAD(self):
        self.head(*self.span())

    def do_GET(self):
        start, end, partial = self.span()
        first = partial and not FlakyFile.requests
        if partial:
            FlakyFile.requests.append(('GET', start))
        self.head(start, end, partial)
        body = PAYLOAD[start:end + 1]
        if first:
            self.wfile.write(body[:100 * 1024])
            self.wfile.flush()
            self.connection.shutdown(socket.SHUT_RDWR)
            self.close_connection = True
            return
        self.wfile.write(body)


class NetworkMessageTests(unittest.TestCase):
    def test_interrupted_or_timed_out_downloads_get_the_network_message(self):
        for text in (SEEN, 'ERROR: [download] Got error: The read operation timed out',
                     'ERROR: Unable to download webpage: <urlopen error [Errno 11001] getaddrinfo failed>',
                     'ERROR: [download] Got error: Remote end closed connection without response',
                     'ERROR: [download] Got error: [WinError 10054] Connection reset by peer'):
            for language in LANGUAGES:
                with self.subTest(text=text, language=language):
                    message = friendly_error(yt_dlp.utils.DownloadError(text), language)
                    self.assertEqual(message, tr(language, 'error_network'))
        self.assertNotIn('update-ytdlp', tr('zh-CN', 'error_network'))

    def test_other_platform_errors_still_suggest_updating_yt_dlp(self):
        error = yt_dlp.utils.DownloadError('ERROR: [BiliBili] BV1: Unable to extract initial state')
        self.assertEqual(friendly_error(error, 'zh-CN'), tr('zh-CN', 'error_platform'))


class ResumeTests(unittest.TestCase):
    def test_options_retry_patiently(self):
        with tempfile.TemporaryDirectory() as folder:
            opts = downloader.options(Path(folder))
        self.assertGreaterEqual(opts['retries'], 10)
        self.assertGreaterEqual(opts['fragment_retries'], 10)
        waits = [opts['retry_sleep_functions']['http'](n) for n in range(10)]
        self.assertEqual(waits, sorted(waits))
        self.assertGreater(waits[1], 0)
        self.assertLessEqual(max(waits), 30)
        self.assertEqual(opts['retry_sleep_functions']['fragment'], opts['retry_sleep_functions']['http'])

    def test_cut_transfer_resumes_from_the_part_already_downloaded(self):
        FlakyFile.requests = []
        server = ThreadingHTTPServer(('127.0.0.1', 0), FlakyFile)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        with tempfile.TemporaryDirectory() as folder:
            task = Path(folder)
            opts = downloader.options(task)
            opts['retry_sleep_functions'] = {'http': lambda n: 0, 'fragment': lambda n: 0}
            opts['outtmpl'] = str(task / 'audio.%(ext)s')
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([f'http://127.0.0.1:{server.server_port}/audio.m4a'])
            files = [path for path in task.iterdir() if path.suffix == '.m4a']
            self.assertEqual(len(files), 1)
            self.assertEqual(files[0].read_bytes(), PAYLOAD)
        gets = [start for method, start in FlakyFile.requests if method == 'GET']
        # After the cut, the next request starts where the saved .part ended (whole 64 KiB blocks), not at zero.
        self.assertGreater(len(gets), 1)
        self.assertGreater(gets[1], 0)
        self.assertLessEqual(gets[1], 100 * 1024)


if __name__ == '__main__':
    unittest.main()
