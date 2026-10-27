"""Ornekleri headless calistirip her karenin hatasiz cizildigini dogrular."""
import importlib.util
import os
import sys
import unittest

from gravitui import Buffer

EX = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "examples")


def load(name):
    sys.path.insert(0, EX)
    spec = importlib.util.spec_from_file_location("ex_" + name, os.path.join(EX, name + ".py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestExamples(unittest.TestCase):
    def test_all_examples_draw(self):
        for name in ("01_hello_ratatui", "02_3d_polyhedron", "03_dashboard", "04_office_mini",
                     "05_procedural_flower", "06_cyber_eye", "07_interstellar_black_hole"):
            mod = load(name)
            for size in ((80, 24), (120, 40), (10, 4)):
                buf = Buffer(*size)
                for _ in range(5):
                    buf.clear()
                    mod.draw(buf, 0.05)
                self.assertTrue(any(c.char != " " for row in buf.cells for c in row), name)
            for key in ("up", "down", "enter", "x", "g", "space", "q"):
                if hasattr(mod, "on_key"):
                    mod.on_key(key)


if __name__ == "__main__":
    unittest.main()
