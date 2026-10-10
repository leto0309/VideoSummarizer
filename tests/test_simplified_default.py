import copy
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from config import ALLOWED_MODELS
from local_llm import LocalLLM, SYSTEM
from pipeline import render_report


class SimplifiedDefaultTests(unittest.TestCase):
    def test_generated_prose_converts_without_changing_source_evidence(self):
        meta = {
            'title': '繁體標題與軟體', 'uploader': '臺灣作者',
            'original_url': 'https://www.youtube.com/watch?v=example#繁體',
            'duration': 1.234, 'transcript_source': {'type': 'manual'},
            'model': ALLOWED_MODELS[1],
            'frames': [{'timestamp': '00:00:01.234', 'description': '畫面顯示軟體與設定'}],
            'limitations': ['請核對原始字幕。'],
        }
        sections = [{'start': '00:00:00.123', 'end': '00:00:01.234', 'note': '字幕說明處理步驟'}]
        original = copy.deepcopy((meta, sections))
        report = render_report(meta, '## 摘要\n這是繁體輸出的測試。', sections)
        for text in ['# 繁體標題與軟體', '臺灣作者', meta['original_url'],
                     '这是繁体输出的测试。', '字幕说明处理步骤', '画面显示软体与设定',
                     '00:00:00.123 – 00:00:01.234']:
            self.assertIn(text, report)
        self.assertEqual((meta, sections), original)

    def test_llm_requests_simplified_and_normalizes_response(self):
        llm = LocalLLM(ALLOWED_MODELS[1])
        with patch.object(llm, 'request', return_value={
            'message': {'content': '重點：軟體設定，時間 00:12。'}}) as request:
            result = llm.ask('整理字幕')
        body = request.call_args.args[1]
        self.assertIn('简体中文', SYSTEM)
        self.assertEqual(body['messages'][0]['content'], SYSTEM)
        self.assertEqual(body['options']['num_ctx'], 4096)
        self.assertIn('重点：软体设定', result)
        self.assertNotIn('00:12', result)

    def test_default_page_renders_simplified(self):
        from streamlit.testing.v1 import AppTest
        with patch('config.gpu_info', return_value={'name': 'Test GPU', 'vram_mib': 4000, 'driver': None}), \
             patch('whisper_models.cached_model', return_value=None):
            app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'app.py')).run(timeout=30)
        self.assertFalse(app.exception)
        self.assertEqual(app.title[0].value, '🎬 本机视频摘要')
        self.assertIn('简体中文', app.caption[0].value)
        self.assertEqual(app.selectbox[0].value, ALLOWED_MODELS[1])
        self.assertEqual(app.selectbox[1].value, '自动：CUDA → CPU')
        self.assertEqual(app.button[0].label, '开始生成摘要')


if __name__ == '__main__':
    unittest.main()
