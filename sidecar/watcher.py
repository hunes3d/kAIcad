import time
from pathlib import Path

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer


class _Handler(FileSystemEventHandler):
    def __init__(self, cb):
        self.cb = cb

    def on_modified(self, event):
        if event.is_directory:
            return
        self.cb(Path(event.src_path))


def watch(path: Path, callback):
    obs = Observer()
    obs.schedule(_Handler(callback), str(path), recursive=True)
    obs.start()
    try:
        while True:
            time.sleep(1)
    finally:
        obs.stop()
        obs.join()
