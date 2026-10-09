import json
import streamlit as st
from config import ALLOWED_MODELS, OUTPUTS, default_model, gpu_info
from pipeline import run

st.set_page_config(page_title='本機影片摘要', page_icon='🎬', layout='wide')
st.title('🎬 本機影片摘要')
st.caption('免費本機 AI · 繁體中文 · 字幕優先 · 單一任務序列處理')
gpu = gpu_info()
st.info(f'{gpu["name"]}｜VRAM {gpu["vram_mib"]} MiB｜Whisper 預設 small，CUDA 不相容時自動使用 CPU int8')
with st.form('video'):
    url = st.text_input('Bilibili、b23.tv 或 YouTube 連結', placeholder='https://www.bilibili.com/video/...')
    visual = st.checkbox('加入約 8 張代表畫面的本機分析（需額外下載低解析度影片）', value=False)
    model = st.selectbox('本機視覺語言模型', ALLOWED_MODELS, index=ALLOWED_MODELS.index(default_model()))
    mode = st.selectbox('語音辨識運算', ['自動：CUDA → CPU', '只用 CPU int8'])
    lawful = st.checkbox('我確認有權存取及處理此影片；此工具不繞過登入、付費、DRM 或平台限制。')
    submit = st.form_submit_button('開始產生摘要', type='primary')
if submit:
    if not lawful:
        st.warning('請先確認你有權處理這支影片。')
    else:
        with st.status('處理中，請保持頁面開啟', expanded=True) as status:
            try:
                folder = run(url, visual, model, mode='cpu' if mode.startswith('只用') else 'auto', progress=status.write)
                st.session_state['result'] = str(folder)
                status.update(label='完成', state='complete')
            except Exception as exc:
                status.update(label='處理停止', state='error')
                st.error(str(exc))
                st.caption('失敗暫存保留 24 小時；下次任務自動清理過期的專案暫存。')
if 'result' in st.session_state:
    from pathlib import Path
    folder = Path(st.session_state['result'])
    st.success(f'產出已保留：{folder}')
    for filename, mime in [('summary.md', 'text/markdown'), ('subtitles.srt', 'text/plain'), ('metadata.json', 'application/json')]:
        st.download_button('下載 ' + filename, (folder / filename).read_bytes(), file_name=filename, mime=mime)
    st.markdown((folder / 'summary.md').read_text(encoding='utf-8'))
