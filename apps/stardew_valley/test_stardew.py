"""Stardew Valley TUI birim testleri (headless; terminal gerektirmez)."""
import os
import random
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from apps.stardew_valley import game as G
from apps.stardew_valley import tools as T
from apps.stardew_valley import town
from apps.stardew_valley.calendar import (DAY_START, DAYS_PER_SEASON, MIDNIGHT, PASSOUT, GameCalendar, Season)
from apps.stardew_valley.crops import CROP_DATABASE, CropState, Stage, crop_by_seed, stage_of
from apps.stardew_valley.farm import FARM_H, FARM_W, Farm, Tile
from apps.stardew_valley.fishing import FishingGame, FishPhase
from apps.stardew_valley.player import Direction, Inventory, Player
from apps.stardew_valley.shipping import ShippingBin


def make_game(seed=7):
    """Başlangıç bölgesini temizlenmiş oyun: oyuncu (5,6), aşağı bakıyor, hedef (5,7) çimen."""
    g = G.Game(seed)
    for y in range(5, 9):
        for x in range(3, 9):
            g.farm.set_tile(x, y, Tile.GRASS)
    g.player.x, g.player.y, g.player.facing = 5, 6, Direction.DOWN
    return g


class TestCalendar(unittest.TestCase):
    def test_start(self):
        c = GameCalendar()
        self.assertEqual((c.season, c.day, c.year, c.minutes), (Season.SPRING, 1, 1, DAY_START))
        self.assertEqual(c.clock_str, "06:00")
        self.assertEqual(c.date_str, "Bahar 1, Yıl 1")

    def test_28_days_then_next_season_then_year(self):
        c = GameCalendar()
        for _ in range(DAYS_PER_SEASON - 1):
            self.assertFalse(c.next_day())
        self.assertEqual((c.season, c.day), (Season.SPRING, 28))
        self.assertTrue(c.next_day())
        self.assertEqual((c.season, c.day, c.year), (Season.SUMMER, 1, 1))
        for _ in range(DAYS_PER_SEASON * 3):
            c.next_day()
        self.assertEqual((c.season, c.day, c.year), (Season.SPRING, 1, 2))

    def test_late_and_passout_events(self):
        c = GameCalendar()
        self.assertEqual(c.advance(MIDNIGHT - DAY_START - 1), [])
        self.assertEqual(c.advance(1), ["late"])
        self.assertTrue(c.is_late)
        self.assertEqual(c.clock_str, "00:00")
        self.assertEqual(c.advance(PASSOUT - MIDNIGHT), ["passout"])
        self.assertEqual(c.clock_str, "02:00")
        self.assertEqual(c.advance(30), [])   # 02:00'den ileri gitmez

    def test_next_day_resets_clock(self):
        c = GameCalendar()
        c.advance(500)
        c.next_day()
        self.assertEqual(c.minutes, DAY_START)


class TestCrops(unittest.TestCase):
    def test_catalog(self):
        self.assertEqual(set(CROP_DATABASE), {"parsnip", "potato", "cauliflower", "strawberry",
                                              "tomato", "corn", "pumpkin", "blue_jazz"})
        for c in CROP_DATABASE.values():
            self.assertGreater(c.days_to_grow, 0)
            self.assertGreater(c.sell_price, 0)
            self.assertTrue(c.seasons)
        self.assertEqual(CROP_DATABASE["parsnip"].days_to_grow, 4)
        self.assertEqual(CROP_DATABASE["strawberry"].regrow_days, 4)
        self.assertEqual(CROP_DATABASE["corn"].seasons, (Season.SUMMER, Season.FALL))

    def test_stage_progression(self):
        d = CROP_DATABASE["parsnip"]
        stages = [stage_of(d, g) for g in range(5)]
        self.assertEqual(stages, [Stage.SEED, Stage.SPROUT, Stage.VEGETATIVE, Stage.BLOOM, Stage.HARVESTABLE])

    def test_grow_stops_when_ready_and_regrow(self):
        s = CropState("strawberry")
        for _ in range(20):
            s.grow()
        self.assertTrue(s.harvestable)
        self.assertEqual(s.growth, 8)
        self.assertTrue(s.harvest())          # tekrar hasat edilebilir
        self.assertFalse(s.harvestable)
        for _ in range(4):
            s.grow()
        self.assertTrue(s.harvestable)
        self.assertFalse(CropState("parsnip").harvest())

    def test_seed_lookup(self):
        self.assertEqual(crop_by_seed("seed:pumpkin").id, "pumpkin")
        self.assertIsNone(crop_by_seed("wood"))


class TestPlayerInventory(unittest.TestCase):
    def test_defaults(self):
        p = Player()
        self.assertEqual((p.energy, p.max_energy, p.gold), (270, 270, 500))
        self.assertEqual(len(p.inventory.slots), 12)
        self.assertEqual(p.selected_slot().item_id, T.HOE)

    def test_hotbar_select(self):
        p = Player()
        p.select(2)
        self.assertEqual(p.selected_slot().item_id, T.WATERING_CAN)
        p.select(9)
        self.assertEqual(p.hotbar_index, 8)
        p.select(0)
        self.assertEqual(p.hotbar_index, 8)

    def test_stacking_and_full(self):
        inv = Inventory()
        self.assertEqual(inv.add(T.WOOD, 1500), 0)       # 999 + 501
        self.assertEqual(inv.count(T.WOOD), 1500)
        self.assertEqual(inv.add(T.HOE), 0)              # alet yığılmaz
        self.assertEqual(inv.add(T.HOE), 0)
        self.assertEqual(inv.free_slots, 8)
        for i in range(8):
            inv.add(T.HOE)                                # her biri ayrı slot
        self.assertEqual(inv.free_slots, 0)
        self.assertFalse(inv.can_add("seed:corn"))
        self.assertEqual(inv.add("seed:corn", 3), 3)

    def test_remove(self):
        inv = Inventory()
        inv.add(T.STONE, 5)
        self.assertFalse(inv.remove(T.STONE, 6))
        self.assertTrue(inv.remove(T.STONE, 5))
        self.assertEqual(inv.free_slots, 12)

    def test_move_blocked_and_turn(self):
        farm = Farm(1)
        p = Player()
        self.assertTrue(p.move(Direction.DOWN, farm))
        self.assertEqual((p.x, p.y), (5, 5))
        p.x, p.y = 5, 4
        self.assertFalse(p.move(Direction.UP, farm))      # çiftlik evi engeli
        self.assertEqual(p.facing, Direction.UP)
        self.assertEqual((p.x, p.y), (5, 4))


class TestFarm(unittest.TestCase):
    def test_layout(self):
        f = Farm(3)
        self.assertEqual((f.width, f.height), (32, 18))
        self.assertEqual((FARM_W, FARM_H), (32, 18))
        for t in (Tile.GRASS, Tile.ROCK, Tile.WOOD, Tile.WEED, Tile.POND, Tile.FARMHOUSE, Tile.SHIPPING_BIN):
            self.assertGreater(f.count(t), 0, t.name)
        self.assertEqual(f.count(Tile.SHIPPING_BIN), 1)
        self.assertTrue(f.walkable(5, 4))
        self.assertFalse(f.walkable(-1, 0))

    def test_advance_night_only_grows_watered_and_dries(self):
        f = Farm(3, generate=False)
        f.set_tile(1, 1, Tile.WATERED)
        f.set_tile(2, 1, Tile.TILLED)
        f.crops[(1, 1)], f.crops[(2, 1)] = CropState("parsnip"), CropState("parsnip")
        grown, _ = f.advance_night()
        self.assertEqual(grown, 1)
        self.assertEqual((f.crops[(1, 1)].growth, f.crops[(2, 1)].growth), (1, 0))
        self.assertEqual(f.tile(1, 1), Tile.TILLED)       # kurudu

    def test_kill_out_of_season(self):
        f = Farm(3, generate=False)
        f.crops[(0, 0)], f.crops[(1, 0)] = CropState("corn"), CropState("parsnip")
        self.assertEqual(f.kill_out_of_season(Season.FALL), 1)
        self.assertIn((0, 0), f.crops)
        self.assertEqual(f.kill_out_of_season(Season.WINTER), 1)
        self.assertFalse(f.crops)


class TestTools(unittest.TestCase):
    def setUp(self):
        self.g = make_game()
        self.rng = random.Random(1)

    def use(self, tool):
        return T.use_tool(tool, self.g.player, self.g.farm, self.rng)

    def test_hoe_tills_grass_and_costs_energy(self):
        r = self.use(T.HOE)
        self.assertTrue(r.ok)
        self.assertEqual(self.g.farm.tile(5, 7), Tile.TILLED)
        self.assertEqual(self.g.player.energy, 268)
        self.assertFalse(self.use(T.HOE).ok)

    def test_watering_can_and_refill(self):
        self.use(T.HOE)
        r = self.use(T.WATERING_CAN)
        self.assertTrue(r.ok)
        self.assertEqual(self.g.farm.tile(5, 7), Tile.WATERED)
        self.assertEqual(self.g.player.water, 39)
        self.g.player.water = 0
        self.g.farm.set_tile(5, 7, Tile.TILLED)
        self.assertFalse(self.use(T.WATERING_CAN).ok)
        self.g.farm.set_tile(5, 7, Tile.POND)
        self.assertTrue(self.use(T.WATERING_CAN).ok)
        self.assertEqual(self.g.player.water, T.WATER_CAPACITY)

    def test_axe_needs_three_hits_and_gives_wood(self):
        self.g.farm.set_tile(5, 7, Tile.WOOD)
        for _ in range(2):
            self.assertTrue(self.use(T.AXE).ok)
            self.assertEqual(self.g.farm.tile(5, 7), Tile.WOOD)
        self.assertTrue(self.use(T.AXE).ok)
        self.assertEqual(self.g.farm.tile(5, 7), Tile.GRASS)
        self.assertGreaterEqual(self.g.player.inventory.count(T.WOOD), 3)
        self.assertEqual(self.g.player.energy, 270 - 12)

    def test_pickaxe_breaks_rock_gives_stone(self):
        self.g.farm.set_tile(5, 7, Tile.ROCK)
        self.use(T.PICKAXE)
        self.assertEqual(self.g.farm.tile(5, 7), Tile.ROCK)
        self.use(T.PICKAXE)
        self.assertEqual(self.g.farm.tile(5, 7), Tile.GRASS)
        self.assertGreaterEqual(self.g.player.inventory.count(T.STONE), 2)

    def test_scythe_clears_weeds_without_energy(self):
        self.g.farm.set_tile(5, 7, Tile.WEED)
        e = self.g.player.energy
        for _ in range(5):                                 # lif şansı için farklı rng akışı
            self.g.farm.set_tile(5, 7, Tile.WEED)
            self.assertTrue(self.use(T.SCYTHE).ok)
        self.assertEqual(self.g.player.energy, e)
        self.assertEqual(self.g.farm.tile(5, 7), Tile.GRASS)
        self.assertGreater(self.g.player.inventory.count(T.FIBER), 0)

    def test_scythe_works_when_exhausted_others_dont(self):
        self.g.player.energy = 0
        self.g.farm.set_tile(5, 7, Tile.WEED)
        self.assertTrue(self.use(T.SCYTHE).ok)
        self.assertFalse(self.use(T.HOE).ok)
        self.assertEqual(self.g.farm.tile(5, 7), Tile.GRASS)

    def test_rod_requires_pond(self):
        self.assertFalse(self.use(T.FISHING_ROD).ok)
        self.g.farm.set_tile(5, 7, Tile.POND)
        r = self.use(T.FISHING_ROD)
        self.assertTrue(r.ok)
        self.assertEqual(r.action, "fish")

    def test_plant_and_season_rules(self):
        self.use(T.HOE)
        p, f = self.g.player, self.g.farm
        self.assertFalse(T.plant_seed("seed:pumpkin", p, f, Season.SPRING).ok)   # mevsim dışı
        self.assertTrue(T.plant_seed("seed:parsnip", p, f, Season.SPRING).ok)
        self.assertEqual(p.inventory.count("seed:parsnip"), 14)
        self.assertFalse(T.plant_seed("seed:parsnip", p, f, Season.SPRING).ok)   # dolu
        self.assertIn((5, 7), f.crops)

    def test_harvest(self):
        p, f = self.g.player, self.g.farm
        f.set_tile(5, 7, Tile.TILLED)
        f.crops[(5, 7)] = CropState("parsnip", 4)
        self.assertTrue(T.harvest_crop(p, f, 5, 7).ok)
        self.assertEqual(p.inventory.count("crop:parsnip"), 1)
        self.assertNotIn((5, 7), f.crops)
        self.assertFalse(T.harvest_crop(p, f, 5, 7).ok)


class TestShippingAndTown(unittest.TestCase):
    def test_settle(self):
        b = ShippingBin()
        self.assertTrue(b.ship("crop:parsnip", 3))
        self.assertTrue(b.ship("crop:pumpkin", 1))
        self.assertFalse(b.ship(T.HOE))                    # aletin satış değeri yok
        self.assertEqual(b.pending_value(), 3 * 35 + 320)
        rep = b.settle()
        self.assertEqual(rep.total, 425)
        self.assertEqual(rep.lines[0].item_id, "crop:pumpkin")   # değere göre azalan
        self.assertTrue(b.is_empty)

    def test_stock_follows_season(self):
        spring = {c.id for c in town.stock(Season.SPRING)}
        self.assertIn("parsnip", spring)
        self.assertNotIn("pumpkin", spring)
        self.assertEqual({c.id for c in town.stock(Season.FALL)}, {"corn", "pumpkin"})
        self.assertEqual(town.stock(Season.WINTER), [])

    def test_buy_and_sell(self):
        p = Player()
        ok, _ = town.buy_seed(p, "potato", 2, Season.SPRING)
        self.assertTrue(ok)
        self.assertEqual((p.gold, p.inventory.count("seed:potato")), (400, 2))
        self.assertFalse(town.buy_seed(p, "pumpkin", 1, Season.SPRING)[0])
        p.gold = 10
        self.assertFalse(town.buy_seed(p, "corn", 1, Season.SUMMER)[0])
        p.inventory.add("crop:cauliflower", 2)
        ok, _ = town.sell_item(p, "crop:cauliflower", 5)
        self.assertTrue(ok)
        self.assertEqual(p.gold, 10 + 2 * int(175 * town.SELL_RATE))
        self.assertFalse(town.sell_item(p, T.HOE, 1)[0])


class TestFishing(unittest.TestCase):
    def test_early_press_loses(self):
        fg = FishingGame(Season.SPRING, random.Random(1))
        fg.press()
        self.assertEqual(fg.phase, FishPhase.LOST)

    def test_bite_timeout_loses(self):
        fg = FishingGame(Season.SPRING, random.Random(1))
        fg.update(10)
        self.assertEqual(fg.phase, FishPhase.BITE)
        fg.update(2)
        self.assertEqual(fg.phase, FishPhase.LOST)

    def test_reel_can_be_won_by_tracking_fish(self):
        fg = FishingGame(Season.SUMMER, random.Random(2))
        fg.update(10)
        fg.press()
        self.assertEqual(fg.phase, FishPhase.REEL)
        for _ in range(4000):
            if fg.done:
                break
            mid = fg.bar + 0.15
            if mid < fg.fish_pos:
                fg.press()
            fg.update(1 / 30)
        self.assertEqual(fg.phase, FishPhase.CAUGHT)

    def test_reel_lost_when_idle(self):
        fg = FishingGame(Season.SUMMER, random.Random(2))
        fg.update(10)
        fg.press()
        fg.fish_pos = fg.target = 0.99
        fg.bar = 0.0
        for _ in range(3000):
            fg.target = 0.99
            fg.update(1 / 30)
            if fg.done:
                break
        self.assertEqual(fg.phase, FishPhase.LOST)


if __name__ == "__main__":
    unittest.main()
