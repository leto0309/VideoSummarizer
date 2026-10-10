"""Retained-note language versions: one task at a time, original artifacts untouched."""
import argparse
import copy
from datetime import datetime, timezone
import json
import os
from pathlib import Path
from filelock import FileLock, Timeout
from config import ROOT, OUTPUTS
from i18n import LANGUAGES, normalize, tr, validate_language
from local_llm import LocalLLM
from pipeline import render_report, source_context
from storage import Task, _unsafe, guard
from terminology import normalize_terms


def checked_folder(folder):
    path = Path(folder).absolute()
    if any(_unsafe(parent) for parent in (path, *path.parents) if parent.exists()):
        raise ValueError('Linked output paths are not allowed')
    path = path.resolve()
    if path.parent != OUTPUTS.resolve():
        raise ValueError('Only task folders directly inside this project outputs are allowed')
    return path


def available_version(folder, language):
    validate_language(language)
    folder = checked_folder(folder)
    for candidate in (folder, folder / 'translations' / language):
        if not candidate.exists():
            continue
        if any(_unsafe(p) for p in (candidate, *candidate.parents) if p.exists()):
            raise ValueError('Linked translation paths are not allowed')
        for filename in ('metadata.json', 'summary.md'):
            file = candidate / filename
            if file.exists() and _unsafe(file):
                raise ValueError('Linked output files are not allowed')
        try:
            meta = json.loads((candidate / 'metadata.json').read_text(encoding='utf-8'))
            if (meta.get('summary_language', 'zh-TW') == language
                    and (candidate / 'summary.md').is_file()):
                return candidate
        except (OSError, ValueError):
            pass
    return None


def create_version(folder, language):
    validate_language(language)
    folder = checked_folder(folder)
    try:
        with FileLock(str(ROOT / '.pipeline.lock'), timeout=0):
            existing = available_version(folder, language)
            if existing:
                return existing
            # Resolve only the original report; one translation never replaces another's source.
            for filename in ('metadata.json', 'summary.md', 'subtitles.srt'):
                if _unsafe(folder / filename):
                    raise ValueError('Linked source artifacts are not allowed')
            original = json.loads((folder / 'metadata.json').read_text(encoding='utf-8'))
            meta = copy.deepcopy(original)
            source_language = meta.get('summary_language', 'zh-TW')
            target = folder / 'translations' / language
            if target.exists():
                raise ValueError('Incomplete version exists; preserve it for manual inspection')
            parent = target.parent
            parent.mkdir(exist_ok=True)
            if _unsafe(parent):
                raise ValueError('Linked translation directory is not allowed')
            task = Task()
            llm = None
            try:
                summary = meta.get('summary_text')
                # Legacy outputs have retained notes but no standalone summary body.
                needs_model = 'en' in (source_language, language) or not summary
                if needs_model:
                    llm = LocalLLM(meta['model'], language=language)
                    llm.check()
                    llm.unload()
                def convert(text):
                    if not needs_model:
                        return normalize(text, language)
                    # Keep the same conservative input budget as initial analysis.
                    pieces = []
                    while text:
                        end = min(1200, len(text))
                        if end < len(text):
                            boundary = max(text.rfind('\n', 0, end), text.rfind(' ', 0, end))
                            if boundary > 600:
                                end = boundary
                        pieces.append(llm.ask(tr(language, 'translate_prompt') + text[:end], predict=1200))
                        text = text[end:]
                    return normalize_terms('\n'.join(pieces), meta)
                for section in meta['timeline']:
                    section['note'] = convert(section['note'])
                for frame in meta['frames']:
                    frame['description'] = convert(frame['description'])
                if summary:
                    summary = convert(summary)
                else:
                    notes = [tr(language, 'note_subtitle')+s['note'] for s in meta['timeline']]
                    notes += [tr(language, 'note_frame')+f['description'] for f in meta['frames']]
                    summary = llm.merge(notes, source_context(meta))
                if not meta.get('limitation_keys'):
                    meta['limitations'] = [convert(value) for value in meta['limitations']]
                else:
                    meta['limitations'] = [tr(language, key) for key in meta['limitation_keys']]
                meta.update(summary_language=language, summary_text=summary,
                            translation_source_language=source_language,
                            translated_at=datetime.now(timezone.utc).isoformat(),
                            translation_llm_calls=llm.calls if llm else [])
                report = render_report(meta, summary, meta['timeline'])
                encoded = json.dumps(meta, ensure_ascii=False, indent=2)
                guard(extra=len(report.encode('utf-8')) + len(encoded.encode('utf-8')))
                staging = task.path / 'language-version'
                staging.mkdir()
                for name, content in [('summary.md', report), ('metadata.json', encoded)]:
                    with (staging / name).open('w', encoding='utf-8') as handle:
                        handle.write(content)
                        handle.flush()
                        os.fsync(handle.fileno())
                staging.rename(target)
                task.success()
                return target
            except BaseException as exc:
                if task.path.exists():
                    task.fail(exc)
                raise
            finally:
                if llm:
                    try:
                        llm.unload()
                    except Exception:
                        pass
    except Timeout:
        raise RuntimeError(tr(language, 'busy'))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('folder')
    parser.add_argument('--language', choices=LANGUAGES, required=True)
    args = parser.parse_args()
    print(create_version(args.folder, args.language))
