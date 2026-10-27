"""Gargantua matematigi: Schwarzschild analitigi, geodezik supurme tablosu (merceklenme), Doppler isinimi,
Kepler diski ve zaman genlesmesi. Birimler: G=c=1, uzunluklar Rs (Schwarzschild yaricapi) cinsinden."""
from __future__ import annotations

import math
from bisect import bisect_right
from typing import List, Optional, Tuple

CRIT_B = 1.5 * math.sqrt(3.0)          # golge (kritik carpma parametresi) yaricapi / Rs = 3*sqrt(3)/2
HOURS_PER_YEAR = 8766.0
SOLAR_RS_KM = 2.9532                   # 1 gunes kutlesinin Schwarzschild yaricapi (km)
MILLER_YEARS_PER_HOUR = 7.0            # Interstellar: Miller gezegeninde 1 saat = 7 yil (mass=1 icin)
MILLER_DELTA = 3.0 / (MILLER_YEARS_PER_HOUR * HOURS_PER_YEAR) ** 2  # fotonkureden mutlak uzaklik (mass=1)
TABLE_B_MAX = CRIT_B * 16.0


def clamp01(v: float) -> float:
    return 0.0 if v < 0 else 1.0 if v > 1 else v


def smoothstep(a: float, b: float, v: float) -> float:
    t = clamp01((v - a) / (b - a)) if b != a else 1.0
    return t * t * (3 - 2 * t)


# --- Schwarzschild analitigi ---------------------------------------------------------------------
def schwarzschild_radius(mass: float = 1.0) -> float:
    """Rs = 2GM/c^2 (G=c=1 geometrik birimde 2*M)."""
    return 2.0 * mass


def schwarzschild_radius_km(mass_1e8_suns: float = 1.0) -> float:
    """Kutle 10^8 gunes kutlesi biriminde (Gargantua ~ 1) -> Rs kilometre."""
    return SOLAR_RS_KM * 1e8 * mass_1e8_suns


def photon_sphere_radius(rs: float = 2.0) -> float:
    return 1.5 * rs


def isco_radius(rs: float = 2.0) -> float:
    """En icteki kararli dairesel yorunge (3 Rs)."""
    return 3.0 * rs


def shadow_radius(rs: float = 2.0) -> float:
    """Gozlemcinin gordugu golgenin yaricapi: b_c = 3*sqrt(3)/2 * Rs (~2.6 Rs)."""
    return CRIT_B * rs


# --- Zaman genlesmesi / Lorentz --------------------------------------------------------------------
def time_dilation(r: float, rs: float = 2.0) -> float:
    """Duragan gozlemci icin dtau/dt = sqrt(1 - Rs/r); r <= Rs icin 0."""
    return math.sqrt(1.0 - rs / r) if r > rs else 0.0


def orbital_velocity(r: float, rs: float = 2.0) -> float:
    """Dairesel yorungenin yerel (duragan gozlemciye gore) hizi v/c = sqrt(Rs / (2 (r - Rs)))."""
    return math.sqrt(rs / (2.0 * (r - rs))) if r > 1.5 * rs else 1.0


def lorentz_factor(v: float) -> float:
    return 1.0 / math.sqrt(1.0 - v * v) if v < 1.0 else math.inf


def orbital_lorentz_factor(r: float, rs: float = 2.0) -> float:
    """Dairesel yorunge yerel Lorentz faktoru: sqrt((r - Rs) / (r - 1.5 Rs)); fotonkurede sonsuz."""
    return math.sqrt((r - rs) / (r - 1.5 * rs)) if r > 1.5 * rs else math.inf


def orbital_time_dilation(r: float, rs: float = 2.0) -> float:
    """Yorungedeki saatin toplam (hiz + yercekimi) genlesmesi: dtau/dt = sqrt(1 - 1.5 Rs / r)."""
    return math.sqrt((r - 1.5 * rs) / r) if r > 1.5 * rs else 0.0


def miller_orbit_radius(mass: float = 1.0) -> float:
    """Miller gezegeni fotonkureden SABIT mutlak uzaklikta (MILLER_DELTA) yorungede varsayilir."""
    return photon_sphere_radius(schwarzschild_radius(mass)) + MILLER_DELTA


def miller_years_per_hour(mass: float = 1.0) -> float:
    """Miller gezegeninde 1 saat = X dis evren yili (mass=1 -> 7 yil)."""
    d = orbital_time_dilation(miller_orbit_radius(mass), schwarzschild_radius(mass))
    return 1.0 / d / HOURS_PER_YEAR if d > 0 else math.inf


# --- Doppler / Kepler diski ----------------------------------------------------------------------
def keplerian_omega(r: float, rs: float = 1.0) -> float:
    """Omega = sqrt(M / r^3), M = Rs/2 -> r^(-1.5) olcekli."""
    return math.sqrt(0.5 * rs / (r * r * r))


def disk_omega(r: float, r_in: float, speed: float = 1.0) -> float:
    """Gorsel donus hizi (rad/s): speed * (r_in / r)^1.5 (Kepler)."""
    return speed * (r_in / r) ** 1.5


def doppler_factor(r: float, x: float, sin_i: float, rs: float = 1.0) -> float:
    """g = nu_gozlenen / nu_yayilan = sqrt(1 - 1.5Rs/r) / (1 + Omega * x * sin i).
    x < 0 (sol, gozlemciye yaklasan taraf) icin g > 1 (maviye kayma), x > 0 icin g < 1 (kizila kayma)."""
    den = max(1.0 + keplerian_omega(r, rs) * x * sin_i, 0.05)
    return orbital_time_dilation(r, rs) / den


def doppler_range(sin_i: float, rs: float = 1.0) -> Tuple[float, float]:
    """ISCO'daki (en parlak) halka icin (g_min, g_max) Doppler araligi."""
    r = isco_radius(rs)
    b = r / math.sqrt(1.0 - rs / r)   # goruntunun yaklasik carpma parametresi
    return doppler_factor(r, b, sin_i, rs), doppler_factor(r, -b, sin_i, rs)


def relativistic_beaming(g: float, exponent: float = 3.0) -> float:
    """Isik siddeti carpani I_gozlenen / I_yayilan = g^3 (monokromatik) ... g^4 (bolometrik)."""
    return g ** exponent


_T_STEPS = [1.0 + 0.02 * k for k in range(1, 400)]


def _t_raw(rn: float) -> float:
    return rn ** -0.75 * (1.0 - 0.7 * rn ** -0.5) ** 0.25


_T_PEAK = max(_t_raw(v) for v in _T_STEPS)


def disk_temperature(r: float, r_in: float) -> float:
    """Novikov-Thorne benzeri normalize sicaklik (tepe=1): T ~ r^-0.75 (1 - 0.7 sqrt(r_in/r))^0.25."""
    return _t_raw(max(r / r_in, 1.0)) / _T_PEAK


def plasma_turbulence(rn: float, phi: float) -> float:
    """Plazma turbulansi 0..1; rn = r / r_in, phi = dokuyla birlikte donen azimut."""
    n = 0.55 + 0.22 * math.sin(9.0 * rn + 3.0 * phi) + 0.18 * math.sin(23.0 * rn - 5.0 * phi + 1.7) \
        + 0.10 * math.sin(7.0 * phi + 41.0 * rn)
    return 0.0 if n < 0 else 1.0 if n > 1 else n


# --- Geodezik supurme tablosu (merceklenme) --------------------------------------------------------
def _f(u: float, b: float) -> float:
    return 1.0 / (b * b) - u * u + u * u * u


def _periapsis_u(b: float) -> float:
    lo, hi = 0.0, 2.0 / 3.0
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        if _f(mid, b) > 0:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def _row(b: float, m: int = 192) -> Tuple[List[float], List[float], float, bool]:
    """b icin (u dizisi, birikimli supurme dizisi, periapsis supurmesi, periapsis var mi)."""
    if b > CRIT_B:
        up = _periapsis_u(b)
        fp = abs(-2.0 * up + 3.0 * up * up)
        hs = [2.0 * up * s / math.sqrt(_f(up * (1 - s * s), b)) if s > 1e-9
              else 2.0 * math.sqrt(up / fp) for s in (k / m for k in range(m + 1))]
        us, psi, acc = [0.0], [0.0], 0.0
        for k in range(m - 1, -1, -1):       # s = k/m, s=1 -> u=0, s=0 -> u=up
            acc += 0.5 * (hs[k] + hs[k + 1]) / m
            s = k / m
            us.append(up * (1 - s * s))
            psi.append(acc)
        return us, psi, acc, True
    us = [k / m for k in range(m + 1)]
    gs = [1.0 / math.sqrt(_f(u, b)) for u in us]
    psi, acc = [0.0], 0.0
    for k in range(m):
        acc += 0.5 * (gs[k] + gs[k + 1]) / m
        psi.append(acc)
    return us, psi, psi[-1], False


NS = 288
SWEEP_MAX = 3.2 * math.pi
_D_SWEEP = SWEEP_MAX / (NS - 1)
_B_LIST: List[float] = []
_U_TABLE: List[List[float]] = []


def _u_at(us: List[float], psi: List[float], target: float) -> float:
    """Birikimli supurmeden u'yu interpolasyonla bulur (psi artan)."""
    k = bisect_right(psi, target)
    if k <= 0:
        return us[0]
    if k >= len(psi):
        return us[-1]
    a, c = psi[k - 1], psi[k]
    return us[k - 1] + (us[k] - us[k - 1]) * ((target - a) / (c - a) if c > a else 0.0)


def _build_table() -> None:
    gs = []
    g = 0.0015
    while g < 0.96:
        gs.append(g)
        g *= 1.15
    outer = []
    g = 0.0015
    while CRIT_B * (1 + g) < TABLE_B_MAX:
        outer.append(g)
        g *= 1.15
    bs = [CRIT_B * (1 - g) for g in reversed(gs)] + [CRIT_B * (1 + g) for g in outer]
    for b in bs:
        us, psi, php, peri = _row(b)
        row = []
        for k in range(NS):
            sw = k * _D_SWEEP
            if sw <= php:
                row.append(_u_at(us, psi, sw))
            elif peri and sw <= 2 * php:
                row.append(_u_at(us, psi, 2 * php - sw))
            else:
                row.append(-1.0)             # yakalandi (ufuk) ya da supurme asilamiyor
        _U_TABLE.append(row)
        _B_LIST.append(b)


def lensed_radius(b: float, sweep: float, rs: float = 1.0) -> Optional[float]:
    """Carpma parametresi b (Rs biriminde `rs` ile olceklenmis) olan isik, gozlemciden `sweep` radyan
    supurdugunde bulundugu yaricap; yakalanmissa/ulasilamiyorsa None."""
    b /= rs
    if sweep <= 0.0 or sweep > SWEEP_MAX:
        return None
    if b >= TABLE_B_MAX:                     # zayif alan: duz cizgi r = b / sin(sweep)
        s = math.sin(sweep)
        return b / s * rs if sweep < math.pi and s > 1e-6 else None
    if not _B_LIST:
        _build_table()
    j = max(0, min(len(_B_LIST) - 2, bisect_right(_B_LIST, b) - 1))
    t = clamp01((b - _B_LIST[j]) / (_B_LIST[j + 1] - _B_LIST[j]))
    x = sweep / _D_SWEEP
    k = min(int(x), NS - 2)
    fx = x - k
    r0, r1 = _U_TABLE[j], _U_TABLE[j + 1]
    c = (r0[k], r0[k + 1], r1[k], r1[k + 1])
    if min(c) < 0.0:                         # kenar: en yakin gecerli koseyi al
        near = c[(2 if t > 0.5 else 0) + (1 if fx > 0.5 else 0)]
        u = near
    else:
        u = (c[0] * (1 - fx) + c[1] * fx) * (1 - t) + (c[2] * (1 - fx) + c[3] * fx) * t
    return rs / u if u > 1e-6 else None


def disk_crossings(sx: float, sy: float, inclination_deg: float, crossings: int = 3,
                   rs: float = 1.0) -> List[Tuple[int, float, float]]:
    """Ekran noktasindan (sx sag, sy yukari; Rs biriminde) cikan isinin disk duzlemini kestigi noktalar:
    [(k, r, phi)]. k=0 ilk (birincil) kesisim, k=1 ikincil (merceklenmis), k=2 ucuncul; r Rs biriminde,
    phi diskte gozlemci yonune gore azimut. Yuz: k cift -> ust yuz, tek -> alt yuz."""
    b = math.hypot(sx, sy)
    if b < 1e-9:
        return []
    inc = math.radians(max(0.0, min(89.5, inclination_deg)))
    c, s = math.cos(inc), math.sin(inc)
    cx, cy = sx / b, sy / b
    dz = s * cy
    psi1 = math.atan2(c, -dz)                # birincil kesisim supurmesi (0..pi)
    out = []
    for k in range(crossings):
        sw = psi1 + k * math.pi
        r = lensed_radius(b, sw, rs)
        if r is None:
            break
        x_d = math.cos(sw) * s - math.sin(sw) * c * cy
        y_d = math.sin(sw) * cx
        out.append((k, r, math.atan2(y_d, x_d)))
    return out


def arc_height(r: float, inclination_deg: float, upper: bool = True, rs: float = 1.0) -> Optional[float]:
    """x=0 dikeyinde r yaricapli halkanin merceklenmis gorunumunun (golge merkezinden) ekran yuksekligi
    (Rs biriminde): upper=True -> golgenin ustunde bukulen yay, False -> altinda bukulen yay."""
    inc = math.radians(max(0.0, min(89.5, inclination_deg)))
    sweep = math.pi / 2 + inc if upper else 1.5 * math.pi - inc
    lo, hi = CRIT_B * 1.0005 * rs, TABLE_B_MAX * 0.99 * rs
    best, best_err = None, 1e9
    for k in range(400):                     # b uzerinde tarama + ince secim (r(b) tekdüze degil olabilir)
        b = lo * (hi / lo) ** (k / 399)
        rr = lensed_radius(b, sweep, rs)
        if rr is not None and abs(rr - r) < best_err:
            best, best_err = b, abs(rr - r)
    return best
