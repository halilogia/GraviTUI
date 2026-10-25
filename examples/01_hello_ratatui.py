"""Temel layout, bloklar, paragraflar ve gauge. Cikis: q"""
import math
import time

from _path import ROOT  # noqa: F401  (sys.path ayari)
from gravitui import (App, Block, Gauge, Layout, Length, Line, Min, Paragraph, Percentage, Span,
                      Style, Color, Tabs, ROUNDED, DOUBLE, VERTICAL, HORIZONTAL, CENTER,
                      CYAN, MAGENTA, YELLOW, GREEN, ORANGE)

START = time.perf_counter()


def draw(buf, dt):
    t = time.perf_counter() - START
    rows = Layout.split(buf.area, VERTICAL, [Length(3), Min(5), Length(3)])
    Tabs(["Hello", "Layout", "Gauge"], int(t) % 3, style=Style(fg=CYAN),
         block=Block(ROUNDED, "GraviTUI", border_style=Style(fg=MAGENTA))).render(rows[0], buf)
    cols = Layout.split(rows[1], HORIZONTAL, [Percentage(60), Min(10)])
    Paragraph([
        Line([Span("Merhaba ", Style(fg=YELLOW, bold=True)),
              Span("GraviTUI!", Style(fg=GREEN, italic=True))]),
        Line.of(""),
        Line.of("Ratatui'den esinlenen, sifir bagimlilikli Pure Python TUI cercevesi. "
                "Word wrap, 24-bit renk ve diff tabanli flicker-free cizim."),
    ], block=Block(DOUBLE, "Paragraf", border_style=Style(fg=ORANGE), padding=(1, 0, 1, 0))
    ).render(cols[0], buf)
    Paragraph("Sag panel\n(ortalanmis)", align=CENTER,
              block=Block(ROUNDED, "Panel", border_style=Style(fg=CYAN))).render(cols[1], buf)
    Gauge((math.sin(t) + 1) / 2, colors=[Color(60, 120, 255), Color(255, 80, 200)],
          block=Block(ROUNDED, "Gauge (q: cikis)")).render(rows[2], buf)


if __name__ == "__main__":
    App(draw, on_key=lambda k: k in ("q", "esc")).run()
