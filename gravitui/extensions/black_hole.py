"""BlackHole: Gargantua (Interstellar) karadeligi; merceklenmis disk, Doppler isinimi, Kepler donusu.
Isin izleme yerine onceden hesaplanan geodezik supurme tablosu ve onbellekli piksel->disk haritasi kullanir."""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List, Tuple, Union

from ..core.buffer import Buffer, Cell
from ..core.style import Color, gradient
from ..layout.rect import Rect
from ..widgets.base import Widget
from .black_hole_math import (CRIT_B, disk_crossings, disk_omega, disk_temperature, doppler_factor,
                              doppler_range, isco_radius, miller_years_per_hour, orbital_lorentz_factor,
                              orbital_time_dilation, photon_sphere_radius, plasma_turbulence,
                              schwarzschild_radius_km, smoothstep)

RAMP_STEPS = 64
MODES = ("halfblock", "ascii")
ASCII_RAMP = " .:-=+*#%@"
EXPOSURE = 2.2
MASS_RANGE = (0.4, 2.5)
DISK_RANGE = (6.0, 20.0)


@dataclass(frozen=True)
class BlackHolePalette:
    name: str
    bg: Color
    stops: Tuple[Color, ...]   # koyudan parlaga (kirmizi kaymis -> mavi kaymis/beyaz)
    star: Color


def _p(name: str, bg: str, stops: Tuple[str, ...], star: str) -> BlackHolePalette:
    return BlackHolePalette(name, Color.from_hex(bg), tuple(Color.from_hex(s) for s in stops), Color.from_hex(star))


BLACK_HOLE_PALETTES = (
    _p("Gargantua Gold", "#030201", ("#0d0300", "#4a1500", "#b04a08", "#ff9a1f", "#ffd27a", "#fff4dc"), "#d8cfc0"),
    _p("Hawking Blue", "#01020a", ("#06041c", "#2a1670", "#2f5be0", "#5cc8ff", "#c8f0ff", "#ffffff"), "#c8d8ff"),
    _p("Crimson Singularity", "#060102", ("#0c0104", "#3a0410", "#9a0f1f", "#ee2a2a", "#ff8a6a", "#ffe6d8"), "#e0b8b8"),
    _p("Cyber Matrix", "#010502", ("#01120a", "#04502a", "#00b050", "#20ff80", "#9dffc8", "#eafff3"), "#a8e8c0"),
)
_RAMPS: Dict[str, List[Color]] = {}
_STAR_LEVELS: Dict[str, List[Color]] = {}


def get_black_hole_palette(p: Union[str, int, BlackHolePalette]) -> BlackHolePalette:
    if isinstance(p, BlackHolePalette):
        return p
    if isinstance(p, int):
        return BLACK_HOLE_PALETTES[p % len(BLACK_HOLE_PALETTES)]
    key = p.lower()
    for pal in BLACK_HOLE_PALETTES:
        if key in pal.name.lower():
            return pal
    raise KeyError(f"bilinmeyen karadelik paleti: {p}")


def palette_ramp(pal: BlackHolePalette) -> List[Color]:
    r = _RAMPS.get(pal.name)
    if r is None:
        r = _RAMPS[pal.name] = gradient(list(pal.stops), RAMP_STEPS)
    return r


def _star_levels(pal: BlackHolePalette) -> List[Color]:
    r = _STAR_LEVELS.get(pal.name)
    if r is None:
        r = _STAR_LEVELS[pal.name] = [pal.bg.lerp(pal.star, 0.25 + 0.75 * k / 7) for k in range(8)]
    return r


class _LensMap:
    """Bir (boyut, egim, kutle, disk) icin piksel basina: (0, T, g, omega, rn, phi, yuz) disk, (1, fx, fy, parilti,
    gx) gokyuzu ya da (2,) golge."""
    def __init__(self, key, px):
        self.key, self.px = key, px


class BlackHole(Widget):
    def __init__(self, palette: Union[str, int, BlackHolePalette] = 0, mode: str = "halfblock",
                 inclination: float = 80.0, azimuth: float = 0.0, mass: float = 1.0,
                 disk_size: float = 12.0, spin: float = 0.55, doppler: bool = True):
        self.palette = get_black_hole_palette(palette)
        self.mode = mode if mode in MODES else MODES[0]
        self.inclination = max(0.0, min(89.0, float(inclination)))
        self.azimuth = azimuth % 360.0
        self.mass = max(MASS_RANGE[0], min(MASS_RANGE[1], mass))
        self.disk_size = max(DISK_RANGE[0], min(DISK_RANGE[1], disk_size))
        self.spin = spin
        self.doppler = doppler
        self.paused = False
        self.time = 0.0
        self._map = None

    # --- kontrol ---
    def tilt(self, d_deg: float) -> float:
        self.inclination = max(0.0, min(89.0, self.inclination + d_deg))
        return self.inclination

    def rotate(self, d_deg: float) -> float:
        self.azimuth = (self.azimuth + d_deg) % 360.0
        return self.azimuth

    def set_mass(self, mass: float) -> float:
        self.mass = max(MASS_RANGE[0], min(MASS_RANGE[1], mass))
        return self.mass

    def set_disk_size(self, size: float) -> float:
        self.disk_size = max(DISK_RANGE[0], min(DISK_RANGE[1], size))
        return self.disk_size

    def set_spin(self, spin: float) -> float:
        self.spin = max(-3.0, min(3.0, spin))
        return self.spin

    def toggle_doppler(self) -> bool:
        self.doppler = not self.doppler
        return self.doppler

    def toggle_pause(self) -> bool:
        self.paused = not self.paused
        return self.paused

    def next_palette(self) -> BlackHolePalette:
        i = BLACK_HOLE_PALETTES.index(self.palette) if self.palette in BLACK_HOLE_PALETTES else -1
        self.palette = BLACK_HOLE_PALETTES[(i + 1) % len(BLACK_HOLE_PALETTES)]
        return self.palette

    def next_mode(self) -> str:
        self.mode = MODES[(MODES.index(self.mode) + 1) % len(MODES)]
        return self.mode

    def tick(self, dt: float) -> None:
        if not self.paused:
            self.time += max(0.0, min(dt, 0.25))

    update = tick

    def telemetry(self) -> Dict[str, float]:
        """Ust/alt bar olculeri (Rs birimi Rs=2*mass geometrik; km 10^8 Msun ile)."""
        rs = 2.0 * self.mass
        sin_i = math.sin(math.radians(self.inclination))
        g_min, g_max = doppler_range(sin_i, 1.0)
        return {"rs_km": schwarzschild_radius_km(self.mass), "rs": rs,
                "photon_sphere": photon_sphere_radius(rs), "shadow": CRIT_B * rs, "isco": isco_radius(rs),
                "lorentz_isco": orbital_lorentz_factor(isco_radius(rs), rs),
                "time_dilation_isco": orbital_time_dilation(isco_radius(rs), rs),
                "miller_years_per_hour": miller_years_per_hour(self.mass), "g_min": g_min, "g_max": g_max}

    # --- harita ---
    def _build_map(self, pw: int, ph: int) -> _LensMap:
        key = (pw, ph, round(self.inclination), round(self.mass, 3), round(self.disk_size, 2))
        r_in, r_out = 3.0, self.disk_size
        sin_i = math.sin(math.radians(key[2]))
        v_ext = max(3.8, r_out * math.sqrt(1.0 - sin_i * sin_i))          # diskin dikey yarim boyu (Rs)
        scale = min(0.47 * pw / r_out, 0.47 * ph / v_ext) * self.mass     # piksel / Rs
        cx, cy = pw / 2.0, ph / 2.0
        px = []
        for j in range(ph):
            y = (cy - (j + 0.5)) / scale
            for i in range(pw):
                x = (i + 0.5 - cx) / scale
                b = math.hypot(x, y)
                hit = None
                for k, r, phi in disk_crossings(x, y, key[2]):
                    if r_in <= r <= r_out:
                        hit = (k, r, phi)
                        break
                if hit is not None:
                    k, r, phi = hit
                    rn = r / r_in
                    t = disk_temperature(r, r_in) * (1.0 - smoothstep(0.6 * r_out, r_out, r))
                    px.append((0, t, doppler_factor(r, x, sin_i), disk_omega(r, r_in, 1.0), rn, phi,
                               1.0 if k % 2 == 0 else 0.8))
                elif b < CRIT_B:
                    px.append((2,))
                else:
                    src = math.sqrt(b * b - CRIT_B * CRIT_B) / b     # gokyuzu merceklenmesi (halka sikismasi)
                    d = (b / CRIT_B - 1.0) / 0.09
                    px.append((1, x * src * 7.0, y * src * 7.0, 0.85 * math.exp(-d * d), x / b * sin_i))
        return _LensMap(key, px)

    # --- cizim ---
    def render(self, area: Rect, buf: Buffer) -> None:
        if area.width < 8 or area.height < 3:
            return
        w, h = area.width, area.height
        pw, ph = w, h * 2
        if self._map is None or self._map.key != (pw, ph, round(self.inclination), round(self.mass, 3),
                                                  round(self.disk_size, 2)):
            self._map = self._build_map(pw, ph)
        pal = self.palette
        ramp, stars, bg = palette_ramp(pal), _star_levels(pal), pal.bg
        black = Color(0, 0, 0)
        top = RAMP_STEPS - 1
        dop, t, spin = self.doppler, self.time, self.spin
        az_rad = math.radians(self.azimuth)
        az_shift = int(self.azimuth * 0.35)
        vals: List[float] = []
        cols: List[Color] = []
        for p in self._map.px:
            kind = p[0]
            if kind == 0:
                g = p[2] if dop else 1.0
                tt = p[1] * g
                turb = plasma_turbulence(p[4], p[5] + az_rad - p[3] * spin * t)
                x = EXPOSURE * tt * tt * tt * (0.45 + 0.95 * turb) * p[6]
                v = x / (1.0 + x)
                vals.append(v)
                cols.append(ramp[int(v * top)])
            elif kind == 1:
                gl = p[3] * (1.0 - 0.45 * p[4]) if dop else p[3]
                hsh = ((int(p[1]) + az_shift) * 73856093 ^ int(p[2]) * 19349663) & 0xFFFF
                if gl > 0.04:
                    v = min(1.0, gl)
                    vals.append(v)
                    cols.append(ramp[int(v * top)])
                elif hsh < 560:
                    vals.append(0.12)
                    cols.append(stars[hsh & 7])
                else:
                    vals.append(0.0)
                    cols.append(bg)
            else:
                vals.append(0.0)
                cols.append(black)
        if self.mode == "ascii":
            self._compose_ascii(area, buf, vals, cols, ramp, bg)
        else:
            for row in range(h):
                a, b2 = 2 * row * pw, (2 * row + 1) * pw
                for col in range(w):
                    buf.set_cell(area.x + col, area.y + row, Cell("▀", cols[a + col], cols[b2 + col]))

    @staticmethod
    def _compose_ascii(area: Rect, buf: Buffer, vals: List[float], cols: List[Color],
                       ramp: List[Color], bg: Color) -> None:
        w, n = area.width, len(ASCII_RAMP) - 1
        for row in range(area.height):
            a, b = 2 * row * w, (2 * row + 1) * w
            for col in range(w):
                v = max(vals[a + col], vals[b + col])
                if v < 0.02:
                    buf.set_cell(area.x + col, area.y + row, Cell(" ", None, bg))
                    continue
                fg = ramp[int(max(v, 0.3) * (RAMP_STEPS - 1))] if v > 0.2 else cols[a + col] if vals[a + col] >= vals[b + col] \
                    else cols[b + col]
                ch = "." if v < 0.15 else ASCII_RAMP[min(n, int(v ** 0.8 * (n + 1)))]
                buf.set_cell(area.x + col, area.y + row, Cell(ch, fg, bg))
