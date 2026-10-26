"""CyberEye matematigi: kure analitigi, goz kapaklari, iris/gozbebegi ve karakter yogunluk shader'i."""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Optional, Tuple, Union

from ..core.style import Color, gradient
from .flower_math import clamp01, smoothstep

LIGHT = (-0.45, -0.55, 0.70)  # sol-ust-onden isik (normalize edilmemis; shade icinde normalize edilir)
DENSITY_RAMP = " .:-=+*#%@"
# Parlaklik bandi -> sifreli karakter havuzu (harf, rakam, matematik sembolu)
CYBER_POOLS = (" .`'", "·:;,-~", "+=*<>^v", "1l7ItfjrxnuvczXY", "2345689abdeghkopqsy",
               "ABCDEFGHJKLMNPRSTUVWXYZ", "0OQ8&B%$#MW@ΣπΩ∂∫√∞≈≠∑")
MATRIX_STYLES = ("cyber", "density")
RAMP_STEPS = 64


@dataclass(frozen=True)
class EyePalette:
    name: str
    bg: Color
    stops: Tuple[Color, ...]   # koyudan parlaga
    glint: Color               # parlama noktasi


def _p(name: str, bg: str, stops: Tuple[str, ...], glint: str) -> EyePalette:
    return EyePalette(name, Color.from_hex(bg), tuple(Color.from_hex(s) for s in stops),
                      Color.from_hex(glint))


EYE_PALETTES = (
    _p("Amber / Kehribar", "#0a0402", ("#2a0d00", "#e65100", "#ff8c00", "#ffaa33", "#fff1d0"), "#fffbe8"),
    _p("Siber Yesil / Matrix", "#010a04", ("#022b0e", "#009933", "#00cc4f", "#00ff66", "#e6fff0"), "#f2fff7"),
    _p("Kanli Ay / Kizil", "#0a0204", ("#2b0508", "#b71c1c", "#e0112f", "#ff1744", "#ffe3e8"), "#fff2f4"),
    _p("Sayborg Mavisi", "#010609", ("#00162b", "#0091ea", "#00b8f0", "#00e5ff", "#e3fbff"), "#f2fdff"),
)
_RAMPS: dict = {}


def get_eye_palette(p: Union[str, EyePalette, int]) -> EyePalette:
    if isinstance(p, EyePalette):
        return p
    if isinstance(p, int):
        return EYE_PALETTES[p % len(EYE_PALETTES)]
    key = p.lower()
    for pal in EYE_PALETTES:
        if key in pal.name.lower():
            return pal
    raise KeyError(f"bilinmeyen goz paleti: {p}")


def palette_ramp(pal: EyePalette) -> List[Color]:
    """Palet icin onceden hesaplanmis 64 adimli parlaklik -> renk tablosu."""
    r = _RAMPS.get(pal.name)
    if r is None:
        r = _RAMPS[pal.name] = gradient(list(pal.stops), RAMP_STEPS)
    return r


# --- kure analitigi ---
def sphere_z(x: float, y: float, r: float) -> Optional[float]:
    """z = sqrt(R^2 - x^2 - y^2); kure disinda None."""
    d = r * r - x * x - y * y
    return math.sqrt(d) if d >= 0 else None


def sphere_normal(x: float, y: float, r: float) -> Optional[Tuple[float, float, float]]:
    z = sphere_z(x, y, r)
    return None if z is None or r <= 0 else (x / r, y / r, z / r)


def shade_curvature(n: Tuple[float, float, float], ambient: float = 0.28) -> float:
    """Lambert + kenar kararmasi (egrilik): merkez parlak, limb karanlik."""
    lx, ly, lz = LIGHT
    inv = 1.0 / math.sqrt(lx * lx + ly * ly + lz * lz)
    lam = max(0.0, (n[0] * lx + n[1] * ly + n[2] * lz) * inv)
    return clamp01(ambient + (1 - ambient) * lam * (0.35 + 0.65 * n[2]))


# --- goz kapaklari ---
def blink_closure(t: float) -> float:
    """Goz kirpma kapanma orani (0 acik, 1 kapali). Hizli kapanir, yavas acilir."""
    t = clamp01(t)
    if t < 0.35:
        return smoothstep(t / 0.35)
    return 1.0 - smoothstep((t - 0.35) / 0.65)


def eyelid_bounds(u: float, lid_h: float, lower_h: float, closure: float = 0.0,
                  shift: float = 0.0) -> Optional[Tuple[float, float]]:
    """u in (-1,1) icin (ust, alt) kapak y siniri (parabolik, y asagi pozitif). Disarida None.
    Kapanma: ust kapak asagi iner, alt kapak hafif yukselir; `shift` bakisi izleyen kayma."""
    if abs(u) >= 1.0:
        return None
    k = 1.0 - u * u
    top = shift - lid_h * k * (1.0 - closure)
    bot = shift + lower_h * k * (1.0 - 0.35 * closure)
    return top, max(top, bot)


# --- iris / gozbebegi ---
def iris_center(gx: float, gy: float, half_w: float, iris_r: float) -> Tuple[float, float, float]:
    """Bakis (gx, gy in [-1,1]) -> iris merkezi (x, y) ve yatay kisalma (kuredeki egim)."""
    cx = max(-1.0, min(1.0, gx)) * half_w * 0.42
    cy = max(-1.0, min(1.0, gy)) * iris_r * 0.55
    squash = math.sqrt(max(0.25, 1 - (cx / (half_w * 1.05)) ** 2))
    return cx, cy, squash


def pupil_radius(iris_r: float, dilation: float) -> float:
    return iris_r * (0.22 + 0.42 * clamp01(dilation))


def iris_intensity(r: float, ang: float, pupil_r: float, t: float = 0.0) -> float:
    """Iris birim yaricapinda (r in 0..1) isik: gozbebegi ~0, radyal lifler, halka, limbal kararma."""
    if r < pupil_r:
        return 0.03
    span = max(1e-6, 1.0 - pupil_r)
    q = (r - pupil_r) / span                       # 0 gozbebegi kenari .. 1 limbus
    fib = 0.5 + 0.5 * math.sin(ang * 26 + math.sin(ang * 5 + t * 0.4) * 2.2 + q * 3.0)
    fib2 = 0.5 + 0.5 * math.sin(ang * 61 - q * 5.0)
    base = 0.50 + 0.30 * fib + 0.12 * fib2
    collarette = 0.22 * math.exp(-((q - 0.18) / 0.10) ** 2)
    limbal = smoothstep((q - 0.78) / 0.22)
    return clamp01((base + collarette) * (1.0 - 0.75 * limbal) * (0.75 + 0.25 * (1 - q)))


# --- karakter shader'i ---
def cell_hash(x: int, y: int, k: int = 0) -> float:
    n = (x * 374761393 + y * 668265263 + k * 1274126177) & 0xFFFFFFFF
    n = ((n ^ (n >> 13)) * 1103515245) & 0xFFFFFFFF
    return ((n ^ (n >> 16)) & 0xFFFF) / 65535.0


def glyph_for(intensity: float, style: str, x: int = 0, y: int = 0, tick: int = 0) -> str:
    """Parlakliktan karakter: 'density' sabit derece, 'cyber' band havuzundan hash + zamanla titresen."""
    v = clamp01(intensity)
    if style == "density":
        return DENSITY_RAMP[min(len(DENSITY_RAMP) - 1, int(v * len(DENSITY_RAMP)))]
    band = min(len(CYBER_POOLS) - 1, int(v * len(CYBER_POOLS)))
    pool = CYBER_POOLS[band]
    # parlak bantlar daha yavas, sonuk bantlar daha hizli degisir
    k = tick // (3 + band * 2)
    return pool[int(cell_hash(x, y, k) * len(pool)) % len(pool)]


def shade_color(intensity: float, pal: EyePalette) -> Color:
    ramp = palette_ramp(pal)
    return ramp[min(RAMP_STEPS - 1, int(clamp01(intensity) * (RAMP_STEPS - 1) + 0.5))]
