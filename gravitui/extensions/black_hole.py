"""BlackHole: Gargantua (Interstellar) karadeligi; merceklenmis disk, Doppler isinimi, Kepler donusu, ince foton halkasi.
Isin izleme yerine onceden hesaplanan geodezik supurme tablosu ve onbellekli piksel->disk haritasi kullanir.
Varsayilan palet "Aurum Amber": TwoHorizonsWallpaper Aurum sahnesinin renk/geometri/Doppler degerleri (ACES tonlama)."""
from __future__ import annotations

import math
from typing import Dict, List, Optional, Union

from ..core.buffer import Buffer, Cell
from ..core.style import Color
from ..layout.rect import Rect
from ..widgets.base import Widget
from .black_hole_math import (CRIT_B, aurum_edge, aurum_temperature, disk_crossings, disk_omega, disk_temperature,
                              doppler_factor, doppler_range, isco_radius, miller_years_per_hour,
                              orbital_lorentz_factor, orbital_time_dilation, photon_ring_weight,
                              photon_sphere_radius, schwarzschild_radius_km, sky_angle, smoothstep)
from .black_hole_palette import (BLACK_HOLE_PALETTES, DEFAULT_PALETTE, HUE_MAX, HUE_STEPS, RAMP_STEPS,  # noqa: F401
                                 BlackHolePalette, get_black_hole_palette, palette_hues, palette_ramp, star_levels,
                                 tone_map)
from .black_hole_plasma import plasma_flow

MODES = ("halfblock", "ascii")
ASCII_RAMP = " .:-=+*#%@"
EXPOSURE = 2.2                      # klasik (tone=None) paletler icin
MASS_RANGE = (0.4, 2.5)
DISK_RANGE = (6.0, 20.0)
SKY_FOV = 0.9                       # yatay gorus acisi (rad); gokyuzu merceklenmesi bu olcekten hesaplanir
STAR_CELL = 0.0087                  # yildiz izgarasi hucre acisi (~0.5 derece)
STAR_DENSITY = 560                  # 65536 uzerinden yildiz esigi
SECONDARY_GAIN = 0.5                # ikincil (merceklenmis, ince) disk goruntusu soluklugu
RING_GAIN = 2.4                     # foton halkasi parlakligi (HDR)
TAU = 2.0 * math.pi


class _LensMap:
    """Bir (boyut, egim, kutle, disk, palet) icin piksel basina (kind, hits, sky, ring_w, ring_g):
    kind 0 disk / 1 gokyuzu / 2 golge; hits = [(T, g, g^3.2, omega, rn, phi, base, edge, face)];
    sky = (aci_hucresi, azimut_turu, azimut_hucre_sayisi) ya da None; ring_w foton halkasi agirligi, ring_g Doppler."""
    def __init__(self, key, px):
        self.key, self.px = key, px


class BlackHole(Widget):
    def __init__(self, palette: Union[str, int, BlackHolePalette] = 0, mode: str = "halfblock",
                 inclination: Optional[float] = None, azimuth: float = 0.0, mass: float = 1.0,
                 disk_size: Optional[float] = None, spin: float = 0.55, doppler: bool = True):
        self.palette = get_black_hole_palette(palette)
        self.mode = mode if mode in MODES else MODES[0]
        inclination = self.palette.inclination if inclination is None else inclination
        disk_size = self.palette.disk_size if disk_size is None else disk_size
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

    def apply_preset(self) -> BlackHolePalette:
        """Paletin onerdigi geometriyi (egim, dis yaricap) uygular; Aurum: ~84.3 derece, rOut=8.4."""
        self.inclination = max(0.0, min(89.0, self.palette.inclination))
        self.disk_size = max(DISK_RANGE[0], min(DISK_RANGE[1], self.palette.disk_size))
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
    def _map_key(self, pw: int, ph: int):
        pal = self.palette
        return (pw, ph, round(self.inclination), round(self.mass, 3), round(self.disk_size, 2),
                pal.tone is not None, pal.rings, round(pal.dopp, 3), round(pal.gain, 3))

    def _build_map(self, pw: int, ph: int) -> _LensMap:
        key = self._map_key(pw, ph)
        pal, inc = self.palette, key[2]
        tone = pal.tone is not None
        r_in, r_out = 3.0, self.disk_size
        sin_i = math.sin(math.radians(inc))
        v_ext = max(3.8, r_out * math.sqrt(1.0 - sin_i * sin_i))          # diskin dikey yarim boyu (Rs)
        scale = min(0.47 * pw / r_out, 0.47 * ph / v_ext) * self.mass     # piksel / Rs
        px_rs = 1.0 / scale
        cx, cy = pw / 2.0, ph / 2.0
        px = []
        for j in range(ph):
            y = (cy - (j + 0.5)) / scale
            for i in range(pw):
                x = (i + 0.5 - cx) / scale
                b = math.hypot(x, y)
                ring_w = photon_ring_weight(b, px_rs)
                ring_g = 1.0 / (1.0 + 0.5 * pal.dopp * sin_i * x / b) if b > 1e-9 else 1.0
                hits = []
                for k, r, phi in disk_crossings(x, y, inc, 3):
                    if 0.88 * r_in <= r <= r_out:
                        g = doppler_factor(r, x, sin_i, 1.0, pal.dopp)
                        if tone:
                            edge, t = aurum_edge(r, r_in, r_out), aurum_temperature(r, r_in)
                            base = t ** 2.2 * edge * pal.gain * (1.0 if k % 2 == 0 else SECONDARY_GAIN)
                        else:
                            edge, base = 1.0, 0.0
                            t = disk_temperature(r, r_in) * (1.0 - smoothstep(0.6 * r_out, r_out, r))
                        hits.append((t, g, g ** 3.2, disk_omega(r, r_in, 1.0), r / r_in, phi, base, edge,
                                     1.0 if k % 2 == 0 else 0.8))
                        if len(hits) >= pal.rings:
                            break
                sky = None
                if b > CRIT_B:
                    a = sky_angle(b, b * scale * SKY_FOV / pw)
                    cell = int(abs(a) / STAR_CELL)
                    n_phi = max(1, int(TAU * math.sin((cell + 0.5) * STAR_CELL) / STAR_CELL))
                    sky = (cell, (math.atan2(y, x) + (math.pi if a < 0.0 else 0.0)) / TAU, n_phi)
                kind = 0 if hits else 1 if b > CRIT_B else 2
                px.append((kind, hits, sky, ring_w, ring_g))
        return _LensMap(key, px)

    # --- cizim ---
    def render(self, area: Rect, buf: Buffer) -> None:
        if area.width < 8 or area.height < 3:
            return
        w, h = area.width, area.height
        pw, ph = w, h * 2
        if self._map is None or self._map.key != self._map_key(pw, ph):
            self._map = self._build_map(pw, ph)
        vals: List[float] = []
        cols: List[Color] = []
        pal = self.palette
        stars, bg, ramp = star_levels(pal), pal.bg, palette_ramp(pal)
        if pal.tone is not None:
            self._shade_tone(self._map.px, vals, cols, stars)
        else:
            self._shade_ramp(self._map.px, vals, cols, stars, bg, ramp)
        if self.mode == "ascii":
            self._compose_ascii(area, buf, vals, cols, ramp, bg)
        else:
            for row in range(h):
                a, b2 = 2 * row * pw, (2 * row + 1) * pw
                for col in range(w):
                    buf.set_cell(area.x + col, area.y + row, Cell("▀", cols[a + col], cols[b2 + col]))

    @staticmethod
    def _star(sky, az_frac: float, stars: List[Color]) -> Optional[Color]:
        cell, f, n_phi = sky
        h = (cell * 374761393 + int(((f + az_frac) % 1.0) * n_phi) * 668265263) & 0xFFFFFFFF
        h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
        hsh = (h ^ (h >> 16)) & 0xFFFF
        return stars[hsh & 7] if hsh < STAR_DENSITY else None

    def _shade_tone(self, px, vals: List[float], cols: List[Color], stars: List[Color]) -> None:
        """Aurum yolu: `diskSample` formulu (T^2.2 g^3.2 turb), on-arka alfa birlesimi, foton halkasi, ACES tonlama."""
        pal = self.palette
        hues, hmax = palette_hues(pal), HUE_STEPS - 1
        hscale = hmax / HUE_MAX
        hot = hues[-1]
        dop, t, spin, exp = self.doppler, self.time, self.spin, pal.exposure
        az = math.radians(self.azimuth)
        az_frac = az / TAU
        shim = 1.0 + 0.08 * math.sin(t * 0.7)
        black, exp_ = Color(0, 0, 0), math.exp
        for kind, hits, sky, ring_w, ring_g in px:
            if kind == 2 and ring_w <= 0.0:
                vals.append(0.0)
                cols.append(black)
                continue
            ar = ag = ab = 0.0
            trans = 1.0
            for tt0, g, g32, om, rn, phi, base, edge, face in hits:
                if not dop:
                    g = g32 = 1.0
                turb = 0.15 + 1.7 * plasma_flow(rn, phi + az, om, spin, t)
                dph = abs(((phi + az) / TAU - t * 0.02 + 0.5) % 1.0 - 0.5) / 0.06
                inten = base * turb * g32 * (1.0 + 0.9 * exp_(-dph * dph)) * shim
                hue = hues[min(hmax, int(tt0 * g * hscale))]
                ar += trans * hue[0] * inten
                ag += trans * hue[1] * inten
                ab += trans * hue[2] * inten
                a = edge * (0.30 + 0.55 * turb)
                trans *= 1.0 - (a if a < 0.92 else 0.92)
            if ring_w > 0.0:
                k = trans * ring_w * RING_GAIN * (ring_g ** 3.2 if dop else 1.0)
                ar, ag, ab = ar + hot[0] * k, ag + hot[1] * k, ab + hot[2] * k
            c = tone_map(ar, ag, ab, exp)
            if trans > 0.02 and sky is not None:
                s = self._star(sky, az_frac, stars)
                if s is not None:
                    c = Color(c.r + s.r * trans, c.g + s.g * trans, c.b + s.b * trans)
            cols.append(c)
            vals.append(max(c.r, c.g, c.b) / 255.0)

    def _shade_ramp(self, px, vals: List[float], cols: List[Color], stars: List[Color], bg: Color,
                    ramp: List[Color]) -> None:
        """Klasik rampa paletleri: tek skaler parlaklik -> palet rampasi (en parlak disk goruntusu kazanir)."""
        top = RAMP_STEPS - 1
        dop, t, spin = self.doppler, self.time, self.spin
        az = math.radians(self.azimuth)
        az_frac = az / TAU
        black = Color(0, 0, 0)
        for kind, hits, sky, ring_w, ring_g in px:
            v = 0.0
            for tt0, g, g32, om, rn, phi, base, edge, face in hits:
                tt = tt0 * (g if dop else 1.0)
                turb = plasma_flow(rn, phi + az, om, spin, t)
                x = EXPOSURE * tt * tt * tt * (0.45 + 0.95 * turb) * face
                v = max(v, x / (1.0 + x))
            if ring_w > 0.0:
                v = max(v, min(1.0, 0.95 * ring_w * (ring_g if dop else 1.0)))
            if v > 0.0:
                vals.append(v)
                cols.append(ramp[int(v * top)])
            elif kind == 2:
                vals.append(0.0)
                cols.append(black)
            else:
                s = self._star(sky, az_frac, stars) if sky else None
                vals.append(0.12 if s is not None else 0.0)
                cols.append(s if s is not None else bg)

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
