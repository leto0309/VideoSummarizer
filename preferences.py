"""Persist only project-local language preferences."""
import json
import os
from pathlib import Path
import tempfile
from config import ROOT
from i18n import DEFAULT_LANGUAGE, LANGUAGES

PATH = ROOT / 'language-settings.json'

def load():
    defaults = {'ui_language': DEFAULT_LANGUAGE, 'summary_language': 'follow'}
    try:
        data = json.loads(PATH.read_text(encoding='utf-8'))
        if data.get('ui_language') in LANGUAGES:
            defaults['ui_language'] = data['ui_language']
        if data.get('summary_language') in (*LANGUAGES, 'follow'):
            defaults['summary_language'] = data['summary_language']
    except (OSError, ValueError, AttributeError):
        pass
    return defaults

def save(ui_language, summary_language):
    if ui_language not in LANGUAGES or summary_language not in (*LANGUAGES, 'follow'):
        raise ValueError('Unsupported language preference')
    fd, name = tempfile.mkstemp(prefix='.language-', suffix='.tmp', dir=PATH.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as handle:
            json.dump({'ui_language': ui_language, 'summary_language': summary_language}, handle)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(name, PATH)
    finally:
        Path(name).unlink(missing_ok=True)
