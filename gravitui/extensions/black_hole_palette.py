"""Karadelik paletleri: klasik rampa paletleri ve Aurum (TwoHorizonsWallpaper) uyumlu sicaklik-tonlu palet.
`tone` (cool, mid, hot) dogrusal RGB ucluleri, `aurum.js` icindeki uCool/uMid/uHot ile birebir aynidir."""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Union

from ..core.style import Color, gradient

RGB = Tuple[float, float, float]
RAMP_STEPS = 64
HUE_STEPS, HUE_MAX = 96, 3.0           # sicaklik*Doppler (tt) 0..3 araliginda renk tablosu
AURUM_TONE: Tuple[RGB, RGB, RGB] = ((0.52, 0.14, 0.03), (1.00, 0.48, 0.12), (1.00, 0.85, 0.52))


def _smooth(a: float, b: float, v: float) -> float:
    t = (v - a) / (b - a)
    t = 0.0 if t < 0.0 else 1.0 if t > 1.0 else t
    return t * t * (3.0 - 2.0 * t)


def tone_hue(tone: Tuple[RGB, RGB, RGB], tt: float) -> RGB:
    """`diskSample` renk karisimi: cool -> mid (tt 0.1..0.7), sonra -> hot (tt 0.8..1.9)."""
    cool, mid, hot = tone
    a, b = _smooth(0.1, 0.7, tt), _smooth(0.8, 1.9, tt)
    r, g, bl = ((cool[k] + (mid[k] - cool[k]) * a) * (1.0 - b) + hot[k] * b for k in range(3))
    return r, g, bl


def aces(x: float) -> float:
    """ACES filmik egrisi (Narkowicz uyarlamasi); three.js ACESFilmicToneMapping'in hafif karsiligi."""
    y = (x * (2.51 * x + 0.03)) / (x * (2.43 * x + 0.59) + 0.14)
    return 0.0 if y < 0.0 else 1.0 if y > 1.0 else y


def tone_map(r: float, g: float, b: float, exposure: float = 1.0) -> Color:
    """Dogrusal HDR -> ekran rengi: pozlama, ACES, sRGB gama (1/2.2)."""
    e = exposure
    return Color(255.0 * aces(r * e) ** 0.4545, 255.0 * aces(g * e) ** 0.4545, 255.0 * aces(b * e) ** 0.4545)


@dataclass(frozen=True)
class BlackHolePalette:
    name: str
    bg: Color
    stops: Tuple[Color, ...]   # koyudan parlaga (kirmizi kaymis -> mavi kaymis/beyaz)
    star: Color
    tone: Optional[Tuple[RGB, RGB, RGB]] = None   # (cool, mid, hot); None -> klasik rampa boyama
    gain: float = 1.0                             # disk parlakligi (aurum: 1.1)
    dopp: float = 1.0                             # Doppler asimetri carpani (aurum: 1.05)
    exposure: float = 1.0                         # ACES pozlamasi (aurum: 0.92)
    rings: int = 1                                # birlestirilen disk goruntusu sayisi (1 = yalniz birincil)
    inclination: float = 82.0                     # onerilen egim (kutuptan, derece)
    disk_size: float = 12.0                       # onerilen dis yaricap (Rs)
    aliases: Tuple[str, ...] = ()


def _p(name: str, bg: str, stops: Tuple[str, ...], star: str) -> BlackHolePalette:
    return BlackHolePalette(name, Color.from_hex(bg), tuple(Color.from_hex(s) for s in stops), Color.from_hex(star))


def _aurum() -> BlackHolePalette:
    tone, exp = AURUM_TONE, 0.92
    samples = ((0.15, 0.04), (0.45, 0.35), (0.8, 1.2), (1.3, 4.0), (2.2, 16.0))
    stops = tuple(tone_map(*(c * i for c in tone_hue(tone, tt)), exp) for tt, i in samples)
    # AURUM: camD=18, inc=0.10 rad (~5.7 derece ufuk ustu) -> kutuptan 90-5.73 derece; rOut=8.4; rIn=3 (ISCO)
    return BlackHolePalette("Aurum Amber", Color.from_hex("#030201"), stops, Color.from_hex("#d8cfc0"), tone,
                            gain=1.1, dopp=1.05, exposure=exp, rings=2,
                            inclination=90.0 - math.degrees(0.10), disk_size=8.4, aliases=("aerum", "amber"))


BLACK_HOLE_PALETTES = (
    _aurum(),
    _p("Gargantua Gold", "#030201", ("#0d0300", "#4a1500", "#b04a08", "#ff9a1f", "#ffd27a", "#fff4dc"), "#d8cfc0"),
    _p("Hawking Blue", "#01020a", ("#06041c", "#2a1670", "#2f5be0", "#5cc8ff", "#c8f0ff", "#ffffff"), "#c8d8ff"),
    _p("Crimson Singularity", "#060102", ("#0c0104", "#3a0410", "#9a0f1f", "#ee2a2a", "#ff8a6a", "#ffe6d8"), "#e0b8b8"),
    _p("Cyber Matrix", "#010502", ("#01120a", "#04502a", "#00b050", "#20ff80", "#9dffc8", "#eafff3"), "#a8e8c0"),
)
DEFAULT_PALETTE = BLACK_HOLE_PALETTES[0]
_RAMPS: Dict[str, List[Color]] = {}
_HUES: Dict[str, List[RGB]] = {}
_STAR_LEVELS: Dict[str, List[Color]] = {}


def get_black_hole_palette(p: Union[str, int, BlackHolePalette]) -> BlackHolePalette:
    if isinstance(p, BlackHolePalette):
        return p
    if isinstance(p, int):
        return BLACK_HOLE_PALETTES[p % len(BLACK_HOLE_PALETTES)]
    key = p.lower()
    for pal in BLACK_HOLE_PALETTES:
        if key in pal.name.lower() or key in pal.aliases:
            return pal
    raise KeyError(f"bilinmeyen karadelik paleti: {p}")


def palette_ramp(pal: BlackHolePalette) -> List[Color]:
    r = _RAMPS.get(pal.name)
    if r is None:
        r = _RAMPS[pal.name] = gradient(list(pal.stops), RAMP_STEPS)
    return r


def palette_hues(pal: BlackHolePalette) -> List[RGB]:
    """`tone` paleti icin tt -> dogrusal renk tablosu (HUE_STEPS adim, 0..HUE_MAX)."""
    h = _HUES.get(pal.name)
    if h is None:
        h = _HUES[pal.name] = [tone_hue(pal.tone, HUE_MAX * k / (HUE_STEPS - 1)) for k in range(HUE_STEPS)] \
            if pal.tone else []
    return h


def star_levels(pal: BlackHolePalette) -> List[Color]:
    r = _STAR_LEVELS.get(pal.name)
    if r is None:
        r = _STAR_LEVELS[pal.name] = [pal.bg.lerp(pal.star, 0.25 + 0.75 * k / 7) for k in range(8)]
    return r
