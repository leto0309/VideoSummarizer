import io
from pathlib import Path
import stat
import tempfile
import unittest
from unittest.mock import patch
import zipfile

import setup_runtime
from scripts.build_ollama_bundle import build, safe_name, validate_ollama


class OllamaBundleTests(unittest.TestCase):
    def test_fresh_setup_with_bundled_ollama_makes_no_ollama_download(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            tools = root / 'tools'
            executable = tools / 'ollama/ollama.exe'
            executable.parent.mkdir(parents=True)
            executable.write_bytes(b'verified official executable fixture')
            with patch.object(setup_runtime, 'ROOT', root), patch.object(setup_runtime, 'TOOLS', tools), \
                 patch.object(setup_runtime, 'setup_node'), \
                 patch('requests.sessions.Session.request', side_effect=AssertionError('Ollama network forbidden')) as get, \
                 patch.object(setup_runtime.subprocess, 'run') as pip, \
                 patch('launcher.pull') as pull, patch('whisper_models.ensure_model') as whisper:
                pip.return_value.returncode = 0
                setup_runtime.setup()
                get.assert_not_called()
                pull.assert_called_once()
                whisper.assert_called_once()
                self.assertEqual(executable.read_bytes(), b'verified official executable fixture')

    def test_unverified_base_is_rejected_before_downloading(self):
        with self.assertRaisesRegex(ValueError, 'SHA256'):
            build('v0.3.1', '')

    def test_vendor_archive_requires_executable_libraries_and_licenses(self):
        for entries in ({'ollama.exe': b'exe'}, {'ollama.exe': b'exe', 'lib/ollama/cpu.dll': b'dll'}):
            with self.subTest(entries=list(entries)), io.BytesIO() as buffer:
                with zipfile.ZipFile(buffer, 'w') as archive:
                    for name, content in entries.items():
                        archive.writestr(name, content)
                buffer.seek(0)
                with zipfile.ZipFile(buffer) as archive, self.assertRaises(ValueError):
                    validate_ollama(archive)

    def test_vendor_archive_rejects_paths_and_links_before_extracting(self):
        for name in ('../escape.exe', '/absolute.exe', 'C:/outside.exe', 'lib\\..\\escape.exe'):
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, 'Unsafe'):
                safe_name(zipfile.ZipInfo(name))
        link = zipfile.ZipInfo('lib/ollama/link')
        link.external_attr = (stat.S_IFLNK | 0o777) << 16
        with self.assertRaisesRegex(ValueError, 'Unsafe'):
            safe_name(link)

    def test_vendor_archive_rejects_windows_case_collisions(self):
        with io.BytesIO() as buffer:
            with zipfile.ZipFile(buffer, 'w') as archive:
                archive.writestr('ollama.exe', b'a')
                archive.writestr('OLLAMA.EXE', b'b')
            buffer.seek(0)
            with zipfile.ZipFile(buffer) as archive, self.assertRaisesRegex(ValueError, 'Duplicate'):
                validate_ollama(archive)


if __name__ == '__main__':
    unittest.main()
