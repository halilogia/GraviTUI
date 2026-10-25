"""24-bit TrueColor renkler, gradyanlar ve metin stilleri."""
from __future__ import annotations

import colorsys
from dataclasses import dataclass
from typing import List, Optional, Tuple


def _clamp(v: float) -> int:
    return max(0, min(255, int(round(v))))


@dataclass(frozen=True)
class Color:
    r: int
    g: int
    b: int

    def __post_init__(self):
        object.__setattr__(self, "r", _clamp(self.r))
        object.__setattr__(self, "g", _clamp(self.g))
        object.__setattr__(self, "b", _clamp(self.b))

    @staticmethod
    def from_hex(value: str) -> "Color":
        s = value.lstrip("#")
        if len(s) == 3:
            s = "".join(c * 2 for c in s)
        if len(s) != 6:
            raise ValueError(f"Gecersiz hex renk: {value!r}")
        return Color(int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16))

    @staticmethod
    def from_hsv(h: float, s: float, v: float) -> "Color":
        """h: 0..360, s/v: 0..1."""
        r, g, b = colorsys.hsv_to_rgb((h % 360) / 360.0, s, v)
        return Color(r * 255, g * 255, b * 255)

    def to_hex(self) -> str:
        return f"#{self.r:02x}{self.g:02x}{self.b:02x}"

    def to_hsv(self) -> Tuple[float, float, float]:
        h, s, v = colorsys.rgb_to_hsv(self.r / 255, self.g / 255, self.b / 255)
        return h * 360, s, v

    def lerp(self, other: "Color", t: float) -> "Color":
        t = max(0.0, min(1.0, t))
        return Color(self.r + (other.r - self.r) * t,
                     self.g + (other.g - self.g) * t,
                     self.b + (other.b - self.b) * t)

    def scale(self, k: float) -> "Color":
        return Color(self.r * k, self.g * k, self.b * k)

    def fg_code(self) -> str:
        return f"38;2;{self.r};{self.g};{self.b}"

    def bg_code(self) -> str:
        return f"48;2;{self.r};{self.g};{self.b}"


def gradient(stops: List[Color], steps: int) -> List[Color]:
    """Birden fazla durak arasinda dogrusal gradyan uretir."""
    if steps <= 0 or not stops:
        return []
    if len(stops) == 1 or steps == 1:
        return [stops[0]] * steps
    out = []
    segs = len(stops) - 1
    for i in range(steps):
        pos = i / (steps - 1) * segs
        k = min(int(pos), segs - 1)
        out.append(stops[k].lerp(stops[k + 1], pos - k))
    return out


def gradient_at(stops: List[Color], t: float) -> Color:
    t = max(0.0, min(1.0, t))
    if len(stops) == 1:
        return stops[0]
    segs = len(stops) - 1
    pos = t * segs
    k = min(int(pos), segs - 1)
    return stops[k].lerp(stops[k + 1], pos - k)


@dataclass(frozen=True)
class Style:
    fg: Optional[Color] = None
    bg: Optional[Color] = None
    bold: bool = False
    dim: bool = False
    italic: bool = False
    underline: bool = False

    def patch(self, other: "Style") -> "Style":
        """`other` ustune biner; None olan alanlar bu stilden kalir."""
        return Style(other.fg or self.fg, other.bg or self.bg,
                     self.bold or other.bold, self.dim or other.dim,
                     self.italic or other.italic, self.underline or other.underline)

    def sgr(self) -> str:
        codes = ["0"]
        if self.bold:
            codes.append("1")
        if self.dim:
            codes.append("2")
        if self.italic:
            codes.append("3")
        if self.underline:
            codes.append("4")
        if self.fg:
            codes.append(self.fg.fg_code())
        if self.bg:
            codes.append(self.bg.bg_code())
        return "\x1b[" + ";".join(codes) + "m"


DEFAULT_STYLE = Style()
WHITE = Color(255, 255, 255)
BLACK = Color(0, 0, 0)
GRAY = Color(128, 128, 128)
RED = Color(255, 85, 85)
GREEN = Color(80, 250, 123)
BLUE = Color(98, 114, 255)
YELLOW = Color(241, 250, 140)
CYAN = Color(139, 233, 253)
MAGENTA = Color(255, 121, 198)
ORANGE = Color(255, 160, 60)
