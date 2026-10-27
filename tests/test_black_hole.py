"""BlackHole: Schwarzschild analitigi, merceklenme, Doppler, Kepler diski, zaman genlesmesi, paletler, render."""
import math
import unittest

from gravitui import (Buffer, BlackHole, BlackHolePalette, BLACK_HOLE_PALETTES, Rect, get_black_hole_palette)
from gravitui.extensions import black_hole_math as bm


def drawn(buf):
    return sum(1 for row in buf.cells for c in row if c.char != " ")


def lum(c):
    return c.r + c.g + c.b


class TestSchwarzschild(unittest.TestCase):
    def test_radii(self):
        self.assertAlmostEqual(bm.schwarzschild_radius(1.0), 2.0)
        rs = 2.0
        self.assertAlmostEqual(bm.photon_sphere_radius(rs), 1.5 * rs)
        self.assertAlmostEqual(bm.isco_radius(rs), 3 * rs)
        self.assertAlmostEqual(bm.shadow_radius(1.0), 3 * math.sqrt(3) / 2)

    def test_km(self):
        self.assertAlmostEqual(bm.schwarzschild_radius_km(1.0), 2.9532e8, delta=1e5)


class TestTimeDilation(unittest.TestCase):
    def test_static_and_orbital(self):
        self.assertEqual(bm.time_dilation(1.0, 1.0), 0.0)
        self.assertAlmostEqual(bm.time_dilation(4.0, 1.0), math.sqrt(0.75))
        self.assertAlmostEqual(bm.orbital_lorentz_factor(3.0, 1.0), math.sqrt(2 / 1.5))
        self.assertTrue(math.isinf(bm.orbital_lorentz_factor(1.5, 1.0)))
        self.assertAlmostEqual(bm.lorentz_factor(0.6), 1.25)

    def test_miller(self):
        self.assertAlmostEqual(bm.miller_years_per_hour(1.0), 7.0, places=3)
        self.assertGreater(bm.miller_years_per_hour(2.0), bm.miller_years_per_hour(1.0))
        self.assertGreater(bm.miller_orbit_radius(1.0), bm.photon_sphere_radius(2.0))


class TestDoppler(unittest.TestCase):
    def test_left_blue_right_red(self):
        left = bm.doppler_factor(4.0, -4.5, 1.0)
        right = bm.doppler_factor(4.0, 4.5, 1.0)
        self.assertGreater(left, 1.0)
        self.assertLess(right, 1.0)
        self.assertGreater(bm.relativistic_beaming(left), bm.relativistic_beaming(right) * 4)

    def test_face_on_symmetric(self):
        self.assertAlmostEqual(bm.doppler_factor(4.0, -3.0, 0.0), bm.doppler_factor(4.0, 3.0, 0.0))

    def test_range(self):
        g_min, g_max = bm.doppler_range(1.0)
        self.assertLess(g_min, 1.0)
        self.assertGreater(g_max, 1.0)


class TestKepler(unittest.TestCase):
    def test_omega_law(self):
        self.assertAlmostEqual(bm.disk_omega(4.0, 1.0) / bm.disk_omega(1.0, 1.0), 4.0 ** -1.5)
        self.assertGreater(bm.keplerian_omega(3.0), bm.keplerian_omega(9.0))

    def test_temperature_and_turbulence(self):
        peak = max(bm.disk_temperature(3.0 * (1 + 0.02 * k), 3.0) for k in range(1, 300))
        self.assertAlmostEqual(peak, 1.0, places=2)
        self.assertLess(bm.disk_temperature(30.0, 3.0), bm.disk_temperature(4.5, 3.0))
        vals = [bm.plasma_turbulence(1 + 0.05 * k, 0.3 * k) for k in range(200)]
        self.assertTrue(all(0.0 <= v <= 1.0 for v in vals))
        self.assertGreater(max(vals) - min(vals), 0.3)


class TestLensing(unittest.TestCase):
    def test_weak_field_is_flat(self):
        self.assertAlmostEqual(bm.lensed_radius(100.0, math.pi / 2), 100.0, delta=1.0)
        self.assertAlmostEqual(bm.lensed_radius(50.0, math.pi / 6), 100.0, delta=2.0)

    def test_bending_makes_far_side_reachable(self):
        # Duz uzayda sweep=pi'ye hic ulasilmaz; merceklenmede kritik b'ye yakin isin sonlu yaricapta ulasir.
        r = bm.lensed_radius(1.3 * bm.CRIT_B, math.pi)
        self.assertIsNotNone(r)
        self.assertGreater(r, 1.0)

    def test_captured_ray(self):
        self.assertIsNone(bm.lensed_radius(1.0, 3 * math.pi))

    def test_arcs_wrap_shadow(self):
        for inc in (20, 60, 85):
            up, low = bm.arc_height(4.0, inc, True), bm.arc_height(4.0, inc, False)
            self.assertGreater(up, bm.CRIT_B)
            self.assertGreater(low, bm.CRIT_B)
            self.assertLess(up, 8.0)
        # Kenardan bakista ust/alt yaylar simetrik; yatik bakista ust yay daha yuksek.
        self.assertAlmostEqual(bm.arc_height(4.0, 89, True), bm.arc_height(4.0, 89, False), delta=0.1)
        self.assertGreater(bm.arc_height(4.0, 30, True), bm.arc_height(4.0, 30, False))

    def test_crossings_front_and_back(self):
        near = bm.disk_crossings(0.0, -4.0, 80)      # golgenin altindaki on disk
        far = bm.disk_crossings(0.0, 3.8, 80)        # golgenin ustundeki merceklenmis arka disk
        self.assertEqual(near[0][0], 0)
        self.assertGreater(near[0][1], 3.0)
        self.assertTrue(far and far[0][1] > 1.0)
        self.assertEqual(bm.disk_crossings(0.0, 0.0, 80), [])


class TestPalettes(unittest.TestCase):
    def test_four_named_palettes(self):
        names = [p.name for p in BLACK_HOLE_PALETTES]
        self.assertGreaterEqual(len(names), 4)
        for n in ("Gargantua Gold", "Hawking Blue", "Crimson Singularity", "Cyber Matrix"):
            self.assertIn(n, names)
            self.assertIsInstance(get_black_hole_palette(n.split()[0]), BlackHolePalette)

    def test_stops_brighten(self):
        for p in BLACK_HOLE_PALETTES:
            self.assertLess(lum(p.stops[0]), lum(p.stops[-1]))
        with self.assertRaises(KeyError):
            get_black_hole_palette("yok")


class TestWidget(unittest.TestCase):
    def render(self, bh, w=60, h=20):
        buf = Buffer(w, h)
        bh.render(Rect(0, 0, w, h), buf)
        return buf

    def test_halfblock_render(self):
        buf = self.render(BlackHole())
        self.assertGreater(drawn(buf), 60 * 20 * 0.9)
        self.assertEqual(buf.get(30, 10).char, "▀")

    def test_ascii_mode_and_toggle(self):
        bh = BlackHole(mode="ascii")
        self.assertGreater(drawn(self.render(bh)), 100)
        self.assertEqual(bh.next_mode(), "halfblock")

    def test_doppler_left_brighter(self):
        bh = BlackHole(inclination=85.0)
        left, right = self.side_light(self.render(bh, 80, 30))
        self.assertGreater(left, right)
        bh.toggle_doppler()
        l2, r2 = self.side_light(self.render(bh, 80, 30))
        self.assertLess(abs(l2 - r2) / (l2 + r2), abs(left - right) / (left + right))

    @staticmethod
    def side_light(buf):
        row = [buf.get(x, 15) for x in range(buf.width)]
        half = buf.width // 2
        return (sum(lum(c.fg) + lum(c.bg) for c in row[:half]), sum(lum(c.fg) + lum(c.bg) for c in row[half:]))

    def test_shadow_is_dark_center(self):
        buf = self.render(BlackHole(inclination=60.0), 80, 30)
        c = buf.get(40, 11)
        self.assertLess(lum(c.fg), 40)

    def test_controls_clamp(self):
        bh = BlackHole()
        bh.tilt(500)
        self.assertLessEqual(bh.inclination, 89.0)
        bh.tilt(-500)
        self.assertEqual(bh.inclination, 0.0)
        bh.rotate(400)
        self.assertAlmostEqual(bh.azimuth, 40.0)
        self.assertEqual(bh.set_mass(99), bh.mass)
        self.assertLessEqual(bh.mass, 2.5)
        self.assertTrue(bh.toggle_pause())

    def test_tick_and_pause(self):
        bh = BlackHole()
        bh.tick(0.1)
        t = bh.time
        self.assertGreater(t, 0.0)
        bh.toggle_pause()
        bh.tick(0.1)
        self.assertEqual(bh.time, t)

    def test_animation_changes_frame(self):
        bh = BlackHole()
        a = self.render(bh)
        bh.tick(0.2)
        b = self.render(bh)
        self.assertNotEqual([c.fg for c in a.cells[8]], [c.fg for c in b.cells[8]])

    def test_telemetry_and_palette_cycle(self):
        bh = BlackHole()
        tm = bh.telemetry()
        self.assertAlmostEqual(tm["photon_sphere"], 1.5 * tm["rs"])
        self.assertAlmostEqual(tm["miller_years_per_hour"], 7.0, places=3)
        self.assertGreater(tm["g_max"], tm["g_min"])
        first = bh.palette
        for _ in BLACK_HOLE_PALETTES:
            bh.next_palette()
        self.assertIs(bh.palette, first)

    def test_small_area_silent(self):
        buf = Buffer(10, 5)
        BlackHole().render(Rect(0, 0, 4, 2), buf)
        self.assertEqual(drawn(buf), 0)

    def test_no_write_outside_area(self):
        buf = Buffer(40, 20)
        BlackHole().render(Rect(5, 5, 20, 8), buf)
        for y in range(20):
            for x in range(40):
                if not (5 <= x < 25 and 5 <= y < 13):
                    self.assertEqual(buf.get(x, y).char, " ")


if __name__ == "__main__":
    unittest.main()
