"""Interstellar Gargantua: Ok/WASD kamera, +/- veya E/Z kutle, [ ] disk, R Doppler, C palet (Aurum Amber ilk), P palet onayarina don, M mod, Space duraklat, Q/Esc cikis"""
from _path import ROOT  # noqa: F401  (sys.path ayari)
from gravitui import (App, BlackHole, Layout, Length, Paragraph, Percentage, Style, VERTICAL, GRAY)

bh = BlackHole()   # varsayilan: Aurum Amber (egim ~84.3 derece, rOut=8.4, Doppler 1.05, gain 1.1)
TILT, TURN = 2.0, 6.0


def fmt_years(v):
    return f"{v:.2f}" if v < 100 else f"{v:,.0f}"


def draw(buf, dt):
    bh.tick(dt)
    rows = Layout.split(buf.area, VERTICAL, [Length(1), Percentage(100), Length(1)])
    pal, tm = bh.palette, bh.telemetry()
    fg, bg = pal.stops[-3], pal.bg
    Paragraph(f" GARGANTUA | Miller: 1 saat = {fmt_years(tm['miller_years_per_hour'])} yil | "
              f"Foton kuresi {1.5 * tm['rs_km']:.3e} km (1.5 Rs) | "
              f"Lorentz g(ISCO) {tm['lorentz_isco']:.3f}", Style(fg=fg, bg=bg)).render(rows[0], buf)
    bh.render(rows[1], buf)
    Paragraph(f" {pal.name} | {bh.mode} | egim {bh.inclination:.0f} az {bh.azimuth:.0f} | kutle {bh.mass:.2f}x10^8 Msun"
              f" Rs={tm['rs_km']:.2e} km | Doppler {'ACIK' if bh.doppler else 'kapali'} g={tm['g_min']:.2f}..{tm['g_max']:.2f}"
              f" {'| DURAKLADI' if bh.paused else ''}", Style(fg=GRAY, bg=bg)).render(rows[2], buf)


def on_key(k):
    k = k.lower()
    if k in ("up", "w"):
        bh.tilt(TILT)
    elif k in ("down", "s"):
        bh.tilt(-TILT)
    elif k in ("left", "a"):
        bh.rotate(-TURN)
    elif k in ("right", "d"):
        bh.rotate(TURN)
    elif k in ("+", "=", "e"):
        bh.set_mass(bh.mass * 1.08)
    elif k in ("-", "_", "z"):
        bh.set_mass(bh.mass / 1.08)
    elif k == "]":
        bh.set_disk_size(bh.disk_size + 1.0)
    elif k == "[":
        bh.set_disk_size(bh.disk_size - 1.0)
    elif k == "r":
        bh.toggle_doppler()
    elif k == "c":
        bh.next_palette()
    elif k == "p":
        bh.apply_preset()
    elif k == "m":
        bh.next_mode()
    elif k == "space":
        bh.toggle_pause()
    return k in ("q", "esc")


if __name__ == "__main__":
    App(draw, on_key, fps=30).run()
