"""Headless verification: python test_rpg.py   (no terminal needed, standard library only)."""
from __future__ import annotations

import random
import unittest

from rpg_colors import FrameWriter, ScreenBuffer, gradient, lerp
from dice_engine import DiceBody, build_shape, mat_vec, q_matrix
from main import App, buffer_to_text
from mechanics import RollMode, default_modifiers, face_for_value, roll_check

FACE_COUNTS = {4: 4, 6: 6, 8: 8, 10: 10, 12: 12, 20: 20, 100: 10}
VERTS_PER_FACE = {4: 3, 6: 4, 8: 3, 10: 4, 12: 5, 20: 3, 100: 4}


class FakeRng(random.Random):
    """Returns queued values for randint, to test advantage / disadvantage deterministically."""

    def __init__(self, values):
        super().__init__(0)
        self.values = list(values)

    def randint(self, a, b):
        return self.values.pop(0) if self.values else a


class GeometryTests(unittest.TestCase):
    def test_face_counts_and_shapes(self):
        for sides, count in FACE_COUNTS.items():
            shape = build_shape(sides)
            self.assertEqual(len(shape.faces), count, f"d{sides} face count")
            self.assertTrue(all(len(f) == VERTS_PER_FACE[sides] for f in shape.faces), f"d{sides} face size")

    def test_roll_settles_on_requested_face(self):
        for sides in FACE_COUNTS:
            shape = build_shape(sides)
            for value in (1, sides if sides != 100 else 90):
                body = DiceBody(shape, random.Random(sides + value))
                idx = face_for_value(sides, value)
                body.throw(idx)
                for _ in range(300):
                    body.update(1 / 30)
                self.assertTrue(body.settled)
                n = mat_vec(q_matrix(body.q), shape.normals[idx])
                self.assertAlmostEqual(n[2], 1.0, places=4, msg=f"d{sides} face {idx} not facing camera")


class MechanicsTests(unittest.TestCase):
    def test_advantage_disadvantage(self):
        r = roll_check(20, 10, RollMode.ADVANTAGE, [], FakeRng([5, 17]))
        self.assertEqual((r.natural, r.kept_index), (17, 1))
        r = roll_check(20, 10, RollMode.DISADVANTAGE, [], FakeRng([5, 17]))
        self.assertEqual((r.natural, r.kept_index), (5, 0))

    def test_dc_and_modifiers(self):
        mods = default_modifiers()  # +3 ability, +2 proficiency
        r = roll_check(20, 15, RollMode.NORMAL, mods, FakeRng([10]))
        self.assertEqual((r.total, r.success, r.crit), (15, True, None))
        r = roll_check(20, 16, RollMode.NORMAL, mods, FakeRng([10]))
        self.assertFalse(r.success)

    def test_dice_modifiers(self):
        mods = default_modifiers()
        mods[2].enabled = True  # Guidance 1d4
        r = roll_check(20, 15, RollMode.NORMAL, mods, FakeRng([10, 4]))
        self.assertEqual(r.total, 10 + 3 + 2 + 4)

    def test_criticals(self):
        r = roll_check(20, 40, RollMode.NORMAL, default_modifiers(), FakeRng([20]))
        self.assertEqual((r.crit, r.success, r.verdict), ("success", True, "CRITICAL SUCCESS"))
        r = roll_check(20, 1, RollMode.NORMAL, default_modifiers(), FakeRng([1]))
        self.assertEqual((r.crit, r.success, r.verdict), ("failure", False, "CRITICAL FAILURE"))
        self.assertIsNone(roll_check(12, 5, RollMode.NORMAL, [], FakeRng([12])).crit)  # crits are d20 only

    def test_forced_rolls_and_distribution(self):
        rng = random.Random(1)
        self.assertEqual(roll_check(20, 10, RollMode.ADVANTAGE, [], rng, forced=1).natural, 1)
        rolls = [roll_check(20, 10, RollMode.NORMAL, [], rng).natural for _ in range(2000)]
        self.assertTrue(1 in rolls and 20 in rolls and 1 <= min(rolls) <= max(rolls) <= 20)


class RenderTests(unittest.TestCase):
    def run_app(self, keys, seconds, size=(120, 34)):
        app = App(*size, seed=3)
        writer = FrameWriter()
        for k in keys:
            app.handle_key(k)
        frames = []
        for i in range(int(seconds * 30)):
            app.update(1 / 30)
            frames.append(writer.present(app.render()))
        return app, frames

    def test_colors(self):
        self.assertEqual(gradient([(0, 0, 0), (100, 100, 100), (200, 200, 200)], 0.75), (150, 150, 150))
        self.assertEqual(lerp((0, 0, 0), (10, 20, 30), 0.5), (5, 10, 15))

    def test_diff_writer_is_incremental(self):
        w = FrameWriter()
        buf = ScreenBuffer(20, 5)
        first = w.present(buf)
        self.assertIn("\033[2J", first)
        self.assertEqual(w.present(buf), "")
        buf.put(3, 2, "X", (255, 0, 0), (0, 0, 255))
        diff = w.present(buf)
        self.assertIn("38;2;255;0;0", diff)
        self.assertIn("48;2;0;0;255", diff)
        self.assertNotIn("\033[2J", diff)

    def test_every_die_and_mode_renders(self):
        for sides in (20, 12, 10, 8, 6, 4, 100):
            for mode_presses in (0, 1, 2):
                app = App(120, 34, seed=sides)
                app._set_sides(sides)
                for _ in range(mode_presses):
                    app.handle_key("a")
                app.handle_key(" ")
                for _ in range(30 * 8):
                    app.update(1 / 30)
                    app.render()
                self.assertEqual(app.state, "result", f"d{sides} mode {mode_presses}")

    def test_normal_roll_flow(self):
        app, frames = self.run_app([" "], 8)
        self.assertEqual(app.state, "result")
        self.assertEqual(len(app.history), 1)
        self.assertGreater(len(frames[0]), 5000)
        self.assertIn(app.result.verdict, ("SUCCESS", "FAILURE", "CRITICAL SUCCESS", "CRITICAL FAILURE"))

    def test_critical_20_effects(self):
        app = App(120, 34, seed=1)
        app.handle_key("c")
        shaken = False
        for _ in range(30 * 5):
            app.update(1 / 30)
            app.render()
            if app.state in ("reveal", "result"):
                shaken = shaken or app.shake.amp > 1
        self.assertEqual(app.result.crit, "success")
        self.assertTrue(shaken)
        self.assertEqual(app.aura.kind, "gold")
        self.assertGreater(len(app.particles.items), 20)

    def test_critical_1_effects(self):
        app = App(120, 34, seed=2)
        app.handle_key("f")
        for _ in range(30 * 5):
            app.update(1 / 30)
            app.render()
        self.assertEqual(app.result.crit, "failure")
        self.assertEqual(app.aura.kind, "blood")
        self.assertGreater(app.glitch_floor, 0)

    def test_controls(self):
        app = App(120, 34, seed=4)
        app.handle_key("+")
        self.assertEqual(app.dc, 16)
        app.handle_key("-")
        app.handle_key("-")
        self.assertEqual(app.dc, 14)
        app.handle_key("d")
        self.assertEqual(app.sides, 12)
        app.handle_key("a")
        self.assertEqual((app.mode, len(app.bodies)), (RollMode.ADVANTAGE, 2))
        app.handle_key("m")
        app.handle_key("DOWN")
        app.handle_key(" ")
        self.assertFalse(app.mods[1].enabled)
        app.handle_key("\x1b")
        self.assertFalse(app.menu_open)
        self.assertFalse(app.quit)
        app.handle_key("q")
        self.assertTrue(app.quit)

    def test_small_terminal_and_resize(self):
        app = App(60, 20)
        app.update(0.1)
        self.assertIn("too small", buffer_to_text(app.render()))
        app.resize(120, 34)
        app.update(0.1)
        self.assertIn("THE TABLE", buffer_to_text(app.render()))
        self.assertIn("R P G   D I C E", buffer_to_text(app.render()))


if __name__ == "__main__":
    unittest.main(verbosity=2)
