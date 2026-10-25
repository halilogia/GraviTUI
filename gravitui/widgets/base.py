"""Widget soyut sinifi."""
from __future__ import annotations

from abc import ABC, abstractmethod

from ..core.buffer import Buffer
from ..layout.rect import Rect


class Widget(ABC):
    @abstractmethod
    def render(self, area: Rect, buf: Buffer) -> None:
        """`area` icine, `buf` uzerine cizer."""
