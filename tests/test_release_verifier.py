import hashlib
import io
import json
import os
import unittest
from unittest.mock import patch
import zipfile

import scripts.verify_release as verifier

TAG = 'v9.9.9'
NAMES = verifier.asset_names(TAG)


def make_zip(members, padding=0):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w') as package:
        if padding:
            package.writestr('VideoSummarizer/runtime/python.dll', os.urandom(padding))
        for name, value in members.items():
            package.writestr('VideoSummarizer/' + name, value if isinstance(value, str) else json.dumps(value))
    return buffer.getvalue()


class FakeRelease:
    """A published release served from memory; the network is never used."""

    def __init__(self):
        version = f"VERSION = '{TAG[1:]}'\n"
        self.files = {NAMES['source']: make_zip({'app_version.py': version, 'app.py': ''}),
                      NAMES['windows-x64']: make_zip({'app_version.py': version, 'PORTABLE_BUILD.json': {
                          'version': TAG, 'edition': 'windows-x64'}}, padding=1024 * 1024)}
        self.files[NAMES['windows-x64-with-whisper']] = make_zip({
            'app_version.py': version, 'PORTABLE_BUILD.json': {'version': TAG, 'edition': 'windows-x64-with-whisper'},
            'WHISPER_BUNDLE.json': {'version': TAG, 'base_sha256': self.sha(NAMES['windows-x64'])}})
        self.files[NAMES['windows-x64-with-whisper-ollama']] = make_zip({
            'app_version.py': version,
            'PORTABLE_BUILD.json': {'version': TAG, 'edition': 'windows-x64-with-whisper-ollama'},
            'WHISPER_BUNDLE.json': {'version': TAG, 'base_sha256': self.sha(NAMES['windows-x64'])},
            'OLLAMA_BUNDLE.json': {'version': TAG,
                                   'base_with_whisper_sha256': self.sha(NAMES['windows-x64-with-whisper'])}})
        zips = list(NAMES.values())
        for manifest, name in zip(verifier.MANIFESTS, zips):
            self.files[manifest] = f'{self.sha(name)} *{name}\n'.encode()
        self.digests = {name: 'sha256:' + self.sha(name) for name in self.files}
        self.ranges = []

    def sha(self, name):
        return hashlib.sha256(self.files[name]).hexdigest()

    def release(self):
        return {'tag_name': TAG, 'draft': False, 'prerelease': False, 'assets': [
            {'name': name, 'size': len(data), 'digest': self.digests[name], 'browser_download_url': 'mem://' + name}
            for name, data in self.files.items()]}

    def fetch(self, url, start=None, end=None):
        data = self.files[url.removeprefix('mem://')]
        if start is None:
            return data
        self.ranges.append((url, start, end))
        return data[start:end + 1]


class ReleaseVerifierTests(unittest.TestCase):
    def check(self, fake, release=None):
        return verifier.verify(TAG, release or fake.release(), fake.fetch)

    def test_consistent_release_passes_and_windows_zips_are_only_partly_read(self):
        fake = FakeRelease()
        report = self.check(fake)
        self.assertTrue(report['ok'], report['problems'])
        self.assertEqual(report['assets'][NAMES['source']]['app_version'], '9.9.9')
        self.assertTrue(all(report['manifests_match_github_digest'].values()))
        standard = report['assets'][NAMES['windows-x64']]
        self.assertLess(standard['range_bytes_read'], standard['bytes'] // 2)
        self.assertNotIn(NAMES['source'], {url.removeprefix('mem://') for url, _, _ in fake.ranges})

    def problems(self, change):
        fake = FakeRelease()
        release = fake.release()
        change(fake, release)
        report = self.check(fake, release)
        self.assertFalse(report['ok'])
        return ' | '.join(report['problems'])

    def rebuild(self, fake, release, name, **members):
        fake.files[name] = make_zip({'app_version.py': f"VERSION = '{TAG[1:]}'\n", **members})
        for asset in release['assets']:
            if asset['name'] == name:
                asset['size'] = len(fake.files[name])

    def test_manifest_that_disagrees_with_github_digest_fails(self):
        def change(fake, release):
            fake.files['WINDOWS_SHA256SUMS.txt'] = b'0' * 64 + f' *{NAMES["windows-x64"]}\n'.encode()
        self.assertIn('checksum manifest', self.problems(change))

    def test_missing_unexpected_and_undigested_assets_fail(self):
        def change(fake, release):
            release['assets'] = [a for a in release['assets'] if a['name'] != 'WITH_WHISPER_OLLAMA_SHA256SUMS.txt']
            release['assets'].append({'name': 'notes.txt', 'size': 1, 'digest': '', 'browser_download_url': 'x'})
            release['assets'][0]['digest'] = None
        text = self.problems(change)
        for expected in ('missing assets: WITH_WHISPER_OLLAMA_SHA256SUMS.txt', 'unexpected assets: notes.txt',
                         'no SHA256 digest'):
            self.assertIn(expected, text)

    def test_source_whose_bytes_or_version_differ_fails(self):
        def change(fake, release):
            fake.files[NAMES['source']] = make_zip({'app_version.py': "VERSION = '9.9.8'\n"})
        text = self.problems(change)
        self.assertIn('downloaded file does not match', text)
        self.assertIn("app_version is '9.9.8'", text)

    def test_wrong_whisper_base_and_ollama_base_fail(self):
        def change(fake, release):
            self.rebuild(fake, release, NAMES['windows-x64-with-whisper-ollama'],
                         **{'PORTABLE_BUILD.json': {'version': TAG, 'edition': 'windows-x64-with-whisper-ollama'},
                            'WHISPER_BUNDLE.json': {'version': TAG, 'base_sha256': 'vocabulary-hash'},
                            'OLLAMA_BUNDLE.json': {'version': TAG, 'base_with_whisper_sha256': fake.sha(
                                NAMES['windows-x64'])}})
        text = self.problems(change)
        self.assertIn('base_sha256 is not the published standard ZIP', text)
        self.assertIn('OLLAMA_BUNDLE base is not the published with-whisper ZIP', text)

    def test_wrong_edition_version_and_missing_metadata_fail(self):
        def change(fake, release):
            self.rebuild(fake, release, NAMES['windows-x64'],
                         **{'PORTABLE_BUILD.json': {'version': 'v9.9.8', 'edition': 'windows-x64-with-whisper'}})
            self.rebuild(fake, release, NAMES['windows-x64-with-whisper'],
                         **{'PORTABLE_BUILD.json': {'version': TAG, 'edition': 'windows-x64-with-whisper'}})
        text = self.problems(change)
        self.assertIn("PORTABLE_BUILD version is 'v9.9.8'", text)
        self.assertIn("PORTABLE_BUILD edition is 'windows-x64-with-whisper'", text)
        self.assertIn('WHISPER_BUNDLE version is None', text)

    def test_draft_release_fails(self):
        self.assertIn('draft', self.problems(lambda fake, release: release.update(draft=True)))

    def test_command_reads_public_api_and_exits_nonzero_on_problems(self):
        fake = FakeRelease()
        release = fake.release()

        def fetch(url, start=None, end=None):
            if url.startswith('https://api.github.com/'):
                self.assertEqual(url, verifier.API.format(repo=verifier.REPO, tag=TAG))
                return json.dumps(release).encode()
            return fake.fetch(url, start, end)
        with patch.object(verifier, 'fetch', fetch), patch('sys.stdout', io.StringIO()) as output:
            self.assertEqual(verifier.main([TAG]), 0)
            self.assertTrue(json.loads(output.getvalue())['ok'])
            release['draft'] = True
            self.assertEqual(verifier.main([TAG]), 1)


if __name__ == '__main__':
    unittest.main()
