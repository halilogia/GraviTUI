"""Hucre izgarasi: Cell ve Buffer."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .style import Style, DEFAULT_STYLE, Color
from ..layout.rect import Rect


@dataclass(frozen=True)
class Cell:
    char: str = " "
    fg: Optional[Color] = None
    bg: Optional[Color] = None
    style: Style = DEFAULT_STYLE

    def full_style(self) -> Style:
        return Style(self.fg or self.style.fg, self.bg or self.style.bg,
                     self.style.bold, self.style.dim, self.style.italic, self.style.underline)


BLANK = Cell()


class Buffer:
    def __init__(self, width: int, height: int):
        self.width = max(0, width)
        self.height = max(0, height)
        self.cells = [[BLANK] * self.width for _ in range(self.height)]

    @property
    def area(self) -> Rect:
        return Rect(0, 0, self.width, self.height)

    def in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    def get(self, x: int, y: int) -> Cell:
        return self.cells[y][x] if self.in_bounds(x, y) else BLANK

    def set_cell(self, x: int, y: int, cell: Cell, clip: Optional[Rect] = None) -> None:
        if not self.in_bounds(x, y):
            return
        if clip is not None and not clip.contains(x, y):
            return
        self.cells[y][x] = cell

    def set_char(self, x: int, y: int, ch: str, style: Style = DEFAULT_STYLE,
                 clip: Optional[Rect] = None) -> None:
        self.set_cell(x, y, Cell(ch, style.fg, style.bg, style), clip)

    def put_str(self, x: int, y: int, text: str, style: Style = DEFAULT_STYLE,
                clip: Optional[Rect] = None) -> int:
        """Metni yazar; clip/tampon disini keser. Yazilan hucre sayisini dondurur."""
        n = 0
        for ch in text:
            if self.in_bounds(x + n, y) and (clip is None or clip.contains(x + n, y)):
                self.cells[y][x + n] = Cell(ch, style.fg, style.bg, style)
            n += 1
        return n

    def set_string(self, x: int, y: int, text: str, style: Style = DEFAULT_STYLE,
                   clip: Optional[Rect] = None) -> int:
        """set_string alias (put_str uyumlulugu)."""
        return self.put_str(x, y, text, style, clip)

    def set_style(self, area: Rect, style: Style) -> None:
        """Alandaki tum hucrelere stil bindirir (karakter korunur)."""
        r = area.intersect(self.area)
        for y in range(r.y, r.bottom):
            for x in range(r.x, r.right):
                c = self.cells[y][x]
                merged = c.full_style().patch(style)
                self.cells[y][x] = Cell(c.char, merged.fg, merged.bg, merged)

    def fill(self, area: Rect, ch: str = " ", style: Style = DEFAULT_STYLE) -> None:
        r = area.intersect(self.area)
        cell = Cell(ch, style.fg, style.bg, style)
        for y in range(r.y, r.bottom):
            row = self.cells[y]
            for x in range(r.x, r.right):
                row[x] = cell

    def clear(self) -> None:
        self.cells = [[BLANK] * self.width for _ in range(self.height)]

    def resize(self, width: int, height: int) -> None:
        self.width, self.height = max(0, width), max(0, height)
        self.clear()

    def to_lines(self) -> list:
        return ["".join(c.char for c in row) for row in self.cells]

    def copy(self) -> "Buffer":
        b = Buffer(self.width, self.height)
        b.cells = [row[:] for row in self.cells]
        return b
