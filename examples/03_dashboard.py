"""Cok panelli canli telemetri panosu. Cikis: q, Up/Down: tablo secimi"""
import math
import random

from _path import ROOT  # noqa: F401  (sys.path ayari)
from gravitui import (App, Block, Color, Fill, Gauge, Layout, Length, ListState, ListWidget, Min,
                      Paragraph, Percentage, Style, TableWidget, Tabs, Tree, TreeNode, ROUNDED,
                      HORIZONTAL, VERTICAL, GREEN, YELLOW, MAGENTA)

rng = random.Random(7)
HOSTS = [["alpha", "12ms", "ok"], ["beta", "48ms", "ok"],
         ["gamma", "230ms", "slow"], ["delta", "-", "down"]]
history = [0.0] * 200
log = ["boot ok"]
table_state = ListState(0)
tree = Tree([TreeNode("sessions", [TreeNode("alpha"),
                                   TreeNode("beta", [TreeNode("job-1"), TreeNode("job-2")])], True)])
st = {"t": 0.0, "next": 0.0}
SPARK = " ▁▂▃▄▅▆▇█"


def draw(buf, dt):
    st["t"] += dt
    t = st["t"]
    cpu = min(1.0, max(0.0, 0.5 + 0.35 * math.sin(t * 0.8) + rng.uniform(-0.05, 0.05)))
    mem = 0.4 + 0.1 * math.sin(t * 0.3)
    history.append(cpu)
    del history[0]
    if t > st["next"]:
        st["next"] = t + 1.2
        log.append(f"{t:6.1f}s cpu={cpu * 100:3.0f}% req={rng.randint(100, 999)}")
        del log[:-50]
    rows = Layout.split(buf.area, VERTICAL, [Length(3), Length(3), Min(6)])
    Tabs(["Overview", "Network", "Logs"], int(t / 3) % 3,
         block=Block(ROUNDED, "Telemetri")).render(rows[0], buf)
    g = Layout.split(rows[1], HORIZONTAL, [Percentage(50), Percentage(50)])
    Gauge(cpu, block=Block(ROUNDED, "CPU")).render(g[0], buf)
    Gauge(mem, colors=[Color(60, 120, 255), Color(255, 80, 200)],
          block=Block(ROUNDED, "MEM")).render(g[1], buf)
    body = Layout.split(rows[2], HORIZONTAL, [Percentage(35), Percentage(35), Fill()])
    width = max(1, body[0].width - 2)
    line = "".join(SPARK[min(8, int(v * 8))] for v in history[-width:])
    Paragraph(line, style=Style(fg=GREEN), wrap=False,
              block=Block(ROUNDED, "CPU gecmisi")).render(body[0], buf)
    TableWidget(HOSTS, [Length(8), Length(7), Fill()], header=["host", "ping", "durum"],
                state=table_state, block=Block(ROUNDED, "Hostlar", border_style=Style(fg=YELLOW))
                ).render(body[1], buf)
    right = Layout.split(body[2], VERTICAL, [Percentage(50), Percentage(50)])
    tree.block = Block(ROUNDED, "Oturumlar")
    tree.render(right[0], buf)
    ListWidget(log[-max(1, right[1].height - 2):], ListState(None),
               block=Block(ROUNDED, "Log", border_style=Style(fg=MAGENTA))).render(right[1], buf)


def on_key(k):
    if k == "up":
        table_state.move(-1, len(HOSTS))
    elif k == "down":
        table_state.move(1, len(HOSTS))
    elif k == "enter":
        tree.toggle()
    elif k == "w":
        tree.move(-1)
    elif k == "s":
        tree.move(1)
    return k in ("q", "esc")


if __name__ == "__main__":
    App(draw, on_key).run()
