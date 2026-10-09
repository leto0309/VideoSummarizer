import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
from filelock import FileLock, Timeout
from config import ROOT, OUTPUTS, configure_runtime, default_model, gpu_info
from storage import Task, guard
from subtitles import chunks, stamp, to_srt
from terminology import normalize_terms, verified_terms


def run(url, visual=False, model=None, whisper='small', mode='auto', progress=lambda x: None):
    configure_runtime()
    from downloader import inspect, get_subtitles, download, metadata
    from frames import extract
    from local_llm import LocalLLM
    from speech import transcribe
    model = model or default_model()
    llm = LocalLLM(model)
    try:
        with FileLock(str(ROOT / '.pipeline.lock'), timeout=0):
            task = Task()
            try:
                progress('檢查本機模型與影片存取權限')
                llm.check()
                llm.unload()
                info = inspect(url, task.path)
                meta = metadata(info, url)
                progress('尋找可公開取得的字幕')
                cues, source = get_subtitles(info, task.path)
                video = None
                if not cues:
                    progress('無字幕，下載音訊並使用 Whisper 轉錄')
                    audio = download(info, task.path)
                    cues, source = transcribe(audio, task.path, whisper, mode)
                meta.update(task_id=task.id, transcript_source=source, created_at=datetime.now(timezone.utc).isoformat(),
                            model=model, context_tokens=4096, gpu=gpu_info(), frames=[])
                frame_notes = []
                if visual:
                    progress('下載低解析度影片並擷取約 8 張代表畫面')
                    video = download(info, task.path, video=True)
                    frames = extract(video, task.path, info.get('duration'), count=8)
                    for index, frame in enumerate(frames):
                        progress(f'本機視覺分析 {index+1}/{len(frames)}')
                        nearby = ' '.join(c.text for c in cues
                                          if c.start <= frame['timestamp_seconds']+8 and c.end >= frame['timestamp_seconds']-8)[:650]
                        note = llm.ask('描述此代表畫面的可見文字、物件或圖表，約 150 字。'
                                       '字幕僅作輔助，不能把字幕敘述當成画面可見事實。\n鄰近字幕：' + nearby,
                                       image=frame['path'])
                        note = normalize_terms(note, meta)
                        data = {k: v for k, v in frame.items() if k != 'path'}
                        data['sha256'] = hashlib.sha256(Path(frame['path']).read_bytes()).hexdigest()
                        data['description'] = note
                        meta['frames'].append(data)
                        frame_notes.append(note)
                sections = []
                transcript_chunks = list(chunks(cues))
                for index, chunk in enumerate(transcript_chunks):
                    progress(f'字幕分段摘要 {index+1}/{len(transcript_chunks)}')
                    note = llm.ask('整理這段字幕的重點、因果關係和實際提及的概念，約 200 字。\n'
                                   + normalize_terms(chunk, meta))
                    note = normalize_terms(note, meta)
                    times = re.findall(r'\[(\d{2,}:\d{2}:\d{2}\.\d{3})–(\d{2,}:\d{2}:\d{2}\.\d{3})\]', chunk)
                    sections.append({'start': times[0][0], 'end': times[-1][1], 'note': note})
                progress('合成繁體中文摘要與可核對時間軸')
                summary = llm.merge(['字幕來源：'+s['note'] for s in sections]
                                    + ['畫面可見資料：'+n for n in frame_notes], source_context(meta))
                meta['llm_calls'] = llm.calls
                meta['timeline'] = sections
                meta['visual_enabled'] = visual
                meta['verified_terminology'] = verified_terms(meta)
                meta['limitations'] = ['模型生成的理解可能有誤，請對照 SRT 與原影片。',
                                       '約 8 張均勻取樣代表畫面不代表完整視覺內容。' if visual else '未分析畫面。']
                report = render_report(meta, summary, sections)
                guard(extra=len(report.encode('utf-8')) + len(to_srt(cues).encode('utf-8')))
                OUTPUTS.mkdir(exist_ok=True)
                folder = OUTPUTS / (datetime.now().strftime('%Y%m%d_%H%M%S') + '_' + task.id[:8])
                staging = task.path / 'pending-output'
                staging.mkdir()
                (staging / 'summary.md').write_text(report, encoding='utf-8')
                (staging / 'subtitles.srt').write_text(to_srt(cues), encoding='utf-8')
                (staging / 'metadata.json').write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding='utf-8')
                # Publish only after every required artifact is durable.
                for file in staging.iterdir():
                    # Windows _commit requires a descriptor opened for writing.
                    with file.open('rb+') as handle:
                        handle.flush()
                        os.fsync(handle.fileno())
                staging.rename(folder)
                task.success()
                progress('摘要、SRT、metadata 已儲存，媒體暫存已刪除')
                return folder
            except BaseException as exc:
                if task.path.exists():
                    task.fail(exc)
                raise
            finally:
                try:
                    llm.unload()
                except Exception:
                    pass
    except Timeout:
        raise RuntimeError('另一個任務正在處理，請等待完成；全程只允許一個任務。')


def render_report(meta, summary, sections):
    title = (meta.get('title') or '影片').replace('\n', ' ')
    url = meta.get('webpage_url') or meta['original_url']
    lines = [f'# {title}', '', f'- 來源：{url}', f'- 作者：{meta.get("uploader") or "未知"}',
             f'- 長度：{stamp(meta.get("duration") or 0)}',
             f'- 字幕來源：{meta["transcript_source"]["type"]}', f'- 本機模型：{meta["model"]}',
             '- 對照檔：subtitles.srt、metadata.json', '', summary, '', '## 字幕時間軸（來源時間）']
    for section in sections:
        lines += ['', f'### {section["start"]} – {section["end"]}', section['note']]
    if meta['frames']:
        lines += ['', '## 代表畫面（FFmpeg 實際影格 PTS）', '',
                  '截圖已依要求清理；時間、影格 SHA256 與畫面描述保留於 metadata，可回原影片核對。']
        for frame in meta['frames']:
            lines += ['', f'### {frame["timestamp"]}', frame['description']]
    lines += ['', '## 核對與限制', '', *['- '+value for value in meta['limitations']]]
    from opencc import OpenCC
    return normalize_terms(OpenCC('s2twp').convert('\n'.join(lines) + '\n'), meta)


def source_context(meta):
    """Ground spelling in original title/description and the clearest English OCR passage."""
    frames = meta.get('frames') or []
    best = max(frames, key=lambda f: sum(c.isascii() and c.isalpha() for c in f['description']), default={})
    title = str(meta.get('title') or '')[:120]
    description = str(meta.get('description') or '')[:100]
    return f'原始影片標題：{title}\n原始說明：{description}\n可见畫面字樣：\n' + best.get('description', '')[:620]


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('url')
    parser.add_argument('--visual', action='store_true')
    parser.add_argument('--model', default=None)
    parser.add_argument('--cpu', action='store_true')
    args = parser.parse_args()
    print(run(args.url, args.visual, args.model, mode='cpu' if args.cpu else 'auto', progress=print))
