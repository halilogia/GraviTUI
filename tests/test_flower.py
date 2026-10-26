"""ProceduralFlower: egriler, yasam dongusu, paletler, render ve ornek kontrolleri."""
import importlib.util
import math
import os
import sys
import unittest

from gravitui import (Buffer, Color, ProceduralFlower, Rect, FlowerPhase, FLOWER_PALETTES,
                      lifecycle, petal_curve, cubic_bezier, polar_point, ease_out_back, get_palette)
from gravitui.extensions.flower_math import PixelCanvas, BrailleLayer, DURATIONS


def drawn(buf):
    return sum(1 for row in buf.cells for c in row if c.char != " ")


def has_braille(lines):
    return any(0x2800 < ord(c) <= 0x28FF for line in lines for c in line)


class TestMath(unittest.TestCase):
    def test_bezier_endpoints(self):
        pts = ((0, 0), (1, 5), (4, 5), (5, 0))
        self.assertEqual(cubic_bezier(*pts, 0.0), (0, 0))
        self.assertEqual(cubic_bezier(*pts, 1.0), (5, 0))

    def test_polar(self):
        x, y = polar_point(10, 10, 5, math.pi / 2)
        self.assertAlmostEqual(x, 10)
        self.assertAlmostEqual(y, 15)

    def test_ease_out_back_overshoots_then_settles(self):
        self.assertAlmostEqual(ease_out_back(0), 0)
        self.assertAlmostEqual(ease_out_back(1), 1)
        self.assertGreater(max(ease_out_back(i / 50) for i in range(51)), 1.0)

    def test_petal_curve(self):
        axis, half = petal_curve(10, 3, 0.0, 0.0, 12)
        self.assertEqual(len(axis), len(half))
        self.assertAlmostEqual(axis[-1][1], -10)  # dik yukari
        self.assertEqual(half[0], 0.0)
        self.assertGreater(max(half), 1.0)
        self.assertLessEqual(max(half), 3.0)
        curled, _ = petal_curve(10, 3, 0.0, 1.0)
        self.assertGreater(curled[-1][0], 0.5)  # curl ucu saga kivirir

    def test_braille_layer(self):
        bl = BrailleLayer(4, 2)
        bl.dot(0, 0, Color(1, 2, 3))
        bl.dot(1, 3, Color(9, 9, 9))
        bl.dot(-1, 0, Color(1, 1, 1))
        bl.dot(99, 0, Color(1, 1, 1))
        self.assertEqual(bl.mask[0], 0x01 | 0x80)
        self.assertEqual(len(bl.mask), 1)

    def test_fill_strip_fills_and_clips(self):
        cv = PixelCanvas(10, 10, Color(0, 0, 0))
        cv.fill_strip([(5, 9), (5, 0), (5, -20)], [2, 2, 2], lambda u, v: Color(255, 0, 0))
        self.assertEqual(cv.px[5 * 10 + 5], Color(255, 0, 0))
        self.assertIsNone(cv.px[5 * 10 + 9])  # x=9, eksenden uzak


class TestLifecycle(unittest.TestCase):
    def test_phase_order(self):
        seen, t = [], 0.0
        while t < sum(DURATIONS) + 1:
            ph, p = lifecycle(t)
            self.assertTrue(0.0 <= p <= 1.0)
            if not seen or seen[-1] != ph:
                seen.append(ph)
            t += 0.1
        self.assertEqual(seen, [FlowerPhase.SPROUT, FlowerPhase.STEM, FlowerPhase.BUD,
                                FlowerPhase.BLOOM, FlowerPhase.FULL])

    def test_boundaries(self):
        self.assertEqual(lifecycle(0), (FlowerPhase.SPROUT, 0.0))
        self.assertEqual(lifecycle(DURATIONS[0])[0], FlowerPhase.STEM)
        self.assertEqual(lifecycle(-5)[0], FlowerPhase.SPROUT)
        self.assertEqual(lifecycle(1e6), (FlowerPhase.FULL, 1.0))


class TestPalettes(unittest.TestCase):
    def test_four_named_palettes(self):
        self.assertEqual([p.name for p in FLOWER_PALETTES],
                         ["Zambak", "Siber Lotus", "Altın Orkide", "Ruh Zambağı"])
        self.assertEqual(get_palette("siber lotus").name, "Siber Lotus")
        with self.assertRaises(ValueError):
            get_palette("yok")

    def test_petal_gradients_are_truecolor(self):
        for p in FLOWER_PALETTES:
            self.assertGreaterEqual(len(p.petal), 3)
            self.assertNotEqual(p.petal[0], p.petal[-1])
            self.assertTrue(all(isinstance(c, Color) for c in p.petal))


class TestWidget(unittest.TestCase):
    def grow(self, f, secs, dt=0.05):
        for _ in range(int(secs / dt)):
            f.update(dt)

    def test_empty_and_tiny_areas(self):
        f = ProceduralFlower(seed=1)
        buf = Buffer(20, 10)
        f.render(Rect(0, 0, 0, 5), buf)
        f.render(Rect(0, 0, 5, 0), buf)
        self.assertEqual(drawn(buf), 0)
        f.age = f.clock = 25.0
        for size in ((1, 1), (3, 2), (8, 4)):
            f.render(Rect(0, 0, *size), Buffer(*size))

    def test_never_writes_outside_area(self):
        f = ProceduralFlower(seed=1)
        self.grow(f, 25)
        buf = Buffer(60, 30)
        f.render(Rect(10, 5, 30, 15), buf)
        for y in range(30):
            for x in range(60):
                if not (10 <= x < 40 and 5 <= y < 20):
                    self.assertEqual(buf.get(x, y).char, " ")

    def test_all_phases_render_and_grow(self):
        counts = {}
        f = ProceduralFlower(seed=3)
        for t in (0.5, 3.5, 7.0, 10.0, 14.0, 25.0):
            f.age = f.clock = t
            buf = Buffer(80, 30)
            f.render(Rect(0, 0, 80, 30), buf)
            counts[t] = drawn(buf)
            self.assertGreater(counts[t], 0)
        self.assertGreater(counts[7.0], counts[0.5])    # sap uzar
        self.assertGreater(counts[25.0], counts[10.0])  # acik zambak tomurcuktan buyuk

    def test_truecolor_cells_and_halfblocks(self):
        f = ProceduralFlower(seed=3)
        f.age = f.clock = 25.0
        buf = Buffer(80, 30)
        f.render(Rect(0, 0, 80, 30), buf)
        self.assertIn("▀", {c.char for row in buf.cells for c in row})
        self.assertTrue(has_braille(buf.to_lines()))  # braille yorunge yaylari
        self.assertTrue(all(c.bg is not None for row in buf.cells for c in row))

    def test_geometry_toggle_changes_output(self):
        a, b = ProceduralFlower(seed=3), ProceduralFlower(seed=3, show_geometry=False)
        for f in (a, b):
            f.age = f.clock = 25.0
        ba, bb = Buffer(80, 30), Buffer(80, 30)
        a.render(Rect(0, 0, 80, 30), ba)
        b.render(Rect(0, 0, 80, 30), bb)
        self.assertNotEqual(ba.to_lines(), bb.to_lines())
        self.assertFalse(has_braille(bb.to_lines()))

    def test_pollen_only_after_bloom_and_toggle(self):
        f = ProceduralFlower(seed=2)
        self.grow(f, 5)
        self.assertEqual(f.pollen, [])
        self.grow(f, 20)
        self.assertGreater(len(f.pollen), 0)
        self.assertLessEqual(len(f.pollen), 160)
        g = ProceduralFlower(seed=2, show_pollen=False)
        self.grow(g, 25)
        self.assertEqual(g.pollen, [])

    def test_pause_restart_speed_palette(self):
        f = ProceduralFlower(seed=1)
        f.update(1.0)
        f.toggle_pause()
        f.update(5.0)
        self.assertAlmostEqual(f.age, 1.0)
        f.toggle_pause()
        f.adjust_speed(2.0)
        f.update(1.0)
        self.assertAlmostEqual(f.age, 3.0)
        self.assertEqual(f.adjust_speed(1000), 8.0)
        self.assertEqual(f.adjust_speed(1e-9), 0.1)
        f.restart()
        self.assertEqual((f.age, f.phase_info[0]), (0.0, FlowerPhase.SPROUT))
        names = [f.next_palette().name for _ in range(4)]
        self.assertEqual(names[-1], "Zambak")
        self.assertEqual(len(set(names)), 4)

    def test_deterministic_with_seed(self):
        out = []
        for _ in range(2):
            f = ProceduralFlower(seed=9)
            self.grow(f, 22)
            buf = Buffer(60, 24)
            f.render(Rect(0, 0, 60, 24), buf)
            out.append(buf.to_lines())
        self.assertEqual(out[0], out[1])

    def test_example_keys(self):
        ex = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "examples")
        sys.path.insert(0, ex)
        spec = importlib.util.spec_from_file_location("ex05", os.path.join(ex, "05_procedural_flower.py"))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        fl = mod.flower
        mod.on_key("space")
        self.assertTrue(fl.paused)
        mod.on_key("space")
        mod.on_key("g")
        mod.on_key("p")
        self.assertFalse(fl.show_geometry or fl.show_pollen)
        before = fl.palette
        mod.on_key("C")
        self.assertNotEqual(fl.palette, before)
        sp = fl.speed
        mod.on_key("+")
        mod.on_key("-")
        self.assertAlmostEqual(fl.speed, sp)
        mod.draw(Buffer(100, 30), 0.1)
        mod.on_key("r")
        self.assertEqual(fl.age, 0.0)
        self.assertTrue(mod.on_key("q"))
        self.assertTrue(mod.on_key("esc"))


if __name__ == "__main__":
    unittest.main()
