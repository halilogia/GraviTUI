"""Tree: hiyerarsik katlanabilir oturum/dosya agaci."""
from __future__ import annotations

from typing import List, Optional, Tuple

from ..core.buffer import Buffer
from ..core.style import Style, DEFAULT_STYLE
from ..layout.rect import Rect
from ..widgets.base import Widget
from ..widgets.block import Block


class TreeNode:
    def __init__(self, label: str, children: Optional[List["TreeNode"]] = None,
                 expanded: bool = False, style: Style = DEFAULT_STYLE):
        self.label = label
        self.children = children or []
        self.expanded = expanded
        self.style = style

    @property
    def is_leaf(self) -> bool:
        return not self.children


class Tree(Widget):
    def __init__(self, roots: List[TreeNode], block: Optional[Block] = None,
                 highlight_style: Style = Style(bold=True, underline=True)):
        self.roots = roots
        self.block = block
        self.highlight_style = highlight_style
        self.selected = 0
        self.offset = 0

    def visible(self) -> List[Tuple[TreeNode, int]]:
        """Gorunur dugumler ve derinlikleri (acik dallar icin ozyinelemeli)."""
        out: List[Tuple[TreeNode, int]] = []

        def walk(nodes: List[TreeNode], depth: int):
            for n in nodes:
                out.append((n, depth))
                if n.expanded:
                    walk(n.children, depth + 1)
        walk(self.roots, 0)
        return out

    def selected_node(self) -> Optional[TreeNode]:
        v = self.visible()
        return v[self.selected][0] if v and 0 <= self.selected < len(v) else None

    def move(self, delta: int) -> None:
        n = len(self.visible())
        self.selected = max(0, min(n - 1, self.selected + delta)) if n else 0

    def toggle(self) -> None:
        node = self.selected_node()
        if node is not None and not node.is_leaf:
            node.expanded = not node.expanded

    def expand(self) -> None:
        node = self.selected_node()
        if node is not None and not node.is_leaf:
            node.expanded = True

    def collapse(self) -> None:
        node = self.selected_node()
        if node is not None and node.expanded:
            node.expanded = False

    def render(self, area: Rect, buf: Buffer) -> None:
        if self.block is not None:
            self.block.render(area, buf)
            area = self.block.inner(area)
        if area.is_empty():
            return
        rows = self.visible()
        self.selected = max(0, min(self.selected, len(rows) - 1)) if rows else 0
        if self.selected < self.offset:
            self.offset = self.selected
        elif self.selected >= self.offset + area.height:
            self.offset = self.selected - area.height + 1
        for r in range(area.height):
            i = self.offset + r
            if i >= len(rows):
                break
            node, depth = rows[i]
            mark = "  " if node.is_leaf else ("▼ " if node.expanded else "▶ ")
            text = ("  " * depth + mark + node.label)[:area.width]
            st = node.style.patch(self.highlight_style) if i == self.selected else node.style
            if i == self.selected:
                text = text.ljust(area.width)
            buf.put_str(area.x, area.y + r, text, st, clip=area)
