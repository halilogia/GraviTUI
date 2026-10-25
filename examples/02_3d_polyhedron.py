"""Terminal panelinde donen 3D d20 ve kup. Cikis: q, Space: sekilleri degistir"""
from _path import ROOT  # noqa: F401  (sys.path ayari)
from gravitui import (App, Block, Canvas3D, Layout, Length, Mesh3D, Paragraph, Percentage,
                      Quaternion, Style, Vector3, ROUNDED, HORIZONTAL, VERTICAL, CYAN, MAGENTA)

d20, cube = Mesh3D.icosahedron(), Mesh3D.cube()
state = {"t": 0.0, "swap": False}


def draw(buf, dt):
    state["t"] += dt
    t = state["t"]
    rows = Layout.split(buf.area, VERTICAL, [Length(1), Percentage(100)])
    Paragraph("q: cikis   space: sekilleri degistir").render(rows[0], buf)
    cols = Layout.split(rows[1], HORIZONTAL, [Percentage(50), Percentage(50)])
    meshes = (cube, d20) if state["swap"] else (d20, cube)
    q1 = Quaternion.from_axis_angle(Vector3(0.3, 1, 0.2), t * 1.1)
    q2 = Quaternion.from_euler(t * 0.8, t * 0.5, t * 0.3)
    for area, mesh, q, title, col in ((cols[0], meshes[0], q1, "Mesh A", CYAN),
                                      (cols[1], meshes[1], q2, "Mesh B", MAGENTA)):
        blk = Block(ROUNDED, title, border_style=Style(fg=col))
        blk.render(area, buf)
        Canvas3D(mesh, q).render(blk.inner(area), buf)


def on_key(k):
    if k == "space":
        state["swap"] = not state["swap"]
    return k in ("q", "esc")


if __name__ == "__main__":
    App(draw, on_key).run()
