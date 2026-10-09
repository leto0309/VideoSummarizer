from dataclasses import dataclass
from datetime import timedelta
import html
import json
import re
import srt


@dataclass
class Cue:
    start: float
    end: float
    text: str


def stamp(seconds):
    value = max(0, round(float(seconds) * 1000))
    h, rem = divmod(value, 3600000)
    m, rem = divmod(rem, 60000)
    s, ms = divmod(rem, 1000)
    return f'{h:02}:{m:02}:{s:02}.{ms:03}'


def _seconds(text):
    parts = text.replace(',', '.').split(':')
    return sum(float(v) * 60**i for i, v in enumerate(reversed(parts)))


def parse(text, ext):
    if ext == 'json':
        cues = [Cue(float(c['from']), float(c['to']), c['content'])
                for c in json.loads(text).get('body', [])]
    elif ext == 'json3':
        cues = [Cue(e['tStartMs']/1000, (e['tStartMs']+e.get('dDurationMs', 0))/1000,
                    ''.join(x.get('utf8', '') for x in e.get('segs', [])))
                for e in json.loads(text).get('events', []) if e.get('segs')]
    elif ext == 'srt':
        cues = [Cue(c.start.total_seconds(), c.end.total_seconds(), c.content) for c in srt.parse(text)]
    elif ext == 'vtt':
        cues = []
        for block in re.split(r'\r?\n\s*\r?\n', text):
            match = re.search(r'(\d{1,2}:\d{2}(?::\d{2})?[.,]\d{3})\s+-->\s+(\d{1,2}:\d{2}(?::\d{2})?[.,]\d{3})[^\n]*\n(.*)', block, re.S)
            if match:
                cues.append(Cue(_seconds(match[1]), _seconds(match[2]), match[3]))
    else:
        raise ValueError(f'未支援的字幕格式：{ext}')
    cleaned = []
    for cue in cues:
        cue.text = html.unescape(re.sub(r'<[^>]*>', '', cue.text)).strip()
        if cue.text and cue.end > cue.start >= 0:
            cleaned.append(cue)
    return sorted(cleaned, key=lambda c: (c.start, c.end))


def to_srt(cues):
    return srt.compose([srt.Subtitle(i, timedelta(seconds=c.start), timedelta(seconds=c.end), c.text)
                        for i, c in enumerate(cues, 1)])


def chunks(cues, budget=1500):
    """Conservative character budget (CJK can exceed one token per character)."""
    chunk, count = [], 0
    for cue in cues:
        for offset in range(0, len(cue.text), 600):
            text = cue.text[offset:offset+600]
            line = f'[{stamp(cue.start)}–{stamp(cue.end)}] {text}'
            if chunk and count + len(line) > budget:
                yield '\n'.join(chunk)
                chunk, count = [], 0
            chunk.append(line)
            count += len(line)
    if chunk:
        yield '\n'.join(chunk)
