"""Siber goz: Space kirp, Ok/WASD bakis, A otonom bakis, D gozbebegi, C palet, M matris stili, Q/Esc cikis"""
from _path import ROOT  # noqa: F401  (sys.path ayari)
from gravitui import App, CyberEye, Layout, Length, Paragraph, Percentage, Style, VERTICAL, GRAY

eye = CyberEye(seed=11)
STEP = 0.25
MOVES = {"up": (0, -STEP), "w": (0, -STEP), "down": (0, STEP), "s": (0, STEP),
         "left": (-STEP, 0), "right": (STEP, 0)}


def draw(buf, dt):
    eye.tick(dt)
    rows = Layout.split(buf.area, VERTICAL, [Length(1), Percentage(100), Length(1)])
    pal = eye.palette
    Paragraph(f" Eye -> Space | {pal.name} | matris: {eye.matrix_style} | bakis "
              f"{'otonom' if eye.auto_gaze else 'manuel'} | gozbebegi {eye.dilation:.2f}",
              Style(fg=pal.stops[-2], bg=pal.bg)).render(rows[0], buf)
    eye.render(rows[1], buf)
    Paragraph(" [Space] kirp  [Ok/W/S] bakis  [A] otonom  [D] gozbebegi  [C] palet  [M] matris  [Q] cikis",
              Style(fg=GRAY, bg=pal.bg)).render(rows[2], buf)


def on_key(k):
    k = k.lower()
    if k == "space":
        eye.blink()
    elif k in MOVES:
        eye.nudge_gaze(*MOVES[k])
    elif k == "a":
        eye.toggle_auto()
    elif k == "d":
        eye.toggle_dilation()
    elif k == "c":
        eye.next_palette()
    elif k == "m":
        eye.next_matrix_style()
    return k in ("q", "esc")


if __name__ == "__main__":
    App(draw, on_key).run()
