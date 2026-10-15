import ast
import json
import os
from pathlib import Path
import re
import string
import sys
import tempfile
import unittest
from unittest.mock import patch

import desktop_launcher
import gpu_setup
from i18n import normalize
import install_support
import network_check
import preferences
import setup_text
import ytdlp_update

ROOT = Path(__file__).resolve().parents[1]
CJK = re.compile(r'[一-鿿]')
# Modules whose messages appear in the setup window, installers, launchers or their logs.
MODULES = ('desktop_launcher.py', 'install_support.py', 'network_check.py', 'setup_runtime.py', 'gpu_setup.py',
           'ytdlp_update.py', 'startup_lock.py', 'launcher.py', 'whisper_models.py', 'bookmark_launcher.py')
STRING = r'"((?:[^"\\]|\\.)*)"'


def fields(text):
    return sorted(name for _, name, _, _ in string.Formatter().parse(text) if name)


def language(value):
    return patch.dict(os.environ, {setup_text.ENVIRONMENT: value})


class MessageTableTests(unittest.TestCase):
    def test_three_languages_match_and_share_placeholders(self):
        for key, (simplified, traditional, english) in setup_text.TEXT.items():
            with self.subTest(key=key):
                self.assertEqual(traditional, normalize(simplified, 'zh-TW'))
                self.assertEqual(fields(simplified), fields(english))
                self.assertIsNone(CJK.search(english))

    def test_setup_modules_have_no_hard_coded_chinese(self):
        found = []
        for name in MODULES:
            tree = ast.parse((ROOT / name).read_text(encoding='utf-8'))
            found += [f'{name}: {node.value[:40]}' for node in ast.walk(tree)
                      if isinstance(node, ast.Constant) and isinstance(node.value, str) and CJK.search(node.value)]
        self.assertEqual(found, [])

    def test_messages_follow_the_language(self):
        with language('en'):
            self.assertEqual(network_check.describe(ConnectionRefusedError()), 'connection refused')
            with patch('importlib.metadata.version', side_effect=ytdlp_update.importlib.metadata.PackageNotFoundError):
                self.assertEqual(ytdlp_update.installed(), 'not installed')
        with language('zh-TW'):
            self.assertEqual(network_check.describe(ConnectionRefusedError()), normalize('连接被拒绝', 'zh-TW'))
        with patch.dict(os.environ), tempfile.TemporaryDirectory() as folder, \
             patch.object(setup_text, 'SETTINGS', Path(folder) / 'language-settings.json'):
            os.environ.pop(setup_text.ENVIRONMENT, None)
            self.assertEqual(network_check.describe(ConnectionRefusedError()), '连接被拒绝')

    def test_installer_progress_is_translated(self):
        # A real child process prints pip's raw progress line; the installer shows it in the chosen language.
        lines = []
        script = "print('Progress 1048576 of 2097152', flush=True)"
        with language('en'), tempfile.TemporaryDirectory() as folder:
            code = install_support.run_installer([sys.executable, '-c', script], timeout=60, root=folder,
                                                 progress=lines.append)
        self.assertEqual(code, 0)
        self.assertIn('Download progress: 1.0 / 2.0 MiB (50.0%)', lines)


class LanguagePreferenceTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.settings = Path(folder.name) / 'language-settings.json'
        for target in (patch.object(setup_text, 'SETTINGS', self.settings),
                       patch.object(preferences, 'PATH', self.settings), patch.dict(os.environ)):
            target.start()
            self.addCleanup(target.stop)
        os.environ.pop(setup_text.ENVIRONMENT, None)

    def test_environment_then_saved_preference_then_simplified_chinese(self):
        self.assertEqual(setup_text.language(), 'zh-CN')
        self.settings.write_text('{"ui_language": "zh-TW"}', encoding='utf-8')
        self.assertEqual(setup_text.language(), 'zh-TW')
        os.environ[setup_text.ENVIRONMENT] = 'en'
        self.assertEqual(setup_text.language(), 'en')
        os.environ[setup_text.ENVIRONMENT] = 'fr'
        self.settings.write_text('{"ui_language": "fr"}', encoding='utf-8')
        self.assertEqual(setup_text.language(), 'zh-CN')
        self.settings.write_text('not json', encoding='utf-8')
        self.assertEqual(setup_text.language(), 'zh-CN')

    def test_saving_keeps_the_summary_language_and_the_page_reads_it(self):
        setup_text.save_language('en')
        self.assertEqual(preferences.load(), {'ui_language': 'en', 'summary_language': 'follow'})
        preferences.save('en', 'zh-TW')
        setup_text.save_language('zh-CN')
        self.assertEqual(preferences.load(), {'ui_language': 'zh-CN', 'summary_language': 'zh-TW'})
        with self.assertRaises(ValueError):
            setup_text.save_language('fr')
        self.assertEqual(list(self.settings.parent.glob('.language-*')), [])

    def test_first_run_choice_is_saved_before_setup(self):
        with patch.object(sys, 'argv', ['desktop_launcher.py', '--setup', '--language', 'en']), \
             patch.object(desktop_launcher, 'needs_setup', return_value=False), \
             patch.object(desktop_launcher, 'rotate'), patch('bookmark_launcher.open_on_demand'):
            desktop_launcher.main()
        self.assertEqual(json.loads(self.settings.read_text(encoding='utf-8'))['ui_language'], 'en')


class PromptTests(unittest.TestCase):
    def test_ytdlp_menu_asks_until_a_valid_choice(self):
        shown, answers = [], iter(['x', ' r '])
        with language('en'), patch.object(ytdlp_update, 'installed', return_value='2026.9.27'):
            self.assertEqual(ytdlp_update.ask(read=lambda prompt: next(answers), show=shown.append), 'R')
        self.assertIn('Current version: 2026.9.27', shown)
        self.assertIn(setup_text.TEXT['ytdlp_choice_update'][2], shown)

        def closed(prompt):
            raise EOFError
        self.assertEqual(ytdlp_update.ask(read=closed, show=lambda line: None), 'C')

    def test_source_gpu_install_asks_for_consent(self):
        self.assertTrue(gpu_setup.confirmed(read=lambda prompt: 'y'))
        self.assertFalse(gpu_setup.confirmed(read=lambda prompt: ''))

        def closed(prompt):
            raise EOFError
        self.assertFalse(gpu_setup.confirmed(read=closed))


class NativeWindowTextTests(unittest.TestCase):
    def setUp(self):
        self.source = (ROOT / 'packaging/Launcher.cs').read_text(encoding='utf-8-sig')
        start = self.source.index('Messages = new Dictionary')
        self.table_text = self.source[start:self.source.index('\n    };', start)]
        self.table = {key: values for key, *values in re.findall(
            r'\{ "(\w+)", new\[\] \{ ' + STRING + r',\s*' + STRING + r',\s*' + STRING + r' \} \}', self.table_text)}

    def test_table_has_three_matching_languages(self):
        self.assertGreater(len(self.table), 20)
        for key, (simplified, traditional, english) in self.table.items():
            with self.subTest(key=key):
                self.assertEqual(traditional, normalize(simplified, 'zh-TW'))
                self.assertIsNone(CJK.search(english))

    def test_window_uses_only_defined_messages_and_no_other_chinese(self):
        used = set(re.findall(r'\bT\("(\w+)"\)', self.source))
        self.assertEqual(used, set(self.table))
        outside = self.source.replace(self.table_text, '')
        literals = [value for value in re.findall(STRING, outside) if CJK.search(value)]
        self.assertEqual(literals, ['简体中文', '繁體中文'])  # the language names in the first-run choice

    def test_first_run_passes_the_choice_to_setup(self):
        self.assertIn('"--setup --language " + lang', self.source)
        self.assertIn('EnvironmentVariables["VIDEOSUMMARIZER_LANGUAGE"] = lang', self.source)
        self.assertIn(f'"{setup_text.ENVIRONMENT}"', self.source)


if __name__ == '__main__':
    unittest.main()
