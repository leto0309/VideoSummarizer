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

ROOT = Path(__file__).resolve().parent
# key: (site, what it provides, probe URLs)
SOURCES = {
    'pypi': ('PyPI', 'Python 依赖、FFmpeg 和可选 CUDA 运行库', ('https://pypi.org/', 'https://files.pythonhosted.org/')),
    'node': ('Node.js 官网', 'Node.js', ('https://nodejs.org/',)),
    'github': ('GitHub', 'Ollama 程序', ('https://api.github.com/', 'https://github.com/')),
    'ollama': ('Ollama 模型库', 'Qwen 摘要模型', ('https://registry.ollama.ai/v2/',)),
    'huggingface': ('Hugging Face', 'Whisper 语音模型', ('https://huggingface.co/',)),
}
ADVICE = {
    'pypi': '可稍后重新打开 VideoSummarizer.exe 重试，已下载的部分保留在 tools/pip-cache；网络需要代理时，请先设置系统代理。',
    'node': '可稍后重试，会接着已下载的部分继续；也可以从另一台已完成配置的同版本软件复制 tools/node 文件夹。',
    'github': '建议改用「内含 Whisper + Ollama 版」安装包，首次配置会跳过这一步；重试时也会接着已下载的部分继续。',
    'ollama': '重试时会接着已下载的部分继续；也可以从另一台已下载完成的电脑复制整个 models/ollama 文件夹，本机已有模型时会跳过下载。',
    'huggingface': '有字幕的视频仍可处理；可改用内含 Whisper 的安装包，或运行 prepare-whisper.bat 重试。',
}


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    # A redirect already proves the site answered; following it would contact other hosts.
    def redirect_request(self, *args, **kwargs):
        return None


def default_opener():
    return urllib.request.build_opener(_NoRedirect())


def describe(reason):
    if isinstance(reason, (socket.timeout, TimeoutError)):
        return '连接超时'
    if isinstance(reason, socket.gaierror):
        return '无法解析域名（DNS）'
    if isinstance(reason, ConnectionResetError):
        return '连接被重置'
    if isinstance(reason, ConnectionRefusedError):
        return '连接被拒绝'
    if isinstance(reason, ssl.SSLError):
        return '安全连接（TLS）失败'
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
    targets = [(key, url) for key in keys for url in SOURCES[key][2]]
    with ThreadPoolExecutor(max_workers=len(targets)) as pool:
        results = list(pool.map(lambda item: {'source': item[0], **probe(item[1], timeout, opener)}, targets))
    progress('网络检查（只测试能否连接下载网站，不上传任何资料）：')
    for key in keys:
        site, provides, _ = SOURCES[key]
        rows = [row for row in results if row['source'] == key]
        if all(row['reachable'] for row in rows):
            detail = f'可以连接（{max(row["seconds"] for row in rows):.1f} 秒）'
        else:
            detail = '无法连接：' + '；'.join(f'{urllib.parse.urlsplit(row["url"]).hostname} {row["error"]}'
                                          for row in rows if not row['reachable'])
        mark = '' if needed is None else '（本次配置需要）' if key in needed else '（本次不需要）'
        progress(f'- {site}：{detail}，用于下载 {provides}{mark}')
    progress('可以连接只表示能建立连接，不保证大文件一定能完整下载。')
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
        site, provides, _ = SOURCES[source]
        exc.download_source = source
        exc.add_note(f'\n下载失败的来源：{site}（{provides}）。{ADVICE[source]}\n'
                     '可运行 check-network.bat 检查各下载网站能否连接，结果保存在 logs/network-check.json。')
    return exc


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--timeout', type=float, default=8)
    args = parser.parse_args()
    results = check(timeout=args.timeout)
    return 0 if all(row['reachable'] for row in results) else 1


if __name__ == '__main__':
    sys.exit(main())
