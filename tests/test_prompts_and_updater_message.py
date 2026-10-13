from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from i18n import LANGUAGES, tr
from subtitles import Cue, chunks
import ytdlp_update

NO_HEADINGS = {'zh-CN': '不加标题', 'zh-TW': '不加標題', 'en': 'without headings'}


class NoHeadingPromptTests(unittest.TestCase):
    """Notes placed under the report's ### headings should be written without titles of their own."""

    def test_frame_and_timeline_prompts_ask_for_plain_text(self):
        for language in LANGUAGES:
            for key in ('frame_prompt', 'chunk_prompt'):
                with self.subTest(language=language, key=key):
                    self.assertIn(NO_HEADINGS[language], tr(language, key))

    def test_longest_timeline_prompt_stays_within_the_request_limit(self):
        # LocalLLM.ask refuses prompts over 1900 characters; tiny cues give the most line breaks.
        cues = [Cue(index, index + .5, 'x') for index in range(400)] + [Cue(500, 501, 'y' * 1500)]
        for language in LANGUAGES:
            for chunk in chunks(cues):
                with self.subTest(language=language):
                    self.assertLessEqual(len(tr(language, 'chunk_prompt') + chunk), 1900)


class UpdaterMessageTests(unittest.TestCase):
    def finish(self, restore):
        messages = []
        with tempfile.TemporaryDirectory() as folder, \
             patch('install_support.run_installer', return_value=0), \
             patch.object(ytdlp_update, 'installed', side_effect=['2026.9.27', '2026.10.10']), \
             patch.object(ytdlp_update, 'LOCK', Path(folder) / '.pipeline.lock'):
            ytdlp_update.update(restore=restore, progress=messages.append)
        return messages[-1]

    def test_completion_message_fits_both_update_and_restore(self):
        for restore, action in ((False, '已更新'), (True, '已恢复')):
            with self.subTest(restore=restore):
                message = self.finish(restore)
                self.assertIn(action, message)
                self.assertIn('2026.9.27 → 2026.10.10', message)
                self.assertNotIn('新版本', message)
                # Closing the page does not stop the background service; a restart does.
                self.assertIn('重启电脑', message)


if __name__ == '__main__':
    unittest.main()
