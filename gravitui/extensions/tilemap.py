"""TileMap: katmanli 2D izgara ve BFS yol bulma."""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple

from ..core.buffer import Buffer
from ..core.style import Style, Color, DEFAULT_STYLE
from ..layout.rect import Rect
from ..widgets.base import Widget

Pos = Tuple[int, int]


@dataclass(frozen=True)
class Tile:
    char: str
    style: Style = DEFAULT_STYLE
    walkable: bool = True


class TileMap(Widget):
    def __init__(self, width: int, height: int, layers: int = 2):
        self.width, self.height = width, height
        self.layers: List[List[List[Optional[Tile]]]] = [
            [[None] * width for _ in range(height)] for _ in range(layers)]
        self.camera: Pos = (0, 0)
        self.highlight: Set[Pos] = set()  # ornegin yol hucreleri
        self.highlight_style = Style(bg=Color(70, 90, 40))

    def in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    def set_tile(self, x: int, y: int, tile: Optional[Tile], layer: int = 0) -> None:
        if self.in_bounds(x, y):
            self.layers[layer][y][x] = tile

    def get_tile(self, x: int, y: int, layer: int = 0) -> Optional[Tile]:
        return self.layers[layer][y][x] if self.in_bounds(x, y) else None

    def clear_layer(self, layer: int) -> None:
        self.layers[layer] = [[None] * self.width for _ in range(self.height)]

    def fill_rect(self, rect: Rect, tile: Tile, layer: int = 0) -> None:
        for y in range(rect.y, rect.bottom):
            for x in range(rect.x, rect.right):
                self.set_tile(x, y, tile, layer)

    def is_walkable(self, x: int, y: int) -> bool:
        if not self.in_bounds(x, y):
            return False
        seen = False
        for layer in self.layers:
            t = layer[y][x]
            if t is not None:
                seen = True
                if not t.walkable:
                    return False
        return seen

    def find_path(self, start: Pos, goal: Pos) -> Optional[List[Pos]]:
        """4 yonlu BFS; yol (start ve goal dahil) ya da None."""
        if not (self.is_walkable(*start) and self.is_walkable(*goal)):
            return None
        prev: Dict[Pos, Optional[Pos]] = {start: None}
        q = deque([start])
        while q:
            cur = q.popleft()
            if cur == goal:
                path = []
                node: Optional[Pos] = cur
                while node is not None:
                    path.append(node)
                    node = prev[node]
                return path[::-1]
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                n = (cur[0] + dx, cur[1] + dy)
                if n not in prev and self.is_walkable(*n):
                    prev[n] = cur
                    q.append(n)
        return None

    def center_on(self, x: int, y: int, area: Rect) -> None:
        self.camera = (x - area.width // 2, y - area.height // 2)

    def render(self, area: Rect, buf: Buffer) -> None:
        cx, cy = self.camera
        for row in range(area.height):
            for col in range(area.width):
                mx, my = cx + col, cy + row
                if not self.in_bounds(mx, my):
                    continue
                for layer in self.layers:
                    t = layer[my][mx]
                    if t is not None:
                        st = t.style
                        if (mx, my) in self.highlight:
                            st = st.patch(self.highlight_style)
                        buf.set_char(area.x + col, area.y + row, t.char, st)
