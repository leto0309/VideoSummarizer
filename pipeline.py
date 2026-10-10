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
                progress('检查本机模型与视频访问权限')
                llm.check()
                llm.unload()
                info = inspect(url, task.path)
                meta = metadata(info, url)
                progress('寻找可公开取得的字幕')
                cues, source = get_subtitles(info, task.path)
                video = None
                if not cues:
                    from whisper_models import ensure_model
                    progress('无字幕，检查 Whisper small 语音模型（首次可能需要下载）')
                    ensure_model(whisper, progress=progress)
                    progress('无字幕，下载音频并使用 Whisper 转录')
                    audio = download(info, task.path)
                    cues, source = transcribe(audio, task.path, whisper, mode)
                meta.update(task_id=task.id, transcript_source=source, created_at=datetime.now(timezone.utc).isoformat(),
                            model=model, summary_language='zh-CN', context_tokens=4096, gpu=gpu_info(), frames=[])
                frame_notes = []
                if visual:
                    progress('下载低分辨率视频并撷取约 8 张代表画面')
                    video = download(info, task.path, video=True)
                    frames = extract(video, task.path, info.get('duration'), count=8)
                    for index, frame in enumerate(frames):
                        progress(f'本机视觉分析 {index+1}/{len(frames)}')
                        nearby = ' '.join(c.text for c in cues
                                          if c.start <= frame['timestamp_seconds']+8 and c.end >= frame['timestamp_seconds']-8)[:650]
                        note = llm.ask('描述此代表画面的可见文字、物件或图表，约 150 字。'
                                       '字幕仅作辅助，不能把字幕叙述当成画面可见事实。\n邻近字幕：' + nearby,
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
                    note = llm.ask('整理这段字幕的重点、因果关系和实际提及的概念，约 200 字。\n'
                                   + normalize_terms(chunk, meta))
                    note = normalize_terms(note, meta)
                    times = re.findall(r'\[(\d{2,}:\d{2}:\d{2}\.\d{3})–(\d{2,}:\d{2}:\d{2}\.\d{3})\]', chunk)
                    sections.append({'start': times[0][0], 'end': times[-1][1], 'note': note})
                progress('合成简体中文摘要与可核对时间轴')
                summary = llm.merge(['字幕来源：'+s['note'] for s in sections]
                                    + ['画面可见资料：'+n for n in frame_notes], source_context(meta))
                meta['llm_calls'] = llm.calls
                meta['timeline'] = sections
                meta['visual_enabled'] = visual
                meta['verified_terminology'] = verified_terms(meta)
                meta['limitations'] = ['模型生成的理解可能有误，请对照 SRT 与原视频。',
                                       '约 8 张均匀取样代表画面不代表完整视觉内容。' if visual else '未分析画面。']
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
                progress('摘要、SRT、metadata 已保存，媒体暂存已删除')
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
        raise RuntimeError('另一个任务正在处理，请等待完成；全程只允许一个任务。')


def render_report(meta, summary, sections):
    from opencc import OpenCC
    cc = OpenCC('t2s')
    # Convert generated prose only; preserve source titles, names and URLs.
    summary = cc.convert(summary)
    title = (meta.get('title') or '视频').replace('\n', ' ')
    url = meta.get('webpage_url') or meta['original_url']
    lines = [f'# {title}', '', f'- 来源：{url}', f'- 作者：{meta.get("uploader") or "未知"}',
             f'- 长度：{stamp(meta.get("duration") or 0)}',
             f'- 字幕来源：{meta["transcript_source"]["type"]}', f'- 本机模型：{meta["model"]}',
             '- 对照文件：subtitles.srt、metadata.json', '', summary, '', '## 字幕时间轴（来源时间）']
    for section in sections:
        lines += ['', f'### {section["start"]} – {section["end"]}', cc.convert(section['note'])]
    if meta['frames']:
        lines += ['', '## 代表画面（FFmpeg 实际帧 PTS）', '',
                  '截图已依要求清理；时间、帧 SHA256 与画面描述保留于 metadata，可回原视频核对。']
        for frame in meta['frames']:
            lines += ['', f'### {frame["timestamp"]}', cc.convert(frame['description'])]
    lines += ['', '## 核对与限制', '', *['- '+cc.convert(value) for value in meta['limitations']]]
    return normalize_terms('\n'.join(lines) + '\n', meta)


def source_context(meta):
    """Ground spelling in original title/description and the clearest English OCR passage."""
    frames = meta.get('frames') or []
    best = max(frames, key=lambda f: sum(c.isascii() and c.isalpha() for c in f['description']), default={})
    title = str(meta.get('title') or '')[:120]
    description = str(meta.get('description') or '')[:100]
    return f'原始视频标题：{title}\n原始说明：{description}\n可见画面字样：\n' + best.get('description', '')[:620]


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('url')
    parser.add_argument('--visual', action='store_true')
    parser.add_argument('--model', default=None)
    parser.add_argument('--cpu', action='store_true')
    args = parser.parse_args()
    print(run(args.url, args.visual, args.model, mode='cpu' if args.cpu else 'auto', progress=print))
