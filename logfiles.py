"""Keep append-only logs bounded: above the limit the log becomes <name>.1, replacing the older copy."""
from pathlib import Path

LIMIT = 2 * 1024**2


def rotate(path, limit=LIMIT):
    path = Path(path)
    try:
        if path.stat().st_size > limit:
            path.replace(path.with_name(path.name + '.1'))
    except OSError:
        pass  # Missing or locked logs are written as before.
    return path
