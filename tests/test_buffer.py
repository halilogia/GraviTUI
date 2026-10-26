import io
import unittest

from gravitui import Buffer, Cell, Color, Style, Rect, gradient, translate_key, Terminal


class TestColor(unittest.TestCase):
    def test_hex_roundtrip(self):
        self.assertEqual(Color.from_hex("#ff8000"), Color(255, 128, 0))
        self.assertEqual(Color.from_hex("f80").to_hex(), "#ff8800")

    def test_hsv(self):
        self.assertEqual(Color.from_hsv(0, 1, 1), Color(255, 0, 0))
        h, s, v = Color(0, 255, 0).to_hsv()
        self.assertAlmostEqual(h, 120)

    def test_gradient(self):
        g = gradient([Color(0, 0, 0), Color(255, 255, 255)], 5)
        self.assertEqual(len(g), 5)
        self.assertEqual(g[0], Color(0, 0, 0))
        self.assertEqual(g[-1], Color(255, 255, 255))

    def test_sgr(self):
        s = Style(fg=Color(1, 2, 3), bg=Color(4, 5, 6), bold=True)
        self.assertEqual(s.sgr(), "\x1b[0;1;38;2;1;2;3;48;2;4;5;6m")

    def test_bad_hex(self):
        with self.assertRaises(ValueError):
            Color.from_hex("#12")


class TestBuffer(unittest.TestCase):
    def test_put_str_and_clip(self):
        b = Buffer(5, 2)
        n = b.put_str(3, 0, "abcd")
        self.assertEqual(n, 4)
        self.assertEqual(b.to_lines()[0], "   ab")  # tampon disi kesildi
        b.put_str(0, 1, "xyz", clip=Rect(1, 1, 1, 1))
        self.assertEqual(b.to_lines()[1], " y   ")

    def test_out_of_bounds_safe(self):
        b = Buffer(2, 2)
        b.set_char(-1, 5, "x")
        self.assertEqual(b.get(9, 9), Cell())

    def test_set_style_keeps_char(self):
        b = Buffer(3, 1)
        b.put_str(0, 0, "abc")
        b.set_style(Rect(0, 0, 2, 1), Style(fg=Color(9, 9, 9), bold=True))
        self.assertEqual(b.get(0, 0).char, "a")
        self.assertEqual(b.get(1, 0).fg, Color(9, 9, 9))
        self.assertIsNone(b.get(2, 0).fg)

    def test_fill_and_copy(self):
        b = Buffer(3, 3)
        b.fill(Rect(1, 1, 5, 5), "#")
        c = b.copy()
        b.clear()
        self.assertEqual(c.to_lines(), ["   ", " ##", " ##"])

    def test_translate_key(self):
        self.assertEqual(translate_key("\xe0", "H"), "up")
        self.assertEqual(translate_key("\r"), "enter")
        self.assertEqual(translate_key("q"), "q")
        self.assertEqual(translate_key("\x03"), "ctrl+c")

    def test_set_string_and_terminal_raw_mode(self):
        b = Buffer(6, 1)
        b.set_string(1, 0, "hi")
        self.assertEqual(b.to_lines()[0], " hi   ")
        out = io.StringIO()
        t = Terminal(out)
        t.enable_raw_mode()
        self.assertTrue(t._active)
        t.disable_raw_mode()
        self.assertFalse(t._active)


if __name__ == "__main__":
    unittest.main()
