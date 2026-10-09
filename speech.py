import gc
import json
import os
import subprocess
import sys
from config import MODELS, ROOT, configure_runtime
from subtitles import Cue


def transcribe(audio, task, model='small', mode='auto'):
    """CUDA runs in a separate process, so a missing native DLL cannot kill Streamlit."""
    target = task / 'transcript.json'
    attempts = ['cuda', 'cpu'] if mode == 'auto' else ['cpu']
    errors = []
    for device in attempts:
        result = subprocess.run([sys.executable, str(ROOT / 'speech.py'), str(audio), str(target),
                                 model, device], capture_output=True, text=True, encoding='utf-8',
                                errors='replace', timeout=14400,
                                env={**os.environ, 'PYTHONIOENCODING': 'utf-8'})
        if result.returncode == 0 and target.is_file():
            data = json.loads(target.read_text(encoding='utf-8'))
            cues = [Cue(**c) for c in data['cues']]
            if not cues:
                raise RuntimeError('音訊沒有可辨識語音，無法生成有依據的摘要')
            return cues, {'type': 'whisper', 'model': model, 'device': device,
                          'compute_type': 'int8_float16' if device == 'cuda' else 'int8',
                          'language': data['language'], 'fallback_reason': errors}
        errors.append(f'{device}: {result.stderr[-1200:]}')
    raise RuntimeError('Whisper 轉錄失敗：' + '\n'.join(errors))


def _worker(audio, target, model_name, device):
    configure_runtime()
    import ctranslate2
    from faster_whisper import WhisperModel
    compute = 'int8_float16' if device == 'cuda' else 'int8'
    if device == 'cuda':
        if ctranslate2.get_cuda_device_count() < 1 or compute not in ctranslate2.get_supported_compute_types('cuda'):
            raise RuntimeError('GPU 不支援 CUDA int8_float16')
    model = WhisperModel(model_name, device=device, compute_type=compute,
                         download_root=str(MODELS / 'whisper'), cpu_threads=4, num_workers=1)
    segments, info = model.transcribe(audio, beam_size=5, vad_filter=True,
                                     condition_on_previous_text=False)
    cues = [{'start': s.start, 'end': s.end, 'text': s.text.strip()} for s in segments if s.text.strip()]
    with open(target, 'w', encoding='utf-8') as handle:
        json.dump({'cues': cues, 'language': info.language}, handle, ensure_ascii=False)
    del model
    gc.collect()


if __name__ == '__main__':
    _worker(*sys.argv[1:])
