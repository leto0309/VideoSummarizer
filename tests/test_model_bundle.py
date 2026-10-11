import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile
from app_version import RELEASE_TAG
import scripts.build_model_bundle as bundle
from scripts.build_model_bundle import build, extract_base, verify

ROOT = Path(__file__).resolve().parents[1]


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

    def test_bundle_record_keeps_verified_portable_base_digest(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            models = root / 'models'
            models.mkdir()
            # Small stand-ins exercise the real checksum and packaging path without downloading Whisper.
            files = {}
            for name in bundle.FILES:
                (models / name).write_bytes(b'stand-in ' + name.encode())
                files[name] = hashlib.sha256((models / name).read_bytes()).hexdigest()
            base = root / 'portable.zip'
            with zipfile.ZipFile(base, 'w') as package:
                package.writestr('VideoSummarizer/PORTABLE_BUILD.json',
                                 json.dumps({'version': RELEASE_TAG, 'edition': 'windows-x64'}))
                package.writestr('VideoSummarizer/app_version.py', (ROOT / 'app_version.py').read_text(encoding='utf-8'))
                for name in ('README.md', 'THIRD_PARTY_NOTICES.md'):
                    package.writestr('VideoSummarizer/' + name, 'base')
            base_digest = bundle.digest(base)

            def offline_notice(url, target):
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text('offline notice', encoding='utf-8')

            with patch.object(bundle, 'ROOT', root / 'checkout'), patch.object(bundle, 'FILES', files), \
                 patch.object(bundle, 'download', side_effect=offline_notice):
                build(portable_zip=base, model_dir=models, version=RELEASE_TAG, base_sha256=base_digest)
            output = root / 'checkout/dist' / f'VideoSummarizer-{RELEASE_TAG}-windows-x64-with-whisper.zip'
            with zipfile.ZipFile(output) as package:
                record = json.loads(package.read('VideoSummarizer/WHISPER_BUNDLE.json'))
                bundled = {name: hashlib.sha256(package.read('VideoSummarizer/models/whisper/small/' + name)).hexdigest()
                           for name in files}
            self.assertEqual(record['base_sha256'], base_digest)
            self.assertNotIn(record['base_sha256'], files.values())
            self.assertEqual(record['files_sha256'], files)
            self.assertEqual(bundled, files)


if __name__ == '__main__':
    unittest.main()
