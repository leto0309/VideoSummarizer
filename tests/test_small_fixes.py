import unittest
from unittest.mock import patch

from config import ALLOWED_MODELS
from downloader import metadata
from i18n import tr
from local_llm import LocalLLM


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


if __name__ == '__main__':
    unittest.main()
