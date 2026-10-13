"""Source-verified ASR spelling corrections; never rewrite the original SRT."""
import re


def verified_terms(meta):
    evidence = '\n'.join(str(meta.get(key) or '') for key in ('title', 'description'))
    evidence += '\n' + '\n'.join(frame.get('description', '') for frame in meta.get('frames', []))
    terms = []
    if re.search(r'\byoinks\b', evidence, re.I):
        terms.append({'canonical': 'Yoinks', 'aliases': ['YawInx', 'Yoyngs'],
                      'source': '视频标题及已确认的项目名称'})
    if re.search(r'\byt-dlp\b', evidence, re.I):
        terms.append({'canonical': 'yt-dlp', 'aliases': ['YT-Dub'],
                      'source': '视频标题、描述或已分析画面中的 yt-dlp 字样'})
    return terms


def normalize_terms(text, meta):
    for term in verified_terms(meta):
        for alias in term['aliases']:
            text = re.sub(r'(?<![A-Za-z0-9_/-])' + re.escape(alias) + r'(?![A-Za-z0-9_/-])',
                          term['canonical'], text, flags=re.I)
    return text
