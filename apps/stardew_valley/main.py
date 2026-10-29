"""Stardew Valley TUI — ana döngü (GraviTUI Terminal + DiffWriter, 30 FPS).

Çalıştır:  python main.py   (Windows Terminal önerilir, en az 96x27)
"""
from __future__ import annotations

import os
import sys
import time

# Betik olarak çalışırken bu klasör sys.path[0] olur ve calendar.py stdlib `calendar`ı gölgeler;
# bu yüzden klasörü çıkarıp depo kökünü ekliyoruz ve paketi mutlak içe aktarıyoruz.
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(os.path.dirname(_HERE))
sys.path[:] = [p for p in sys.path if os.path.abspath(p or ".") != _HERE]
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

FPS = 30


def run() -> int:
    from gravitui import Buffer, Color, DiffWriter, Style, Terminal
    from apps.stardew_valley.game import Game
    from apps.stardew_valley.renderer import SCREEN_H, SCREEN_W, render

    game = Game()
    term = Terminal()
    writer = DiffWriter(sys.stdout)
    buf = None
    last = time.perf_counter()
    with term:
        try:
            while True:
                now = time.perf_counter()
                dt, last = min(now - last, 0.1), now
                w, h = term.size()
                if buf is None or (buf.width, buf.height) != (w, h):
                    buf = Buffer(w, h)
                    writer.invalidate()
                while (k := term.poll_key()) is not None:
                    if not game.handle_key(k):
                        return _bye(game)
                game.update(dt)
                buf.clear()
                if w < SCREEN_W or h < SCREEN_H:
                    msg = f"Terminal çok küçük: {w}x{h} (gerekli {SCREEN_W}x{SCREEN_H})"
                    buf.put_str(0, 0, msg[:w], Style(fg=Color(255, 120, 100)))
                else:
                    render(game, buf, now)
                writer.flush(buf)
                spare = 1.0 / FPS - (time.perf_counter() - now)
                if spare > 0:
                    time.sleep(spare)
        except KeyboardInterrupt:
            return _bye(game)


def _bye(game) -> int:
    c, p = game.calendar, game.player
    print(f"Görüşürüz! {c.date_str}, kasada {p.gold}g.")
    return 0


if __name__ == "__main__":
    sys.exit(run())
