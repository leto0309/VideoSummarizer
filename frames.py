import re
import subprocess
import time
from config import ffmpeg
from storage import guard
from subtitles import stamp


def extract(video, task, duration, count=8):
    if not duration or duration <= 0:
        raise RuntimeError('缺少影片長度，無法產生可核對的截圖')
    targets = [duration * (i + .5) / count for i in range(count)]
    parts = [f'gte(t,{targets[0]:.6f})*isnan(prev_selected_t)']
    parts += [f'gte(t,{t:.6f})*lt(prev_selected_t,{t:.6f})' for t in targets[1:]]
    expression = '+'.join(parts).replace(',', '\\,')
    logfile = task / 'ffmpeg-frames.log'
    with logfile.open('w', encoding='utf-8') as log:
        process = subprocess.Popen([ffmpeg(), '-hide_banner', '-nostdin', '-i', str(video),
                                    '-an', '-vf', f'select={expression},showinfo,scale=960:960:force_original_aspect_ratio=decrease:force_divisible_by=2',
                                    '-fps_mode', 'vfr', '-frames:v', str(count), '-q:v', '3',
                                    str(task / 'frame_%02d.jpg')], stdout=subprocess.DEVNULL, stderr=log)
        try:
            started = time.monotonic()
            while process.poll() is None:
                guard()
                if time.monotonic() - started > 7200:
                    raise RuntimeError('截圖處理逾時')
                time.sleep(.25)
            if process.returncode:
                raise RuntimeError('FFmpeg 截圖失敗：' + logfile.read_text(encoding='utf-8')[-1000:])
        except BaseException:
            process.kill()
            process.wait()
            raise
    log = logfile.read_text(encoding='utf-8')
    times = re.findall(r'\bn:\s*\d+.*?\bpts_time:([\d.eE+\-]+)', log)
    paths = sorted(task.glob('frame_*.jpg'))
    if len(times) != len(paths) or not paths:
        raise RuntimeError('無法核對截圖影格與 FFmpeg PTS，停止畫面分析')
    return [{'path': str(p), 'timestamp_seconds': float(t), 'timestamp': stamp(float(t)),
             'requested_seconds': targets[i], 'timing_source': 'FFmpeg showinfo decoded frame PTS'}
            for i, (p, t) in enumerate(zip(paths, times))]
