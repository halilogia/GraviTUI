"""BlackHole Aurum Amber: TwoHorizonsWallpaper `AURUM` uyumu, foton halkasi, gokyuzu merceklenmesi, plazma akisi."""
import math
import unittest

from gravitui import BLACK_HOLE_PALETTES, Buffer, BlackHole, Color, Rect, get_black_hole_palette
from gravitui.extensions import black_hole_math as bm
from gravitui.extensions.black_hole_palette import tone_hue, tone_map
from gravitui.extensions.black_hole_plasma import plasma_flow, sample_plasma

PAL = BLACK_HOLE_PALETTES[0]


def lum(c):
    return c.r + c.g + c.b


def render(bh, w=100, h=40):
    buf = Buffer(w, h)
    bh.render(Rect(0, 0, w, h), buf)
    return buf


class TestAurumPalette(unittest.TestCase):
    def test_default_and_aliases(self):
        self.assertEqual(PAL.name, "Aurum Amber")
        self.assertIs(get_black_hole_palette(0), PAL)
        for key in ("aurum", "Aerum", "amber"):
            self.assertIs(get_black_hole_palette(key), PAL)
        self.assertIs(BlackHole().palette, PAL)

    def test_constants_match_wallpaper(self):
        self.assertEqual(PAL.tone, ((0.52, 0.14, 0.03), (1.00, 0.48, 0.12), (1.00, 0.85, 0.52)))
        self.assertEqual((PAL.gain, PAL.dopp, PAL.disk_size), (1.1, 1.05, 8.4))
        self.assertAlmostEqual(PAL.inclination, 90.0 - math.degrees(0.10), places=6)
        self.assertAlmostEqual(PAL.inclination, 84.27, places=2)

    def test_widget_uses_preset_and_restores_it(self):
        bh = BlackHole()
        self.assertAlmostEqual(bh.inclination, 84.27, places=2)
        self.assertEqual(bh.disk_size, 8.4)
        bh.tilt(-30)
        bh.set_disk_size(15)
        bh.apply_preset()
        self.assertEqual((round(bh.inclination, 2), bh.disk_size), (84.27, 8.4))
        self.assertEqual(BlackHole(inclination=60.0, disk_size=10.0).inclination, 60.0)

    def test_hue_follows_shader_mix(self):
        cool, mid, hot = PAL.tone
        self.assertEqual(tone_hue(PAL.tone, 0.0), cool)
        self.assertEqual(tone_hue(PAL.tone, 0.7), mid)
        for a, b in zip(tone_hue(PAL.tone, 1.9), hot):
            self.assertAlmostEqual(a, b)
        self.assertEqual(len(PAL.stops), 5)

    def test_tone_map_is_warm_and_monotonic(self):
        dim, mid, hi = (tone_map(*(c * i for c in PAL.tone[1]), 0.92) for i in (0.2, 1.0, 12.0))
        self.assertLess(lum(dim), lum(mid))
        self.assertLess(lum(mid), lum(hi))
        self.assertGreater(mid.r, mid.g)
        self.assertGreater(mid.g, mid.b)                      # kehribar: R > G > B
        self.assertEqual(tone_map(0, 0, 0, 0.92), Color(0, 0, 0))

    def test_temperature_and_edge(self):
        self.assertAlmostEqual(bm.aurum_temperature(3.0, 3.0), 1.3)
        self.assertAlmostEqual(bm.aurum_temperature(24.0, 3.0), 1.3 * 8 ** -0.75)
        self.assertEqual(bm.aurum_edge(3.0, 3.0, 8.4), 0.0)
        self.assertEqual(bm.aurum_edge(8.4, 3.0, 8.4), 0.0)
        self.assertEqual(bm.aurum_edge(4.2, 3.0, 8.4), 1.0)

    def test_doppler_strength_scales_asymmetry(self):
        weak = bm.doppler_factor(4.0, -4.5, 1.0, 1.0, 1.0)
        self.assertGreater(bm.doppler_factor(4.0, -4.5, 1.0, 1.0, 1.05), weak)
        self.assertEqual(bm.doppler_factor(4.0, -4.5, 1.0), weak)

    def test_frame_is_amber_with_dark_shadow(self):
        buf = render(BlackHole())
        warm = [c.fg for c in (buf.get(x, 20) for x in range(100)) if lum(c.fg) > 200]
        self.assertTrue(warm)
        self.assertTrue(all(c.r >= c.g >= c.b for c in warm))
        self.assertLess(lum(buf.get(50, 15).fg), 30)          # golge

    def test_all_palettes_render_and_cycle(self):
        bh = BlackHole()
        for _ in BLACK_HOLE_PALETTES:
            buf = render(bh, 60, 20)
            self.assertGreater(sum(1 for row in buf.cells for c in row if c.char != " "), 60 * 20 * 0.9)
            bh.next_palette()
        self.assertIs(bh.palette, PAL)


class TestPhotonRingAndSky(unittest.TestCase):
    def test_deflection_limits(self):
        self.assertTrue(math.isinf(bm.deflection_angle(bm.CRIT_B)))
        e = 0.0005
        bozza = -math.log(e) + math.log(216 * (7 - 4 * math.sqrt(3))) - math.pi
        self.assertAlmostEqual(bm.deflection_angle(bm.CRIT_B * (1 + e)), bozza, delta=0.02)
        self.assertAlmostEqual(bm.deflection_angle(200.0), 2 / 200.0, delta=1e-3)
        vals = [bm.deflection_angle(bm.CRIT_B * (1 + 0.01 * 1.3 ** k)) for k in range(25)]
        self.assertTrue(all(a > b for a, b in zip(vals, vals[1:])))   # b buyudukce sapma azalir
        self.assertAlmostEqual(bm.deflection_angle(10.0, 1.0), bm.deflection_angle(20.0, 2.0))

    def test_sky_angle(self):
        self.assertLessEqual(abs(bm.sky_angle(bm.CRIT_B * 1.3, 0.1)), math.pi)
        self.assertLess(bm.sky_angle(10.0, 0.05), 0.0)               # guclu merceklenme: eksenin karsi tarafi
        self.assertAlmostEqual(bm.sky_angle(500.0, 0.3), 0.3 - 2 / 500.0, delta=1e-3)
        self.assertTrue(math.isinf(bm.sky_angle(1.0, 0.1)))

    def test_ring_is_thin_and_resolution_independent(self):
        for px in (0.05, 0.2, 0.5):
            self.assertGreater(bm.photon_ring_weight(bm.CRIT_B + 0.01, px), 0.5)
            self.assertLess(bm.photon_ring_weight(bm.CRIT_B + 4.0 * px, px), 0.02)
            self.assertEqual(bm.photon_ring_weight(bm.CRIT_B - px, px), 0.0)
        self.assertGreater(bm.photon_ring_weight(bm.CRIT_B - 0.1, 0.5), 0.0)   # golge kenarinda kenar yumusatma

    def test_ring_glows_at_shadow_edge(self):
        buf = render(BlackHole(inclination=30.0))
        lit = [lum(buf.get(x, 20).fg) for x in range(100)]
        self.assertLess(lit[50], 60)                                  # merkez karanlik
        self.assertGreater(max(lit[30:50]), 200)                      # kenarda parlak halka


class TestPlasmaFlow(unittest.TestCase):
    def test_range_and_no_jump_over_reset_period(self):
        prev = None
        for k in range(300):
            v = plasma_flow(1.8, 0.7, 0.4, 0.55, 0.1 * k)
            self.assertTrue(0.0 <= v <= 1.0)
            if prev is not None:
                self.assertLess(abs(v - prev), 0.35)                  # akis-haritasi sifirlamasinda atlama yok
            prev = v

    def test_periodic_static_and_animated(self):
        self.assertAlmostEqual(sample_plasma(2.0, 0.3), sample_plasma(2.0, 0.3 + 2 * math.pi), places=9)
        self.assertEqual(plasma_flow(2.0, 1.0, 0.3, 0.0, 5.0), plasma_flow(2.0, 1.0, 0.3, 0.0, 17.0))  # spin=0
        a = [plasma_flow(1.2, 0.01 * k, 1.0, 0.55, 4.0) for k in range(60)]
        b = [plasma_flow(1.2, 0.01 * k, 1.0, 0.55, 8.0) for k in range(60)]
        self.assertNotEqual(a, b)

    def test_differential_rotation(self):
        # Ic halka (r_in) dis halkadan hizli doner: ayni surede farkli azimut kaymasi -> farkli faz.
        inner = [plasma_flow(1.0, 0.1 * k, 1.0, 1.0, 3.0) for k in range(60)]
        outer = [plasma_flow(1.0, 0.1 * k, 0.2, 1.0, 3.0) for k in range(60)]
        self.assertNotEqual(inner, outer)
        self.assertGreater(bm.disk_omega(3.0, 3.0), bm.disk_omega(8.4, 3.0))


if __name__ == "__main__":
    unittest.main()
