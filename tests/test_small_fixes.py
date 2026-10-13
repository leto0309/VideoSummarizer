import unittest

from downloader import metadata


class TrackingParameterTests(unittest.TestCase):
    def test_saved_addresses_keep_only_playback_selectors(self):
        shared = 'https://www.bilibili.com/video/BV1nTcQzYEnc/?p=2&share_source=copy_web&vd_source=abc#reply'
        info = {'webpage_url': 'https://www.youtube.com/watch?v=abc&si=tracking&feature=share'}
        meta = metadata(info, shared)
        self.assertEqual(meta['original_url'], 'https://www.bilibili.com/video/BV1nTcQzYEnc/?p=2')
        self.assertEqual(meta['webpage_url'], 'https://www.youtube.com/watch?v=abc')
        self.assertEqual(metadata({}, 'https://youtu.be/abc?si=tracking')['original_url'], 'https://youtu.be/abc')


if __name__ == '__main__':
    unittest.main()
