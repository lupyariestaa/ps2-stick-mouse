"""Hot-reload config berbasis watchdog (T2.4).

Memantau file `config.json`; bila berubah, memuat ulang config dan memanggil
callback. Aman dipakai tanpa watchdog (fallback: tidak ada hot-reload).
"""

from __future__ import annotations

import os
import threading
import time
from typing import Callable

try:
    from watchdog.events import FileSystemEventHandler
    from watchdog.observers import Observer

    _HAS_WATCHDOG = True
except ImportError:  # pragma: no cover - watchdog opsional
    _HAS_WATCHDOG = False


class ConfigWatcher:
    """Memantau perubahan file config dan menjalankan callback saat berubah."""

    def __init__(
        self,
        config_path: str,
        on_change: Callable[[], None],
        debounce_seconds: float = 0.4,
    ) -> None:
        self._path = os.path.abspath(config_path)
        self._on_change = on_change
        self._debounce = debounce_seconds
        self._observer = None
        self._last_event = 0.0
        self._lock = threading.Lock()
        self._enabled = _HAS_WATCHDOG

    @property
    def enabled(self) -> bool:
        return self._enabled

    def start(self) -> None:
        if not self._enabled:
            return

        directory = os.path.dirname(self._path)
        filename = os.path.basename(self._path)

        watcher = self

        class _Handler(FileSystemEventHandler):
            def on_modified(self, event):  # type: ignore[override]
                if event.is_directory:
                    return
                if os.path.abspath(event.src_path) != watcher._path:
                    return
                # Debounce: editor sering menulis file beberapa kali sekaligus.
                now = time.monotonic()
                with watcher._lock:
                    if now - watcher._last_event < watcher._debounce:
                        return
                    watcher._last_event = now
                try:
                    watcher._on_change()
                except Exception as exc:  # pragma: no cover
                    print(f"[WARN] Gagal memuat ulang config: {exc}")

        self._observer = Observer()
        self._observer.schedule(_Handler(), directory, recursive=False)
        self._observer.daemon = True
        self._observer.start()

    def stop(self) -> None:
        if self._observer is not None:
            self._observer.stop()
            self._observer.join(timeout=2.0)
            self._observer = None
