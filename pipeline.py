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
from i18n import DEFAULT_LANGUAGE, LANGUAGE_NAMES, normalize, tr, validate_language


def run(url, visual=False, model=None, whisper='small', mode='auto', progress=lambda x: None,
        language=DEFAULT_LANGUAGE, ui_language=None):
    validate_language(language)
    ui = validate_language(ui_language or language)
    configure_runtime()
    from downloader import inspect, get_subtitles, download, metadata
    from frames import extract
    from local_llm import LocalLLM
    from speech import transcribe
    model = model or default_model()
    llm = LocalLLM(model, language=language)
    try:
        with FileLock(str(ROOT / '.pipeline.lock'), timeout=0):
            task = Task()
            try:
                progress(tr(ui, 'checking'))
                llm.check()
                llm.unload()
                info = inspect(url, task.path)
                meta = metadata(info, url)
                progress(tr(ui, 'subtitles'))
                cues, source = get_subtitles(info, task.path)
                video = None
                if not cues:
                    from whisper_models import ensure_model
                    progress(tr(ui, 'speech_check'))
                    ensure_model(whisper, progress=lambda _: progress(tr(ui, 'model_downloading')))
                    progress(tr(ui, 'transcribing'))
                    audio = download(info, task.path)
                    cues, source = transcribe(audio, task.path, whisper, mode)
                meta.update(task_id=task.id, transcript_source=source, created_at=datetime.now(timezone.utc).isoformat(),
                            model=model, summary_language=language, ui_language=ui,
                            context_tokens=4096, gpu=gpu_info(), frames=[])
                frame_notes = []
                if visual:
                    progress(tr(ui, 'extracting'))
                    video = download(info, task.path, video=True)
                    frames = extract(video, task.path, info.get('duration'), count=8)
                    for index, frame in enumerate(frames):
                        progress(tr(ui, 'frame_progress', index=index+1, total=len(frames)))
                        nearby = ' '.join(c.text for c in cues
                                          if c.start <= frame['timestamp_seconds']+8 and c.end >= frame['timestamp_seconds']-8)[:650]
                        note = llm.ask(tr(language, 'frame_prompt') + nearby,
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
                    progress(tr(ui, 'chunk_progress', index=index+1, total=len(transcript_chunks)))
                    note = llm.ask(tr(language, 'chunk_prompt')
                                   + normalize_terms(chunk, meta))
                    note = normalize_terms(note, meta)
                    times = re.findall(r'\[(\d{2,}:\d{2}:\d{2}\.\d{3})–(\d{2,}:\d{2}:\d{2}\.\d{3})\]', chunk)
                    sections.append({'start': times[0][0], 'end': times[-1][1], 'note': note})
                progress(tr(ui, 'merging', language=LANGUAGE_NAMES[language]))
                summary = llm.merge([tr(language, 'note_subtitle')+s['note'] for s in sections]
                                    + [tr(language, 'note_frame')+n for n in frame_notes], source_context(meta))
                meta['summary_text'] = summary
                meta['llm_calls'] = llm.calls
                meta['timeline'] = sections
                meta['visual_enabled'] = visual
                meta['verified_terminology'] = verified_terms(meta)
                meta['limitation_keys'] = ['limit_model', 'limit_frames' if visual else 'limit_no_frames']
                meta['limitations'] = [tr(language, key) for key in meta['limitation_keys']]
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
                progress(tr(ui, 'cleaned'))
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
        raise RuntimeError(tr(ui, 'busy'))


def render_report(meta, summary, sections):
    language = validate_language(meta.get('summary_language', DEFAULT_LANGUAGE))
    # Convert generated prose only; preserve source titles, names and URLs.
    summary = normalize(summary, language)
    title = (meta.get('title') or tr(language, 'video')).replace('\n', ' ')
    url = meta.get('webpage_url') or meta['original_url']
    lines = [f'# {title}', '', f'- {tr(language, "source")}：{url}',
             f'- {tr(language, "author")}：{meta.get("uploader") or tr(language, "unknown")}',
             f'- {tr(language, "duration")}：{stamp(meta.get("duration") or 0)}',
             f'- {tr(language, "subtitle_source")}：{meta["transcript_source"]["type"]}',
             f'- {tr(language, "local_model")}：{meta["model"]}',
             f'- {tr(language, "summary_language")}：{LANGUAGE_NAMES[language]}',
             f'- {tr(language, "references")}：subtitles.srt、metadata.json', '', summary, '',
             '## ' + tr(language, 'timeline')]
    for section in sections:
        lines += ['', f'### {section["start"]} – {section["end"]}', normalize(section['note'], language)]
    if meta['frames']:
        lines += ['', '## ' + tr(language, 'frames'), '', tr(language, 'frame_retained')]
        for frame in meta['frames']:
            lines += ['', f'### {frame["timestamp"]}', normalize(frame['description'], language)]
    limits = ([tr(language, key) for key in meta['limitation_keys']] if meta.get('limitation_keys')
              else [normalize(value, language) for value in meta['limitations']])
    lines += ['', '## ' + tr(language, 'limitations'), '', *['- '+value for value in limits]]
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
    parser.add_argument('--language', choices=('zh-CN', 'zh-TW', 'en'), default=DEFAULT_LANGUAGE)
    args = parser.parse_args()
    print(run(args.url, args.visual, args.model, mode='cpu' if args.cpu else 'auto',
              language=args.language, progress=print))
