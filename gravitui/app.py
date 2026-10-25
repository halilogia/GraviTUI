"""App: alt-screen + 60 FPS dongu (draw/key/update) yardimcisi."""
from __future__ import annotations

import sys
import time
from typing import Callable, Optional

from .core.buffer import Buffer
from .core.diff import DiffWriter
from .core.terminal import Terminal


class App:
    def __init__(self, draw: Callable[[Buffer, float], None],
                 on_key: Optional[Callable[[str], bool]] = None, fps: int = 60):
        """`draw(buf, dt)` her karede cagrilir; `on_key(key)` True donerse cikilir."""
        self.draw = draw
        self.on_key = on_key
        self.frame_time = 1.0 / fps

    def run(self) -> None:
        term = Terminal()
        writer = DiffWriter(sys.stdout)
        last = time.perf_counter()
        buf: Optional[Buffer] = None
        with term:
            try:
                while True:
                    w, h = term.size()
                    if buf is None or (buf.width, buf.height) != (w, h):
                        buf = Buffer(w, h)
                        writer.invalidate()
                    while (k := term.poll_key()) is not None:
                        if k == "ctrl+c" or (self.on_key and self.on_key(k)):
                            return
                    now = time.perf_counter()
                    dt, last = now - last, now
                    buf.clear()
                    self.draw(buf, dt)
                    writer.flush(buf)
                    spare = self.frame_time - (time.perf_counter() - now)
                    if spare > 0:
                        time.sleep(spare)
            except KeyboardInterrupt:
                return
