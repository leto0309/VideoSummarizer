import ctypes
import json
import platform
import subprocess
import sys
from config import ROOT, configure_runtime, ffmpeg, gpu_info, default_model, node_runtime


def collect():
    configure_runtime()
    import ctranslate2
    result = {'python': sys.version, 'windows': platform.platform(), 'gpu': gpu_info(),
              'default_model': default_model(), 'project': str(ROOT)}
    if sys.platform == 'win32':
        from ctypes import wintypes
        class MemoryStatus(ctypes.Structure):
            _fields_ = [('length', wintypes.DWORD), ('load', wintypes.DWORD)] + [
                (name, ctypes.c_ulonglong) for name in ('total', 'available', 'page', 'availpage',
                                                      'virtual', 'availvirtual', 'extended')]
        memory = MemoryStatus()
        memory.length = ctypes.sizeof(memory)
        ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(memory))
        result['ram_gib'] = round(memory.total / 1024**3, 2)
    result['ffmpeg'] = subprocess.run([ffmpeg(), '-version'], capture_output=True, text=True).stdout.splitlines()[0]
    if node_runtime():
        result['node'] = subprocess.run([node_runtime(), '--version'], capture_output=True, text=True).stdout.strip()
    import yt_dlp.version
    result['yt_dlp'] = yt_dlp.version.__version__
    try:
        result['cuda_devices'] = ctranslate2.get_cuda_device_count()
        result['cuda_compute_types'] = sorted(ctranslate2.get_supported_compute_types('cuda'))
    except Exception as exc:
        result['cuda_error'] = str(exc)
    try:
        from local_llm import LocalLLM
        llm = LocalLLM(default_model())
        result['ollama_version'] = llm.request('/api/version')
        result['ollama_models'] = llm.request('/api/tags')
    except Exception as exc:
        result['ollama_error'] = str(exc)
    return result


if __name__ == '__main__':
    result = collect()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    logs = ROOT / 'logs'
    logs.mkdir(exist_ok=True)
    (logs / 'diagnostics.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
