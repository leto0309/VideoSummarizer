"""Offline application version, shared by the running page and release builders."""
import ast
from dataclasses import dataclass
import json
from pathlib import Path

VERSION = '0.3.5'
RELEASE_TAG = 'v' + VERSION
RELEASE_URL = 'https://github.com/leto0309/VideoSummarizer/releases/tag/' + RELEASE_TAG
EDITIONS = ('windows-x64', 'windows-x64-with-whisper', 'windows-x64-with-whisper-ollama')


def validate_release_version(tag):
    if tag != RELEASE_TAG:
        raise ValueError(f'Release tag {tag!r} does not match application version {RELEASE_TAG}')


def validate_packaged_version(source, tag):
    """Check packaged source without executing code from an archive."""
    validate_release_version(tag)
    tree = ast.parse(source)
    assignments = [node.value for node in tree.body if isinstance(node, ast.Assign)
                   and any(isinstance(target, ast.Name) and target.id == 'VERSION'
                           for target in node.targets)]
    if len(assignments) != 1 or ast.literal_eval(assignments[0]) != VERSION:
        raise ValueError('Packaged application version does not match release tag')


def portable_record(record, tag, edition):
    validate_release_version(tag)
    if not isinstance(record, dict) or record.get('version') != tag or edition not in EDITIONS:
        raise ValueError('Portable build metadata does not match requested release')
    return {**record, 'edition': edition}


@dataclass(frozen=True)
class VersionInfo:
    version: str
    edition: str
    build_status: str = 'ok'
    release_url: str = RELEASE_URL


def get_version_info(root=None):
    """The code version wins; filenames, downloaded models and GitHub are not consulted."""
    root = Path(root) if root is not None else Path(__file__).resolve().parent
    manifest = root / 'PORTABLE_BUILD.json'
    try:
        if not manifest.exists():
            if (root / 'runtime' / 'python.exe').exists():
                return VersionInfo(RELEASE_TAG, 'unknown', 'unavailable')
            return VersionInfo(RELEASE_TAG, 'source')
        if manifest.stat().st_size > 65536:
            raise ValueError('Oversized build metadata')
        record = json.loads(manifest.read_text(encoding='utf-8'))
        if not isinstance(record, dict):
            raise ValueError('Invalid build metadata')
        if record.get('version') != RELEASE_TAG:
            return VersionInfo(RELEASE_TAG, 'unknown', 'mismatch')
        if record.get('edition') not in EDITIONS:
            raise ValueError('Unknown edition')
        return VersionInfo(RELEASE_TAG, record['edition'])
    except (OSError, UnicodeError, ValueError):
        return VersionInfo(RELEASE_TAG, 'unknown', 'unavailable')
