"""Pennywise: Space duraklat, R yeniden başlat, M matris stili, Q/Esc çıkış."""
from _path import ROOT  # noqa: F401
from gravitui import App, Layout, Length, Paragraph, Pennywise, Style, VERTICAL, GRAY

portrait = Pennywise()


def draw(buf, dt):
    portrait.tick(dt)
    rows = Layout.split(buf.area, VERTICAL, [Length(1), Length(max(0, buf.height - 2)), Length(1)])
    Paragraph(" Pennywise | Karakter matrisinden beliren yüz | " +
              ("Duraklatıldı" if portrait.paused else "Canlı"),
              Style(fg=GRAY, bg=portrait.BACKGROUND)).render(rows[0], buf)
    portrait.render(rows[1], buf)
    Paragraph(" [Space] duraklat  [R] yeniden belir  [M] matris stili  [Q/Esc] çıkış",
              Style(fg=GRAY, bg=portrait.BACKGROUND)).render(rows[2], buf)


def on_key(key):
    key = key.lower()
    if key == "space":
        portrait.toggle_pause()
    elif key == "r":
        portrait.restart()
    elif key == "m":
        portrait.next_matrix_style()
    return key in ("q", "esc")


if __name__ == "__main__":
    App(draw, on_key, fps=30).run()
