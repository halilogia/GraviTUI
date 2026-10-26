"""CyberEye: kure analitigi, kapaklar, iris, shader ve widget render testleri."""
import unittest

from gravitui import Buffer, CyberEye, EyePalette, EYE_PALETTES, Rect, get_eye_palette
from gravitui.extensions.eye_math import (CYBER_POOLS, DENSITY_RAMP, blink_closure, eyelid_bounds,
                                          glyph_for, iris_center, iris_intensity, pupil_radius,
                                          shade_color, shade_curvature, sphere_normal, sphere_z)


def drawn(buf):
    return sum(1 for row in buf.cells for c in row if c.char != " ")


def lum(c):
    return c.r + c.g + c.b


class TestSphere(unittest.TestCase):
    def test_z_equation(self):
        self.assertAlmostEqual(sphere_z(3, 4, 5), 0.0)
        self.assertAlmostEqual(sphere_z(0, 0, 5), 5.0)
        self.assertIsNone(sphere_z(4, 4, 5))

    def test_normal_unit_and_shading(self):
        n = sphere_normal(1.0, 2.0, 5.0)
        self.assertAlmostEqual(sum(c * c for c in n), 1.0)
        self.assertGreater(shade_curvature(sphere_normal(0, 0, 5)), shade_curvature(sphere_normal(4.9, 0, 5)))


class TestLids(unittest.TestCase):
    def test_parabola(self):
        self.assertEqual(eyelid_bounds(0.0, 10, 8), (-10, 8))
        self.assertIsNone(eyelid_bounds(1.0, 10, 8))
        self.assertAlmostEqual(eyelid_bounds(0.5, 10, 8)[0], -7.5)

    def test_blink_curve(self):
        self.assertEqual(blink_closure(0.0), 0.0)
        self.assertAlmostEqual(blink_closure(0.35), 1.0)
        self.assertAlmostEqual(blink_closure(1.0), 0.0)
        top, bot = eyelid_bounds(0.0, 10, 8, closure=1.0)
        self.assertGreater(top, -1.0)
        self.assertLessEqual(top, bot)


class TestIris(unittest.TestCase):
    def test_gaze_moves_center(self):
        x0, _, s0 = iris_center(0, 0, 40, 12)
        x1, y1, s1 = iris_center(1, -1, 40, 12)
        self.assertEqual(x0, 0)
        self.assertGreater(x1, 0)
        self.assertLess(y1, 0)
        self.assertLess(s1, s0)  # kenara bakista iris yatayda kisalir

    def test_pupil_dilation_and_fibers(self):
        self.assertGreater(pupil_radius(10, 1.0), pupil_radius(10, 0.0))
        self.assertLess(iris_intensity(0.1, 0.0, 0.4), 0.1)
        vals = {round(iris_intensity(0.6, a / 10, 0.3), 3) for a in range(60)}
        self.assertGreater(len(vals), 10)  # radyal lifler aciya gore degisir


class TestShader(unittest.TestCase):
    def test_density_ends(self):
        self.assertEqual(glyph_for(0.0, "density"), " ")
        self.assertEqual(glyph_for(1.0, "density"), DENSITY_RAMP[-1])

    def test_cyber_pools_and_determinism(self):
        for v in (0.1, 0.5, 0.99):
            g = glyph_for(v, "cyber", 3, 4, 10)
            self.assertTrue(any(g in p for p in CYBER_POOLS))
        self.assertEqual(glyph_for(0.9, "cyber", 5, 6, 2), glyph_for(0.9, "cyber", 5, 6, 2))

    def test_palettes(self):
        self.assertEqual(len(EYE_PALETTES), 4)
        self.assertIsInstance(get_eye_palette("matrix"), EyePalette)
        self.assertEqual(get_eye_palette("amber").name, EYE_PALETTES[0].name)
        for pal in EYE_PALETTES:
            self.assertGreater(lum(shade_color(1.0, pal)), lum(shade_color(0.0, pal)))


class TestWidget(unittest.TestCase):
    def test_render_and_tiny_area(self):
        eye = CyberEye(seed=1)
        for style in ("cyber", "density"):
            eye.matrix_style = style
            buf = Buffer(80, 24)
            eye.tick(0.016)
            eye.render(Rect(0, 0, 80, 24), buf)
            self.assertGreater(drawn(buf), 300)
        buf = Buffer(5, 2)
        eye.render(Rect(0, 0, 5, 2), buf)
        self.assertEqual(drawn(buf), 0)
        eye.render(Rect(0, 0, 0, 0), Buffer(0, 0))

    def test_render_stays_in_area(self):
        buf = Buffer(60, 20)
        area = Rect(10, 4, 30, 10)
        CyberEye(seed=2).render(area, buf)
        self.assertGreater(drawn(buf), 0)
        for y, row in enumerate(buf.cells):
            for x, c in enumerate(row):
                if c.char != " ":
                    self.assertTrue(area.contains(x, y))

    def test_blink_cycle(self):
        eye = CyberEye(seed=3, auto_gaze=False)
        eye.blink()
        peak = 0.0
        for _ in range(60):
            eye.tick(0.01)
            peak = max(peak, eye.closure)
        self.assertGreater(peak, 0.95)
        self.assertIsNone(eye.blink_t)
        self.assertEqual(eye.closure, 0.0)

    def test_natural_blink_happens(self):
        eye = CyberEye(seed=4, auto_gaze=False)
        seen = False
        for _ in range(400):
            eye.tick(0.02)
            seen = seen or eye.blink_t is not None
        self.assertTrue(seen)

    def test_blink_closes_eye_visually(self):
        eye = CyberEye(seed=8, auto_gaze=False)
        open_buf, shut_buf = Buffer(80, 24), Buffer(80, 24)
        eye.render(Rect(0, 0, 80, 24), open_buf)
        eye.blink_t = 0.35
        eye.render(Rect(0, 0, 80, 24), shut_buf)
        self.assertLess(drawn(shut_buf), drawn(open_buf))

    def test_gaze_converges_and_manual_mode(self):
        eye = CyberEye(seed=5)
        eye.nudge_gaze(0.5, 0.0)
        self.assertFalse(eye.auto_gaze)
        for _ in range(60):
            eye.tick(0.016)
        self.assertAlmostEqual(eye.gx, 0.5, delta=0.05)
        eye.nudge_gaze(5, 5)
        self.assertEqual(eye.target, [1.0, 1.0])

    def test_auto_saccade_moves_target(self):
        eye = CyberEye(seed=6, auto_gaze=True)
        targets = set()
        for _ in range(500):
            eye.tick(0.02)
            targets.add(tuple(eye.target))
        self.assertGreater(len(targets), 3)

    def test_dilation_palette_style_toggle(self):
        eye = CyberEye(seed=7)
        d0 = eye.dilation
        eye.toggle_dilation()
        for _ in range(300):
            eye.tick(0.02)
        self.assertGreater(abs(eye.dilation - d0), 0.2)
        self.assertEqual(len({eye.next_palette().name for _ in range(4)}), 4)
        self.assertNotEqual(eye.next_matrix_style(), eye.next_matrix_style())


if __name__ == "__main__":
    unittest.main()
