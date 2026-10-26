"""CyberEye: karakter matrisinden olusan prosedurel 3D siber goz (saccade, goz kirpma, nefes)."""
from __future__ import annotations

import math
import random
from typing import Optional, Union

from ..core.buffer import Buffer, Cell
from ..layout.rect import Rect
from ..widgets.base import Widget
from .eye_math import (EYE_PALETTES, MATRIX_STYLES, EyePalette, blink_closure, cell_hash, eyelid_bounds,
                       get_eye_palette, glyph_for, iris_center, iris_intensity, pupil_radius,
                       shade_color, shade_curvature, sphere_normal)

BLINK_DURATION = 0.34
DILATED, CONSTRICTED = 0.95, 0.08


class CyberEye(Widget):
    def __init__(self, palette: Union[str, int, EyePalette] = 0, matrix_style: str = "cyber",
                 seed: Optional[int] = None, auto_gaze: bool = True):
        self.palette = get_eye_palette(palette)
        self.matrix_style = matrix_style if matrix_style in MATRIX_STYLES else MATRIX_STYLES[0]
        self.auto_gaze = auto_gaze
        self.rng = random.Random(seed)
        self.gx = self.gy = 0.0            # anlik bakis
        self.target = [0.0, 0.0]           # hedef bakis (manuel veya saccade)
        self.dilation = 0.5
        self.dilation_target = 0.5
        self.time = 0.0
        self.blink_t: Optional[float] = None
        self._next_blink = self.rng.uniform(1.5, 4.0)
        self._next_saccade = self.rng.uniform(0.6, 1.8)
        self._tremor = (0.0, 0.0)

    # --- kontrol ---
    def blink(self) -> None:
        if self.blink_t is None:
            self.blink_t = 0.0

    def set_gaze(self, gx: float, gy: float) -> None:
        self.target = [max(-1.0, min(1.0, gx)), max(-1.0, min(1.0, gy))]

    def nudge_gaze(self, dx: float, dy: float) -> None:
        self.auto_gaze = False
        self.set_gaze(self.target[0] + dx, self.target[1] + dy)

    def toggle_auto(self) -> bool:
        self.auto_gaze = not self.auto_gaze
        return self.auto_gaze

    def toggle_dilation(self) -> float:
        self.dilation_target = CONSTRICTED if self.dilation_target > 0.5 else DILATED
        return self.dilation_target

    def next_palette(self) -> EyePalette:
        i = EYE_PALETTES.index(self.palette) if self.palette in EYE_PALETTES else -1
        self.palette = EYE_PALETTES[(i + 1) % len(EYE_PALETTES)]
        return self.palette

    def next_matrix_style(self) -> str:
        self.matrix_style = MATRIX_STYLES[(MATRIX_STYLES.index(self.matrix_style) + 1) % len(MATRIX_STYLES)]
        return self.matrix_style

    @property
    def closure(self) -> float:
        return 0.0 if self.blink_t is None else blink_closure(self.blink_t)

    # --- animasyon ---
    def tick(self, dt: float) -> None:
        dt = max(0.0, min(dt, 0.25))
        self.time += dt
        if self.blink_t is not None:
            self.blink_t += dt / BLINK_DURATION
            if self.blink_t >= 1.0:
                self.blink_t = None
                self._next_blink = self.rng.uniform(2.0, 5.5)
        else:
            self._next_blink -= dt
            if self._next_blink <= 0:
                self.blink()
        if self.auto_gaze:
            self._next_saccade -= dt
            if self._next_saccade <= 0:
                self._next_saccade = self.rng.uniform(0.5, 2.2)
                if self.rng.random() < 0.3:
                    self.set_gaze(0.0, 0.0)  # merkeze donus
                else:
                    self.set_gaze(self.rng.uniform(-0.9, 0.9), self.rng.uniform(-0.7, 0.7))
        k = 1.0 - math.exp(-dt * 16.0)       # saccade: hizli, yumusak varis
        self.gx += (self.target[0] - self.gx) * k
        self.gy += (self.target[1] - self.gy) * k
        if self.rng.random() < dt * 30:      # mikro-titreme
            self._tremor = (self.rng.uniform(-0.025, 0.025), self.rng.uniform(-0.02, 0.02))
        self.dilation += (self.dilation_target - self.dilation) * (1.0 - math.exp(-dt * 4.0))

    update = tick

    # --- cizim ---
    def render(self, area: Rect, buf: Buffer) -> None:
        if area.width < 8 or area.height < 3:
            return
        pal, style = self.palette, self.matrix_style
        w, h = area.width, area.height
        breath = math.sin(self.time * 1.6)
        iris_r = min(h * 0.9, (w / 2 - 1) / 3.0) * (1.0 + 0.015 * breath)
        half_w = min(w / 2 - 1, iris_r * 3.2)
        sphere_r = half_w * 1.05
        gx, gy = self.gx + self._tremor[0], self.gy + self._tremor[1]
        ix, iy, squash = iris_center(gx, gy, half_w, iris_r)
        pupil = pupil_radius(iris_r, self.dilation + 0.04 * breath) / iris_r
        closure = self.closure
        shift = iy * 0.35
        lid_h, low_h = iris_r * 1.12, iris_r * 0.85
        glint_x, glint_y = ix * 0.5 - iris_r * 0.34, iy * 0.5 - iris_r * 0.38
        tick = int(self.time * 24)
        t = self.time
        cx, cy = w / 2.0, h / 2.0
        for row in range(h):
            py = (row + 0.5 - cy) * 2.0
            for col in range(w):
                px = col + 0.5 - cx
                b = eyelid_bounds(px / half_w, lid_h, low_h, closure, shift)
                if b is None or py < b[0] or py > b[1]:
                    near = 0.0 if b is None else min(abs(py - b[0]), abs(py - b[1]))
                    v = 0.07 + 0.03 * cell_hash(col, row, tick // 9) if (b is None or near > 2.2) else 0.0
                    if b is not None and near <= 2.2:
                        v = 0.55 - 0.18 * near  # kapak kenari / kirpik hatti
                    if cell_hash(col, row, 7) > (0.35 if v > 0.2 else 0.88):
                        continue
                    inten = v
                else:
                    n = sphere_normal(px, py, sphere_r)
                    inten = 0.12 + 0.35 * (shade_curvature(n) if n else 0.0)
                    edge = min(py - b[0], b[1] - py)
                    inten *= 0.45 + 0.55 * min(1.0, edge / (iris_r * 0.35))  # kapak golgesi
                    dx, dy = (px - ix) / squash, py - iy
                    r = math.hypot(dx, dy) / iris_r
                    if r < 1.0:
                        base = iris_intensity(r, math.atan2(dy, dx), pupil, t)
                        inten = base * (0.55 + 0.45 * (shade_curvature(sphere_normal(dx, dy, iris_r * 1.15)
                                                                       or (0, 0, 1))))
                    gd = math.hypot(px - glint_x, (py - glint_y)) / (iris_r * 0.16)
                    if gd < 1.0:
                        inten = max(inten, 1.15 - 0.2 * gd)
                if inten < 0.02:
                    continue
                color = pal.glint if inten > 1.0 else shade_color(inten, pal)
                buf.set_cell(area.x + col, area.y + row,
                             Cell(glyph_for(inten, style, col, row, tick), color, pal.bg))
