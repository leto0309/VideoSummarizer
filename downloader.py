from pathlib import Path
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode
import yt_dlp
from config import ffmpeg, TEMP_LIMIT, RESERVE, node_runtime
from storage import guard, size
from subtitles import parse


def validate_url(url):
    value = urlparse(url.strip())
    host = (value.hostname or '').lower()
    allowed = ('bilibili.com', 'b23.tv', 'youtube.com', 'youtu.be')
    if value.scheme != 'https' or value.username or value.password or value.port not in (None, 443):
        raise ValueError('请输入 HTTPS 的 Bilibili、b23.tv 或 YouTube 链接')
    if not any(host == h or host.endswith('.'+h) for h in allowed):
        raise ValueError('只支持 Bilibili、b23.tv 与 YouTube')
    return url.strip()


def options(task):
    result = {'quiet': True, 'noprogress': True, 'no_warnings': False, 'noplaylist': True, 'playlist_items': '1',
            'socket_timeout': 30, 'retries': 2, 'fragment_retries': 2,
            'outtmpl': str(task / 'media.%(ext)s'), 'ffmpeg_location': ffmpeg(),
            'progress_hooks': [lambda _: guard()], 'continuedl': False,
            'overwrites': False, 'concurrent_fragment_downloads': 1,
            'max_filesize': max(1, (TEMP_LIMIT - RESERVE - size()) // 3),
            'buffersize': 65536, 'http_chunk_size': 1024**2,
            'allow_unplayable_formats': False, 'cachedir': False}
    node = node_runtime()
    if node:
        result['js_runtimes'] = {'node': {'path': node}}
    result['remote_components'] = []  # use only the installed official yt-dlp-ejs package
    return result


def inspect(url, task):
    opts = options(task)
    # Subtitle-only processing must remain possible even without a playable media format.
    opts['ignore_no_formats_error'] = True
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(validate_url(url), download=False)
    if not info or info.get('_type') in ('playlist', 'multi_video') or info.get('is_live'):
        raise RuntimeError('此工具只处理单支已完成的视频；不处理播放清单或直播')
    if info.get('has_drm') or info.get('availability') in ('premium_only', 'subscriber_only', 'needs_auth', 'private'):
        raise RuntimeError('内容需要付费、登录或 DRM，已停止；不绕过访问限制')
    return info


def metadata(info, original_url):
    fields = ('id', 'title', 'uploader', 'uploader_id', 'duration', 'upload_date', 'webpage_url',
              'extractor', 'description', 'chapters')
    data = {key: info.get(key) for key in fields}
    # Preserve only playback selectors; remove shared-link tracking parameters.
    if data.get('webpage_url'):
        parsed = urlparse(data['webpage_url'])
        query = parse_qs(parsed.query)
        keep = {k: query[k][0] for k in ('p', 'v') if k in query}
        data['webpage_url'] = urlunparse(parsed._replace(query=urlencode(keep), fragment=''))
    data['original_url'] = original_url
    # Signed stream URLs and platform authentication data are intentionally not exported.
    return data


def get_subtitles(info, task):
    candidates = []
    for source, tracks in [('manual', info.get('subtitles') or {}), ('automatic', info.get('automatic_captions') or {})]:
        for lang, formats in tracks.items():
            if lang == 'live_chat':
                continue
            rank = 0 if lang.lower().startswith(('zh', 'ai-zh')) else (1 if lang.startswith('en') else 2)
            for track in formats:
                ext = track.get('ext')
                if ext in ('srt', 'vtt', 'json', 'json3'):
                    candidates.append((source != 'manual', rank, lang, track))
    candidates.sort(key=lambda item: item[:3])
    errors = []
    with yt_dlp.YoutubeDL(options(task)) as ydl:
        for auto, _, lang, track in candidates:
            try:
                if 'data' in track:
                    text = track['data']
                else:
                    # yt-dlp's networking preserves extractor headers; no cookies are configured.
                    headers = dict(info.get('http_headers') or {})
                    headers.update(track.get('http_headers') or {})
                    from yt_dlp.networking import Request
                    with ydl.urlopen(Request(track['url'], headers=headers)) as response:
                        raw = response.read(16 * 1024**2 + 1)
                    if len(raw) > 16 * 1024**2:
                        raise RuntimeError('字幕超过 16 MB 限制')
                    text = raw.decode('utf-8-sig')
                cues = parse(text, track['ext'])
                if cues:
                    return cues, {'type': 'automatic' if auto else 'manual', 'language': lang}
            except Exception as exc:
                errors.append(str(exc)[:300])
    if candidates and errors:
        raise RuntimeError('平台列出字幕但无法读取，已停止以避免绕过限制：' + errors[0])
    return [], {'type': 'none', 'language': None}


def download(info, task, video=False):
    if not info.get('formats') and not info.get('url'):
        raise RuntimeError('平台没有提供可公开下载的媒体格式；已停止，不尝试登录或绕过限制。')
    guard()
    opts = options(task)
    opts['format'] = ('best[height<=480][vcodec!=none][acodec!=none]/bestvideo[height<=480]/worstvideo/worst[vcodec!=none]' if video
                      else 'bestaudio/best')
    opts['outtmpl'] = str(task / ('video.%(ext)s' if video else 'audio.%(ext)s'))
    with yt_dlp.YoutubeDL(opts) as ydl:
        # extract_info(download=False) contains postprocessors for its default format.
        # Re-extract with the explicit audio/video selector to avoid reusing those merge plans.
        result = ydl.extract_info(validate_url(info['webpage_url']), download=True)
        if result.get('id') != info.get('id'):
            raise RuntimeError('下载的视频 ID 与先前验证不符，停止处理')
        path = Path(ydl.prepare_filename(result))
    guard()
    if not path.is_file():
        matches = list(task.glob(('video' if video else 'audio') + '.*'))
        matches = [p for p in matches if p.suffix not in ('.part', '.ytdl')]
        if len(matches) != 1:
            raise RuntimeError('下载完成但找不到唯一媒体文件')
        path = matches[0]
    return path
