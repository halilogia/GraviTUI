"""Gauge: yatay ilerleme cubugu (yuzde/oran, gradyan)."""
from __future__ import annotations

from typing import List, Optional

from ..core.buffer import Buffer
from ..core.style import Style, Color, gradient_at, GREEN, YELLOW, RED, GRAY, BLACK
from ..layout.rect import Rect
from .base import Widget
from .block import Block

_PARTIAL = " ▏▎▍▌▋▊▉"


class Gauge(Widget):
    def __init__(self, ratio: float = 0.0, label: Optional[str] = None,
                 colors: Optional[List[Color]] = None, empty_color: Color = Color(50, 50, 60),
                 block: Optional[Block] = None, label_color: Color = Color(255, 255, 255)):
        self.ratio = max(0.0, min(1.0, ratio))
        self.label = label
        self.colors = colors or [GREEN, YELLOW, RED]
        self.empty_color = empty_color
        self.block = block
        self.label_color = label_color

    @staticmethod
    def percent(p: float, **kw) -> "Gauge":
        return Gauge(p / 100.0, **kw)

    def render(self, area: Rect, buf: Buffer) -> None:
        if self.block is not None:
            self.block.render(area, buf)
            area = self.block.inner(area)
        if area.is_empty():
            return
        label = self.label if self.label is not None else f"{self.ratio * 100:.0f}%"
        exact = self.ratio * area.width
        full = int(exact)
        frac = int((exact - full) * 8)
        lx = area.x + (area.width - len(label)) // 2
        mid = area.y + area.height // 2
        for y in range(area.y, area.bottom):
            for i in range(area.width):
                x = area.x + i
                color = gradient_at(self.colors, i / max(1, area.width - 1))
                if i < full:
                    ch, st = " ", Style(bg=color)
                elif i == full and frac:
                    ch, st = _PARTIAL[frac], Style(fg=color, bg=self.empty_color)
                else:
                    ch, st = " ", Style(bg=self.empty_color)
                if y == mid and lx <= x < lx + len(label):
                    ch = label[x - lx]
                    st = Style(fg=self.label_color, bg=st.bg or color, bold=True)
                buf.set_char(x, y, ch, st)
