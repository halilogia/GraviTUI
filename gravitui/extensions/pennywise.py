"""Karakter matrisinden beliren prosedürel Pennywise portresi."""
from __future__ import annotations

import math

from ..core.buffer import Buffer
from ..core.style import Color, Style
from ..layout.rect import Rect
from ..widgets.base import Widget


class Pennywise(Widget):
    """Dosya ve paket gerektirmeyen animasyonlu ASCII portre.

    ``tick(dt)`` zamanı ilerletir; ``render`` yalnızca verilen alana yazar.
    İlk iki saniye gözler görünür, ardından yüz matristen belirir.
    """

    BACKGROUND = Color(2, 4, 8)
    GLYPHS = "01:;+=xX#%"

    def __init__(self, *, seed: int = 11):
        self.seed = int(seed)
        self.time = 0.0
        self.paused = False
        self.matrix_style = "matrix"

    @property
    def reveal(self) -> float:
        phase = self.time % 12.0
        value = min(1.0, max(0.0, (phase - 2.0) / 3.0),
                    max(0.0, (12.0 - phase) / 2.0))
        return value * value * (3.0 - 2.0 * value)

    def tick(self, dt: float) -> None:
        if not math.isfinite(dt) or dt < 0:
            raise ValueError("dt sonlu ve negatif olmayan bir sayı olmalı")
        if not self.paused:
            self.time += dt

    def restart(self) -> None:
        self.time = 0.0

    def toggle_pause(self) -> None:
        self.paused = not self.paused

    def next_matrix_style(self) -> None:
        self.matrix_style = "density" if self.matrix_style == "matrix" else "matrix"

    def _portrait(self, x: float, y: float):
        """Normalize koordinatlarda renk ve yüzey yoğunluğu (saf örnekleme)."""
        r = self.reveal
        sway = 0.025 * math.sin(self.time * 0.8)
        x -= sway
        # Soğuk ışıklı omuzlar ve pileli palyaço yakalığı.
        if 0.60 < y < 1.02 and abs(x) < 0.82 - 0.25 * (y - 0.6):
            fold = 0.35 + 0.65 * abs(math.sin(math.atan2(x, y - 0.5) * 19))
            if y < 0.83 - 0.15 * abs(x):
                return (145, 164, 180), r * fold * 0.8
            return (35, 48, 66), r * (0.3 + fold * 0.35)
        # Geriye taranmış turuncu/kızıl saçın iki kanadı.
        hair = ((abs(x) - 0.47) / 0.29) ** 2 + ((y + 0.34) / 0.53) ** 2
        if hair < 1 and abs(x) > 0.30 + 0.12 * max(0, -y):
            strand = 0.55 + 0.45 * abs(math.sin(36 * x + 13 * y))
            return (155, 51, 22), r * strand * (1 - hair * 0.5)
        # Uzun alın, daralan çene ve küresel yüz gölgesi.
        face = (x / (0.43 - 0.10 * max(0, y))) ** 2 + ((y + 0.14) / 0.79) ** 2
        if face > 1:
            return (18, 35, 57), 0.035
        shade = (0.40 + 0.60 * math.sqrt(max(0, 1 - face)))
        color, intensity = (192, 203, 211), r * shade
        ax = abs(x)
        # Kötücül kaşlar ve karanlık göz çukurları.
        eye_y = -0.18 - 0.23 * (ax - 0.18)
        socket = ((ax - 0.18) / 0.135) ** 2 + ((y - eye_y) / 0.095) ** 2
        if socket < 1.7:
            color, intensity = (17, 19, 25), 0.08 * r
        if abs(y - (eye_y - 0.095)) < 0.022 and 0.08 < ax < 0.31:
            color, intensity = (12, 12, 16), 0.2 * r
        # Gözler yüz belirmeden önce de yanar; ince dikey gözbebekleri.
        eye = ((ax - 0.18) / 0.085) ** 2 + ((y - eye_y) / 0.027) ** 2
        if eye < 1:
            pulse = 0.83 + 0.17 * math.sin(self.time * 2.3)
            return ((255, 186, 55), pulse) if abs(ax - 0.18) > 0.010 else ((30, 16, 5), 0.3)
        # Gözlerden dudak köşelerine uzanan karakteristik kırmızı makyaj.
        stripe_x = 0.18 + 0.10 * math.sin(max(0, y + 0.12) * 5)
        if -0.55 < y < 0.37 and abs(ax - stripe_x) < 0.020:
            color, intensity = (180, 29, 33), r * 0.9
        if (x / 0.073) ** 2 + ((y - 0.12) / 0.065) ** 2 < 1:
            color, intensity = (218, 40, 43), r
        # Geniş sırıtış, kırmızı dudaklar ve tek tek dişler.
        mouth_y = 0.37 - 1.5 * x * x
        mouth = (x / 0.25) ** 2 + ((y - mouth_y) / 0.105) ** 2
        if mouth < 1.35:
            color, intensity = (160, 23, 31), r * 0.85
        if mouth < 0.92:
            color, intensity = (9, 7, 12), r * 0.3
            if abs(y - mouth_y) > 0.028 and int((x + 0.3) * 65) % 3 != 0:
                color, intensity = (220, 211, 178), r * 0.85
        return color, intensity

    def render(self, area: Rect, buf: Buffer) -> None:
        visible = area.intersect(buf.area)
        if visible.is_empty():
            return
        buf.fill(visible, " ", Style(bg=self.BACKGROUND))
        if area.width < 12 or area.height < 6:
            return
        # Terminal hücreleri yaklaşık 1:2; koordinatlar yeniden boyutlanınca korunur.
        scale = min(area.width / 2.0, area.height)
        frame = int(self.time * 12)
        ramp = " .:-=+*#%@"
        styles = {}
        for row in range(visible.y, visible.bottom):
            y = (row + 0.5 - area.y - area.height / 2) / (scale / 2)
            for col in range(visible.x, visible.right):
                x = (col + 0.5 - area.x - area.width / 2) / scale
                rgb, strength = self._portrait(x, y)
                noise = (col * 73 + row * 151 + self.seed * 31 + frame * 17) % 101
                strength *= 0.72 + noise / 360
                if strength < 0.025:
                    continue
                level = min(15, max(1, int(strength * 15)))
                key = (rgb, level)
                if key not in styles:
                    styles[key] = Style(fg=Color(*(int(c * level / 15) for c in rgb)),
                                        bg=self.BACKGROUND)
                glyph = (ramp[min(9, int(strength * 9))] if self.matrix_style == "density"
                         else self.GLYPHS[noise % len(self.GLYPHS)])
                buf.set_char(col, row, glyph, styles[key], clip=area)
