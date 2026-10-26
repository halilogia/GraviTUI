"""TrueColor particle system: bursts, sparks, shockwaves, auras (gold victory / blood doom), glitch and screen shake."""
from __future__ import annotations

import math
import random
from dataclasses import dataclass
from collections.abc import Sequence
from typing import List, Tuple

from rpg_colors import (RGB, VOID, ScreenBuffer, add, gradient, lerp, scale)

GOLD_SPARKS = [(255, 250, 220), (255, 214, 90), (255, 160, 30), (150, 60, 10)]
BLOOD_SHARDS = [(255, 90, 70), (220, 24, 40), (120, 8, 22), (30, 2, 8)]
CYAN_SPARKS = [(220, 255, 255), (60, 240, 255), (20, 120, 200), (10, 30, 80)]
EMBER_DRIFT = [(255, 200, 120), (255, 120, 30), (140, 40, 10), (30, 10, 10)]
DUST = [(200, 180, 150), (140, 110, 80), (60, 46, 40), (20, 16, 18)]


@dataclass
class Particle:
    x: float
    y: float
    vx: float
    vy: float
    life: float
    palette: Sequence[RGB]
    glyph: str
    gravity: float = 0.0
    drag: float = 0.0
    glow: float = 0.3
    age: float = 0.0


@dataclass
class Shockwave:
    x: float
    y: float
    speed: float
    max_r: float
    palette: Sequence[RGB]
    r: float = 0.0


class ParticleSystem:
    MAX = 700

    def __init__(self, rng: random.Random):
        self.rng = rng
        self.items: List[Particle] = []
        self.waves: List[Shockwave] = []

    def clear(self) -> None:
        self.items.clear()
        self.waves.clear()

    def _add(self, p: Particle) -> None:
        if len(self.items) < self.MAX:
            self.items.append(p)

    def burst(self, x: float, y: float, n: int, speed: float, palette: Sequence[RGB], glyphs: str = "·*+x",
              life: Tuple[float, float] = (0.8, 1.6), gravity: float = 8.0, drag: float = 0.9, glow: float = 0.3,
              angle: Tuple[float, float] = (0.0, math.tau)) -> None:
        r = self.rng
        for _ in range(n):
            a = r.uniform(*angle)
            s = speed * r.uniform(0.25, 1.0)
            self._add(Particle(x, y, math.cos(a) * s, math.sin(a) * s * 0.5, r.uniform(*life), palette,
                               r.choice(glyphs), gravity, drag, glow))

    def sparkle(self, x: float, y: float, rx: float, ry: float, n: int, palette: Sequence[RGB],
                glyphs: str = "·+*x") -> None:
        r = self.rng
        for _ in range(n):
            a, d = r.uniform(0, math.tau), math.sqrt(r.random())
            self._add(Particle(x + math.cos(a) * rx * d, y + math.sin(a) * ry * d, r.uniform(-1, 1),
                               r.uniform(-3, -0.5), r.uniform(0.4, 1.1), palette, r.choice(glyphs), -1.0, 0.5, 0.35))

    def rain(self, x0: float, x1: float, y: float, n: int, palette: Sequence[RGB], glyphs: str = "▖▗▘▝▚▞",
             gravity: float = 14.0) -> None:
        r = self.rng
        for _ in range(n):
            self._add(Particle(r.uniform(x0, x1), y, r.uniform(-2, 2), r.uniform(0, 3), r.uniform(0.8, 1.8),
                               palette, r.choice(glyphs), gravity, 0.1, 0.2))

    def shockwave(self, x: float, y: float, max_r: float, palette: Sequence[RGB], speed: float = 40.0) -> None:
        self.waves.append(Shockwave(x, y, speed, max_r, palette))

    def update(self, dt: float) -> None:
        keep = []
        for p in self.items:
            p.age += dt
            if p.age >= p.life:
                continue
            damp = max(0.0, 1.0 - p.drag * dt)
            p.vx *= damp
            p.vy = p.vy * damp + p.gravity * dt
            p.x += p.vx * dt
            p.y += p.vy * dt
            keep.append(p)
        self.items = keep
        for w in self.waves:
            w.r += w.speed * dt * (1.0 - 0.6 * w.r / w.max_r)
        self.waves = [w for w in self.waves if w.r < w.max_r]

    def draw(self, buf: ScreenBuffer) -> None:
        for w in self.waves:
            f = w.r / w.max_r
            col = scale(gradient(w.palette, f), 1.0 - f * f)
            steps = int(w.r * 6) + 16
            for k in range(steps):
                a = math.tau * k / steps
                cx, cy = int(round(w.x + math.cos(a) * w.r)), int(round(w.y + math.sin(a) * w.r * 0.5))
                buf.put(cx, cy, "·" if f > 0.5 else "•", col)
                buf.glow(cx, cy, col, 0.18)
        for p in self.items:
            f = p.age / p.life
            col = scale(gradient(p.palette, f), 1.0 - f * f * 0.8)
            x, y = int(p.x), int(p.y)
            buf.put(x, y, p.glyph, col)
            buf.glow(x, y, col, p.glow * (1.0 - f))


class ScreenShake:
    def __init__(self) -> None:
        self.amp = 0.0
        self.decay = 3.0
        self.t = 0.0

    def trigger(self, amp: float, decay: float = 3.0) -> None:
        self.amp = max(self.amp, amp)
        self.decay = decay

    def update(self, dt: float) -> None:
        self.t += dt
        self.amp = max(0.0, self.amp - self.decay * dt * max(1.0, self.amp) * 0.5)

    def offset(self) -> Tuple[int, int]:
        if self.amp < 0.25:
            return 0, 0
        return (int(round(math.sin(self.t * 71.0) * self.amp * 1.6)),
                int(round(math.cos(self.t * 59.0) * self.amp * 0.7)))


class Aura:
    """Pulsing radial light with rotating rays. 'gold' = victory, 'blood' = doom."""

    def __init__(self) -> None:
        self.kind = ""
        self.strength = 0.0

    def start(self, kind: str) -> None:
        self.kind, self.strength = kind, 0.0

    def stop(self) -> None:
        self.kind = ""
        self.strength = 0.0

    def update(self, dt: float) -> None:
        if self.kind:
            self.strength = min(1.0, self.strength + dt * 1.6)

    def apply(self, buf: ScreenBuffer, cx: float, cy: float, radius: float, t: float,
              clip: Tuple[int, int, int, int]) -> None:
        if not self.kind:
            return
        x0, y0, x1, y1 = clip
        gold = self.kind == "gold"
        core = (255, 190, 60) if gold else (170, 10, 28)
        rim = (255, 240, 170) if gold else (70, 0, 12)
        pul = 0.75 + 0.25 * math.sin(t * (3.0 if gold else 7.0))
        for y in range(max(y0, int(cy - radius * 0.55)), min(y1, int(cy + radius * 0.55) + 1)):
            dy = (y - cy) * 2.0
            row = y * buf.w
            for x in range(max(x0, int(cx - radius)), min(x1, int(cx + radius) + 1)):
                dx = x - cx
                d = math.sqrt(dx * dx + dy * dy) / radius
                if d >= 1.0:
                    continue
                ang = math.atan2(dy, dx)
                ray = 0.5 + 0.5 * math.cos(ang * (9 if gold else 5) + t * (0.9 if gold else -1.7))
                k = (1.0 - d) ** 2 * (0.55 + 0.45 * ray) * pul * self.strength
                i = row + x
                if gold:
                    buf.bg[i] = add(buf.bg[i], lerp(core, rim, 1.0 - d), 0.55 * k)
                else:
                    buf.bg[i] = add(scale(buf.bg[i], 1.0 - 0.45 * k), core, 0.45 * k * ray)
                    if k > 0.2 and (x + y + int(t * 12)) % 7 == 0:
                        buf.ch[i], buf.fg[i] = "░", scale(core, 0.8)


def apply_glitch(buf: ScreenBuffer, clip: Tuple[int, int, int, int], intensity: float, rng: random.Random) -> None:
    """Red/cyan digital tear: row displacement, chroma split and corrupted block characters."""
    if intensity <= 0.02:
        return
    x0, y0, x1, y1 = clip
    w = buf.w
    rows = max(1, int((y1 - y0) * intensity * 0.7))
    for _ in range(rows):
        y = rng.randrange(y0, y1)
        shift = rng.randint(-9, 9)
        if shift == 0:
            continue
        a, b = y * w + x0, y * w + x1
        for lst in (buf.ch, buf.fg, buf.bg):
            seg = lst[a:b]
            s = shift % len(seg)
            lst[a:b] = seg[-s:] + seg[:-s]
        for x in range(x0, x1):
            i = y * w + x
            buf.fg[i] = add(buf.fg[i], (120, 0, 0), 0.8 * intensity)
    blocks = int((x1 - x0) * (y1 - y0) * 0.0035 * intensity)
    for _ in range(blocks):
        bx, by = rng.randrange(x0, x1 - 1), rng.randrange(y0, y1)
        bw = rng.randint(2, 9)
        col = rng.choice(((255, 30, 50), (0, 220, 255), (90, 0, 20), (255, 255, 255)))
        ch = rng.choice("▓▒░█▌▐▄▀")
        for x in range(bx, min(x1, bx + bw)):
            i = by * w + x
            buf.ch[i], buf.fg[i] = ch, col
            buf.bg[i] = lerp(buf.bg[i], VOID, 0.6)
