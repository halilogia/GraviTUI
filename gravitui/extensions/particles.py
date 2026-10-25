"""ParticleFX: parcacik firtinasi, screen shake ve glitch efektleri."""
from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import List, Optional, Sequence

from ..core.buffer import Buffer, Cell, BLANK
from ..core.style import Color, Style, WHITE
from ..layout.rect import Rect
from ..widgets.base import Widget


@dataclass
class Particle:
    x: float
    y: float
    vx: float
    vy: float
    life: float
    max_life: float
    color: Color
    char: str = "*"
    gravity: float = 0.0
    fade_to: Optional[Color] = None


class ParticleFX(Widget):
    def __init__(self, seed: Optional[int] = None, max_particles: int = 2000):
        self.rng = random.Random(seed)
        self.particles: List[Particle] = []
        self.max_particles = max_particles
        self.shake_time = 0.0
        self.shake_power = 0.0
        self.glitch_time = 0.0
        self.glitch_power = 0.0
        self.shake_offset = (0, 0)

    def emit(self, p: Particle) -> None:
        if len(self.particles) < self.max_particles:
            self.particles.append(p)

    def burst(self, x: float, y: float, count: int, speed: float = 12.0, life: float = 1.0,
              colors: Sequence[Color] = (WHITE,), chars: str = "*+.", gravity: float = 0.0) -> None:
        for _ in range(count):
            ang = self.rng.uniform(0, math.tau)
            sp = self.rng.uniform(0.2, 1.0) * speed
            lf = life * self.rng.uniform(0.6, 1.0)
            self.emit(Particle(x, y, math.cos(ang) * sp, math.sin(ang) * sp * 0.5, lf, lf,
                               self.rng.choice(list(colors)), self.rng.choice(chars), gravity))

    def storm(self, area: Rect, count: int, colors: Sequence[Color] = (WHITE,),
              speed: float = 10.0, angle: float = math.pi / 2, chars: str = "|:.") -> None:
        """Alanin ust kenarindan `angle` yonunde akan parcaciklar."""
        for _ in range(count):
            x = self.rng.uniform(area.x, area.right)
            y = area.y
            sp = self.rng.uniform(0.5, 1.0) * speed
            lf = self.rng.uniform(0.8, 2.0)
            self.emit(Particle(x, y, math.cos(angle) * sp * 0.3, math.sin(angle) * sp * 0.5,
                               lf, lf, self.rng.choice(list(colors)), self.rng.choice(chars)))

    def shake(self, power: float = 2.0, duration: float = 0.4) -> None:
        self.shake_power, self.shake_time = power, duration

    def glitch(self, power: float = 0.3, duration: float = 0.3) -> None:
        self.glitch_power, self.glitch_time = power, duration

    def update(self, dt: float) -> None:
        alive = []
        for p in self.particles:
            p.life -= dt
            if p.life <= 0:
                continue
            p.vy += p.gravity * dt
            p.x += p.vx * dt
            p.y += p.vy * dt
            alive.append(p)
        self.particles = alive
        if self.shake_time > 0:
            self.shake_time = max(0.0, self.shake_time - dt)
            k = self.shake_power * (self.shake_time > 0)
            self.shake_offset = (round(self.rng.uniform(-k, k)), round(self.rng.uniform(-k, k) / 2))
        else:
            self.shake_offset = (0, 0)
        self.glitch_time = max(0.0, self.glitch_time - dt)

    def render(self, area: Rect, buf: Buffer) -> None:
        for p in self.particles:
            x, y = int(round(p.x)), int(round(p.y))
            if not area.contains(x, y):
                continue
            t = max(0.0, p.life / p.max_life)
            end = p.fade_to or Color(0, 0, 0)
            buf.set_char(x, y, p.char, Style(fg=end.lerp(p.color, t), bold=t > 0.6))

    def post_process(self, buf: Buffer, area: Optional[Rect] = None) -> None:
        """Render sonrasi: shake kaydirmasi + glitch (karede cagrilir)."""
        area = (area or buf.area).intersect(buf.area)
        if self.shake_offset != (0, 0):
            shake_buffer(buf, *self.shake_offset, area=area)
        if self.glitch_time > 0:
            glitch_buffer(buf, self.glitch_power, self.rng, area=area)


def shake_buffer(buf: Buffer, dx: int, dy: int, area: Optional[Rect] = None) -> None:
    """Alan icerigini (dx, dy) kaydirir; bosalan hucreler BLANK olur."""
    a = area or buf.area
    src = [[buf.cells[y][x] for x in range(a.x, a.right)] for y in range(a.y, a.bottom)]
    for y in range(a.height):
        for x in range(a.width):
            sx, sy = x - dx, y - dy
            ok = 0 <= sx < a.width and 0 <= sy < a.height
            buf.cells[a.y + y][a.x + x] = src[sy][sx] if ok else BLANK


def glitch_buffer(buf: Buffer, power: float, rng: random.Random,
                  area: Optional[Rect] = None) -> None:
    """Rastgele satir kaydirma + renk kanali kaydirma."""
    a = area or buf.area
    for y in range(a.y, a.bottom):
        if rng.random() > power * 0.4:
            continue
        shift = rng.randint(-4, 4)
        row = buf.cells[y][a.x:a.right]
        if not row:
            continue
        shift %= len(row)
        row = row[-shift:] + row[:-shift] if shift else row
        out = []
        for c in row:
            fg = c.fg
            if fg is not None and rng.random() < power:
                fg = Color(fg.b, fg.r, fg.g)
            out.append(Cell(c.char, fg, c.bg, c.style))
        buf.cells[y][a.x:a.right] = out
