"""Only marked UUID task directories under this project's temp may be deleted."""
from datetime import datetime, timezone
import json
import re
import shutil
import time
import uuid
from pathlib import Path
from config import TEMP, TEMP_LIMIT, RESERVE

MARKER = 'videosummarizer-task-v1'


def _unsafe(path):
    return path.is_symlink() or (hasattr(path, 'is_junction') and path.is_junction()) or bool(
        getattr(path.lstat(), 'st_file_attributes', 0) & 0x400)


def size(root=TEMP):
    if not root.exists():
        return 0
    if _unsafe(root):
        raise RuntimeError('拒绝使用链接或 junction 作为暂存目录')
    total = 0
    for entry in root.rglob('*'):
        if _unsafe(entry):
            raise RuntimeError('暂存目录含链接，停止处理以保护非项目文件')
        if entry.is_file():
            total += entry.stat().st_size
    return total


def guard(extra=0, root=TEMP):
    if size(root) + extra > TEMP_LIMIT - RESERVE:
        raise RuntimeError('暂存接近 5 GB 上限；已停止。未满 24 小时的失败暂存会保留，请稍后重试。')


def _read(task):
    if not re.fullmatch(r'[0-9a-f]{32}', task.name) or _unsafe(task):
        return None
    marker = task / 'task.json'
    if not marker.is_file() or _unsafe(marker):
        return None
    try:
        data = json.loads(marker.read_text(encoding='utf-8'))
        return data if data.get('owner') == MARKER and data.get('id') == task.name else None
    except (OSError, ValueError):
        return None


def remove_task(task, root=TEMP):
    task, root = Path(task), Path(root)
    # Windows 8.3 aliases resolve to long names without being links. Reject
    # actual reparse points, including ancestors, rather than comparing names.
    if any(_unsafe(parent) for parent in (root, *root.parents)):
        raise RuntimeError('拒绝清理链接或 junction 中的暂存')
    if task.absolute().parent != root.absolute() or task.resolve().parent != root.resolve() or not _read(task):
        raise RuntimeError('拒绝清理非本项目暂存')
    size(task)  # reject all reparse points before recursive removal
    shutil.rmtree(task)


def cleanup(root=TEMP, now=None):
    root.mkdir(parents=True, exist_ok=True)
    size(root)
    now = time.time() if now is None else now
    for task in root.iterdir():
        if not task.is_dir():
            continue
        data = _read(task)
        if not data:
            continue
        if data['status'] == 'success':
            remove_task(task, root)
        elif data['status'] == 'running':
            # Called while holding the global pipeline lock: prior process was interrupted.
            data.update(status='failed', failed_at=now, error='先前程序中断')
            (task / 'task.json').write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
        elif data['status'] == 'failed' and now - data.get('failed_at', now) >= 86400:
            remove_task(task, root)


class Task:
    def __init__(self):
        cleanup()
        guard()
        self.id = uuid.uuid4().hex
        self.path = TEMP / self.id
        self.path.mkdir()
        self.data = {'owner': MARKER, 'id': self.id, 'status': 'running',
                     'created_at': datetime.now(timezone.utc).isoformat()}
        self.save()

    def save(self):
        (self.path / 'task.json').write_text(json.dumps(self.data, ensure_ascii=False, indent=2), encoding='utf-8')

    def fail(self, error):
        self.data.update(status='failed', failed_at=time.time(), error=str(error))
        self.save()

    def success(self):
        self.data.update(status='success')
        self.save()
        remove_task(self.path)
