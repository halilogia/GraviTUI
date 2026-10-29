import io
import unittest
from unittest.mock import patch

from gravitui.core.terminal import Terminal, terminal_size, translate_key, enable_windows_vt


class TestTerminal(unittest.TestCase):
    def test_terminal_properties(self):
        term = Terminal()
        w, h = term.size()
        self.assertIsInstance(w, int)
        self.assertIsInstance(h, int)
        self.assertGreater(w, 0)
        self.assertGreater(h, 0)
        self.assertEqual(term.width, w)
        self.assertEqual(term.height, h)

    def test_mocked_terminal_size(self):
        with patch("gravitui.core.terminal.terminal_size", return_value=(120, 40)):
            term = Terminal()
            self.assertEqual(term.width, 120)
            self.assertEqual(term.height, 40)
            self.assertEqual(term.size(), (120, 40))

    def test_terminal_write(self):
        stream = io.StringIO()
        term = Terminal(out=stream)
        term.write("test_output")
        self.assertEqual(stream.getvalue(), "test_output")

    def test_terminal_enter_leave(self):
        stream = io.StringIO()
        term = Terminal(out=stream)
        term.enter()
        self.assertTrue(term._active)
        term.leave()
        self.assertFalse(term._active)
        output = stream.getvalue()
        self.assertIn("\x1b[?1049h", output)  # ALT_ON
        self.assertIn("\x1b[?1049l", output)  # ALT_OFF

    def test_poll_key_no_input(self):
        term = Terminal()
        # Non-blocking poll when no key is pressed returns None
        key = term.poll_key(timeout_ms=5)
        self.assertIsNone(key)

    def test_translate_key(self):
        self.assertEqual(translate_key("\r"), "enter")
        self.assertEqual(translate_key("\x1b"), "esc")
        self.assertEqual(translate_key("\x00", "H"), "up")
        self.assertEqual(translate_key("\xe0", "P"), "down")
        self.assertEqual(translate_key("a"), "a")


if __name__ == "__main__":
    unittest.main()
