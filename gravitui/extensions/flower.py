"""ProceduralFlower: prosedurel zambak buyume/acilis animasyonu + kutsal geometri yorungeleri."""
from __future__ import annotations

import math
import random
from typing import List, Optional, Sequence, Union

from ..core.buffer import Buffer, Cell
from ..core.style import Color, WHITE
from ..layout.rect import Rect
from ..widgets.base import Widget
from .flower_math import (DURATIONS, FLOWER_PALETTES, BrailleLayer, FlowerPalette, FlowerPhase,
                          PixelCanvas, clamp01, cubic_bezier, ease_in_out_cubic, ease_out_back,
                          ease_out_cubic, get_palette, lifecycle, petal_curve, smoothstep)

# (dikeyden derece, boy, genislik, gecikme): arka katman -> sarkan -> on katman
PETALS = ((-80, 1.0, 1.0, 0.0), (80, 1.0, 1.0, 0.0), (0, 1.1, 1.05, 0.0),
          (-118, 0.82, 0.9, 0.35), (118, 0.82, 0.9, 0.35), (-42, 0.95, 0.9, 0.18), (42, 0.95, 0.9, 0.18))
LEAVES = ((0.28, -1, 1.0), (0.42, 1, 1.0), (0.58, -1, 0.8), (0.70, 1, 0.7))
RINGS = (1.35, 2.0, 2.7)
MAX_POLLEN = 160


class ProceduralFlower(Widget):
    def __init__(self, palette: Union[str, FlowerPalette] = "Zambak", speed: float = 1.0,
                 show_geometry: bool = True, show_pollen: bool = True, seed: Optional[int] = None,
                 durations: Sequence[float] = DURATIONS):
        self.palette = get_palette(palette)
        self.speed = speed
        self.show_geometry = show_geometry
        self.show_pollen = show_pollen
        self.durations = tuple(durations)
        self.rng = random.Random(seed)
        self.paused = False
        self.age = 0.0      # yasam dongusu saati
        self.clock = 0.0    # ortam animasyon saati (sway, yorungeler)
        self.pollen: List[list] = []  # [x, y, vx, vy, omur, max_omur]  (x,y: bas merkezine gore, L biriminde)
        self._emit = 0.0

    # --- kontrol ---
    def restart(self) -> None:
        self.age = self.clock = self._emit = 0.0
        self.pollen.clear()

    def toggle_pause(self) -> None:
        self.paused = not self.paused

    def next_palette(self) -> FlowerPalette:
        i = FLOWER_PALETTES.index(self.palette) if self.palette in FLOWER_PALETTES else -1
        self.palette = FLOWER_PALETTES[(i + 1) % len(FLOWER_PALETTES)]
        return self.palette

    def adjust_speed(self, factor: float) -> float:
        self.speed = max(0.1, min(8.0, self.speed * factor))
        return self.speed

    @property
    def phase_info(self):
        return lifecycle(self.age, self.durations)

    def status(self) -> str:
        phase, p = self.phase_info
        return f"{phase.value} %{int(p * 100)}" if phase != FlowerPhase.FULL else phase.value

    # --- zaman ilerletme ---
    def update(self, dt: float) -> None:
        if self.paused or dt <= 0:
            return
        dt *= self.speed
        self.age += dt
        self.clock += dt
        phase, p = self.phase_info
        amount = 1.0 if phase == FlowerPhase.FULL else p if phase == FlowerPhase.BLOOM else 0.0
        if self.show_pollen and amount > 0.6 and len(self.pollen) < MAX_POLLEN:
            self._emit += dt * 16 * amount
            while self._emit >= 1 and len(self.pollen) < MAX_POLLEN:
                self._emit -= 1
                life = self.rng.uniform(2.5, 5.0)
                self.pollen.append([self.rng.gauss(0, 0.12), -0.05, self.rng.uniform(-0.08, 0.08),
                                    -self.rng.uniform(0.12, 0.4), life, life])
        for q in self.pollen:
            q[0] += q[2] * dt + 0.12 * math.sin(self.clock * 1.7 + q[1] * 6) * dt
            q[1] += q[3] * dt
            q[4] -= dt
        self.pollen = [q for q in self.pollen if q[4] > 0]

    # --- cizim ---
    def render(self, area: Rect, buf: Buffer) -> None:
        if area.width <= 0 or area.height <= 0:
            return
        pal, pw, ph = self.palette, area.width, area.height * 2
        cv = PixelCanvas(pw, ph, pal.bg)
        phase, p = self.phase_info
        clock = self.clock
        L = max(1.0, min(ph * 0.26, pw * 0.2))
        ground = ph - 3
        sw = math.sin(clock * 0.9) + 0.5 * math.sin(clock * 1.9 + 1.3)
        h = ground - max(ph * 0.42, L * 1.4)
        cx = pw / 2
        pts = ((cx, ground), (cx + 0.05 * h * sw - 0.08 * h, ground - 0.4 * h),
               (cx + 0.08 * h * sw + 0.10 * h, ground - 0.75 * h), (cx + 0.05 * h * sw, ground - h))
        if phase == FlowerPhase.SPROUT:
            g = 0.28 * ease_out_cubic(p)
        elif phase == FlowerPhase.STEM:
            g = 0.28 + 0.72 * ease_in_out_cubic(p)
        else:
            g = 1.0
        self._stem(cv, pts, g, h)
        self._leaves(cv, pts, g, h, sw)
        if phase in (FlowerPhase.SPROUT, FlowerPhase.STEM):
            cot = ease_out_cubic(p) if phase == FlowerPhase.SPROUT else max(0.0, 1 - 3 * p)
            tip = cubic_bezier(*pts, max(g, 1e-3))
            for side in (-1, 1):
                self._leaf(cv, tip, side, 0.07 * h * cot, 0.022 * h * cot, 0.0)
        hx, hy = pts[3]
        amount = 0.0
        if phase in (FlowerPhase.BUD, FlowerPhase.BLOOM, FlowerPhase.FULL):
            amount = self._head(cv, hx, hy, L, pts, phase, p)
        self._soil(cv, cx, ground, pw, ph)
        glints = self._pollen(cv, hx, hy, L)
        bl = None
        if self.show_geometry:
            t0 = self.durations[0] + self.durations[1]
            geo = smoothstep((self.age - t0) / 5.0)
            if geo > 0:
                bl = BrailleLayer(pw, area.height)
                self._geometry(bl, hx, hy, L, geo)
        self._compose(cv, bl, area, buf, glints)

    def _stem(self, cv, pts, g, h) -> None:
        pal = self.palette
        n = max(6, int(h * g / 2))
        axis = [cubic_bezier(*pts, g * i / n) for i in range(n + 1)]
        half = [max(0.8, 1.15 - 0.3 * i / n) for i in range(n + 1)]
        cv.fill_strip(axis, half, lambda u, v: pal.stem.scale(0.65 + 0.35 * u).lerp(WHITE, 0.18 * (1 - abs(v)) ** 2))

    def _leaves(self, cv, pts, g, h, sw) -> None:
        for s, side, k in LEAVES:
            grow = ease_out_cubic((g - s) / 0.22)
            if grow > 0:
                sway = 0.08 * math.sin(self.clock * 1.3 + s * 5) + 0.04 * sw
                self._leaf(cv, cubic_bezier(*pts, s), side, 0.26 * h * k * grow, 0.075 * h * k * grow, sway)

    def _leaf(self, cv, pos, side, length, width, sway) -> None:
        pal = self.palette
        n = 10
        axis, half = [pos], [0.0]
        x, y = pos
        for i in range(1, n + 1):
            u = i / n
            a = side * (math.radians(38) + math.radians(75) * u * u) + sway
            x, y = x + math.sin(a) * length / n, y - math.cos(a) * length / n
            axis.append((x, y))
            half.append(width * math.sin(math.pi * u ** 0.7))
        if length < 1:
            return
        cv.fill_strip(axis, half, lambda u, v: pal.leaf.scale(0.55 + 0.45 * u).lerp(
            WHITE, 0.25 if abs(v) < 0.15 else 0.0))

    def _soil(self, cv, cx, ground, pw, ph) -> None:
        soil = self.palette.soil
        for x in range(pw):
            top = ground - (2.2 * math.exp(-((x - cx) / (pw * 0.18 + 1)) ** 2) + 1.2)
            for y in range(max(0, int(top)), ph):
                cv.set(x, y, soil.scale(0.7 + 0.5 * ((x * 7919 + y * 104729) % 11) / 11))

    def _head(self, cv, hx, hy, L, pts, phase, p) -> float:
        pal, clock = self.palette, self.clock
        if phase == FlowerPhase.BUD:
            scale, ripe = 0.12 + 0.43 * ease_out_cubic(p), 0.7 * smoothstep(p)
        elif phase == FlowerPhase.BLOOM:
            scale, ripe = 0.55 + 0.45 * ease_in_out_cubic(p), 0.7 + 0.3 * clamp01(p * 1.5)
        else:
            scale, ripe = 1.0, 1.0
        bre = 1 + 0.04 * math.sin(clock * 2.1) if phase == FlowerPhase.FULL else 1.0
        tilt = 0.8 * math.atan2(pts[3][0] - pts[2][0], pts[2][1] - pts[3][1])
        opens, tint = [], 1 - ripe
        n = len(PETALS)
        for i, (deg, ls, ws, delay) in enumerate(PETALS):
            o = 1.0 if phase == FlowerPhase.FULL else ease_out_back((p - delay * 0.9) / 0.6) \
                if phase == FlowerPhase.BLOOM else 0.0
            o = max(0.0, o)
            opens.append(o)
            ang = math.radians(deg) * (0.10 + 0.90 * o * bre) + tilt
            curl = (1 if deg >= 0 else -1) * math.radians(55) * o
            lp = L * ls * scale * bre
            axis, half = petal_curve(lp, 0.40 * lp * ws * (1 + 0.3 * (1 - o)), ang, curl, 12, hx, hy)
            shade = 0.78 + 0.22 * i / n

            def col(u, v, shade=shade):
                c = pal.petal[0].lerp(pal.petal[1], clamp01(u * 2)) if u < 0.5 else pal.petal[1].lerp(pal.petal[2], (u - 0.5) * 2)
                c = c.lerp(WHITE, 0.22 * (1 - abs(v)) ** 2).scale(shade * (1 - 0.15 * abs(v) ** 3))
                return c.lerp(pal.bud, tint * 0.9)
            cv.fill_strip(axis, half, col)
        omean = sum(opens) / n
        if omean > 0.05:
            self._core(cv, hx, hy, L * scale * bre, tilt, clamp01(omean), phase, p)
        return omean

    def _core(self, cv, hx, hy, L, tilt, o, phase, p) -> None:
        pal, clock = self.palette, self.clock
        R = 0.32 * L * (1 + 0.08 * math.sin(clock * 3.0))
        r = int(R) + 1
        for dy in range(-r, r + 1):
            for dx in range(-r, r + 1):
                d = math.hypot(dx, dy) / R
                if d < 1:
                    cv.blend(int(hx) + dx, int(hy) + dy, pal.core, (1 - d) ** 1.5 * 0.9 * clamp01(o * 1.2))
        grow = 1.0 if phase == FlowerPhase.FULL else ease_out_cubic((p - 0.45) / 0.5) if phase == FlowerPhase.BLOOM else 0.0
        if grow <= 0:
            return
        for k, deg in enumerate((-52, -30, -10, 10, 30, 52, 0)):
            ln = L * (0.8 if deg == 0 else 0.62) * grow
            axis, half = petal_curve(ln, 0.0, math.radians(deg) + tilt, math.radians(20 if deg >= 0 else -20), 6, hx, hy)
            cv.fill_strip(axis, [0.75 if deg == 0 else 0.6] * len(axis), lambda u, v: pal.stamen.lerp(WHITE, 0.3 * u))
            ax, ay = int(axis[-1][0]), int(axis[-1][1])
            glow = pal.stamen.lerp(WHITE, 0.35 + 0.35 * math.sin(clock * 3 + k))
            for dx in (0, 1):
                for dy in (0, 1):
                    cv.set(ax + dx, ay + dy, glow)

    def _pollen(self, cv, hx, hy, L) -> list:
        glints = []
        for i, (x, y, _, _, life, mx) in enumerate(self.pollen):
            a = min(1.0, life / mx * 2) * min(1.0, (mx - life) * 4)
            px, py = int(hx + x * L), int(hy + y * L)
            cv.blend(px, py, self.palette.pollen, 0.9 * a)
            if a > 0.6 and i % 5 == 0:
                glints.append((px, py, self.palette.pollen.lerp(WHITE, 0.4)))
        return glints

    def _geometry(self, bl: BrailleLayer, hx, hy, L, amount) -> None:
        pal, clock = self.palette, self.clock
        cx, cy = hx * 2 + 1, hy * 2 + 1  # piksel -> nokta koordinati
        dim = lambda c, k: pal.bg.lerp(c, amount * k)
        for k, rad in enumerate(RINGS):
            r = 2 * L * rad * (0.6 + 0.4 * amount)
            rot = clock * (0.35 + 0.2 * k) * (-1) ** k
            bl.arc(cx, cy, r, 0, math.tau, lambda t, k=k: dim(pal.orbit_a, 0.45), 3)
            bl.arc(cx, cy, r, rot, rot + 1.9, lambda t: dim(pal.orbit_a.lerp(pal.orbit_b, t), 0.3 + 0.7 * t))
            hx2, hy2 = cx + r * math.cos(rot + 1.9), cy + r * math.sin(rot + 1.9)
            for dx in range(-1, 2):
                for dy in range(-1, 2):
                    bl.dot(hx2 + dx, hy2 + dy, dim(WHITE, 0.9))
        rr = 2 * L * 0.95 * amount
        rot = clock * 0.12
        for k in range(6):
            a = rot + k * math.pi / 3
            bl.arc(cx + rr * math.cos(a), cy + rr * math.sin(a), rr, 0, math.tau,
                   lambda t: dim(pal.orbit_b, 0.35), 2)

    def _compose(self, cv, bl, area, buf, glints) -> None:
        pw, bgc = cv.w, self.palette.bg
        for cy in range(area.height):
            for cx in range(pw):
                top, bot = cv.px[2 * cy * pw + cx], cv.px[(2 * cy + 1) * pw + cx]
                if top is not None:
                    ch, fg, bg = "▀", top, bot or bgc
                elif bot is not None:
                    ch, fg, bg = "▄", bot, bgc
                else:
                    key = cy * pw + cx
                    m = bl.mask.get(key) if bl else None
                    ch, fg, bg = (chr(0x2800 + m), bl.color[key], bgc) if m else (" ", None, bgc)
                buf.set_cell(area.x + cx, area.y + cy, Cell(ch, fg, bg))
        for px, py, color in glints:
            if 0 <= px < pw and 0 <= py // 2 < area.height:
                x, y = area.x + px, area.y + py // 2
                buf.set_cell(x, y, Cell("•", color, buf.get(x, y).bg or bgc))
