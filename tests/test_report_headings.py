import copy
import unittest

from config import ALLOWED_MODELS
from pipeline import note_body, render_report


def report_for(summary, note, description):
    meta = {'title': '测试视频', 'uploader': '作者', 'original_url': 'https://youtu.be/abc', 'duration': 19,
            'transcript_source': {'type': 'manual'}, 'model': ALLOWED_MODELS[1], 'summary_language': 'zh-CN',
            'frames': [{'timestamp': '00:00:01.200', 'description': description}], 'limitations': ['请核对。']}
    sections = [{'start': '00:00:00.000', 'end': '00:00:19.000', 'note': note}]
    original = copy.deepcopy((meta, sections))
    report = render_report(meta, summary, sections)
    return report, (meta, sections) == original


class ReportHeadingTests(unittest.TestCase):
    """Model notes sit under the report's own ### headings and must not break its outline."""

    def test_leading_title_is_dropped_and_inner_headings_become_bold(self):
        self.assertEqual(note_body('# 电驴\n\n画面中有一头大象。'), '画面中有一头大象。')
        self.assertEqual(note_body('## 画面分析\n# 第二个标题\n一名男子\n### 细节\n长鼻子'),
                         '一名男子\n**细节**\n长鼻子')
        self.assertEqual(note_body('  # 画面描述 ##\n文字'), '文字')
        self.assertEqual(note_body('只有正文，#3 号不是标题'), '只有正文，#3 号不是标题')

    def test_a_note_that_is_only_a_heading_keeps_its_text(self):
        self.assertEqual(note_body('# 画面里只有一张图表'), '**画面里只有一张图表**')

    def test_report_keeps_one_title_and_section_levels(self):
        report, unchanged = report_for('# 总结\n**标题：大象**\n正文', '# 时间线标题\n字幕要点',
                                       '# 电驴\n\n画面中有一头大象。\n## 细节\n长鼻子')
        self.assertTrue(unchanged)  # metadata.json keeps the model's original text
        headings = [line for line in report.splitlines() if line.startswith('#')]
        self.assertEqual([line for line in headings if line.startswith('# ')], ['# 测试视频'])
        self.assertIn('## 总结', headings)
        self.assertNotIn('电驴', report)
        self.assertNotIn('时间线标题', report)
        self.assertIn('### 00:00:01.200\n画面中有一头大象。\n**细节**\n长鼻子', report)
        self.assertIn('### 00:00:00.000 – 00:00:19.000\n字幕要点', report)


if __name__ == '__main__':
    unittest.main()
