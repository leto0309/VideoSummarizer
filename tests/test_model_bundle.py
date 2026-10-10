from pathlib import Path
import tempfile
import unittest
import zipfile
from scripts.build_model_bundle import build, extract_base, verify


class ModelBundleTests(unittest.TestCase):
    def test_checksum_rejects_modified_input(self):
        with tempfile.TemporaryDirectory() as folder:
            file = Path(folder) / 'input.zip'
            file.write_bytes(b'modified')
            with self.assertRaisesRegex(ValueError, 'SHA256'):
                verify(file, '0' * 64)

    def test_archive_cannot_escape_destination_or_include_user_outputs(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for name in ('VideoSummarizer/../../outside.txt', 'VideoSummarizer/outputs/private.md',
                         'VideoSummarizer/language-settings.json'):
                archive = root / 'input.zip'
                with zipfile.ZipFile(archive, 'w') as package:
                    package.writestr(name, b'private')
                with self.assertRaises(ValueError):
                    extract_base(archive, root / 'extracted')
            self.assertFalse((root / 'outside.txt').exists())

    def test_new_release_cannot_use_unverified_old_portable_base(self):
        with self.assertRaisesRegex(ValueError, 'SHA256'):
            build(version='v0.3.0')


if __name__ == '__main__':
    unittest.main()
