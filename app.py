import json
import streamlit as st
from config import ALLOWED_MODELS, OUTPUTS, default_model, gpu_info
from pipeline import run

st.set_page_config(page_title='本机视频摘要', page_icon='🎬', layout='wide')
st.title('🎬 本机视频摘要')
st.caption('免费本机 AI · 简体中文 · 字幕优先 · 单一任务序列处理')
gpu = gpu_info()
st.info(f'{gpu["name"]}｜VRAM {gpu["vram_mib"]} MiB｜Whisper 默认 small，CUDA 不兼容时自动使用 CPU int8')
with st.expander('Whisper 语音模型状态 / 下载失败处理'):
    from whisper_models import cached_model
    if cached_model():
        st.success('Whisper small 必要文件已就绪；转录时使用本机文件，不再连接下载。')
    else:
        st.warning('Whisper small 尚未准备完成。有字幕的视频可直接处理；无字幕视频需先下载语音模型。')
        st.write('双击软件文件夹中的 prepare-whisper.bat 预先下载（约 464 MiB）。'
                 '如果 Hugging Face 无法连接，可复制其他电脑已下载的 models/whisper 文件夹；'
                 '也可将官方模型文件放到 models/whisper/small。详见 README。')
with st.form('video'):
    url = st.text_input('Bilibili、b23.tv 或 YouTube 链接', placeholder='https://www.bilibili.com/video/...')
    visual = st.checkbox('加入约 8 张代表画面的本机分析（需额外下载低分辨率视频）', value=False)
    model = st.selectbox('本机视觉语言模型', ALLOWED_MODELS, index=ALLOWED_MODELS.index(default_model()))
    mode = st.selectbox('语音识别运算', ['自动：CUDA → CPU', '只用 CPU int8'])
    lawful = st.checkbox('我确认有权访问及处理此视频；此工具不绕过登录、付费、DRM 或平台限制。')
    submit = st.form_submit_button('开始生成摘要', type='primary')
if submit:
    if not lawful:
        st.warning('请先确认你有权处理这支视频。')
    else:
        with st.status('处理中，请保持页面开启', expanded=True) as status:
            try:
                folder = run(url, visual, model, mode='cpu' if mode.startswith('只用') else 'auto', progress=status.write)
                st.session_state['result'] = str(folder)
                status.update(label='完成', state='complete')
            except Exception as exc:
                status.update(label='处理停止', state='error')
                st.error(str(exc))
                st.caption('失败暂存保留 24 小时；下次任务自动清理过期的项目暂存。')
if 'result' in st.session_state:
    from pathlib import Path
    folder = Path(st.session_state['result'])
    st.success(f'产出已保留：{folder}')
    for filename, mime in [('summary.md', 'text/markdown'), ('subtitles.srt', 'text/plain'), ('metadata.json', 'application/json')]:
        st.download_button('下载 ' + filename, (folder / filename).read_bytes(), file_name=filename, mime=mime)
    st.markdown((folder / 'summary.md').read_text(encoding='utf-8'))
