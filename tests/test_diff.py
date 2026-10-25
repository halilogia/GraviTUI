import io
import re
import unittest

from gravitui import Buffer, DiffWriter, Color, Style


class TestDiff(unittest.TestCase):
    def test_first_frame_clears_and_draws(self):
        w = DiffWriter()
        b = Buffer(4, 2)
        b.put_str(0, 0, "hi")
        out = w.render(b)
        self.assertIn("\x1b[2J", out)
        self.assertIn("\x1b[1;1H", out)
        self.assertIn("hi", out)

    def test_identical_frame_emits_nothing(self):
        w = DiffWriter()
        b = Buffer(4, 2)
        b.put_str(0, 0, "hi")
        w.render(b)
        self.assertEqual(w.render(b), "")

    def test_only_changed_cells(self):
        w = DiffWriter()
        b = Buffer(10, 3)
        b.put_str(0, 0, "aaaaaaaaaa")
        w.render(b)
        b.set_char(4, 2, "Z")
        out = w.render(b)
        self.assertIn("\x1b[3;5H", out)
        self.assertEqual(out.count("Z"), 1)
        self.assertNotIn("a", out)

    def test_adjacent_cells_share_one_cursor_jump(self):
        w = DiffWriter()
        b = Buffer(10, 1)
        w.render(b)
        b.put_str(2, 0, "xyz")
        out = w.render(b)
        self.assertEqual(len(re.findall(r"\x1b\[\d+;\d+H", out)), 1)
        self.assertIn("xyz", out)

    def test_truecolor_and_style_dedup(self):
        w = DiffWriter()
        b = Buffer(5, 1)
        w.render(b)
        st = Style(fg=Color(10, 20, 30))
        b.put_str(0, 0, "abc", st)
        out = w.render(b)
        self.assertEqual(out.count("38;2;10;20;30"), 1)

    def test_resize_forces_full(self):
        w = DiffWriter()
        w.render(Buffer(3, 3))
        self.assertIn("\x1b[2J", w.render(Buffer(4, 3)))

    def test_flush_writes_stream(self):
        s = io.StringIO()
        w = DiffWriter(s)
        b = Buffer(3, 1)
        b.put_str(0, 0, "ok")
        n = w.flush(b)
        self.assertEqual(n, len(s.getvalue()))
        self.assertIn("ok", s.getvalue())


if __name__ == "__main__":
    unittest.main()
