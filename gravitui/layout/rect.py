"""Rect: dikdortgen alan islemleri."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class Rect:
    x: int
    y: int
    width: int
    height: int

    def __post_init__(self):
        object.__setattr__(self, "width", max(0, self.width))
        object.__setattr__(self, "height", max(0, self.height))

    @property
    def right(self) -> int:
        return self.x + self.width

    @property
    def bottom(self) -> int:
        return self.y + self.height

    @property
    def area(self) -> int:
        return self.width * self.height

    def is_empty(self) -> bool:
        return self.width == 0 or self.height == 0

    def contains(self, x: int, y: int) -> bool:
        return self.x <= x < self.right and self.y <= y < self.bottom

    def pad(self, left: int = 0, top: int = 0, right: int = 0, bottom: int = 0) -> "Rect":
        return Rect(self.x + left, self.y + top,
                    self.width - left - right, self.height - top - bottom)

    def inner(self, n: int = 1) -> "Rect":
        return self.pad(n, n, n, n)

    def intersect(self, other: "Rect") -> "Rect":
        x1, y1 = max(self.x, other.x), max(self.y, other.y)
        x2, y2 = min(self.right, other.right), min(self.bottom, other.bottom)
        if x2 <= x1 or y2 <= y1:
            return Rect(x1, y1, 0, 0)
        return Rect(x1, y1, x2 - x1, y2 - y1)

    def union(self, other: "Rect") -> "Rect":
        x1, y1 = min(self.x, other.x), min(self.y, other.y)
        return Rect(x1, y1, max(self.right, other.right) - x1,
                    max(self.bottom, other.bottom) - y1)

    def centered(self, width: int, height: int) -> "Rect":
        w, h = min(width, self.width), min(height, self.height)
        return Rect(self.x + (self.width - w) // 2, self.y + (self.height - h) // 2, w, h)

    def split_h(self, at: int) -> List["Rect"]:
        """Yatayda (sol|sag) `at` genislikte boler."""
        at = max(0, min(at, self.width))
        return [Rect(self.x, self.y, at, self.height),
                Rect(self.x + at, self.y, self.width - at, self.height)]

    def split_v(self, at: int) -> List["Rect"]:
        """Dikeyde (ust/alt) `at` yukseklikte boler."""
        at = max(0, min(at, self.height))
        return [Rect(self.x, self.y, self.width, at),
                Rect(self.x, self.y + at, self.width, self.height - at)]
