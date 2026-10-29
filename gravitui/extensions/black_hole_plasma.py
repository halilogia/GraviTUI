"""Gargantua plazma dokusu: azimutta periyodik, onceden uretilen fbm (buyuk olcek + ince seritler) ve akis-haritasi
karisimli Keplerian diferansiyel donus. Bagimsiz modul: yalnizca stdlib, karadelik matematigine bagimli degil."""
from __future__ import annotations

import math
from typing import List

TEX_W, TEX_H = 192, 160
RN_MAX = 7.7                         # doku r/r_in = 1..RN_MAX araligini kapsar (r_in=3 icin r ~ 3..23 Rs)
_ROWS_PER_RN = (TEX_H - 1) / (RN_MAX - 1.0)
FLOW_PERIOD = 12.0                   # diferansiyel kayma bu sureden sonra ters bir katmanla yumusakca sifirlanir (sn)
FLOW_REF_RN = 1.7                    # donen referans cercevesi (katmanin sert govdesi bu yaricapla doner)
_TEX: List[float] = []


def _hash(ix: int, iy: int, seed: int) -> float:
    h = (ix * 374761393 + iy * 668265263 + seed * 1442695041) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((h ^ (h >> 16)) & 0xFFFF) / 65535.0


class _Lattice:
    """Azimutta periyodik, yaricapta duz kenarli deger gurultusu izgarasi."""
    def __init__(self, nx: int, ny: int, seed: int):
        self.nx, self.ny = nx, ny
        self.v = [[_hash(i, j, seed) for i in range(nx)] for j in range(ny + 2)]

    def at(self, u: float, y: float) -> float:
        """u: 0..1 azimut (periyodik), y: 0..ny hucre biriminde yaricap."""
        x = (u % 1.0) * self.nx
        i = int(x)
        fx = x - i
        fx = fx * fx * (3.0 - 2.0 * fx)
        j = min(int(y), self.ny)
        fy = y - j
        fy = fy * fy * (3.0 - 2.0 * fy)
        i1 = (i + 1) % self.nx
        a, b = self.v[j], self.v[j + 1]
        top = a[i] + (a[i1] - a[i]) * fx
        bot = b[i] + (b[i1] - b[i]) * fx
        return top + (bot - top) * fy


def _build_texture() -> None:
    """warp -> coarse/fine/strand katmanlari; Aurum kabugundaki `diskSample` gurultusunun TUI olcekli karsiligi."""
    warp = _Lattice(5, 28, 11)
    coarse = _Lattice(6, 36, 23)
    fine = _Lattice(20, 84, 37)
    strand = _Lattice(24, 126, 53)
    for j in range(TEX_H):
        y = j / (TEX_H - 1)
        for i in range(TEX_W):
            u = i / TEX_W
            w = warp.at(u, y * 28)
            c = coarse.at(u + w * 0.15, y * 36)
            f = fine.at(u, y * 84)
            s = strand.at(u + w * 0.04, y * 126)
            _TEX.append(c * 0.42 + f * 0.28 + s * 0.38)


def _smoothstep(a: float, b: float, v: float) -> float:
    t = (v - a) / (b - a)
    t = 0.0 if t < 0.0 else 1.0 if t > 1.0 else t
    return t * t * (3.0 - 2.0 * t)


def sample_plasma(rn: float, phi: float) -> float:
    """Ham plazma dokusu (yaklasik 0.2..0.8); rn = r / r_in, phi radyan (2*pi periyodik)."""
    if not _TEX:
        _build_texture()
    y = (rn - 1.0) * _ROWS_PER_RN
    y = 0.0 if y < 0.0 else TEX_H - 1.001 if y > TEX_H - 1.001 else y
    j = int(y)
    fy = y - j
    x = ((phi / 6.283185307179586) % 1.0) * TEX_W
    i = int(x)
    fx = x - i
    i1 = i + 1 if i + 1 < TEX_W else 0
    a, b = j * TEX_W, (j + 1) * TEX_W
    t = _TEX
    top = t[a + i] + (t[a + i1] - t[a + i]) * fx
    bot = t[b + i] + (t[b + i1] - t[b + i]) * fx
    return top + (bot - top) * fy


def plasma_turbulence(rn: float, phi: float) -> float:
    """Plazma turbulansi 0..1; rn = r / r_in, phi = dokuyla birlikte donen azimut."""
    return _smoothstep(0.22, 0.82, sample_plasma(rn, phi))


def plasma_flow(rn: float, phi: float, omega: float, spin: float, t: float) -> float:
    """Akis-haritasi karisimi: sert govde `FLOW_REF_RN` hizinda doner, gerisi diferansiyel (Kepler) kayar.
    Iki katman yarim periyot farkla yaslanir ve ucgen agirlikla birlesir; kayma sonsuza sarilip titremez.
    omega = diskin (r_in/r)^1.5 hizi, spin = donus carpani, t = saniye. Donus 0..1 turbulans."""
    ref = FLOW_REF_RN ** -1.5
    rigid = phi - ref * spin * t
    shear = (omega - ref) * spin
    f = (t / FLOW_PERIOD) % 1.0
    g = (f + 0.5) % 1.0
    wa = 1.0 - abs(2.0 * f - 1.0)
    wb = 1.0 - wa
    na = sample_plasma(rn, rigid - shear * f * FLOW_PERIOD) - 0.5
    nb = sample_plasma(rn, rigid - shear * g * FLOW_PERIOD + 3.14159265) - 0.5
    norm = math.sqrt(wa * wa + wb * wb)          # varyans korunumu: karisim ortasinda kontrast dusmez
    return _smoothstep(0.22, 0.82, 0.5 + (wa * na + wb * nb) / norm)
