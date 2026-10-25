"""Paragraph: word wrap, hizalama, cok renkli Span/Line."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Union

from ..core.buffer import Buffer
from ..core.style import Style, DEFAULT_STYLE
from ..layout.rect import Rect
from .base import Widget
from .block import Block, LEFT, CENTER, RIGHT


@dataclass(frozen=True)
class Span:
    text: str
    style: Style = DEFAULT_STYLE


@dataclass
class Line:
    spans: List[Span] = field(default_factory=list)
    align: Optional[str] = None

    @staticmethod
    def of(content: Union[str, "Line", List[Span]], style: Style = DEFAULT_STYLE) -> "Line":
        if isinstance(content, Line):
            return content
        if isinstance(content, str):
            return Line([Span(content, style)])
        return Line(list(content))

    @property
    def width(self) -> int:
        return sum(len(s.text) for s in self.spans)

    def plain(self) -> str:
        return "".join(s.text for s in self.spans)


def _chars(line: Line):
    return [(ch, s.style) for s in line.spans for ch in s.text]


def wrap_line(line: Line, width: int) -> List[Line]:
    """Kelime sarma; sigmayan uzun kelimeler harf harf bolunur."""
    if width <= 0:
        return []
    cells = _chars(line)
    if len(cells) <= width:
        return [Line(_regroup(cells), line.align)]
    out, cur, word = [], [], []

    def flush_word():
        nonlocal cur, word
        while len(word) > width:  # cok uzun kelime
            if cur:
                out.append(cur)
                cur = []
            out.append(word[:width])
            word = word[width:]
        if len(cur) + len(word) > width and cur:
            while cur and cur[-1][0] == " ":
                cur.pop()
            out.append(cur)
            cur = []
        cur = cur + word
        word = []

    for ch, st in cells:
        if ch == " ":
            flush_word()
            cur.append((ch, st))
            if len(cur) > width:
                cur = cur[:width]
        else:
            word.append((ch, st))
    flush_word()
    while cur and cur[-1][0] == " ":
        cur.pop()
    if cur:
        out.append(cur)
    return [Line(_regroup(c), line.align) for c in out] or [Line([], line.align)]


def _regroup(cells) -> List[Span]:
    spans: List[Span] = []
    for ch, st in cells:
        if spans and spans[-1].style == st:
            spans[-1] = Span(spans[-1].text + ch, st)
        else:
            spans.append(Span(ch, st))
    return spans


class Paragraph(Widget):
    def __init__(self, text: Union[str, Line, List[Union[str, Line]]] = "",
                 style: Style = DEFAULT_STYLE, align: str = LEFT, wrap: bool = True,
                 block: Optional[Block] = None, scroll: int = 0):
        items = text if isinstance(text, list) else str(text).split("\n") if isinstance(text, str) else [text]
        self.lines = [Line.of(t, style) for t in items]
        self.style = style
        self.align = align
        self.wrap = wrap
        self.block = block
        self.scroll = scroll

    def render(self, area: Rect, buf: Buffer) -> None:
        if self.block is not None:
            self.block.render(area, buf)
            area = self.block.inner(area)
        if area.is_empty():
            return
        if self.style != DEFAULT_STYLE:
            buf.fill(area, " ", self.style)
        rows: List[Line] = []
        for ln in self.lines:
            rows.extend(wrap_line(ln, area.width) if self.wrap else [ln])
        for i, ln in enumerate(rows[self.scroll:self.scroll + area.height]):
            align = ln.align or self.align
            w = ln.width
            if align == CENTER:
                x = area.x + max(0, (area.width - w) // 2)
            elif align == RIGHT:
                x = area.x + max(0, area.width - w)
            else:
                x = area.x
            for sp in ln.spans:
                x += buf.put_str(x, area.y + i, sp.text, sp.style, clip=area)
