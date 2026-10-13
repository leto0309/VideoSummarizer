from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from config import ALLOWED_MODELS
import desktop_launcher
from downloader import metadata
from i18n import tr
from local_llm import LocalLLM
from logfiles import rotate

ROOT = Path(__file__).resolve().parents[1]


class TrackingParameterTests(unittest.TestCase):
    def test_saved_addresses_keep_only_playback_selectors(self):
        shared = 'https://www.bilibili.com/video/BV1nTcQzYEnc/?p=2&share_source=copy_web&vd_source=abc#reply'
        info = {'webpage_url': 'https://www.youtube.com/watch?v=abc&si=tracking&feature=share'}
        meta = metadata(info, shared)
        self.assertEqual(meta['original_url'], 'https://www.bilibili.com/video/BV1nTcQzYEnc/?p=2')
        self.assertEqual(meta['webpage_url'], 'https://www.youtube.com/watch?v=abc')
        self.assertEqual(metadata({}, 'https://youtu.be/abc?si=tracking')['original_url'], 'https://youtu.be/abc')


class TimestampScrubTests(unittest.TestCase):
    def ask(self, answer):
        llm = LocalLLM(ALLOWED_MODELS[1], language='en')
        with patch.object(llm, 'request', return_value={'message': {'content': answer}}):
            return llm.ask('notes')

    def test_model_written_times_are_replaced_but_ratios_and_scores_stay(self):
        placeholder = tr('en', 'time_placeholder')
        for text in ('At 02:15 the host', 'from 1:02:03.500 on', 'clip 00:01:02,500', 'around 1:23'):
            with self.subTest(text=text):
                self.assertIn(placeholder, self.ask(text))
        for text in ('Shot in 16:9 widescreen', 'The final score was 3:1', 'A 4:3 frame', 'Version 2.10'):
            with self.subTest(text=text):
                self.assertEqual(self.ask(text), text)


class LogRotationTests(unittest.TestCase):
    def test_large_log_keeps_one_previous_generation(self):
        with tempfile.TemporaryDirectory() as folder:
            log, previous = Path(folder) / 'app.log', Path(folder) / 'app.log.1'
            log.write_bytes(b'x' * 11)
            previous.write_bytes(b'older')
            self.assertEqual(rotate(log, limit=10), log)
            self.assertFalse(log.exists())
            self.assertEqual(previous.read_bytes(), b'x' * 11)
            log.write_bytes(b'small')
            rotate(log, limit=10)
            self.assertEqual(log.read_bytes(), b'small')
            rotate(Path(folder) / 'missing.log', limit=10)

    def test_every_appended_log_goes_through_rotation(self):
        offenders = [f'{path.name}:{number}' for path in ROOT.glob('*.py')
                     for number, line in enumerate(path.read_text(encoding='utf-8').splitlines(), 1)
                     if ".open('a'" in line and 'rotate(' not in line]
        self.assertEqual(offenders, [])

    def test_native_window_log_is_rotated_on_start(self):
        with patch.object(desktop_launcher, 'rotate') as rotated, patch.object(sys, 'argv', ['x', '--check']), \
             patch.object(desktop_launcher, 'needs_setup', return_value=False), self.assertRaises(SystemExit):
            desktop_launcher.main()
        rotated.assert_called_once_with(desktop_launcher.ROOT / 'logs' / 'desktop.log')


if __name__ == '__main__':
    unittest.main()
