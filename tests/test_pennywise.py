"""Pennywise animasyon ve Buffer sınır sözleşmesi testleri."""
import importlib.util
from pathlib import Path
import sys
import unittest

from gravitui import Buffer, Pennywise, Rect, Style, Color


class TestPennywise(unittest.TestCase):
    def test_reveal_pause_restart_and_invalid_time(self):
        face = Pennywise()
        self.assertEqual(face.reveal, 0)
        face.tick(5)
        self.assertEqual(face.reveal, 1)
        face.toggle_pause()
        face.tick(3)
        self.assertEqual(face.time, 5)
        face.restart()
        self.assertEqual(face.time, 0)
        face.toggle_pause()
        face.tick(12)
        self.assertEqual(face.reveal, 0)
        for dt in (-1, float('inf'), float('nan')):
            with self.assertRaises(ValueError):
                face.tick(dt)

    def test_eyes_precede_face(self):
        face = Pennywise()
        self.assertGreater(face._portrait(0.20, -0.185)[1], 0.5)
        self.assertEqual(face._portrait(0, -0.5)[1], 0)
        face.tick(6)
        self.assertGreater(face._portrait(0, -0.5)[1], 0.5)

    def test_clipping_including_negative_origin(self):
        for area in (Rect(8, 4, 50, 20), Rect(-12, -5, 50, 20), Rect(60, 25, 50, 20)):
            buf = Buffer(80, 30)
            buf.fill(buf.area, '!', Style(fg=Color(1, 2, 3)))
            before = buf.copy()
            face = Pennywise()
            face.tick(6)
            face.render(area, buf)
            self.assertNotEqual(buf.cells, before.cells)
            for y in range(buf.height):
                for x in range(buf.width):
                    if not area.contains(x, y):
                        self.assertEqual(buf.get(x, y), before.get(x, y))

    def test_small_empty_and_offscreen(self):
        face = Pennywise()
        for w, h in ((0, 0), (1, 1), (11, 5), (80, 24)):
            face.render(Rect(0, 0, w, h), Buffer(w, h))
        buf = Buffer(20, 10)
        face.render(Rect(30, 30, 40, 20), buf)
        self.assertEqual(buf.cells, Buffer(20, 10).cells)

    def test_deterministic_render_animation_and_modes(self):
        face = Pennywise(seed=7)
        a, b = Buffer(100, 40), Buffer(100, 40)
        face.tick(6)
        face.render(a.area, a)
        face.render(b.area, b)
        self.assertEqual(a.cells, b.cells)
        self.assertGreater(sum(c.fg.r > 60 for row in a.cells for c in row if c.fg), 100)
        face.tick(0.2)
        face.render(b.area, b)
        self.assertNotEqual(a.cells, b.cells)
        face.next_matrix_style()
        face.render(b.area, b)
        self.assertTrue(set(''.join(b.to_lines())) <= set(' .:-=+*#%@'))
        face.next_matrix_style()
        self.assertEqual(face.matrix_style, 'matrix')

    def test_demo_controls_and_hub_entry(self):
        root = Path(__file__).resolve().parents[1]
        sys.path.insert(0, str(root / 'examples'))
        try:
            spec = importlib.util.spec_from_file_location('pennywise_demo', root / 'examples/08_pennywise.py')
            demo = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(demo)
        finally:
            sys.path.pop(0)
        demo.on_key('space')
        self.assertTrue(demo.portrait.paused)
        demo.on_key('m')
        self.assertEqual(demo.portrait.matrix_style, 'density')
        self.assertTrue(demo.on_key('esc'))
        for w, h in ((0, 0), (1, 1), (80, 24)):
            demo.draw(Buffer(w, h), 0.1)
        import run_hub
        item = next(it for it in run_hub.ITEMS if it['id'] == 'pennywise')
        self.assertTrue(Path(item['path']).is_file())


if __name__ == '__main__':
    unittest.main()
