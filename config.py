from pathlib import Path
import os
import subprocess
import shutil

ROOT = Path(__file__).resolve().parent
TEMP = ROOT / 'temp'
OUTPUTS = ROOT / 'outputs'
MODELS = ROOT / 'models'
TOOLS = ROOT / 'tools'
OLLAMA_URL = 'http://127.0.0.1:11435'
ALLOWED_MODELS = ('qwen3-vl:4b-instruct', 'qwen3-vl:2b-instruct')
TEMP_LIMIT = 5 * 1024**3
RESERVE = 64 * 1024**2


def gpu_info():
    try:
        result = subprocess.run(['nvidia-smi', '--query-gpu=name,memory.total,driver_version',
                                 '--format=csv,noheader,nounits'], capture_output=True,
                                text=True, timeout=10, check=True)
        name, memory, driver = result.stdout.splitlines()[0].split(',')
        return {'name': name.strip(), 'vram_mib': int(memory.strip()), 'driver': driver.strip()}
    except (OSError, ValueError, subprocess.SubprocessError):
        return {'name': '未偵測 NVIDIA GPU', 'vram_mib': 0, 'driver': None}


def default_model():
    return ALLOWED_MODELS[0] if gpu_info()['vram_mib'] >= 6000 else ALLOWED_MODELS[1]


def configure_runtime():
    os.environ['OLLAMA_NO_CLOUD'] = '1'
    os.environ['HF_HOME'] = str(MODELS / 'huggingface')
    os.environ['HF_HUB_DISABLE_TELEMETRY'] = '1'
    os.environ['DO_NOT_TRACK'] = '1'
    # Keep DLL directory handles alive for the entire Python process.
    global _dll_handles
    _dll_handles = []
    import site
    if os.name == 'nt':
        for base in site.getsitepackages():
            for pattern in ('nvidia/cublas/bin', 'nvidia/cudnn/bin', 'nvidia/cuda_nvrtc/bin',
                            'nvidia/cublas/lib', 'nvidia/cudnn/lib'):
                directory = Path(base) / pattern
                if directory.is_dir():
                    os.environ['PATH'] = str(directory) + os.pathsep + os.environ.get('PATH', '')
                    _dll_handles.append(os.add_dll_directory(str(directory)))


def ffmpeg():
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def node_runtime():
    local = TOOLS / 'node' / 'node.exe'
    return str(local) if local.is_file() else shutil.which('node')
