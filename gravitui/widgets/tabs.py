"""Tabs: sekme cubugu."""
from __future__ import annotations

from typing import Optional, Sequence

from ..core.buffer import Buffer
from ..core.style import Style, DEFAULT_STYLE
from ..layout.rect import Rect
from .base import Widget
from .block import Block


class Tabs(Widget):
    def __init__(self, titles: Sequence[str], selected: int = 0,
                 style: Style = DEFAULT_STYLE, highlight_style: Style = Style(bold=True, underline=True),
                 divider: str = "│", block: Optional[Block] = None):
        self.titles = list(titles)
        self.selected = selected
        self.style = style
        self.highlight_style = highlight_style
        self.divider = divider
        self.block = block

    def render(self, area: Rect, buf: Buffer) -> None:
        if self.block is not None:
            self.block.render(area, buf)
            area = self.block.inner(area)
        if area.is_empty():
            return
        x = area.x
        for i, title in enumerate(self.titles):
            text = f" {title} "
            st = self.style.patch(self.highlight_style) if i == self.selected else self.style
            x += buf.put_str(x, area.y, text, st, clip=area)
            if i < len(self.titles) - 1:
                x += buf.put_str(x, area.y, self.divider, self.style, clip=area)
            if x >= area.right:
                break
