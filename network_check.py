"""Report which download sites are reachable. Standard library only: runs before pip installs anything."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
from pathlib import Path
import socket
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

from setup_text import t

ROOT = Path(__file__).resolve().parent
# key: probe URLs. Site names, what each provides and the advice are setup_text messages
# site_<key>, provides_<key> and advice_<key>.
SOURCES = {
    'pypi': ('https://pypi.org/', 'https://files.pythonhosted.org/'),
    'node': ('https://nodejs.org/',),
    'github': ('https://api.github.com/', 'https://github.com/'),
    'ollama': ('https://registry.ollama.ai/v2/',),
    'huggingface': ('https://huggingface.co/',),
}


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    # A redirect already proves the site answered; following it would contact other hosts.
    def redirect_request(self, *args, **kwargs):
        return None


def default_opener():
    return urllib.request.build_opener(_NoRedirect())


def describe(reason):
    if isinstance(reason, (socket.timeout, TimeoutError)):
        return t('err_timeout')
    if isinstance(reason, socket.gaierror):
        return t('err_dns')
    if isinstance(reason, ConnectionResetError):
        return t('err_reset')
    if isinstance(reason, ConnectionRefusedError):
        return t('err_refused')
    if isinstance(reason, ssl.SSLError):
        return t('err_tls')
    return f'{type(reason).__name__}: {str(reason)[:120]}'


def probe(url, timeout=8, opener=None):
    """Any HTTP response proves DNS, TCP and TLS work. Sends HEAD only and reads no body."""
    request = urllib.request.Request(url, method='HEAD', headers={'User-Agent': 'VideoSummarizer-network-check'})
    started = time.monotonic()
    try:
        with (opener or default_opener()).open(request, timeout=timeout) as response:
            status = response.status
    except urllib.error.HTTPError as exc:
        status = exc.code
        exc.close()
    except (urllib.error.URLError, OSError) as exc:
        return {'url': url, 'reachable': False, 'seconds': round(time.monotonic() - started, 2),
                'error': describe(getattr(exc, 'reason', exc))}
    return {'url': url, 'reachable': True, 'status': status, 'seconds': round(time.monotonic() - started, 2)}


def check(keys=None, needed=None, progress=print, timeout=8, opener=None, root=ROOT):
    keys = list(keys or SOURCES)
    targets = [(key, url) for key in keys for url in SOURCES[key]]
    with ThreadPoolExecutor(max_workers=len(targets)) as pool:
        results = list(pool.map(lambda item: {'source': item[0], **probe(item[1], timeout, opener)}, targets))
    progress(t('check_title'))
    for key in keys:
        rows = [row for row in results if row['source'] == key]
        if all(row['reachable'] for row in rows):
            detail = t('check_ok', seconds=max(row['seconds'] for row in rows))
        else:
            detail = t('check_failed', details=t('list_separator').join(
                f'{urllib.parse.urlsplit(row["url"]).hostname} {row["error"]}' for row in rows if not row['reachable']))
        mark = '' if needed is None else t('needed_yes') if key in needed else t('needed_no')
        progress(t('check_line', site=t(f'site_{key}'), detail=detail, provides=t(f'provides_{key}'), mark=mark))
    progress(t('check_note'))
    try:
        logs = Path(root) / 'logs'
        logs.mkdir(exist_ok=True)
        (logs / 'network-check.json').write_text(json.dumps(
            {'checked_at': datetime.now(timezone.utc).isoformat(), 'needed': needed, 'results': results},
            ensure_ascii=False, indent=2), encoding='utf-8')
    except OSError:
        pass
    return results


def explain(exc, source):
    """Name the download source behind a failed setup step, keeping the original exception type."""
    if getattr(exc, 'download_source', None) is None:
        exc.download_source = source
        exc.add_note(t('failed_source', site=t(f'site_{source}'), provides=t(f'provides_{source}'),
                       advice=t(f'advice_{source}')))
    return exc


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--timeout', type=float, default=8)
    args = parser.parse_args()
    results = check(timeout=args.timeout)
    return 0 if all(row['reachable'] for row in results) else 1


if __name__ == '__main__':
    sys.exit(main())
