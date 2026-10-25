"""Popup/Modal: ortalanmis pencere katmani."""
from __future__ import annotations

from typing import Optional

from ..core.buffer import Buffer
from ..core.style import Style
from ..layout.rect import Rect
from .base import Widget
from .block import Block, ROUNDED


class Popup(Widget):
    def __init__(self, content: Widget, width: int, height: int, title: str = "",
                 style: Optional[Style] = None, border_style: Style = Style(), dim_background: bool = True):
        self.content = content
        self.width = width
        self.height = height
        self.block = Block(ROUNDED, title, border_style=border_style, style=style or Style())
        self.dim_background = dim_background

    def popup_area(self, area: Rect) -> Rect:
        return area.centered(self.width, self.height)

    def render(self, area: Rect, buf: Buffer) -> None:
        if self.dim_background:
            buf.set_style(area, Style(dim=True))
        box = self.popup_area(area)
        if box.is_empty():
            return
        buf.fill(box, " ", self.block.style)
        self.block.render(box, buf)
        self.content.render(self.block.inner(box), buf)


Modal = Popup
