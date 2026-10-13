"""Check a published GitHub release after the release workflows finish.

The source ZIP and checksum manifests are downloaded in full; the Windows ZIPs are read
through HTTP Range requests (central directory and a few metadata members only).
Uses the public GitHub API without credentials. Prints a JSON report and exits 1 on any problem.

    python scripts/verify_release.py v0.3.7
"""
import argparse
import ast
import hashlib
import io
import json
from pathlib import Path
import sys
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app_version import EDITIONS

REPO = 'leto0309/VideoSummarizer'
API = 'https://api.github.com/repos/{repo}/releases/tags/{tag}'
MANIFESTS = ('SHA256SUMS.txt', 'WINDOWS_SHA256SUMS.txt', 'WITH_WHISPER_SHA256SUMS.txt',
             'WITH_WHISPER_OLLAMA_SHA256SUMS.txt')
PREFIX = 'VideoSummarizer/'


def fetch(url, start=None, end=None):
    headers = {'User-Agent': 'VideoSummarizer-release-verification', 'Accept': 'application/vnd.github+json'}
    if start is not None:
        headers['Range'] = f'bytes={start}-{end}'
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=120) as response:
        if start is not None and response.status != 206:
            raise RuntimeError('Range request not honoured: ' + url)
        return response.read()


class RemoteFile(io.RawIOBase):
    """Seekable read-only view of a remote file, fetched on demand with Range requests."""

    def __init__(self, url, size, fetch=fetch):
        self.url, self.size, self.fetch, self.pos, self.fetched = url, size, fetch, 0, 0

    def readable(self):
        return True

    def seekable(self):
        return True

    def tell(self):
        return self.pos

    def seek(self, offset, whence=0):
        self.pos = {0: offset, 1: self.pos + offset, 2: self.size + offset}[whence]
        return self.pos

    def readinto(self, buffer):
        if self.pos >= self.size or not len(buffer):
            return 0
        data = self.fetch(self.url, self.pos, min(self.size, self.pos + len(buffer)) - 1)
        buffer[:len(data)] = data
        self.pos += len(data)
        self.fetched += len(data)
        return len(data)


def asset_names(tag):
    return {'source': f'VideoSummarizer-{tag}-source.zip',
            **{edition: f'VideoSummarizer-{tag}-{edition}.zip' for edition in EDITIONS}}


def code_version(source):
    tree = ast.parse(source)
    values = [ast.literal_eval(node.value) for node in tree.body if isinstance(node, ast.Assign)
              and any(isinstance(target, ast.Name) and target.id == 'VERSION' for target in node.targets)]
    return values[0] if len(values) == 1 else None


def read_json(package, name):
    try:
        return json.loads(package.read(PREFIX + name))
    except KeyError:
        return None


def verify(tag, release, fetch=fetch):
    problems = []

    def require(condition, message):
        if not condition:
            problems.append(message)

    names = asset_names(tag)
    assets = {asset['name']: asset for asset in release.get('assets', [])}
    digests = {name: (asset.get('digest') or '').removeprefix('sha256:') for name, asset in assets.items()}
    expected = [*names.values(), *MANIFESTS]
    report = {'tag': tag, 'draft': release.get('draft'), 'prerelease': release.get('prerelease'),
              'missing_assets': [name for name in expected if name not in assets],
              'unexpected_assets': sorted(set(assets) - set(expected)), 'assets': {}}
    require(release.get('tag_name') == tag, f'release tag is {release.get("tag_name")!r}')
    require(not release.get('draft'), 'release is still a draft')
    require(not report['missing_assets'], 'missing assets: ' + ', '.join(report['missing_assets']))
    require(not report['unexpected_assets'], 'unexpected assets: ' + ', '.join(report['unexpected_assets']))
    for name in names.values():
        require(name not in assets or digests[name], f'{name}: GitHub reports no SHA256 digest')

    # Every ZIP must be listed in a checksum manifest, with the digest GitHub computed.
    listed = {}
    for manifest in MANIFESTS:
        if manifest not in assets:
            continue
        for line in fetch(assets[manifest]['browser_download_url']).decode('utf-8').splitlines():
            if line.strip():
                value, name = line.split(maxsplit=1)
                listed[name.lstrip('*')] = value.lower()
    report['manifests_match_github_digest'] = {name: listed[name] == digests.get(name)
                                               for name in sorted(listed)}
    for name in names.values():
        require(name not in assets or listed.get(name) == digests[name],
                f'{name}: checksum manifest does not match the GitHub digest')

    version = tag.removeprefix('v')
    source = names['source']
    if source in assets:
        data = fetch(assets[source]['browser_download_url'])
        with zipfile.ZipFile(io.BytesIO(data)) as package:
            files = [item.filename for item in package.infolist() if not item.is_dir()]
            info = {'bytes': len(data), 'sha256_matches': hashlib.sha256(data).hexdigest() == digests[source],
                    'zip_crc': package.testzip() is None, 'files': len(files),
                    'app_version': code_version(package.read(PREFIX + 'app_version.py').decode('utf-8'))}
        require(info['sha256_matches'], f'{source}: downloaded file does not match the GitHub digest')
        require(info['zip_crc'], f'{source}: ZIP CRC check failed')
        require(info['app_version'] == version, f'{source}: app_version is {info["app_version"]!r}')
        report['assets'][source] = info

    standard, whisper = names['windows-x64'], names['windows-x64-with-whisper']
    for edition in EDITIONS:
        name = names[edition]
        if name not in assets:
            continue
        remote = RemoteFile(assets[name]['browser_download_url'], assets[name]['size'], fetch)
        with zipfile.ZipFile(io.BufferedReader(remote, buffer_size=256 * 1024)) as package:
            build = read_json(package, 'PORTABLE_BUILD.json') or {}
            info = {'bytes': assets[name]['size'], 'files': sum(not n.endswith('/') for n in package.namelist()),
                    'app_version': code_version(package.read(PREFIX + 'app_version.py').decode('utf-8')),
                    'portable_build_version': build.get('version'), 'edition': build.get('edition')}
            require(info['app_version'] == version, f'{name}: app_version is {info["app_version"]!r}')
            require(build.get('version') == tag, f'{name}: PORTABLE_BUILD version is {build.get("version")!r}')
            require(build.get('edition') == edition, f'{name}: PORTABLE_BUILD edition is {build.get("edition")!r}')
            if edition != 'windows-x64':
                bundle = read_json(package, 'WHISPER_BUNDLE.json') or {}
                info['whisper_base_sha256'] = bundle.get('base_sha256')
                require(bundle.get('version') == tag, f'{name}: WHISPER_BUNDLE version is {bundle.get("version")!r}')
                require(bundle.get('base_sha256') == digests.get(standard),
                        f'{name}: WHISPER_BUNDLE base_sha256 is not the published standard ZIP')
            if edition == 'windows-x64-with-whisper-ollama':
                bundle = read_json(package, 'OLLAMA_BUNDLE.json') or {}
                info['ollama_base_sha256'] = bundle.get('base_with_whisper_sha256')
                require(bundle.get('version') == tag, f'{name}: OLLAMA_BUNDLE version is {bundle.get("version")!r}')
                require(bundle.get('base_with_whisper_sha256') == digests.get(whisper),
                        f'{name}: OLLAMA_BUNDLE base is not the published with-whisper ZIP')
            info['range_bytes_read'] = remote.fetched
        report['assets'][name] = info

    report['standard_zip_sha256'] = digests.get(standard)
    report['problems'] = problems
    report['ok'] = not problems
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('tag')
    parser.add_argument('--repo', default=REPO)
    args = parser.parse_args(argv)
    release = json.loads(fetch(API.format(repo=args.repo, tag=args.tag)))
    report = verify(args.tag, release, fetch)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report['ok'] else 1


if __name__ == '__main__':
    sys.exit(main())
