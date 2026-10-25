"""Block: kenarlik, baslik, padding."""
from __future__ import annotations

from typing import Optional

from ..core.buffer import Buffer
from ..core.style import Style, DEFAULT_STYLE
from ..layout.rect import Rect
from .base import Widget

LEFT, CENTER, RIGHT = "left", "center", "right"

# Borders: ad -> (yatay, dikey, ust-sol, ust-sag, alt-sol, alt-sag)
NONE = "none"
ALL = "all"
ROUNDED = "rounded"
DOUBLE = "double"
_CHARS = {
    ALL: ("─", "│", "┌", "┐", "└", "┘"),
    ROUNDED: ("─", "│", "╭", "╮", "╰", "╯"),
    DOUBLE: ("═", "║", "╔", "╗", "╚", "╝"),
}


class Block(Widget):
    def __init__(self, borders: str = NONE, title: str = "", title_align: str = LEFT,
                 border_style: Style = DEFAULT_STYLE, title_style: Optional[Style] = None,
                 style: Optional[Style] = None, padding=(0, 0, 0, 0)):
        self.borders = borders
        self.title = title
        self.title_align = title_align
        self.border_style = border_style
        self.title_style = title_style or border_style
        self.style = style
        self.padding = padding  # (sol, ust, sag, alt)

    def inner(self, area: Rect) -> Rect:
        b = 0 if self.borders == NONE else 1
        l, t, r, bt = self.padding
        return area.pad(b + l, b + t, b + r, b + bt)

    def render(self, area: Rect, buf: Buffer) -> None:
        if area.is_empty():
            return
        if self.style is not None:
            buf.fill(area, " ", self.style)
        if self.borders == NONE:
            return
        h, v, tl, tr, bl, br = _CHARS[self.borders]
        st = self.border_style
        if self.style is not None:
            st = self.style.patch(st)
        x0, y0, x1, y1 = area.x, area.y, area.right - 1, area.bottom - 1
        for x in range(x0 + 1, x1):
            buf.set_char(x, y0, h, st)
            buf.set_char(x, y1, h, st)
        for y in range(y0 + 1, y1):
            buf.set_char(x0, y, v, st)
            buf.set_char(x1, y, v, st)
        buf.set_char(x0, y0, tl, st)
        buf.set_char(x1, y0, tr, st)
        buf.set_char(x0, y1, bl, st)
        buf.set_char(x1, y1, br, st)
        if self.title and area.width > 4:
            text = " " + self.title + " "
            room = area.width - 2
            text = text[:room]
            if self.title_align == CENTER:
                tx = x0 + 1 + (room - len(text)) // 2
            elif self.title_align == RIGHT:
                tx = x1 - len(text)
            else:
                tx = x0 + 1
            ts = st.patch(self.title_style) if self.title_style is not self.border_style else st
            buf.put_str(tx, y0, text, ts)
