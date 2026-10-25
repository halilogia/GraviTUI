import random
import unittest

from gravitui import (Buffer, Rect, Block, ALL, ROUNDED, DOUBLE, NONE, CENTER, RIGHT, Paragraph,
                      Line, Span, Style, Color, ListWidget, ListState, TableWidget, Length, Fill,
                      Gauge, Tabs, Popup, TileMap, Tile, Tree, TreeNode, ParticleFX)
from gravitui.extensions import shake_buffer, glitch_buffer
from gravitui.widgets import wrap_line


def render(widget, w, h):
    b = Buffer(w, h)
    widget.render(b.area, b)
    return b


class TestBlock(unittest.TestCase):
    def test_borders(self):
        for kind, tl in ((ALL, "┌"), (ROUNDED, "╭"), (DOUBLE, "╔")):
            self.assertEqual(render(Block(kind), 6, 3).get(0, 0).char, tl)

    def test_none_and_inner(self):
        blk = Block(NONE, padding=(1, 1, 1, 1))
        self.assertEqual(blk.inner(Rect(0, 0, 10, 10)), Rect(1, 1, 8, 8))
        self.assertEqual(render(blk, 4, 4).to_lines()[0], "    ")
        self.assertEqual(Block(ALL).inner(Rect(0, 0, 10, 5)), Rect(1, 1, 8, 3))

    def test_title_alignment(self):
        self.assertIn(" Hi ", render(Block(ALL, "Hi"), 12, 3).to_lines()[0])
        self.assertTrue(render(Block(ALL, "Hi", RIGHT), 12, 3).to_lines()[0].endswith(" Hi ┐"))
        line = render(Block(ALL, "Hi", CENTER), 12, 3).to_lines()[0]
        self.assertEqual(line.index(" Hi "), 4)

    def test_tiny_area_no_crash(self):
        self.assertNotIn("L", render(Block(ALL, "Long title"), 2, 1).to_lines()[0])
        self.assertEqual(len(render(Block(ALL, "Long title"), 1, 1).to_lines()[0]), 1)


class TestParagraph(unittest.TestCase):
    def test_wrap(self):
        lines = [x.plain() for x in wrap_line(Line.of("hello brave new world"), 11)]
        self.assertEqual(lines, ["hello brave", "new world"])

    def test_long_word_split(self):
        lines = [x.plain() for x in wrap_line(Line.of("abcdefghij"), 4)]
        self.assertEqual(lines, ["abcd", "efgh", "ij"])

    def test_align(self):
        self.assertEqual(render(Paragraph("ab", align=CENTER), 6, 1).to_lines()[0], "  ab  ")
        self.assertEqual(render(Paragraph("ab", align=RIGHT), 6, 1).to_lines()[0], "    ab")

    def test_spans_keep_color(self):
        red = Style(fg=Color(255, 0, 0))
        p = Paragraph([Line([Span("ab", red), Span("cd")])])
        b = render(p, 6, 1)
        self.assertEqual(b.get(1, 0).fg, Color(255, 0, 0))
        self.assertIsNone(b.get(2, 0).fg)

    def test_multiline_and_block(self):
        b = render(Paragraph("a\nb", block=Block(ALL)), 5, 4)
        self.assertEqual(b.to_lines()[1][1], "a")
        self.assertEqual(b.to_lines()[2][1], "b")

    def test_scroll(self):
        self.assertEqual(render(Paragraph("a\nb\nc", scroll=1), 3, 1).to_lines()[0], "b  ")


class TestListTable(unittest.TestCase):
    def test_list_selection_and_scroll(self):
        st = ListState(selected=5)
        b = render(ListWidget([f"i{i}" for i in range(10)], st), 8, 3)
        self.assertEqual(st.offset, 3)
        self.assertTrue(b.to_lines()[2].startswith("> i5"))

    def test_state_move_clamps(self):
        st = ListState(0)
        st.move(-1, 3)
        self.assertEqual(st.selected, 0)
        st.move(10, 3)
        self.assertEqual(st.selected, 2)

    def test_table(self):
        t = TableWidget([["a", "1"], ["bb", "22"]], [Length(4), Fill()], header=["N", "V"],
                        state=ListState(1))
        b = render(t, 10, 3)
        lines = b.to_lines()
        self.assertTrue(lines[0].startswith("N    V"))
        self.assertTrue(lines[2].startswith("bb   22"))
        self.assertTrue(b.get(0, 2).style.bold)


class TestGaugeTabsPopup(unittest.TestCase):
    def test_gauge_fill(self):
        b = render(Gauge(0.5, label=""), 10, 1)
        filled = [b.get(x, 0).bg for x in range(10)]
        self.assertEqual(sum(1 for c in filled if c != Color(50, 50, 60)), 5)

    def test_gauge_label_default(self):
        self.assertIn("50%", render(Gauge(0.5), 10, 1).to_lines()[0])

    def test_gauge_clamps(self):
        self.assertEqual(Gauge(5).ratio, 1.0)
        self.assertEqual(Gauge.percent(25).ratio, 0.25)

    def test_tabs(self):
        b = render(Tabs(["A", "B"], selected=1), 12, 1)
        self.assertEqual(b.to_lines()[0].strip(), "A │ B")
        self.assertTrue(b.get(5, 0).style.underline)

    def test_popup_centered(self):
        p = Popup(Paragraph("hi"), 8, 3, title="T")
        b = render(p, 20, 7)
        self.assertEqual(p.popup_area(Rect(0, 0, 20, 7)), Rect(6, 2, 8, 3))
        self.assertEqual(b.get(6, 2).char, "╭")
        self.assertEqual(b.get(7, 3).char, "h")


class TestExtensions(unittest.TestCase):
    def test_tilemap_bfs(self):
        m = TileMap(5, 3, layers=1)
        floor, wall = Tile("."), Tile("#", walkable=False)
        m.fill_rect(Rect(0, 0, 5, 3), floor)
        for y in (0, 1):
            m.set_tile(2, y, wall)
        path = m.find_path((0, 0), (4, 0))
        self.assertEqual(path[0], (0, 0))
        self.assertEqual(path[-1], (4, 0))
        self.assertEqual(len(path), 9)  # duvarin altindan dolanir
        m.set_tile(2, 2, wall)
        self.assertIsNone(m.find_path((0, 0), (4, 0)))
        self.assertIsNone(m.find_path((0, 0), (2, 1)))

    def test_tilemap_render_layers(self):
        m = TileMap(3, 1)
        m.set_tile(0, 0, Tile("."), 0)
        m.set_tile(0, 0, Tile("@"), 1)
        self.assertEqual(render(m, 3, 1).get(0, 0).char, "@")

    def test_tree(self):
        t = Tree([TreeNode("root", [TreeNode("a"), TreeNode("b", [TreeNode("c")])])])
        self.assertEqual(len(t.visible()), 1)
        t.expand()
        self.assertEqual(len(t.visible()), 3)
        t.move(2)
        t.toggle()
        self.assertEqual([n.label for n, _ in t.visible()], ["root", "a", "b", "c"])
        t.collapse()
        t.selected = 0
        t.collapse()
        self.assertEqual(len(t.visible()), 1)
        t.toggle()
        self.assertIn("▼ root", render(t, 20, 4).to_lines()[0])

    def test_particles_lifecycle(self):
        fx = ParticleFX(seed=1)
        fx.burst(5, 5, 20, colors=[Color(255, 0, 0)], life=0.5)
        self.assertEqual(len(fx.particles), 20)
        b = render(fx, 12, 12)
        self.assertTrue(any(c.char != " " for row in b.cells for c in row))
        fx.update(1.0)
        self.assertEqual(fx.particles, [])

    def test_shake_and_glitch(self):
        b = Buffer(4, 2)
        b.put_str(0, 0, "abcd")
        shake_buffer(b, 1, 1)
        self.assertEqual(b.to_lines(), ["    ", " abc"])
        b.put_str(0, 0, "wxyz")
        glitch_buffer(b, 1.0, random.Random(0))
        self.assertEqual(sorted(b.to_lines()[0]), sorted("wxyz"))

    def test_fx_shake_resets(self):
        fx = ParticleFX(seed=2)
        fx.shake(3, 0.1)
        fx.update(0.05)
        fx.update(0.1)
        self.assertEqual(fx.shake_offset, (0, 0))


if __name__ == "__main__":
    unittest.main()
