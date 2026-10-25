"""Ratatui tarzi flex layout hesaplayici."""
from __future__ import annotations

from typing import List, Sequence

from .constraint import Constraint, Fill, Length, Max, Min, Percentage, Ratio
from .rect import Rect

HORIZONTAL = "horizontal"
VERTICAL = "vertical"


def _solve(total: int, constraints: Sequence[Constraint], spacing: int) -> List[int]:
    n = len(constraints)
    if n == 0:
        return []
    avail = max(0, total - spacing * (n - 1))
    sizes = [0] * n
    flex = []  # (index, weight, lo, hi)
    for i, c in enumerate(constraints):
        if isinstance(c, (Length, Percentage, Ratio)):
            sizes[i] = c.resolve(avail)
        elif isinstance(c, Min):
            sizes[i] = c.value
            flex.append((i, 1, c.value, avail))
        elif isinstance(c, Max):
            flex.append((i, 1, 0, c.value))
        elif isinstance(c, Fill):
            flex.append((i, max(1, c.weight), 0, avail))
        else:
            raise TypeError(f"Bilinmeyen kisit: {c!r}")

    # Sabit parcalar sigmiyorsa sondan kirp
    over = sum(sizes) - avail
    for i in range(n - 1, -1, -1):
        if over <= 0:
            break
        cut = min(sizes[i], over)
        sizes[i] -= cut
        over -= cut

    # Kalan alani agirlikli dagit; Max siniri asilan parca doyar, dongu tekrarlanir
    pending = list(flex)
    while pending:
        rest = avail - sum(sizes)
        if rest <= 0:
            break
        wsum = sum(w for _, w, _, _ in pending)
        saturated = [(i, w, hi) for i, w, _, hi in pending
                     if rest * w // wsum >= hi - sizes[i]]
        if saturated:
            for i, _, hi in saturated:
                sizes[i] = max(sizes[i], hi)
            done = {i for i, _, _ in saturated}
            pending = [p for p in pending if p[0] not in done]
            continue
        given = 0
        for k, (i, w, _, _) in enumerate(pending):
            share = rest - given if k == len(pending) - 1 else rest * w // wsum
            sizes[i] += share
            given += share
        break
    return sizes


class Layout:
    def __init__(self, direction: str = VERTICAL, constraints: Sequence[Constraint] = (),
                 margin: int = 0, spacing: int = 0):
        self.direction = direction
        self.constraints = list(constraints)
        self.margin = margin
        self.spacing = spacing

    @staticmethod
    def split(area: Rect, direction: str, constraints: Sequence[Constraint],
              margin: int = 0, spacing: int = 0) -> List[Rect]:
        area = area.inner(margin) if margin else area
        horizontal = direction == HORIZONTAL
        total = area.width if horizontal else area.height
        sizes = _solve(total, constraints, spacing)
        rects, pos = [], area.x if horizontal else area.y
        for s in sizes:
            if horizontal:
                rects.append(Rect(pos, area.y, s, area.height))
            else:
                rects.append(Rect(area.x, pos, area.width, s))
            pos += s + spacing
        return rects

    def areas(self, area: Rect) -> List[Rect]:
        return Layout.split(area, self.direction, self.constraints, self.margin, self.spacing)
