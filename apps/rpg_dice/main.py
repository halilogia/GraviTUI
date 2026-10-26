"""RPG Dice TUI - cinematic 24-bit TrueColor d20 roller (pure standard library).

Run:  python main.py        (Windows Terminal recommended, >= 90x28 cells)
"""
from __future__ import annotations

import math
import os
import random
import sys
import time
from collections import deque
from dataclasses import dataclass
from typing import Deque, List, Optional, Tuple

from rpg_colors import (AMBER, BLOOD, CRIMSON, CYAN, CYAN_DIM, DIM, EMBER, EMERALD, GOLD, GOLD_HI, IVORY, MUTED,
                    NEBULA, NEBULA_TEAL, OBSIDIAN, PANEL_BG, RGB, VOID, WHITE, FrameWriter, ScreenBuffer, add,
                    gradient, lerp, scale, text_gradient)
from dice_engine import DiceBody, PixelCanvas, build_shape, render_die
from mechanics import (DC_MAX, DEFAULT_DC, DICE_TYPES, CheckResult, RollMode, default_modifiers, face_for_value,
                       roll_check)
from particles import (BLOOD_SHARDS, CYAN_SPARKS, DUST, EMBER_DRIFT, GOLD_SPARKS, Aura, ParticleSystem, ScreenShake,
                       apply_glitch)

MIN_W, MIN_H = 90, 28
RESULT_ROWS = 6
STEP = 0.45  # seconds per reveal step (natural roll, then each modifier)
FPS = 30

# --------------------------------------------------------------------------- terminal / input

ENTER_SEQ = "\033[?1049h\033[?25l\033[?7l\033]0;RPG Dice TUI\007\033[2J"
LEAVE_SEQ = "\033[0m\033[?7h\033[?25h\033[?1049l"


def enable_vt() -> None:
    """Switch the Windows console to UTF-8 and enable VT100 / TrueColor escape processing."""
    if os.name != "nt":
        return
    import ctypes
    k32 = ctypes.windll.kernel32
    k32.SetConsoleOutputCP(65001)
    handle = k32.GetStdHandle(-11)
    mode = ctypes.c_uint32()
    if k32.GetConsoleMode(handle, ctypes.byref(mode)):
        k32.SetConsoleMode(handle, mode.value | 0x0004 | 0x0001)
    try:
        ctypes.windll.winmm.timeBeginPeriod(1)
    except OSError:
        pass


def term_size() -> Tuple[int, int]:
    try:
        s = os.get_terminal_size(sys.__stdout__.fileno())
        return s.columns, s.lines
    except (OSError, ValueError, AttributeError):
        return 100, 32


class KeyReader:
    """Non-blocking keyboard polling: msvcrt on Windows, termios/select elsewhere."""

    WIN_ARROWS = {"H": "UP", "P": "DOWN", "K": "LEFT", "M": "RIGHT"}

    def __init__(self) -> None:
        self.win = os.name == "nt"
        self._old = None
        if not self.win:
            import termios
            import tty
            self._termios = termios
            self._old = termios.tcgetattr(sys.stdin.fileno())
            tty.setcbreak(sys.stdin.fileno())

    def poll(self) -> List[str]:
        out: List[str] = []
        if self.win:
            import msvcrt
            while msvcrt.kbhit():
                ch = msvcrt.getwch()
                if ch in ("\x00", "\xe0"):
                    code = msvcrt.getwch()
                    if code in self.WIN_ARROWS:
                        out.append(self.WIN_ARROWS[code])
                else:
                    out.append(ch)
            return out
        import select
        while select.select([sys.stdin], [], [], 0)[0]:
            ch = sys.stdin.read(1)
            if ch == "\x1b" and select.select([sys.stdin], [], [], 0.01)[0]:
                seq = sys.stdin.read(2)
                out.append({"[A": "UP", "[B": "DOWN", "[D": "LEFT", "[C": "RIGHT"}.get(seq, ""))
            else:
                out.append(ch)
        return [k for k in out if k]

    def close(self) -> None:
        if self._old is not None:
            self._termios.tcsetattr(sys.stdin.fileno(), self._termios.TCSADRAIN, self._old)


# --------------------------------------------------------------------------- layout + backdrop


@dataclass
class Layout:
    w: int
    h: int
    pw: int
    sx: int
    sy: int
    sw: int
    sh: int
    ix: int
    iy: int
    iw: int
    ih: int
    dice_rows: int
    rz_y: int
    floor_px: int
    floor_row: int
    radius: float
    px: int
    py: int
    ph: int


def make_layout(w: int, h: int) -> Layout:
    pw = 34 if w >= 100 else 30
    sx, sy, sw, sh = 1, 3, w - pw - 3, h - 5
    ix, iy, iw, ih = sx + 1, sy + 1, sw - 2, sh - 2
    dice_rows = ih - RESULT_ROWS
    floor_px = int(dice_rows * 2 * 0.84)
    return Layout(w, h, pw, sx, sy, sw, sh, ix, iy, iw, ih, dice_rows, iy + dice_rows, floor_px,
                  iy + floor_px // 2, min(dice_rows * 2 * 0.27, iw * 0.15), sx + sw + 1, sy, sh)


class Backdrop:
    """Static layer: cosmic obsidian nebula, stage floor glow, frames, star positions."""

    def __init__(self, L: Layout, rng: random.Random):
        w, h = L.w, L.h
        buf = ScreenBuffer(w, h, OBSIDIAN)
        for y in range(h):
            vert = 1.0 - 0.35 * abs(y / h - 0.45)
            for x in range(w):
                n = math.sin(x * 0.085 + y * 0.19) + math.sin(x * 0.041 - y * 0.13 + 1.7) + math.sin((x * 0.5 + y) * 0.07 + 3.1)
                c = lerp(OBSIDIAN, NEBULA, ((n + 3) / 6) ** 3 * 0.55)
                c = lerp(c, NEBULA_TEAL, max(0.0, math.sin(x * 0.03 + y * 0.09 + 5)) ** 4 * 0.35)
                buf.bg[y * w + x] = scale(c, vert)
        gcx, gcy = L.ix + L.iw / 2, L.floor_row + 1
        rx, ry = L.iw * 0.44, L.dice_rows * 0.32
        for y in range(L.iy, L.iy + L.ih):
            for x in range(L.ix, L.ix + L.iw):
                i = y * w + x
                c = scale(buf.bg[i], 0.62)
                d = math.hypot((x - gcx) / rx, (y - gcy) / ry)
                if d < 1.0:
                    c = add(c, (96, 52, 14), (1 - d) ** 1.7)
                buf.bg[i] = c
        buf.box(L.sx, L.sy, L.sw, L.sh, text_gradient([GOLD, AMBER, (120, 66, 28), AMBER, GOLD]), "double",
                title="THE TABLE", title_fg=GOLD_HI)
        for x in range(L.ix + 3, L.ix + L.iw - 3):
            buf.put(x, L.rz_y - 1, "─", (62, 46, 40))
        self.buf = buf
        self.stars: List[Tuple[int, float, float, str, RGB]] = []
        for _ in range(w * h // 38):
            x, y = rng.randrange(w), rng.randrange(h)
            if x >= L.px or buf.ch[y * w + x] != " " or (L.rz_y - 1 <= y and L.sx <= x < L.sx + L.sw):
                continue
            col = rng.choice(((255, 244, 214), (190, 210, 255), (255, 200, 120)))
            self.stars.append((y * w + x, rng.uniform(0, 6.3), rng.uniform(0.6, 2.6), rng.choice("·.·+"), col))


# --------------------------------------------------------------------------- big pixel digits

FONT = {
    "0": ("111", "101", "101", "101", "111"), "1": ("010", "110", "010", "010", "111"),
    "2": ("111", "001", "111", "100", "111"), "3": ("111", "001", "111", "001", "111"),
    "4": ("101", "101", "111", "001", "001"), "5": ("111", "100", "111", "001", "111"),
    "6": ("111", "100", "111", "101", "111"), "7": ("111", "001", "001", "001", "001"),
    "8": ("111", "101", "111", "101", "111"), "9": ("111", "101", "111", "001", "111"),
    "-": ("000", "000", "111", "000", "000"),
}
DIGIT_W = 6  # 3 font pixels * 2
DIGIT_GAP = 2


def big_text_width(s: str) -> int:
    return len(s) * DIGIT_W + (len(s) - 1) * DIGIT_GAP


def draw_big(canvas: PixelCanvas, s: str, x0: int, colors: Tuple[RGB, RGB], jitter: int = 0,
             rng: Optional[random.Random] = None) -> None:
    x = x0
    for chx in s:
        glyph = FONT.get(chx, FONT["-"])
        for ry, row in enumerate(glyph):
            col = lerp(colors[0], colors[1], ry / 4)
            for rx, bit in enumerate(row):
                if bit == "1":
                    dx = rng.randint(-jitter, jitter) if jitter and rng else 0
                    for sy in range(2):
                        for sx in range(2):
                            canvas.set(x + rx * 2 + sx + dx, ry * 2 + sy, col)
        x += DIGIT_W + DIGIT_GAP


# --------------------------------------------------------------------------- application


class App:
    def __init__(self, w: int, h: int, seed: Optional[int] = None):
        self.rng = random.Random(seed)
        self.fx_rng = random.Random(seed)
        self.sides = 20
        self.dc = DEFAULT_DC[20]
        self.mode = RollMode.NORMAL
        self.mods = default_modifiers()
        self.menu_open = False
        self.menu_idx = 0
        self.history: Deque[CheckResult] = deque(maxlen=12)
        self.particles = ParticleSystem(self.fx_rng)
        self.shake = ScreenShake()
        self.aura = Aura()
        self.t = 0.0
        self.state = "idle"  # idle | rolling | reveal | result
        self.result: Optional[CheckResult] = None
        self.reveal_t = 0.0
        self._last_step = -1
        self.flash = 0.0
        self.flash_color: RGB = GOLD
        self.glitch = 0.0
        self.glitch_floor = 0.0
        self.focus = (0, 0)
        self.quit = False
        self.bodies: List[DiceBody] = []
        self.L: Optional[Layout] = None
        self.resize(w, h)
        self._idle_bodies()

    # ---- setup helpers

    def resize(self, w: int, h: int) -> None:
        self.w, self.h = w, h
        self.buf = ScreenBuffer(w, h)
        if w < MIN_W or h < MIN_H:
            self.L = None
            return
        self.L = make_layout(w, h)
        self.backdrop = Backdrop(self.L, random.Random(7))

    def _idle_bodies(self) -> None:
        shape = build_shape(self.sides)
        self.bodies = [DiceBody(shape, self.fx_rng) for _ in range(self.mode.dice_count)]
        self.state = "idle"
        self.result = None
        self.aura.stop()
        self.glitch = self.glitch_floor = 0.0

    # ---- input

    def handle_key(self, k: str) -> None:
        if k == "\x03":
            self.quit = True
            return
        if self.menu_open and self._menu_key(k):
            return
        key = k.lower() if len(k) == 1 else k
        busy = self.state == "rolling"
        if key in ("q", "\x1b"):
            self.quit = True
        elif key in (" ", "\r", "\n"):
            self.start_roll()
        elif key in ("d", "RIGHT") and not busy:
            self._set_sides(DICE_TYPES[(DICE_TYPES.index(self.sides) + 1) % len(DICE_TYPES)])
        elif key == "LEFT" and not busy:
            self._set_sides(DICE_TYPES[(DICE_TYPES.index(self.sides) - 1) % len(DICE_TYPES)])
        elif key in ("+", "=", "UP"):
            self._set_dc(self.dc + 1)
        elif key in ("-", "_", "DOWN"):
            self._set_dc(self.dc - 1)
        elif key == "a" and not busy:
            self.mode = self.mode.next()
            self._idle_bodies()
        elif key == "m":
            self.menu_open = True
        elif key == "c":
            self.start_roll(forced=20)
        elif key == "f":
            self.start_roll(forced=1)

    def _menu_key(self, k: str) -> bool:
        key = k.lower() if len(k) == 1 else k
        mod = self.mods[self.menu_idx]
        if key in ("m", "\x1b"):
            self.menu_open = False
        elif key in ("UP", "w"):
            self.menu_idx = (self.menu_idx - 1) % len(self.mods)
        elif key in ("DOWN", "s"):
            self.menu_idx = (self.menu_idx + 1) % len(self.mods)
        elif key in (" ", "\r", "\n"):
            mod.enabled = not mod.enabled
        elif key in ("LEFT", "-", "_"):
            mod.adjust(-1)
        elif key in ("RIGHT", "+", "="):
            mod.adjust(1)
        else:
            return False
        return True

    def _set_sides(self, sides: int) -> None:
        self.sides = sides
        self.dc = DEFAULT_DC[sides]
        self._idle_bodies()

    def _set_dc(self, dc: int) -> None:
        self.dc = max(1, min(DC_MAX, dc))
        if self.result is not None:
            self.result = self.result.with_dc(self.dc)

    # ---- rolling

    def start_roll(self, forced: Optional[int] = None) -> None:
        if self.state == "rolling":
            return
        if forced is not None and self.sides != 20:
            self.sides, self.dc = 20, DEFAULT_DC[20]
        self.menu_open = False
        self.particles.clear()
        self.aura.stop()
        self.glitch = self.glitch_floor = 0.0
        res = roll_check(self.sides, self.dc, self.mode, self.mods, self.rng, forced)
        shape = build_shape(self.sides)
        self.bodies = []
        for i, value in enumerate(res.rolls):
            body = DiceBody(shape, self.fx_rng)
            body.throw(face_for_value(self.sides, value), duration=3.6 + 0.25 * i,
                       side=self.fx_rng.choice((-1.0, 1.0)), delay=0.18 * i)
            self.bodies.append(body)
        self.result = res
        self.state = "rolling"
        self.reveal_t = 0.0
        self._last_step = -1

    def die_geom(self, i: int) -> Tuple[float, float, float]:
        """Canvas-pixel centre (x, y) and radius of die i."""
        L, b, n = self.L, self.bodies[i], len(self.bodies)
        slot = L.iw / 2 if n == 1 else L.iw / 2 + (-1 if i == 0 else 1) * L.iw * 0.2
        r = L.radius * (1.0 if n == 1 else 0.86)
        return slot + b.x * L.iw * 0.2, L.floor_px - r * 0.9 - b.h * 2 * r, r

    def _die_cell(self, i: int) -> Tuple[float, float]:
        cx, cy, _ = self.die_geom(i)
        return self.L.ix + cx, self.L.iy + cy / 2

    # ---- simulation

    def update(self, dt: float) -> None:
        self.t += dt
        if self.L is None:
            return
        L = self.L
        self.shake.update(dt)
        self.aura.update(dt)
        self.particles.update(dt)
        self.flash = max(0.0, self.flash - dt * 1.8)
        self.glitch = max(self.glitch_floor, self.glitch - dt * 0.9)
        for i, body in enumerate(self.bodies):
            for strength in body.update(dt):
                cx, _ = self._die_cell(i)
                self.particles.burst(cx, L.floor_row, int(5 + 10 * strength), 12 * strength + 4, DUST, "·.:",
                                     (0.4, 0.9), 6.0, 1.5, 0.1, (math.pi * 1.1, math.pi * 1.9))
                if strength > 0.6:
                    self.shake.trigger(0.9 * strength, 7.0)
        if self.state == "rolling" and all(b.settled for b in self.bodies):
            self._on_settled()
        if self.state in ("reveal", "result"):
            self.reveal_t += dt
            self._advance_reveal()
        if self.fx_rng.random() < dt * 6:
            x = self.fx_rng.uniform(L.ix, L.ix + L.iw)
            self.particles.burst(x, L.floor_row + self.fx_rng.uniform(0, 5), 1, 2.0, EMBER_DRIFT, "·.",
                                 (2.5, 4.5), -0.5, 0.2, 0.15, (-math.pi / 2 - 0.4, -math.pi / 2 + 0.4))
        if self.state == "result" and self.result and self.result.crit and self.bodies:
            self._ambient_crit()

    def _on_settled(self) -> None:
        res = self.result
        self.result = res.with_dc(self.dc)
        res = self.result
        self.state = "reveal"
        self.reveal_t = 0.0
        fx, fy = self._die_cell(res.kept_index)
        self.focus = (fx, fy)
        L = self.L
        if res.crit == "success":
            self.particles.burst(fx, fy, 150, 40, GOLD_SPARKS, "*+x.·", (0.9, 2.0), 7.0, 0.6, 0.4)
            self.particles.burst(fx, fy, 60, 22, GOLD_SPARKS, "*+.", (1.2, 2.4), -2.0, 0.4, 0.4,
                                 (math.pi * 1.1, math.pi * 1.9))
            self.particles.shockwave(fx, L.floor_row, 46, GOLD_SPARKS)
            self.shake.trigger(3.4, 2.2)
            self.flash, self.flash_color = 1.0, GOLD_HI
            self.aura.start("gold")
        elif res.crit == "failure":
            self.glitch, self.glitch_floor = 1.0, 0.10
            self.particles.burst(fx, fy, 80, 26, BLOOD_SHARDS, "▖▗▘▝▚▞▪", (0.8, 1.8), 14.0, 0.3, 0.3)
            self.particles.rain(fx - 14, fx + 14, fy - 7, 40, BLOOD_SHARDS)
            self.particles.shockwave(fx, L.floor_row, 40, BLOOD_SHARDS)
            self.shake.trigger(2.6, 2.4)
            self.flash, self.flash_color = 0.8, CRIMSON
            self.aura.start("blood")
        else:
            self.particles.shockwave(fx, L.floor_row, 22, CYAN_SPARKS if res.success else EMBER_DRIFT, 30.0)

    def _advance_reveal(self) -> None:
        res = self.result
        steps = 1 + len(res.parts)
        step = min(steps - 1, int(self.reveal_t / STEP))
        if step != self._last_step:
            self._last_step = step
            if step > 0:
                nx, ny = self._number_cell()
                self.particles.burst(nx, ny, 10, 12, GOLD_SPARKS, "+*·", (0.4, 0.9), 4.0, 1.0, 0.3)
        if self.state == "reveal" and self.reveal_t >= steps * STEP:
            self.state = "result"
            self.history.appendleft(res)
            nx, ny = self._number_cell()
            if not res.crit:
                if res.success:
                    self.particles.burst(nx, ny, 40, 26, CYAN_SPARKS, "*+·", (0.7, 1.5), 3.0, 0.8, 0.3)
                else:
                    self.particles.burst(nx, ny, 24, 10, EMBER_DRIFT, "·:.", (0.8, 1.6), 9.0, 0.6, 0.15,
                                         (0.2, math.pi - 0.2))

    def _number_cell(self) -> Tuple[float, float]:
        L = self.L
        return L.ix + L.iw / 2 - 12, L.rz_y + 2

    def _ambient_crit(self) -> None:
        fx, fy = self.focus
        if self.result.crit == "success":
            if self.fx_rng.random() < 0.6:
                self.particles.sparkle(fx, fy, 16, 7, 2, GOLD_SPARKS)
        elif self.fx_rng.random() < 0.07:
            self.glitch = max(self.glitch, 0.65)
            self.particles.rain(fx - 12, fx + 12, fy - 6, 6, BLOOD_SHARDS)

    # ---- rendering

    def render(self) -> ScreenBuffer:
        buf = self.buf
        if self.L is None:
            buf.copy_from(ScreenBuffer(self.w, self.h, VOID))
            msg = f"Terminal too small: need {MIN_W}x{MIN_H}, have {self.w}x{self.h}"
            buf.text(max(0, (self.w - len(msg)) // 2), self.h // 2, msg, GOLD)
            return buf
        L = self.L
        buf.copy_from(self.backdrop.buf)
        t = self.t
        for i, ph, sp, ch, col in self.backdrop.stars:
            k = 0.25 + 0.75 * math.sin(t * sp + ph) ** 2
            buf.ch[i], buf.fg[i] = ch, scale(col, k * 0.8)
        clip = (L.ix, L.iy, L.ix + L.iw, L.iy + L.dice_rows)
        res = self.result
        crit = res.crit if res and self.state in ("reveal", "result") else None
        fx, fy = self.focus
        self.aura.apply(buf, fx, fy, 26, t, clip)
        self._draw_circle(crit)
        self._draw_dice(crit)
        self.particles.draw(buf)
        self._draw_result_zone()
        self._draw_panel()
        self._draw_header()
        self._draw_footer()
        if self.glitch > 0:
            full = (0, 0, self.w, self.h) if self.glitch > 0.7 else (L.ix, L.iy, L.ix + L.iw, L.iy + L.ih)
            apply_glitch(buf, full, self.glitch, self.fx_rng)
        if self.flash > 0.02:
            buf.tint(0, 0, self.w, self.h, self.flash_color, min(0.85, self.flash * 0.6))
        dx, dy = self.shake.offset()
        buf.shift(dx, dy)
        return buf

    def _draw_header(self) -> None:
        w, t = self.w, self.t
        title = "R P G   D I C E"
        shimmer = math.sin(t * 0.8) * 0.5 + 0.5
        buf = self.buf
        side = "═" * 14
        full = f"{side}  {title}  {side}"
        x = (w - len(full)) // 2
        buf.text(x, 1, full, text_gradient([CRIMSON, AMBER, GOLD_HI, AMBER, CRIMSON], shimmer), None)
        sub = "roll for initiative  -  fate favours the bold"
        buf.text((w - len(sub)) // 2, 2, sub, MUTED)

    def _draw_footer(self) -> None:
        items = [("SPACE", "Roll"), ("D", "Die"), ("+/-", "DC"), ("A", "Adv/Dis"), ("M", "Mods"),
                 ("C", "Nat 20"), ("F", "Nat 1"), ("Q", "Quit")]
        total = sum(len(k) + len(v) + 5 for k, v in items)
        x = (self.w - total) // 2
        y = self.h - 2
        for k, v in items:
            self.buf.text(x, y, f"[{k}]", GOLD)
            self.buf.text(x + len(k) + 3, y, v, MUTED)
            x += len(k) + len(v) + 5

    def _ring_color(self, crit: Optional[str]) -> RGB:
        if crit == "success":
            return lerp(GOLD, GOLD_HI, 0.5 + 0.5 * math.sin(self.t * 6))
        if crit == "failure":
            return lerp(BLOOD, CRIMSON, 0.5 + 0.5 * math.sin(self.t * 9))
        return (150, 108, 46)

    def _draw_circle(self, crit: Optional[str]) -> None:
        L, buf = self.L, self.buf
        cx, cy = L.ix + L.iw / 2, L.floor_row + 1
        col = self._ring_color(crit)
        for ring, (rx, glyphs, spin) in enumerate(((L.iw * 0.36, "·+·x", 0.12), (L.iw * 0.27, "·:·o", -0.2))):
            ry = rx * 0.16
            n = int(rx * 1.5)
            for k in range(n):
                a = math.tau * k / n + self.t * spin
                x, y = int(round(cx + math.cos(a) * rx)), int(round(cy + math.sin(a) * ry))
                if y >= L.rz_y - 1 or y < L.iy:
                    continue
                shade = 0.45 + 0.55 * (0.5 + 0.5 * math.sin(a * 3 + self.t * 2))
                buf.put(x, y, glyphs[k % len(glyphs)], scale(col, shade * (0.7 if ring else 1.0)))

    def _draw_dice(self, crit: Optional[str]) -> None:
        L, buf = self.L, self.buf
        canvas = PixelCanvas(L.iw, L.dice_rows)
        labels = []
        res = self.result
        settled_view = self.state in ("reveal", "result") and res is not None
        for i, body in enumerate(self.bodies):
            cx, cy, r = self.die_geom(i)
            # soft table shadow (cells)
            shx, shy = L.ix + cx, L.floor_row
            srx = r * 1.05 / (1 + 1.4 * body.h)
            sry = max(1.0, srx * 0.16)
            alpha = 0.75 / (1 + 2.5 * body.h)
            for y in range(int(shy - sry), int(shy + sry) + 1):
                for x in range(int(shx - srx), int(shx + srx) + 1):
                    d = ((x - shx) / srx) ** 2 + ((y - shy) / sry) ** 2
                    if d < 1.0 and 0 <= x < buf.w and 0 <= y < buf.h:
                        j = y * buf.w + x
                        buf.bg[j] = scale(buf.bg[j], 1 - alpha * (1 - d))
            tint = None
            dim = 0.0
            jitter = 0.0
            if settled_view:
                if i != res.kept_index:
                    dim = 0.75
                elif crit == "success":
                    tint = (GOLD, 0.28 + 0.12 * math.sin(self.t * 5))
                elif crit == "failure":
                    tint = (BLOOD, 0.6)
                    jitter = self.glitch * 1.4
            labels += [(lb, ) for lb in render_die(canvas, build_shape(self.sides), body.q, cx, cy, r, tint, dim,
                                                   jitter, self.fx_rng)]
        canvas.blit(buf, L.ix, L.iy)
        for (lb,) in labels:
            for k, c in enumerate(lb.text):
                buf.put(L.ix + lb.x + k, L.iy + lb.y, c, lb.fg, lb.bg)
        if settled_view and len(self.bodies) > 1:
            for i in range(len(self.bodies)):
                if i != res.kept_index:
                    cx, cy, r = self.die_geom(i)
                    tag = "discarded"
                    self.buf.text(int(L.ix + cx - len(tag) / 2), int(L.iy + (cy + r * 1.25) / 2), tag, DIM)

    def _draw_result_zone(self) -> None:
        L, buf = self.L, self.buf
        res = self.result
        cx = L.ix + L.iw // 2
        y0 = L.rz_y
        if self.state == "idle" or res is None:
            msg = f"Press SPACE to roll d{self.sides}  vs  DC {self.dc}"
            k = 0.55 + 0.45 * math.sin(self.t * 3)
            buf.text(cx - len(msg) // 2, y0 + 2, msg, scale(GOLD, k))
            return
        if self.state == "rolling":
            dots = "." * (1 + int(self.t * 4) % 3)
            msg = f"the dice are cast{dots}"
            buf.text(cx - len(msg) // 2, y0 + 2, msg, scale(CYAN, 0.6 + 0.4 * math.sin(self.t * 8)))
            return
        steps = 1 + len(res.parts)
        step = min(steps - 1, int(self.reveal_t / STEP))
        shown = res.natural + sum(p.value for p in res.parts[:step])
        done = self.state == "result"
        num = str(shown)
        vw = 30
        total_w = big_text_width(num) + 4 + vw
        left = max(L.ix, cx - total_w // 2)
        canvas = PixelCanvas(L.iw, 5)
        if done:
            cols = {"success": (GOLD_HI, GOLD), "failure": (CRIMSON, BLOOD)}.get(res.crit or "", None)
            if cols is None:
                cols = (CYAN, EMERALD) if res.success else (IVORY, CRIMSON)
            if res.crit == "success":
                cols = (lerp(GOLD_HI, WHITE, 0.5 + 0.5 * math.sin(self.t * 7)), GOLD)
        else:
            cols = (IVORY, GOLD)
        jit = 1 if (res.crit == "failure" and done and self.glitch > 0.3) else 0
        draw_big(canvas, num, left - L.ix, cols, jit, self.fx_rng)
        canvas.blit(buf, L.ix, y0)
        if done:
            vx = left + big_text_width(num) + 4
            self._draw_verdict(vx, y0, res)
        # progressive formula line
        lead = f"d{res.sides}: " + (f"{res.rolls[0]} | {res.rolls[1]} -> {res.natural}" if len(res.rolls) > 1
                                     else f"{res.natural}")
        parts = "".join(f"  {p.value:+d} {p.name}" + (f"({'+'.join(map(str, p.dice))})" if p.dice else "")
                        for p in res.parts[:step])
        line = f"{lead}{parts}  =  {shown}" + (f"   vs   DC {res.dc}" if done else "")
        line = line[:L.iw - 2]
        buf.text(cx - len(line) // 2, y0 + 5, line, IVORY if done else MUTED)

    def _draw_verdict(self, x: int, y0: int, res: CheckResult) -> None:
        buf, t = self.buf, self.t
        rng = self.fx_rng
        v = res.verdict
        if res.crit == "success":
            stops, sub = [GOLD_HI, GOLD, AMBER, GOLD_HI], "NATURAL 20 - FATE BOWS TO YOU"
            v = f"== {v} =="
        elif res.crit == "failure":
            stops, sub = [CRIMSON, BLOOD, CRIMSON], "NATURAL 1 - DICE BETRAY YOU"
            v = f"== {v} =="
            if self.glitch > 0.3:
                v = "".join(rng.choice("▓▒░#") if rng.random() < self.glitch * 0.25 and c != " " else c for c in v)
        elif res.success:
            stops, sub = [CYAN, EMERALD], f"beat DC {res.dc} by {res.margin}"
        else:
            stops, sub = [EMBER, CRIMSON], f"missed DC {res.dc} by {-res.margin}"
        buf.text(x, y0 + 1, v, text_gradient(stops, (t * 0.6) % 2.0))
        buf.text(x, y0 + 2, sub, MUTED if not res.crit else lerp(MUTED, stops[0], 0.6))
        buf.text(x, y0 + 3, "━" * min(30, max(len(v), len(sub))), scale(stops[0], 0.55))

    def _draw_panel(self) -> None:
        L, buf = self.L, self.buf
        buf.box(L.px, L.py, L.pw, L.ph, text_gradient([GOLD, AMBER, (120, 66, 28)]), "round", PANEL_BG,
                "CHECK", GOLD_HI)
        x0, W = L.px + 2, L.pw - 4
        y = L.py + 1
        bottom = L.py + L.ph - 1

        def line(text: str, color: RGB, right: str = "", rcolor: RGB = MUTED, bg_: Optional[RGB] = None) -> None:
            nonlocal y
            if y >= bottom:
                return
            text = text[:W]
            if bg_ is not None:
                buf.fill(x0 - 1, y, W + 2, 1, bg_)
            buf.text(x0, y, text, color, bg_)
            if right:
                buf.text(x0 + W - len(right), y, right, rcolor, bg_)
            y += 1

        def sep() -> None:
            line("─" * W, (60, 48, 44))

        mode_col = {RollMode.ADVANTAGE: EMERALD, RollMode.DISADVANTAGE: CRIMSON}.get(self.mode, IVORY)
        line(f"DIE    d{self.sides}", IVORY, "[D]", GOLD)
        line(f"DC     {self.dc}", IVORY, "[+/-]", GOLD)
        line(f"ROLL   {self.mode.value}", mode_col, "[A]", GOLD)
        sep()
        line("MODIFIERS", GOLD_HI, "EDIT" if self.menu_open else "[M]", GOLD)
        for i, m in enumerate(self.mods):
            sel = self.menu_open and i == self.menu_idx
            mark = "[x]" if m.enabled else "[ ]"
            name = f"{'>' if sel else ' '}{mark} {m.name}"
            col = IVORY if m.enabled else DIM
            line(name, GOLD_HI if sel else col, m.label, col if m.enabled else DIM, (44, 30, 70) if sel else None)
        if self.menu_open:
            line("Up/Dn pick  Space toggle", MUTED)
            line("Left/Right adjust  M close", MUTED)
        sep()
        line("LAST CHECK", GOLD_HI)
        res = self.result
        if self.state == "result" and res is not None:
            rolls = " | ".join(map(str, res.rolls))
            line(f"d{res.sides}  {rolls}" + (f"  keep {res.natural}" if len(res.rolls) > 1 else ""), IVORY)
            for p in res.parts:
                dice = f" ({'+'.join(map(str, p.dice))})" if p.dice else ""
                line(f" {p.name}{dice}", MUTED, f"{p.value:+d}", IVORY)
            line(f"TOTAL {res.total}  vs  DC {res.dc}", IVORY)
            vcol = GOLD if res.crit == "success" else CRIMSON if res.crit == "failure" else (
                EMERALD if res.success else EMBER)
            line(res.verdict, vcol)
        else:
            line("-", DIM)
        sep()
        line("HISTORY", GOLD_HI)
        for r in self.history:
            vcol = GOLD if r.crit == "success" else CRIMSON if r.crit == "failure" else (
                EMERALD if r.success else EMBER)
            tag = "CRIT" if r.crit == "success" else "FUMB" if r.crit == "failure" else "pass" if r.success else "fail"
            line(f"{r.total:>3} vs {r.dc:<3} d{r.sides:<3}", MUTED, tag, vcol)


# --------------------------------------------------------------------------- main loop


def buffer_to_text(buf: ScreenBuffer) -> str:
    return "\n".join("".join(buf.ch[y * buf.w:(y + 1) * buf.w]) for y in range(buf.h))


def run() -> None:
    enable_vt()
    out = sys.stdout.buffer
    app = App(*term_size())
    writer = FrameWriter()
    keys = KeyReader()
    out.write(ENTER_SEQ.encode())
    out.flush()
    frame = 1.0 / FPS
    try:
        last = time.perf_counter()
        while not app.quit:
            start = time.perf_counter()
            for k in keys.poll():
                app.handle_key(k)
            size = term_size()
            if size != (app.w, app.h):
                app.resize(*size)
                writer.invalidate()
            app.update(min(0.05, start - last))
            last = start
            out.write(writer.present(app.render()).encode("utf-8"))
            out.flush()
            spare = frame - (time.perf_counter() - start)
            if spare > 0:
                time.sleep(spare)
    except KeyboardInterrupt:
        pass
    finally:
        keys.close()
        out.write(LEAVE_SEQ.encode())
        out.flush()


if __name__ == "__main__":
    run()
