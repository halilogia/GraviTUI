"""DiffWriter: yalnizca degisen hucreleri tek parca halinde yazan motor."""
from __future__ import annotations

import sys
from typing import Optional

from .buffer import Buffer, Cell


class DiffWriter:
    def __init__(self, out=None):
        self.out = sys.stdout if out is None else out
        self.prev: Optional[Buffer] = None

    def invalidate(self) -> None:
        """Bir sonraki cizimi tam cizime zorlar (resize vb.)."""
        self.prev = None

    def render(self, buf: Buffer) -> str:
        """Onceki kareyle farki ANSI dizisi olarak uretir ve prev'i gunceller."""
        full = (self.prev is None or self.prev.width != buf.width
                or self.prev.height != buf.height)
        parts = []
        if full:
            parts.append("\x1b[0m\x1b[2J")
        last_style = None
        cx = cy = -1  # imlecin tahmini konumu
        for y in range(buf.height):
            row = buf.cells[y]
            prow = None if full else self.prev.cells[y]
            for x in range(buf.width):
                cell: Cell = row[x]
                if prow is not None and prow[x] == cell:
                    continue
                if full and cell == Cell():
                    continue  # 2J zaten temizledi
                if not (cy == y and cx == x):
                    parts.append(f"\x1b[{y + 1};{x + 1}H")
                st = cell.full_style()
                if st != last_style:
                    parts.append(st.sgr())
                    last_style = st
                parts.append(cell.char)
                cx, cy = x + 1, y
        if parts:
            parts.append("\x1b[0m")
        self.prev = buf.copy()
        return "".join(parts)

    def flush(self, buf: Buffer) -> int:
        data = self.render(buf)
        if data and self.out is not None:
            self.out.write(data)
            self.out.flush()
        return len(data)
