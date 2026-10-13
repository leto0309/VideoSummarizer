import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

from config import ALLOWED_MODELS
from downloader import validate_url
from i18n import tr
import pipeline
from subtitles import Cue

ROOT = Path(__file__).resolve().parents[1]
SHARED = ('【自由的龙儿是关不住的《笑声客的救赎》】 '
          'https://www.bilibili.com/video/BV1nTcQzYEnc/?share_source=copy_web&vd_source=example')
LINK = 'https://www.bilibili.com/video/BV1nTcQzYEnc/?share_source=copy_web&vd_source=example'


class ShareTextTests(unittest.TestCase):
    def test_link_is_taken_from_platform_share_text(self):
        cases = {
            SHARED: LINK,
            '【标题】 https://b23.tv/AbC123': 'https://b23.tv/AbC123',
            '看这个：https://b23.tv/AbC123，很好看！': 'https://b23.tv/AbC123',
            'Watch (https://youtu.be/abc?si=xyz).': 'https://youtu.be/abc?si=xyz',
            '  https://www.youtube.com/watch?v=abc  ': 'https://www.youtube.com/watch?v=abc',
        }
        for text, expected in cases.items():
            with self.subTest(text=text):
                self.assertEqual(validate_url(text), expected)

    def test_saved_report_records_the_link_not_the_pasted_title(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)

            class FakeTask:
                id = 'b' * 32

                def __init__(self):
                    self.path = root / 'temp' / self.id
                    self.path.mkdir(parents=True)

                def success(self):
                    shutil.rmtree(self.path)

                def fail(self, exc):
                    pass
            # No webpage_url from the platform: the report falls back to the address the user gave.
            with patch.object(pipeline, 'ROOT', root), patch.object(pipeline, 'OUTPUTS', root / 'outputs'), \
                 patch.object(pipeline, 'Task', FakeTask), patch.object(pipeline, 'guard'), \
                 patch.object(pipeline, 'configure_runtime'), patch.object(pipeline, 'gpu_info', return_value={}), \
                 patch('downloader.inspect', return_value={'title': '原标题', 'duration': 2.0}) as inspect, \
                 patch('downloader.get_subtitles', return_value=([Cue(0, 2, '字幕')], {'type': 'manual', 'language': 'zh-CN'})), \
                 patch('local_llm.LocalLLM') as model:
                model.return_value.ask.return_value = '有依据的说明'
                model.return_value.merge.return_value = '## 摘要\n有依据的摘要'
                model.return_value.calls = []
                folder = pipeline.run(SHARED, model=ALLOWED_MODELS[1])
            self.assertEqual(inspect.call_args.args[0], LINK)
            meta = json.loads((folder / 'metadata.json').read_text(encoding='utf-8'))
            report = (folder / 'summary.md').read_text(encoding='utf-8')
            # Saved addresses also drop the share tracking parameters.
            self.assertEqual(meta['original_url'], 'https://www.bilibili.com/video/BV1nTcQzYEnc/')
            self.assertIn('https://www.bilibili.com/video/BV1nTcQzYEnc/', report)
            self.assertNotIn('【', report)
            self.assertNotIn('vd_source', report)

    def test_share_text_does_not_relax_the_allowlist(self):
        for text in ('【标题】 http://b23.tv/AbC123', '【标题】 https://b23.tv.evil.test/x',
                     '【标题】 https://user:pass@www.youtube.com/watch?v=abc', '【标题】 没有链接',
                     '【标题】 https://example.com/x https://b23.tv/AbC123'):
            with self.subTest(text=text), self.assertRaises(ValueError):
                validate_url(text)


def page(run, root):
    # The page writes logs/app-errors.log under config.ROOT; keep test failures out of the project folder.
    with patch('config.gpu_info', return_value={'name': 'Test GPU', 'vram_mib': 12000, 'driver': None}), \
         patch('config.ROOT', Path(root)), patch('whisper_models.cached_model', return_value=None), \
         patch('preferences.load', return_value={'ui_language': 'zh-CN', 'summary_language': 'follow'}), \
         patch('preferences.save'), patch('pipeline.run', run):
        app = AppTest.from_file(str(ROOT / 'app.py')).run(timeout=30)
        app.text_input(key='video_url').set_value(SHARED).run()
        app.checkbox(key='lawful').check().run()
        app.button(key='generate').click().run(timeout=30)
        return app


class SharePageTests(unittest.TestCase):
    def test_page_shows_and_uses_the_extracted_link(self):
        calls = []

        def stop(url, *args, **kwargs):
            calls.append(url)
            raise RuntimeError('stop')
        with tempfile.TemporaryDirectory() as folder:
            app = page(stop, folder)
        self.assertFalse(app.exception)
        self.assertIn(tr('zh-CN', 'url_extracted', url=LINK), [item.value for item in app.caption])
        self.assertEqual(calls, [LINK])

    def test_failure_message_stays_visible_outside_the_collapsed_status(self):
        def fail(*args, **kwargs):
            raise ValueError('请输入 HTTPS 的 Bilibili、b23.tv 或 YouTube 链接')
        with tempfile.TemporaryDirectory() as folder:
            app = page(fail, folder)
            log = (Path(folder) / 'logs/app-errors.log').read_text(encoding='utf-8')
        self.assertFalse(app.exception)
        top_level = [child for child in app.main.children.values() if child.type == 'error']
        self.assertEqual([item.value for item in top_level], [tr('zh-CN', 'error_url')])
        self.assertEqual(app.status[0].label, tr('zh-CN', 'stopped'))
        self.assertIn('Traceback (most recent call last)', log)
        self.assertIn('ValueError: 请输入 HTTPS', log)


if __name__ == '__main__':
    unittest.main()
