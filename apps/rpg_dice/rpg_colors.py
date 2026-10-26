"""24-bit TrueColor palette, gradient helpers, ANSI formatters and the double-buffered cell grid."""
from __future__ import annotations

import math
from functools import lru_cache
from collections.abc import Sequence
from typing import Callable, List, Optional, Tuple, Union

RGB = Tuple[int, int, int]
ESC = "\033["
RESET = ESC + "0m"

# --- Palette: cosmic obsidian + gold / amber / neon cyan / crimson -------------------------
VOID: RGB = (4, 3, 10)
OBSIDIAN: RGB = (9, 7, 19)
OBSIDIAN_HI: RGB = (20, 16, 38)
PANEL_BG: RGB = (13, 10, 26)
NEBULA: RGB = (58, 28, 108)
NEBULA_TEAL: RGB = (14, 60, 90)
GOLD: RGB = (255, 200, 64)
GOLD_HI: RGB = (255, 238, 160)
AMBER: RGB = (255, 150, 30)
EMBER: RGB = (255, 96, 24)
CYAN: RGB = (40, 240, 255)
CYAN_DIM: RGB = (24, 130, 150)
CRIMSON: RGB = (224, 32, 52)
BLOOD: RGB = (120, 8, 22)
EMERALD: RGB = (70, 235, 140)
IVORY: RGB = (238, 230, 212)
MUTED: RGB = (126, 116, 156)
DIM: RGB = (70, 64, 96)
WHITE: RGB = (255, 255, 255)


def clamp8(v: float) -> int:
    return 0 if v <= 0 else 255 if v >= 255 else int(v)


def lerp(a: RGB, b: RGB, t: float) -> RGB:
    if t <= 0.0:
        return a
    if t >= 1.0:
        return b
    return (int(a[0] + (b[0] - a[0]) * t), int(a[1] + (b[1] - a[1]) * t), int(a[2] + (b[2] - a[2]) * t))


def add(a: RGB, b: RGB, k: float = 1.0) -> RGB:
    return (clamp8(a[0] + b[0] * k), clamp8(a[1] + b[1] * k), clamp8(a[2] + b[2] * k))


def scale(c: RGB, k: float) -> RGB:
    return (clamp8(c[0] * k), clamp8(c[1] * k), clamp8(c[2] * k))


def luminance(c: RGB) -> float:
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def desaturate(c: RGB, amount: float) -> RGB:
    g = int(luminance(c))
    return lerp(c, (g, g, g), amount)


def gradient(stops: Sequence[RGB], t: float) -> RGB:
    """Sample an evenly spaced multi-stop gradient at t in [0, 1]."""
    if t <= 0.0:
        return stops[0]
    if t >= 1.0:
        return stops[-1]
    pos = t * (len(stops) - 1)
    i = int(pos)
    return lerp(stops[i], stops[i + 1], pos - i)


def hsv(h: float, s: float, v: float) -> RGB:
    h = (h % 1.0) * 6.0
    i = int(h)
    f = h - i
    p, q, t = v * (1 - s), v * (1 - s * f), v * (1 - s * (1 - f))
    r, g, b = ((v, t, p), (q, v, p), (p, v, t), (p, q, v), (t, p, v), (v, p, q))[i % 6]
    return (clamp8(r * 255), clamp8(g * 255), clamp8(b * 255))


@lru_cache(maxsize=16384)
def fg(c: RGB) -> str:
    return f"{ESC}38;2;{c[0]};{c[1]};{c[2]}m"


@lru_cache(maxsize=16384)
def bg(c: RGB) -> str:
    return f"{ESC}48;2;{c[0]};{c[1]};{c[2]}m"


def cursor(x: int, y: int) -> str:
    return f"{ESC}{y + 1};{x + 1}H"


ColorSpec = Union[RGB, Callable[[int, int], RGB]]

BOX_STYLES = {
    "round": "╭╮╰╯─│",
    "double": "╔╗╚╝═║",
    "single": "┌┐└┘─│",
}


class ScreenBuffer:
    """Flat cell grid (char, fg, bg). Everything is composed here, then diffed once per frame."""

    __slots__ = ("w", "h", "ch", "fg", "bg")

    def __init__(self, w: int, h: int, base_bg: RGB = OBSIDIAN):
        self.w, self.h = w, h
        n = w * h
        self.ch: List[str] = [" "] * n
        self.fg: List[RGB] = [IVORY] * n
        self.bg: List[RGB] = [base_bg] * n

    def copy_from(self, other: "ScreenBuffer") -> None:
        self.ch[:] = other.ch
        self.fg[:] = other.fg
        self.bg[:] = other.bg

    def put(self, x: int, y: int, c: str, fg_: Optional[RGB] = None, bg_: Optional[RGB] = None) -> None:
        if 0 <= x < self.w and 0 <= y < self.h:
            i = y * self.w + x
            self.ch[i] = c
            if fg_ is not None:
                self.fg[i] = fg_
            if bg_ is not None:
                self.bg[i] = bg_

    def text(self, x: int, y: int, s: str, color: ColorSpec, bg_: Optional[RGB] = None) -> None:
        n = len(s)
        for k, c in enumerate(s):
            if c == " " and bg_ is None:
                continue
            self.put(x + k, y, c, color(k, n) if callable(color) else color, bg_)

    def fill(self, x: int, y: int, w: int, h: int, bg_: RGB, ch: str = " ") -> None:
        for yy in range(max(0, y), min(self.h, y + h)):
            for xx in range(max(0, x), min(self.w, x + w)):
                i = yy * self.w + xx
                self.ch[i] = ch
                self.bg[i] = bg_

    def tint(self, x: int, y: int, w: int, h: int, color: RGB, alpha: float) -> None:
        for yy in range(max(0, y), min(self.h, y + h)):
            row = yy * self.w
            for xx in range(max(0, x), min(self.w, x + w)):
                i = row + xx
                self.bg[i] = lerp(self.bg[i], color, alpha)
                self.fg[i] = lerp(self.fg[i], color, alpha * 0.6)

    def glow(self, x: int, y: int, color: RGB, k: float) -> None:
        if 0 <= x < self.w and 0 <= y < self.h:
            i = y * self.w + x
            self.bg[i] = add(self.bg[i], color, k)

    def box(self, x: int, y: int, w: int, h: int, color: ColorSpec, style: str = "round",
            bg_: Optional[RGB] = None, title: str = "", title_fg: RGB = GOLD) -> None:
        tl, tr, bl, br, hz, vt = BOX_STYLES[style]
        if bg_ is not None:
            self.fill(x, y, w, h, bg_)
        col = color if callable(color) else (lambda k, n: color)
        perim = 2 * (w + h)
        for k in range(w):
            self.put(x + k, y, hz, col(k, perim), bg_)
            self.put(x + k, y + h - 1, hz, col(w + h + k, perim), bg_)
        for k in range(h):
            self.put(x, y + k, vt, col(2 * w + h + k, perim), bg_)
            self.put(x + w - 1, y + k, vt, col(w + k, perim), bg_)
        self.put(x, y, tl, col(0, perim), bg_)
        self.put(x + w - 1, y, tr, col(w, perim), bg_)
        self.put(x, y + h - 1, bl, col(2 * w + h, perim), bg_)
        self.put(x + w - 1, y + h - 1, br, col(w + h, perim), bg_)
        if title:
            for k, c in enumerate(f" {title} "):
                self.put(x + 2 + k, y, c, title_fg)

    def shift(self, dx: int, dy: int, fill_bg: RGB = VOID) -> None:
        """Translate the whole frame (screen shake); uncovered cells become void."""
        if dx == 0 and dy == 0:
            return
        w, h = self.w, self.h
        for lst, blank in ((self.ch, " "), (self.fg, IVORY), (self.bg, fill_bg)):
            new: list = []
            for ny in range(h):
                sy = ny - dy
                if 0 <= sy < h:
                    row = lst[sy * w:(sy + 1) * w]
                    if dx > 0:
                        row = [blank] * min(dx, w) + row[:max(0, w - dx)]
                    elif dx < 0:
                        row = row[min(-dx, w):] + [blank] * min(-dx, w)
                    new.extend(row)
                else:
                    new.extend([blank] * w)
            lst[:] = new


class FrameWriter:
    """Diffs the new buffer against the last presented one and emits ONE escape string per frame."""

    def __init__(self) -> None:
        self.prev: Optional[ScreenBuffer] = None

    def invalidate(self) -> None:
        self.prev = None

    def present(self, buf: ScreenBuffer) -> str:
        w = buf.w
        prev = self.prev
        parts: List[str] = []
        fresh = prev is None or prev.w != buf.w or prev.h != buf.h
        if fresh:
            parts.append(RESET + ESC + "2J")
            pch = pfg = pbg = None
        else:
            pch, pfg, pbg = prev.ch, prev.fg, prev.bg
        cur_fg = cur_bg = None
        last = -2
        ch, fgl, bgl = buf.ch, buf.fg, buf.bg
        for i in range(w * buf.h):
            c, f, b = ch[i], fgl[i], bgl[i]
            if pch is not None and pch[i] == c and pfg[i] == f and pbg[i] == b:
                continue
            if i != last + 1 or i % w == 0:
                parts.append(cursor(i % w, i // w))
            if b != cur_bg:
                parts.append(bg(b))
                cur_bg = b
            if f != cur_fg and c != " ":
                parts.append(fg(f))
                cur_fg = f
            parts.append(c)
            last = i
        if fresh:
            self.prev = ScreenBuffer(buf.w, buf.h)
        self.prev.copy_from(buf)
        if parts:
            parts.append(RESET)
        return "".join(parts)


def text_gradient(stops: Sequence[RGB], shift: float = 0.0) -> Callable[[int, int], RGB]:
    """Per-character gradient colour function for ScreenBuffer.text()."""
    def fn(k: int, n: int) -> RGB:
        t = (k / max(1, n - 1) + shift) % 2.0
        if t > 1.0:
            t = 2.0 - t
        return gradient(stops, t)
    return fn


def pulse(t: float, speed: float = 1.0, lo: float = 0.0, hi: float = 1.0) -> float:
    return lo + (hi - lo) * (0.5 + 0.5 * math.sin(t * speed * math.tau))
