import gc
import json
import os
import subprocess
import sys
from config import ROOT, configure_runtime
from subtitles import Cue
from whisper_models import ensure_model


def transcribe(audio, task, model='small', mode='auto'):
    """CUDA runs in a separate process, so a missing native DLL cannot kill Streamlit."""
    target = task / 'transcript.json'
    # A network failure must not be mistaken for a GPU failure and downloaded twice.
    model_path = ensure_model(model)
    attempts = ['cuda', 'cpu'] if mode == 'auto' else ['cpu']
    errors = []
    for device in attempts:
        result = subprocess.run([sys.executable, str(ROOT / 'speech.py'), str(audio), str(target),
                                 str(model_path), device], capture_output=True, text=True, encoding='utf-8',
                                errors='replace', timeout=14400,
                                env={**os.environ, 'PYTHONIOENCODING': 'utf-8'})
        if result.returncode == 0 and target.is_file():
            data = json.loads(target.read_text(encoding='utf-8'))
            cues = [Cue(**c) for c in data['cues']]
            if not cues:
                raise RuntimeError('音频没有可识别语音，无法生成有依据的摘要')
            return cues, {'type': 'whisper', 'model': model, 'device': device,
                          'compute_type': 'int8_float16' if device == 'cuda' else 'int8',
                          'language': data['language'], 'fallback_reason': errors}
        errors.append(f'{device}: {result.stderr[-1200:]}')
    raise RuntimeError('Whisper 转录失败：' + '\n'.join(errors))


def cpu_threads():
    # More cores speed up CPU transcription; beyond eight the gain is small and the PC stays usable.
    return min(os.cpu_count() or 4, 8)


def _worker(audio, target, model_name, device):
    configure_runtime()
    import ctranslate2
    from faster_whisper import WhisperModel
    compute = 'int8_float16' if device == 'cuda' else 'int8'
    if device == 'cuda':
        if ctranslate2.get_cuda_device_count() < 1 or compute not in ctranslate2.get_supported_compute_types('cuda'):
            raise RuntimeError('GPU 不支持 CUDA int8_float16')
    model = WhisperModel(model_name, device=device, compute_type=compute,
                         local_files_only=True, cpu_threads=cpu_threads(), num_workers=1)
    segments, info = model.transcribe(audio, beam_size=5, vad_filter=True,
                                     condition_on_previous_text=False)
    cues = [{'start': s.start, 'end': s.end, 'text': s.text.strip()} for s in segments if s.text.strip()]
    with open(target, 'w', encoding='utf-8') as handle:
        json.dump({'cues': cues, 'language': info.language}, handle, ensure_ascii=False)
    del model
    gc.collect()


if __name__ == '__main__':
    _worker(*sys.argv[1:])
