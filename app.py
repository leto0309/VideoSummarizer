from datetime import datetime, timezone
from pathlib import Path
import json
import traceback
import streamlit as st
from app_version import get_version_info
from config import ALLOWED_MODELS, ROOT, default_model, gpu_info
from i18n import LANGUAGES, LANGUAGE_NAMES, friendly_error, tr
from links import extract_url
import preferences
from pipeline import run
from summary_versions import available_version, create_version

prefs = preferences.load()
st.session_state.setdefault('ui_language', prefs['ui_language'])
st.session_state.setdefault('summary_language', prefs['summary_language'])
ui = st.session_state['ui_language']
st.set_page_config(page_title=tr(ui, 'title'), page_icon='🎬', layout='wide')
left, right = st.columns(2)
with left:
    ui = st.selectbox(tr(ui, 'language'), LANGUAGES, format_func=LANGUAGE_NAMES.get, key='ui_language')
with right:
    selection = st.selectbox(tr(ui, 'summary_language'), ('follow', *LANGUAGES),
                            format_func=lambda code: tr(ui, 'follow') if code == 'follow' else LANGUAGE_NAMES[code],
                            key='summary_language')
language = ui if selection == 'follow' else selection
if prefs != {'ui_language': ui, 'summary_language': selection}:
    try:
        preferences.save(ui, selection)
    except OSError:
        st.warning(tr(ui, 'preferences_failed'))
st.title('🎬 ' + tr(ui, 'title'))
version_info = get_version_info()
st.caption('VideoSummarizer · ' + tr(ui, 'app_version', version=version_info.version))
st.caption(tr(ui, 'caption') + ' · ' + LANGUAGE_NAMES[language])
with st.expander(tr(ui, 'about')):
    st.write(tr(ui, 'app_version', version=version_info.version))
    st.write(tr(ui, 'app_edition', edition=tr(ui, 'edition_' + version_info.edition)))
    st.markdown(f'[{tr(ui, "release_notes")}]({version_info.release_url})')
    st.caption(tr(ui, 'running_version_help'))
if version_info.build_status != 'ok':
    st.warning(tr(ui, 'version_' + version_info.build_status))
gpu = gpu_info()
name = gpu['name'] if gpu['vram_mib'] else tr(ui, 'no_gpu')
st.info(tr(ui, 'gpu', name=name, memory=gpu['vram_mib']))
with st.expander(tr(ui, 'model_status')):
    from whisper_models import cached_model
    if cached_model():
        st.success(tr(ui, 'model_ready'))
    else:
        st.warning(tr(ui, 'model_missing'))
        st.write(tr(ui, 'model_help'))
# Stable keys and immediate commits preserve inputs across language changes.
url = st.text_input(tr(ui, 'url'), placeholder='https://www.bilibili.com/video/...', key='video_url')
link = extract_url(url)
if link and link != url.strip():
    st.caption(tr(ui, 'url_extracted', url=link))
visual = st.checkbox(tr(ui, 'visual'), value=False, key='visual')
model = st.selectbox(tr(ui, 'model'), ALLOWED_MODELS,
                     index=ALLOWED_MODELS.index(default_model()), key='model')
mode = st.selectbox(tr(ui, 'mode'), ('auto', 'cpu'), index=1, format_func=lambda code: tr(ui, code), key='mode')
lawful = st.checkbox(tr(ui, 'lawful'), key='lawful')

def show_error(exc):
    # Called after the status block closes, so the message is not hidden in the collapsed status.
    try:
        logs = ROOT / 'logs'
        logs.mkdir(exist_ok=True)
        with (logs / 'app-errors.log').open('a', encoding='utf-8') as handle:
            handle.write(datetime.now(timezone.utc).isoformat() + '\n')
            traceback.print_exception(exc, file=handle)
    except OSError:
        pass
    st.error(friendly_error(exc, ui))
    st.caption(tr(ui, 'failure_temp'))

if st.button(tr(ui, 'start'), type='primary', key='generate'):
    if not lawful:
        st.warning(tr(ui, 'consent'))
    else:
        failure = None
        with st.status(tr(ui, 'processing'), expanded=True) as status:
            try:
                folder = run(link, visual, model, mode=mode, language=language,
                             ui_language=ui, progress=status.write)
                st.session_state['result'] = str(folder)
                status.update(label=tr(ui, 'done'), state='complete')
            except Exception as exc:
                status.update(label=tr(ui, 'stopped'), state='error')
                failure = exc
        if failure:
            show_error(failure)
if 'result' in st.session_state:
    folder = Path(st.session_state['result'])
    version = available_version(folder, language) or folder
    meta = json.loads((version / 'metadata.json').read_text(encoding='utf-8'))
    actual_language = meta.get('summary_language', 'zh-TW')
    st.success(tr(ui, 'saved', folder=str(folder)))
    st.caption(tr(ui, 'existing_language', language=LANGUAGE_NAMES.get(actual_language, actual_language)))
    if actual_language != language:
        st.caption(tr(ui, 'version_help'))
        if st.button(tr(ui, 'make_version', language=LANGUAGE_NAMES[language]), key='translate'):
            failure = None
            with st.status(tr(ui, 'processing'), expanded=True) as status:
                try:
                    create_version(folder, language)
                    status.update(label=tr(ui, 'done'), state='complete')
                    st.rerun()
                except Exception as exc:
                    status.update(label=tr(ui, 'stopped'), state='error')
                    failure = exc
            if failure:
                show_error(failure)
    for filename, mime in [('summary.md', 'text/markdown'), ('subtitles.srt', 'text/plain'), ('metadata.json', 'application/json')]:
        source = folder if filename == 'subtitles.srt' else version
        download_name = filename if version == folder or filename == 'subtitles.srt' else filename.replace('.', '.' + language + '.', 1)
        st.download_button(tr(ui, 'download', filename=download_name), (source / filename).read_bytes(),
                           file_name=download_name, mime=mime, key='download_' + filename)
    st.markdown((version / 'summary.md').read_text(encoding='utf-8'))
