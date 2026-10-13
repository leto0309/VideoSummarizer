from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import downloader
from i18n import LANGUAGES, friendly_error, tr
from test_share_links import page


class NoMediaTests(unittest.TestCase):
    """Bilibili's risk control can answer with no media formats; the page must not blame the network or model."""

    def test_download_without_formats_raises_the_dedicated_error_before_contacting_the_platform(self):
        with tempfile.TemporaryDirectory() as folder, patch('yt_dlp.YoutubeDL') as client:
            with self.assertRaises(downloader.NoMediaError) as raised:
                downloader.download({'id': 'BV1', 'webpage_url': 'https://www.bilibili.com/video/BV1/',
                                     'formats': []}, Path(folder))
        client.assert_not_called()
        self.assertIsInstance(raised.exception, RuntimeError)
        self.assertIn('暂时限制', str(raised.exception))

    def test_message_explains_the_temporary_limit_in_every_language(self):
        error = downloader.NoMediaError('no formats')
        for language in LANGUAGES:
            with self.subTest(language=language):
                message = friendly_error(error, language)
                self.assertEqual(message, tr(language, 'error_no_media'))
                self.assertNotEqual(message, tr(language, 'error_generic'))
                self.assertIn('update-ytdlp.bat', message)
                self.assertIn('logs/app-errors.log', message)
        self.assertIn('过一段时间再试', tr('zh-CN', 'error_no_media'))
        self.assertIn('過一段時間再試', tr('zh-TW', 'error_no_media'))
        self.assertIn('音訊或影片', tr('zh-TW', 'error_no_media'))  # not the mis-converted 音影片
        self.assertIn('try again later', tr('en', 'error_no_media'))

    def test_page_shows_the_specific_message(self):
        def fail(*args, **kwargs):
            raise downloader.NoMediaError('平台没有提供可公开下载的媒体格式')
        with tempfile.TemporaryDirectory() as folder:
            app = page(fail, folder)
        self.assertFalse(app.exception)
        errors = [child.value for child in app.main.children.values() if child.type == 'error']
        self.assertEqual(errors, [tr('zh-CN', 'error_no_media')])


if __name__ == '__main__':
    unittest.main()
