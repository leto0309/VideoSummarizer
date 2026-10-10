"""Regenerate Markdown from retained notes without redownloading media; SRT stays original."""
import argparse
import json
from pathlib import Path
from filelock import FileLock
from config import ROOT, OUTPUTS
from local_llm import LocalLLM
from pipeline import render_report, source_context
from terminology import normalize_terms, verified_terms
from i18n import DEFAULT_LANGUAGE, LANGUAGES, tr, validate_language


def refresh(folder, language=DEFAULT_LANGUAGE):
    validate_language(language)
    folder = Path(folder).resolve()
    if not folder.is_relative_to(OUTPUTS.resolve()) or folder == OUTPUTS.resolve():
        raise ValueError('只允许本项目 outputs 内的任务文件夹')
    with FileLock(str(ROOT / '.pipeline.lock'), timeout=0):
        meta = json.loads((folder / 'metadata.json').read_text(encoding='utf-8'))
        if meta.get('summary_language', 'zh-TW') != language:
            raise ValueError('Use summary_versions.py --language to preserve the original language version')
        llm = LocalLLM(meta['model'], language=language)
        try:
            llm.check()
            notes = [tr(language, 'note_subtitle')+normalize_terms(s['note'], meta) for s in meta['timeline']]
            notes += [tr(language, 'note_frame')+normalize_terms(f['description'], meta) for f in meta['frames']]
            summary = llm.merge(notes, source_context(meta))
            meta['summary_language'] = language
            meta['summary_text'] = summary
            (folder / 'summary.md').write_text(render_report(meta, summary, meta['timeline']), encoding='utf-8')
            meta['llm_calls'] += llm.calls
            meta['summary_refreshed_from_retained_notes'] = True
            meta['verified_terminology'] = verified_terms(meta)
            (folder / 'metadata.json').write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding='utf-8')
        finally:
            llm.unload()
    print(folder)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('folder')
    parser.add_argument('--language', choices=LANGUAGES, default=DEFAULT_LANGUAGE)
    args = parser.parse_args()
    refresh(args.folder, args.language)
