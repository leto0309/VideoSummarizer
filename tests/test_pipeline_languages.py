import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch
from config import ALLOWED_MODELS
from subtitles import Cue
import pipeline


class PipelineLanguageTests(unittest.TestCase):
    def test_output_language_is_separate_from_ui_and_subtitles_stay_original(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            class FakeTask:
                id = 'a'*32
                def __init__(self):
                    self.path = root/'temp'/self.id
                    self.path.mkdir(parents=True)
                def success(self):
                    shutil.rmtree(self.path)
                def fail(self, exc):
                    pass
            cues = [Cue(.123, 2.345, '繁體原始字幕')]
            progress = []
            with patch.object(pipeline, 'ROOT', root), patch.object(pipeline, 'OUTPUTS', root/'outputs'), \
                 patch.object(pipeline, 'Task', FakeTask), patch.object(pipeline, 'guard'), \
                 patch.object(pipeline, 'configure_runtime'), patch.object(pipeline, 'gpu_info', return_value={}), \
                 patch('downloader.inspect', return_value={'title':'繁體原標題', 'duration':2.345}), \
                 patch('downloader.get_subtitles', return_value=(cues, {'type':'manual', 'language':'zh-TW'})), \
                 patch('downloader.download') as download, patch('local_llm.LocalLLM') as model:
                llm = model.return_value
                llm.ask.return_value = 'A supported explanation.'
                llm.merge.return_value = '## Summary\nA supported summary.'
                llm.calls = []
                folder = pipeline.run('https://b23.tv/example', model=ALLOWED_MODELS[1],
                                      language='en', ui_language='zh-CN', progress=progress.append)
                model.assert_called_once_with(ALLOWED_MODELS[1], language='en')
                download.assert_not_called()
            meta = json.loads((folder/'metadata.json').read_text(encoding='utf-8'))
            self.assertEqual(meta['summary_language'], 'en')
            self.assertEqual(meta['ui_language'], 'zh-CN')
            self.assertEqual(meta['timeline'][0]['start'], '00:00:00.123')
            self.assertIn('繁體原始字幕', (folder/'subtitles.srt').read_text(encoding='utf-8'))
            self.assertIn('Subtitle timeline', (folder/'summary.md').read_text(encoding='utf-8'))
            self.assertTrue(any('检查' in message for message in progress))
            self.assertFalse((root/'temp'/FakeTask.id).exists())


if __name__ == '__main__':
    unittest.main()
