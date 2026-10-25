"""2D karo haritasi + BFS yol + parcacik gosterimi.
Oklar: hareket, Enter: kasaya git (BFS), x: patlama+shake, g: glitch, q: cikis"""
from _path import ROOT  # noqa: F401  (sys.path ayari)
from gravitui import (App, Block, Color, ParticleFX, Rect, Style, Tile, TileMap, ROUNDED,
                      YELLOW, ORANGE, CYAN, MAGENTA)

FLOOR = Tile("·", Style(fg=Color(70, 70, 90)))
WALL = Tile("█", Style(fg=Color(110, 90, 140)), walkable=False)
DESK = Tile("▒", Style(fg=Color(180, 130, 70)), walkable=False)
SAFE = Tile("◙", Style(fg=YELLOW))
PLAYER = Tile("@", Style(fg=CYAN, bold=True))
SAFE_POS = (34, 10)

W, H = 40, 14
m = TileMap(W, H, layers=2)
m.fill_rect(Rect(0, 0, W, H), FLOOR)
m.fill_rect(Rect(0, 0, W, 1), WALL)
m.fill_rect(Rect(0, H - 1, W, 1), WALL)
m.fill_rect(Rect(0, 0, 1, H), WALL)
m.fill_rect(Rect(W - 1, 0, 1, H), WALL)
m.fill_rect(Rect(20, 1, 1, H - 5), WALL)  # ara duvar, altta gecit
for x in range(4, 16, 3):
    m.fill_rect(Rect(x, 3, 1, 2), DESK)
pos = [2, 2]
path = []
fx = ParticleFX(seed=3)
acc = [0.0]


def draw(buf, dt):
    acc[0] += dt
    if path and acc[0] > 0.06:
        acc[0] = 0
        pos[:] = path.pop(0)
        m.highlight = set(path)
        if not path:
            fx.burst(inner_origin[0] + SAFE_POS[0], inner_origin[1] + SAFE_POS[1], 40,
                     colors=[YELLOW, ORANGE], life=1.2, gravity=6)
    blk = Block(ROUNDED, "Mini Ofis", border_style=Style(fg=MAGENTA))
    area = buf.area.pad(0, 0, 0, 1)
    blk.render(area, buf)
    inner = blk.inner(area)
    inner_origin[:] = [inner.x, inner.y]
    m.clear_layer(1)
    m.set_tile(*SAFE_POS, SAFE, 1)
    m.set_tile(pos[0], pos[1], PLAYER, 1)
    m.render(inner, buf)
    fx.update(dt)
    fx.render(inner, buf)
    fx.post_process(buf)
    buf.put_str(0, buf.height - 1,
                "oklar: yurume | enter: BFS ile kasaya | x: patlama | g: glitch | q: cikis")


inner_origin = [1, 1]


def on_key(k):
    d = {"up": (0, -1), "down": (0, 1), "left": (-1, 0), "right": (1, 0)}
    if k in d:
        path.clear()
        m.highlight = set()
        nx, ny = pos[0] + d[k][0], pos[1] + d[k][1]
        if m.is_walkable(nx, ny):
            pos[:] = [nx, ny]
    elif k == "enter":
        p = m.find_path(tuple(pos), SAFE_POS)
        if p:
            path[:] = p[1:]
            m.highlight = set(path)
    elif k == "x":
        fx.burst(inner_origin[0] + pos[0], inner_origin[1] + pos[1], 60,
                 colors=[ORANGE, YELLOW], life=0.9)
        fx.shake(3, 0.4)
    elif k == "g":
        fx.glitch(0.6, 0.5)
    return k in ("q", "esc")


if __name__ == "__main__":
    App(draw, on_key).run()
