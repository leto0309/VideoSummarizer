import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from streamlit.testing.v1 import AppTest
from config import ALLOWED_MODELS
from i18n import LANGUAGES, TEXT, tr
from local_llm import LocalLLM
from pipeline import render_report
import preferences
import summary_versions as versions


def metadata():
    return {'title': '繁體標題', 'uploader': '臺灣作者',
            'original_url': 'https://www.youtube.com/watch?v=test#繁體', 'duration': 2.345,
            'model': ALLOWED_MODELS[1], 'transcript_source': {'type': 'manual'},
            'summary_language': 'zh-CN', 'summary_text': '## 摘要\n这是测试。',
            'timeline': [{'start': '00:00:00.123', 'end': '00:00:02.345', 'note': '字幕说明软件。'}],
            'frames': [{'timestamp': '00:00:01.234', 'timestamp_seconds': 1.234,
                        'sha256': 'a'*64, 'description': '画面显示软件。'}],
            'limitations': ['请对照原始字幕。'], 'llm_calls': []}


class LanguageTests(unittest.TestCase):
    def test_english_application_templates_are_translated(self):
        import re
        for key, (_, en) in TEXT.items():
            self.assertIsNone(re.search('[\u4e00-\u9fff]', en), key)
        self.assertIn('繁體中文', tr('zh-TW', 'final_prompt'))
        self.assertNotIn('簡體中文', tr('zh-TW', 'final_prompt'))
        original_path = 'C:/軟體/影片'
        self.assertIn(original_path, tr('zh-CN', 'saved', folder=original_path))
        self.assertIn('English', tr('en', 'existing_language', language='English'))

    def test_model_instructions_and_report_language_are_consistent(self):
        for language in LANGUAGES:
            with self.subTest(language=language):
                llm = LocalLLM(ALLOWED_MODELS[1], language=language)
                answer = '## Summary\nSoftware setup.' if language == 'en' else '## 摘要\n軟體設定。'
                with patch.object(llm, 'request', return_value={'message': {'content': answer}}) as request:
                    result = llm.ask('source')
                self.assertEqual(request.call_args.args[1]['options']['num_ctx'], 4096)
                if language == 'en':
                    self.assertIn('English', llm.system_prompt)
                    self.assertEqual(result, answer)
                elif language == 'zh-TW':
                    self.assertIn('繁體中文', llm.system_prompt)
                    self.assertIn('軟體', result)
                else:
                    self.assertIn('简体中文', llm.system_prompt)
                    self.assertIn('软体', result)
                meta = metadata()
                meta['summary_language'] = language
                meta['limitation_keys'] = ['limit_model']
                report = render_report(meta, result, meta['timeline'])
                self.assertIn('## ' + tr(language, 'timeline'), report)
                self.assertIn('繁體標題', report)
                self.assertIn(meta['original_url'], report)
                self.assertIn('00:00:00.123 – 00:00:02.345', report)
        with self.assertRaises(ValueError):
            LocalLLM(ALLOWED_MODELS[1], language='fr')

    def test_preferences_persist_and_reject_invalid_values(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(preferences, 'PATH', Path(directory)/'settings.json'):
            self.assertEqual(preferences.load()['ui_language'], 'zh-CN')
            preferences.save('en', 'zh-TW')
            self.assertEqual(preferences.load(), {'ui_language': 'en', 'summary_language': 'zh-TW'})
            with self.assertRaises(ValueError):
                preferences.save('../other', 'en')
            preferences.PATH.write_text('{broken', encoding='utf-8')
            self.assertEqual(preferences.load()['summary_language'], 'follow')
            self.assertFalse(list(Path(directory).glob('.language-*.tmp')))

    def test_page_language_switch_preserves_url_permissions_and_device(self):
        with patch('config.gpu_info', return_value={'name': 'Test GPU', 'vram_mib': 4000, 'driver': None}), \
             patch('whisper_models.cached_model', return_value=None), \
             patch('preferences.load', return_value={'ui_language': 'zh-CN', 'summary_language': 'follow'}), \
             patch('preferences.save'):
            app = AppTest.from_file(str(Path(__file__).resolve().parents[1]/'app.py')).run(timeout=30)
            app.text_input(key='video_url').set_value('https://b23.tv/example')
            app.selectbox(key='mode').select('cpu')
            app.checkbox(key='lawful').check()
            app.checkbox(key='visual').check()
            app.run()
            for language in ('zh-TW', 'en', 'zh-CN'):
                app.selectbox(key='ui_language').select(language).run()
                self.assertFalse(app.exception)
                self.assertEqual(app.title[0].value, '🎬 '+tr(language, 'title'))
                self.assertEqual(app.text_input(key='video_url').value, 'https://b23.tv/example')
                self.assertEqual(app.selectbox(key='mode').value, 'cpu')
                self.assertTrue(app.checkbox(key='lawful').value)
                self.assertTrue(app.checkbox(key='visual').value)
            app.selectbox(key='summary_language').select('en').run()
            self.assertEqual(app.selectbox(key='ui_language').value, 'zh-CN')
            self.assertTrue(any('English' in caption.value for caption in app.caption))


class VersionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.outputs = self.root/'outputs'
        self.folder = self.outputs/'task'
        self.folder.mkdir(parents=True)
        self.meta = metadata()
        (self.folder/'metadata.json').write_text(json.dumps(self.meta, ensure_ascii=False), encoding='utf-8')
        (self.folder/'summary.md').write_text('Original report', encoding='utf-8')
        (self.folder/'subtitles.srt').write_bytes('1\n00:00:00,123 --> 00:00:02,345\n繁體原始字幕\n'.encode())
        self.original = {p.name:p.read_bytes() for p in self.folder.iterdir()}
        root = self.root
        class FakeTask:
            def __init__(self):
                self.path = Path(tempfile.mkdtemp(dir=root))
            def success(self):
                import shutil
                shutil.rmtree(self.path)
            def fail(self, exc):
                (self.path/'failed.txt').write_text(str(exc))
        self.patches = [patch.object(versions, 'OUTPUTS', self.outputs), patch.object(versions, 'ROOT', self.root),
                        patch.object(versions, 'Task', FakeTask), patch.object(versions, 'guard')]
        for item in self.patches:
            item.start()

    def tearDown(self):
        for item in reversed(self.patches):
            item.stop()
        self.temp.cleanup()

    def assert_original(self):
        self.assertEqual(self.original, {n:(self.folder/n).read_bytes() for n in self.original})

    def test_chinese_variant_needs_no_model_and_is_cached(self):
        with patch.object(versions, 'LocalLLM') as model:
            version = versions.create_version(self.folder, 'zh-TW')
            model.assert_not_called()
            self.assertEqual(versions.create_version(self.folder, 'zh-TW'), version)
        meta = json.loads((version/'metadata.json').read_text(encoding='utf-8'))
        self.assertEqual(meta['summary_language'], 'zh-TW')
        self.assertEqual(meta['frames'][0]['sha256'], self.meta['frames'][0]['sha256'])
        self.assertIn('這是測試', meta['summary_text'])
        self.assert_original()

    def test_english_version_translates_prose_and_keeps_verified_times(self):
        with patch.object(versions, 'LocalLLM') as model:
            llm = model.return_value
            llm.ask.return_value = 'Translated explanation.'
            llm.calls = []
            version = versions.create_version(self.folder, 'en')
            model.assert_called_once_with(ALLOWED_MODELS[1], language='en')
            for call in llm.ask.call_args_list:
                self.assertNotIn('00:00:01.234', call.args[0])
        report = (version/'summary.md').read_text(encoding='utf-8')
        self.assertIn('Subtitle timeline', report)
        self.assertIn('00:00:01.234', report)
        self.assertIn('繁體標題', report)
        self.assert_original()

    def test_failed_translation_does_not_publish_incomplete_version(self):
        with patch.object(versions, 'LocalLLM') as model:
            model.return_value.ask.side_effect = RuntimeError('translation failed')
            with self.assertRaises(RuntimeError):
                versions.create_version(self.folder, 'en')
        self.assertFalse((self.folder/'translations/en').exists())
        self.assert_original()

    def test_output_boundary_is_enforced(self):
        with self.assertRaises(ValueError):
            versions.create_version(self.root, 'en')
        with self.assertRaises(ValueError):
            versions.create_version(self.folder, '../outside')


if __name__ == '__main__':
    unittest.main()
