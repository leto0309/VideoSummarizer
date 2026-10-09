import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import unittest
from terminology import normalize_terms


class TerminologyTests(unittest.TestCase):
    def test_source_evidence_corrects_names_even_without_images(self):
        meta = {'title': 'Yoinks：下載影片', 'description': 'Powered by yt-dlp', 'frames': []}
        self.assertEqual(normalize_terms('YawInx 使用 YT-Dub。', meta), 'Yoinks 使用 yt-dlp。')

    def test_title_alone_does_not_guess_download_engine(self):
        self.assertEqual(normalize_terms('YawInx 使用 YT-Dub。', {'title': 'Yoinks'}),
                         'Yoinks 使用 YT-Dub。')

    def test_unrelated_video_does_not_guess_names(self):
        self.assertEqual(normalize_terms('YawInx 使用 YT-Dub。', {'id': 'other', 'title': '另一影片'}),
                         'YawInx 使用 YT-Dub。')

    def test_case_and_chinese_boundaries(self):
        meta = {'title': 'Yoinks'}
        self.assertEqual(normalize_terms('yawinx把影片下載。Yoyngs採用MIT。', meta),
                         'Yoinks把影片下載。Yoinks採用MIT。')

    def test_preserve_urls_and_larger_identifiers(self):
        self.assertEqual(normalize_terms('https://example.com/YawInx abcYawInx YawInx', {'title': 'Yoinks'}),
                         'https://example.com/YawInx abcYawInx Yoinks')


if __name__ == '__main__':
    unittest.main()
