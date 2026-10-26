"""Zambak matematigi: easing, Bezier, polar egriler, yasam dongusu FSM, paletler, alt-piksel tuvalleri."""
from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Dict, List, Optional, Sequence, Tuple, Union

from ..core.style import Color

Point = Tuple[float, float]


def clamp01(v: float) -> float:
    return 0.0 if v < 0 else 1.0 if v > 1 else v


def smoothstep(t: float) -> float:
    t = clamp01(t)
    return t * t * (3 - 2 * t)


def ease_out_cubic(t: float) -> float:
    return 1 - (1 - clamp01(t)) ** 3


def ease_in_out_cubic(t: float) -> float:
    t = clamp01(t)
    return 4 * t * t * t if t < 0.5 else 1 - (-2 * t + 2) ** 3 / 2


def ease_out_back(t: float, s: float = 1.70158) -> float:
    """Gerilimli easing: hedefi hafifce asip geri oturur (taç yaprak açilisi)."""
    u = clamp01(t) - 1
    return 1 + (s + 1) * u ** 3 + s * u * u


def cubic_bezier(p0: Point, p1: Point, p2: Point, p3: Point, t: float) -> Point:
    u = 1 - t
    a, b, c, d = u * u * u, 3 * u * u * t, 3 * u * t * t, t * t * t
    return (a * p0[0] + b * p1[0] + c * p2[0] + d * p3[0],
            a * p0[1] + b * p1[1] + c * p2[1] + d * p3[1])


def polar_point(cx: float, cy: float, r: float, theta: float) -> Point:
    return (cx + r * math.cos(theta), cy + r * math.sin(theta))


def petal_curve(length: float, width: float, angle: float, curl: float = 0.0,
                n: int = 12, x: float = 0.0, y: float = 0.0) -> Tuple[List[Point], List[float]]:
    """Yaprak ekseni + yari genislik profili. `angle` dikeyden radyan (+ saga), `curl` uca dogru
    eklenen dis kivrim. Genislik tabanda ve uçta 0, ortada `width` (sivri sinuzoidal profil)."""
    axis, half = [(x, y)], [0.0]
    step = length / n
    for i in range(1, n + 1):
        u = i / n
        a = angle + curl * u * u
        x, y = x + math.sin(a) * step, y - math.cos(a) * step
        axis.append((x, y))
        half.append(width * math.sin(math.pi * u ** 0.75) ** 0.8 * (1 - 0.25 * u))
    return axis, half


class FlowerPhase(Enum):
    SPROUT = "Filiz"
    STEM = "Sap ve Yapraklar"
    BUD = "Tomurcuk"
    BLOOM = "Açılış"
    FULL = "Tam Zambak"


PHASE_ORDER = (FlowerPhase.SPROUT, FlowerPhase.STEM, FlowerPhase.BUD, FlowerPhase.BLOOM)
DURATIONS = (4.0, 5.0, 3.5, 6.0)


def lifecycle(age: float, durations: Sequence[float] = DURATIONS) -> Tuple[FlowerPhase, float]:
    """Yasam dongusu FSM'i: (faz, faz ici ilerleme 0..1). Son fazdan sonra FULL, 1.0."""
    t = max(0.0, age)
    for phase, d in zip(PHASE_ORDER, durations):
        if t < d:
            return phase, t / d
        t -= d
    return FlowerPhase.FULL, 1.0


@dataclass(frozen=True)
class FlowerPalette:
    name: str
    petal: Tuple[Color, ...]      # taban -> uc gradyani
    stem: Color
    leaf: Color
    bud: Color
    core: Color
    stamen: Color
    pollen: Color
    orbit_a: Color
    orbit_b: Color
    bg: Color
    soil: Color


def _p(name, petal, stem, leaf, bud, core, stamen, pollen, oa, ob, bg, soil) -> FlowerPalette:
    h = Color.from_hex
    return FlowerPalette(name, tuple(h(c) for c in petal), h(stem), h(leaf), h(bud), h(core),
                         h(stamen), h(pollen), h(oa), h(ob), h(bg), h(soil))


FLOWER_PALETTES: Tuple[FlowerPalette, ...] = (
    _p("Zambak", ("#fff5fa", "#ffb0d8", "#e0218a"), "#2fa062", "#13804d", "#6fcf7a", "#ffd24a",
       "#ffb000", "#ffe27a", "#7a3cff", "#36e0ff", "#070612", "#3a2418"),
    _p("Siber Lotus", ("#e6ffff", "#26d9ff", "#7a3cff"), "#0f9d8a", "#0b6f8a", "#2fd6c4", "#f0ffff",
       "#4dffea", "#7dfcff", "#00e5ff", "#b04dff", "#03040f", "#101830"),
    _p("Altın Orkide", ("#fff1c1", "#ffb627", "#8a2e08"), "#6b7a2e", "#46541f", "#c9a227", "#fff3b0",
       "#ff8c00", "#ffd45e", "#ffb000", "#8a5a00", "#050403", "#1a120a"),
    _p("Ruh Zambağı", ("#ffffff", "#cfd8ff", "#7f9cff"), "#8aa0c8", "#5f78a8", "#b8c6ee", "#ffffff",
       "#dfe8ff", "#e8f0ff", "#c0c8e0", "#4f7bff", "#04050c", "#14182a"),
)


def get_palette(p: Union[str, FlowerPalette]) -> FlowerPalette:
    if isinstance(p, FlowerPalette):
        return p
    for pal in FLOWER_PALETTES:
        if pal.name.lower() == p.lower():
            return pal
    raise ValueError(f"Bilinmeyen palet: {p!r}")


ColorFn = Callable[[float, float], Color]  # (u: eksen boyunca 0..1, v: yanal -1..1) -> renk


class PixelCanvas:
    """Yari blok alt-pikselleri: genislik = hucre, yukseklik = 2 x hucre (kare pikseller)."""

    def __init__(self, w: int, h: int, bg: Color):
        self.w, self.h, self.bg = w, h, bg
        self.px: List[Optional[Color]] = [None] * (w * h)

    def set(self, x: int, y: int, c: Color) -> None:
        if 0 <= x < self.w and 0 <= y < self.h:
            self.px[y * self.w + x] = c

    def blend(self, x: int, y: int, c: Color, a: float) -> None:
        if 0 <= x < self.w and 0 <= y < self.h:
            i = y * self.w + x
            self.px[i] = (self.px[i] or self.bg).lerp(c, a)

    def fill_strip(self, axis: Sequence[Point], half: Sequence[float], color_fn: ColorFn) -> None:
        """Eksen boyunca yari genislikli seridi dortgenlere bolup tarama cizgisiyle doldurur."""
        n = len(axis)
        if n < 2:
            return
        left, right = [], []
        for i, (x, y) in enumerate(axis):
            x0, y0 = axis[max(i - 1, 0)]
            x1, y1 = axis[min(i + 1, n - 1)]
            dx, dy = x1 - x0, y1 - y0
            ln = math.hypot(dx, dy) or 1.0
            nx, ny = -dy / ln, dx / ln
            left.append((x + nx * half[i], y + ny * half[i]))
            right.append((x - nx * half[i], y - ny * half[i]))
        for i in range(n - 1):
            self._fill_quad((left[i], left[i + 1], right[i + 1], right[i]), color_fn, (i + 0.5) / (n - 1))

    def _fill_quad(self, quad, color_fn: ColorFn, u: float) -> None:
        ys = [p[1] for p in quad]
        for y in range(max(0, math.ceil(min(ys) - 0.5)), min(self.h - 1, math.floor(max(ys) - 0.5)) + 1):
            yc, xs = y + 0.5, []
            for k in range(4):
                (xa, ya), (xb, yb) = quad[k], quad[(k + 1) % 4]
                if ya <= yc < yb or yb <= yc < ya:
                    xs.append(xa + (yc - ya) * (xb - xa) / (yb - ya))
            if len(xs) < 2:
                continue
            x0, x1 = min(xs), max(xs)
            span = (x1 - x0) or 1.0
            for x in range(max(0, math.ceil(x0 - 0.5)), min(self.w - 1, math.floor(x1 - 0.5)) + 1):
                self.px[y * self.w + x] = color_fn(u, 2 * ((x + 0.5 - x0) / span) - 1)


_DOT = ((0x01, 0x08), (0x02, 0x10), (0x04, 0x20), (0x40, 0x80))  # [satir][sutun]


class BrailleLayer:
    """Hucre basina 2x4 nokta: ince yorunge yaylari icin."""

    def __init__(self, cols: int, rows: int):
        self.cols, self.rows = cols, rows
        self.mask: Dict[int, int] = {}
        self.color: Dict[int, Color] = {}

    def dot(self, bx: float, by: float, color: Color) -> None:
        bx, by = math.floor(bx), math.floor(by)
        if bx < 0 or by < 0 or bx >= self.cols * 2 or by >= self.rows * 4:
            return
        key = (by // 4) * self.cols + bx // 2
        self.mask[key] = self.mask.get(key, 0) | _DOT[by % 4][bx % 2]
        old = self.color.get(key)
        if old is None or color.r + color.g + color.b > old.r + old.g + old.b:
            self.color[key] = color

    def arc(self, cx: float, cy: float, r: float, a0: float, a1: float,
            color_fn: Callable[[float], Color], skip: int = 1) -> None:
        """(cx, cy, r) nokta koordinatindadir; skip>1 noktalı (kesikli) cizgi verir."""
        steps = max(8, int(abs(a1 - a0) * r / 0.6))
        for i in range(0, steps + 1, skip):
            t = i / steps
            x, y = polar_point(cx, cy, r, a0 + (a1 - a0) * t)
            self.dot(x, y, color_fn(t))
