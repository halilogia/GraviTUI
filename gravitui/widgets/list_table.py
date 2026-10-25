"""ListWidget (secilebilir satirlar) ve TableWidget (sutun genislikli)."""
from __future__ import annotations

from typing import List, Optional, Sequence, Union

from ..core.buffer import Buffer
from ..core.style import Style, DEFAULT_STYLE, Color
from ..layout.layout import Layout, HORIZONTAL
from ..layout.constraint import Constraint, Fill
from ..layout.rect import Rect
from .base import Widget
from .block import Block


class ListState:
    def __init__(self, selected: Optional[int] = 0, offset: int = 0):
        self.selected = selected
        self.offset = offset

    def move(self, delta: int, count: int) -> None:
        if count == 0:
            self.selected = None
            return
        cur = 0 if self.selected is None else self.selected
        self.selected = max(0, min(count - 1, cur + delta))


def _scroll_offset(state: ListState, visible: int, count: int) -> int:
    if state.selected is None or visible <= 0:
        return state.offset
    off = state.offset
    if state.selected < off:
        off = state.selected
    elif state.selected >= off + visible:
        off = state.selected - visible + 1
    return max(0, min(off, max(0, count - visible)))


class ListWidget(Widget):
    def __init__(self, items: Sequence[str], state: Optional[ListState] = None,
                 block: Optional[Block] = None, style: Style = DEFAULT_STYLE,
                 highlight_style: Style = Style(bold=True), highlight_symbol: str = "> "):
        self.items = list(items)
        self.state = state or ListState()
        self.block = block
        self.style = style
        self.highlight_style = highlight_style
        self.highlight_symbol = highlight_symbol

    def render(self, area: Rect, buf: Buffer) -> None:
        if self.block is not None:
            self.block.render(area, buf)
            area = self.block.inner(area)
        if area.is_empty():
            return
        self.state.offset = _scroll_offset(self.state, area.height, len(self.items))
        pad = " " * len(self.highlight_symbol)
        for row in range(area.height):
            idx = self.state.offset + row
            if idx >= len(self.items):
                break
            sel = idx == self.state.selected
            st = self.style.patch(self.highlight_style) if sel else self.style
            line = (self.highlight_symbol if sel else pad) + self.items[idx]
            line = line[:area.width].ljust(area.width)
            buf.put_str(area.x, area.y + row, line, st, clip=area)


class TableWidget(Widget):
    def __init__(self, rows: Sequence[Sequence[str]], widths: Sequence[Constraint],
                 header: Optional[Sequence[str]] = None, state: Optional[ListState] = None,
                 block: Optional[Block] = None, style: Style = DEFAULT_STYLE,
                 header_style: Style = Style(bold=True, underline=True),
                 highlight_style: Style = Style(bold=True), column_spacing: int = 1):
        self.rows = [list(r) for r in rows]
        self.widths = list(widths)
        self.header = list(header) if header else None
        self.state = state or ListState(selected=None)
        self.block = block
        self.style = style
        self.header_style = header_style
        self.highlight_style = highlight_style
        self.column_spacing = column_spacing

    def _draw_row(self, buf: Buffer, cols: List[Rect], y: int, cells: Sequence[str],
                  style: Style, clip: Rect) -> None:
        for rect, text in zip(cols, cells):
            buf.put_str(rect.x, y, text[:rect.width].ljust(rect.width), style, clip=clip)

    def render(self, area: Rect, buf: Buffer) -> None:
        if self.block is not None:
            self.block.render(area, buf)
            area = self.block.inner(area)
        if area.is_empty():
            return
        cols = Layout.split(Rect(area.x, area.y, area.width, 1), HORIZONTAL,
                            self.widths, spacing=self.column_spacing)
        y = area.y
        if self.header:
            self._draw_row(buf, cols, y, self.header, self.header_style, area)
            y += 1
        visible = area.bottom - y
        if visible <= 0:
            return
        self.state.offset = _scroll_offset(self.state, visible, len(self.rows))
        for r in range(visible):
            idx = self.state.offset + r
            if idx >= len(self.rows):
                break
            st = self.style.patch(self.highlight_style) if idx == self.state.selected else self.style
            if idx == self.state.selected:
                buf.fill(Rect(area.x, y + r, area.width, 1), " ", st)
            self._draw_row(buf, cols, y + r, self.rows[idx], st, area)
