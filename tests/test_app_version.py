import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from streamlit.testing.v1 import AppTest
from app_version import (EDITIONS, RELEASE_TAG, RELEASE_URL, VERSION, VersionInfo,
                         get_version_info, portable_record, validate_packaged_version)
from i18n import LANGUAGES, tr
from scripts.build_portable import build as build_portable
from scripts.build_source import build as build_source

ROOT = Path(__file__).resolve().parents[1]


class AppVersionTests(unittest.TestCase):
    def test_release_builders_reject_other_tags_before_writing(self):
        for builder in (build_portable, build_source):
            with self.subTest(builder=builder.__module__), self.assertRaisesRegex(ValueError, 'application version'):
                builder('v9.9.9')

    def test_archive_source_must_match_tag_without_execution(self):
        validate_packaged_version(f"VERSION = {VERSION!r}\n", RELEASE_TAG)
        for source in ("VERSION = '9.9.9'", "VERSION = __import__('os').getcwd()", "# missing version"):
            with self.subTest(source=source), self.assertRaises(ValueError):
                validate_packaged_version(source, RELEASE_TAG)

    def test_all_portable_editions_keep_provenance_and_running_version(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for edition in EDITIONS:
                record = portable_record({'version': RELEASE_TAG, 'python_archive_sha256': 'a' * 64},
                                         RELEASE_TAG, edition)
                self.assertEqual(record['python_archive_sha256'], 'a' * 64)
                (root / 'PORTABLE_BUILD.json').write_text(json.dumps(record), encoding='utf-8')
                self.assertEqual(get_version_info(root), VersionInfo(RELEASE_TAG, edition))

    def test_old_manifest_cannot_change_running_version_or_link(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'PORTABLE_BUILD.json').write_text(json.dumps({
                'version': 'v0.3.2', 'edition': EDITIONS[0], 'release_url': 'https://example.org'}))
            info = get_version_info(root)
            self.assertEqual(info.version, RELEASE_TAG)
            self.assertEqual(info.release_url, RELEASE_URL)
            self.assertEqual((info.edition, info.build_status), ('unknown', 'mismatch'))

    def test_source_and_missing_portable_metadata_are_distinguished(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            self.assertEqual(get_version_info(root), VersionInfo(RELEASE_TAG, 'source'))
            (root / 'runtime').mkdir()
            (root / 'runtime/python.exe').touch()
            self.assertEqual(get_version_info(root), VersionInfo(RELEASE_TAG, 'unknown', 'unavailable'))

    def test_damaged_metadata_never_breaks_page_version(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for content in (b'{broken', b'[]', b'\xff', b' ' * 65537,
                            json.dumps({'version': RELEASE_TAG, 'edition': 'invented'}).encode()):
                with self.subTest(content=content[:60]):
                    (root / 'PORTABLE_BUILD.json').write_bytes(content)
                    self.assertEqual(get_version_info(root), VersionInfo(RELEASE_TAG, 'unknown', 'unavailable'))

    def test_actual_deliverable_metadata_matches_code_and_edition(self):
        info = get_version_info()
        self.assertEqual(info.version, RELEASE_TAG)
        self.assertEqual(info.build_status, 'ok')
        if (ROOT / 'PORTABLE_BUILD.json').exists():
            expected = ('windows-x64-with-whisper-ollama' if (ROOT / 'OLLAMA_BUNDLE.json').exists()
                        else 'windows-x64-with-whisper' if (ROOT / 'WHISPER_BUNDLE.json').exists()
                        else 'windows-x64')
            self.assertEqual(info.edition, expected)
            for name in ('WHISPER_BUNDLE.json', 'OLLAMA_BUNDLE.json'):
                if (ROOT / name).exists():
                    self.assertEqual(json.loads((ROOT / name).read_text())['version'], RELEASE_TAG)
        else:
            self.assertEqual(info.edition, 'source')

    def test_release_documents_lead_with_running_version(self):
        # Edition notes prepended to packaged README files have no level-2 headings.
        headings = {name: next(line for line in (ROOT / name).read_text(encoding='utf-8').splitlines()
                               if line.startswith('## '))
                    for name in ('CHANGELOG.md', 'README.md', 'README.en.md')}
        self.assertTrue(headings['CHANGELOG.md'].startswith(f'## {VERSION} '), headings['CHANGELOG.md'])
        self.assertTrue(headings['README.md'].startswith(f'## {RELEASE_TAG}：'), headings['README.md'])
        self.assertTrue(headings['README.en.md'].startswith(f'## {RELEASE_TAG}: '), headings['README.en.md'])
        english = (ROOT / 'README.en.md').read_text(encoding='utf-8')
        self.assertIn(f'releases/download/{RELEASE_TAG}/VideoSummarizer-{RELEASE_TAG}-', english)

    def test_readme_keeps_earlier_release_notes_under_history(self):
        for name, history in (('README.md', '## 历史版本说明'), ('README.en.md', '## Release history')):
            with self.subTest(readme=name):
                sections = [line for line in (ROOT / name).read_text(encoding='utf-8').splitlines()
                            if line.startswith('## ')]
                # Only the running release is a top-level section; older notes must not read as current steps.
                self.assertEqual([line for line in sections if line.startswith('## v')], [sections[0]])
                self.assertEqual(sections[-1], history)

    def test_readmes_link_to_each_other(self):
        self.assertIn('[English](README.en.md)', (ROOT / 'README.md').read_text(encoding='utf-8'))
        english = (ROOT / 'README.en.md').read_text(encoding='utf-8')
        self.assertIn('[简体中文](README.md)', english)
        self.assertIn('[CHANGELOG.md](CHANGELOG.md)', english)

    def test_three_language_page_shows_version_and_about_without_network(self):
        with patch('config.gpu_info', return_value={'name': 'Test GPU', 'vram_mib': 4000, 'driver': None}), \
             patch('gpu_setup.installed', return_value=False), \
             patch('whisper_models.cached_model', return_value=None), \
             patch('preferences.load', return_value={'ui_language': 'zh-CN', 'summary_language': 'follow'}), \
             patch('preferences.save'), \
             patch('app_version.get_version_info', return_value=VersionInfo(RELEASE_TAG, EDITIONS[2])), \
             patch('requests.sessions.Session.request', side_effect=AssertionError('Version display must work offline')), \
             patch('urllib.request.urlopen', side_effect=AssertionError('Version display must work offline')):
            app = AppTest.from_file(str(ROOT / 'app.py')).run(timeout=30)
            app.text_input(key='video_url').set_value('https://b23.tv/example').run()
            for language in LANGUAGES:
                app.selectbox(key='ui_language').select(language).run()
                self.assertFalse(app.exception)
                self.assertEqual(app.caption[0].value, 'VideoSummarizer · ' + tr(language, 'app_version', version=RELEASE_TAG))
                self.assertEqual(app.expander[0].label, tr(language, 'about'))
                self.assertTrue(any(tr(language, 'edition_' + EDITIONS[2]) in item.value for item in app.markdown))
                self.assertTrue(any(RELEASE_URL in item.value for item in app.markdown))
                self.assertEqual(app.text_input(key='video_url').value, 'https://b23.tv/example')
                self.assertEqual(app.selectbox(key='mode').value, 'cpu')

    def test_page_explains_mismatched_install_without_losing_inputs(self):
        with patch('config.gpu_info', return_value={'name': 'Test GPU', 'vram_mib': 4000, 'driver': None}), \
             patch('gpu_setup.installed', return_value=False), \
             patch('whisper_models.cached_model', return_value=None), \
             patch('preferences.load', return_value={'ui_language': 'zh-CN', 'summary_language': 'follow'}), \
             patch('preferences.save'), \
             patch('app_version.get_version_info', return_value=VersionInfo(RELEASE_TAG, 'unknown', 'mismatch')):
            app = AppTest.from_file(str(ROOT / 'app.py')).run(timeout=30)
            self.assertFalse(app.exception)
            self.assertIn(tr('zh-CN', 'version_mismatch'), [item.value for item in app.warning])
            self.assertIn(RELEASE_TAG, app.caption[0].value)
            self.assertEqual(app.selectbox(key='mode').value, 'cpu')
