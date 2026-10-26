"""Prosedurel zambak: tohumdan tam acilisa. Space: duraklat, R: bastan, C: palet, G: geometri,
P: polen, +/-: hiz, Q/Esc: cikis"""
from _path import ROOT  # noqa: F401  (sys.path ayari)
from gravitui import (App, Layout, Length, Paragraph, Percentage, ProceduralFlower, Style,
                      VERTICAL, GRAY)

flower = ProceduralFlower(seed=7)


def draw(buf, dt):
    flower.update(dt)
    rows = Layout.split(buf.area, VERTICAL, [Length(1), Percentage(100), Length(1)])
    pal = flower.palette
    state = "DURAKLATILDI" if flower.paused else flower.status()
    Paragraph(f" {pal.name} | {state} | hiz x{flower.speed:.2f} | geometri "
              f"{'acik' if flower.show_geometry else 'kapali'} | polen "
              f"{'acik' if flower.show_pollen else 'kapali'}",
              Style(fg=pal.petal[-1], bg=pal.bg)).render(rows[0], buf)
    flower.render(rows[1], buf)
    Paragraph(" [Space] duraklat  [R] bastan  [C] palet  [G] geometri  [P] polen  [+/-] hiz  [Q] cikis",
              Style(fg=GRAY, bg=pal.bg)).render(rows[2], buf)


def on_key(k):
    k = k.lower()
    if k == "space":
        flower.toggle_pause()
    elif k == "r":
        flower.restart()
    elif k == "c":
        flower.next_palette()
    elif k == "g":
        flower.show_geometry = not flower.show_geometry
    elif k == "p":
        flower.show_pollen = not flower.show_pollen
    elif k in ("+", "="):
        flower.adjust_speed(1.25)
    elif k in ("-", "_"):
        flower.adjust_speed(0.8)
    return k in ("q", "esc")


if __name__ == "__main__":
    App(draw, on_key).run()
