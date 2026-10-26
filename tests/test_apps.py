"""GraviTUI Monorepo Apps Suite Unit Tests."""
import os
import random
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import apps.rpg_dice
import apps.office_manager
import apps.monopoly

from apps.rpg_dice.mechanics import roll_check, RollMode, DICE_TYPES, CheckResult
from apps.rpg_dice.dice_engine import build_shape
from apps.office_manager.simulation import Simulation, UPGRADES
from apps.office_manager.worker import Worker, State, Role
from apps.monopoly.board_data import TILES, Group, GROUP_RGB, Kind
from apps.monopoly.monopoly_game import Game


class TestRpgDiceApp(unittest.TestCase):
    def test_dice_types(self):
        self.assertIn(20, DICE_TYPES)
        self.assertIn(100, DICE_TYPES)

    def test_roll_check(self):
        res = roll_check(20, 15, RollMode.NORMAL, [], random.Random(42))
        self.assertIsInstance(res, CheckResult)
        self.assertTrue(1 <= res.natural <= 20)

    def test_build_shape(self):
        shape = build_shape(20)
        self.assertEqual(len(shape.faces), 20)
        self.assertGreater(len(shape.verts), 0)


class TestOfficeManagerApp(unittest.TestCase):
    def test_simulation_init(self):
        sim = Simulation(seed=123)
        self.assertEqual(len(sim.workers), 6)
        self.assertGreater(len(sim.projects), 0)

    def test_worker_state(self):
        sim = Simulation(seed=123)
        w = sim.workers[0]
        self.assertIn(w.state.name, ["WORKING", "COFFEE_RUN", "LOUNGE", "SLEEPING", "STRESSED"])

    def test_upgrades_exist(self):
        self.assertGreater(len(UPGRADES), 0)


class TestMonopolyApp(unittest.TestCase):
    def test_tiles_count(self):
        self.assertEqual(len(TILES), 40)
        self.assertEqual(TILES[0].kind, Kind.GO)
        self.assertEqual(TILES[10].kind, Kind.JAIL)

    def test_property_groups(self):
        self.assertIn(Group.ORANGE, GROUP_RGB)
        self.assertIn(Group.DARK_BLUE, GROUP_RGB)

    def test_game_init(self):
        game = Game([("Player 1", False), ("Player 2", False)], seed=42)
        self.assertEqual(len(game.players), 2)
        self.assertEqual(game.players[0].cash, 1500)
        self.assertEqual(game.current, 0)
        self.assertEqual(game.round_no, 1)
        self.assertFalse(game.over)


if __name__ == "__main__":
    unittest.main()
