"""Stardew Valley TUI oyun akışı, girdi ve render testleri (headless)."""
import os
import random
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from gravitui import Buffer
from apps.stardew_valley import game as G
from apps.stardew_valley import tools as T
from apps.stardew_valley.calendar import DAY_START, DAYS_PER_SEASON, MIDNIGHT, PASSOUT, Season
from apps.stardew_valley.crops import CropState
from apps.stardew_valley.farm import Tile
from apps.stardew_valley.fishing import FishingGame, FishPhase
from apps.stardew_valley.player import Direction
from apps.stardew_valley.renderer import SCREEN_H, SCREEN_W, render
from apps.stardew_valley.test_stardew import make_game


class TestGame(unittest.TestCase):
    def test_sleep_full_cycle(self):
        g = make_game()
        p, f, c = g.player, g.farm, g.calendar
        g.handle_key("1")
        g.handle_key("c")                                   # çapa
        g.handle_key("7")
        g.handle_key("c")                                   # tohum ek
        self.assertIn((5, 7), f.crops)
        g.handle_key("2")
        g.handle_key("c")                                   # sula
        self.assertEqual(f.tile(5, 7), Tile.WATERED)
        p.inventory.add("crop:corn", 4)
        p.hotbar_index = 7                                  # 8. slot: mısır yığını
        p.x, p.y, p.facing = 9, 4, Direction.UP             # kutunun altı (9,3)
        g.handle_key("c")
        self.assertEqual(g.bin.items, {"crop:corn": 4})
        gold = p.gold
        p.energy = 10
        c.advance(300)
        s = g.sleep()
        self.assertEqual(f.crops[(5, 7)].growth, 1)         # sulanmış ekin büyüdü
        self.assertEqual(f.tile(5, 7), Tile.TILLED)          # toprak kurudu
        self.assertEqual(p.gold, gold + 200)                 # 4 x 50 satıldı
        self.assertEqual(s.report.total, 200)
        self.assertTrue(g.bin.is_empty)
        self.assertEqual(p.energy, p.max_energy)
        self.assertEqual((c.day, c.minutes), (2, DAY_START))
        self.assertEqual(g.mode, G.SUMMARY)

    def test_unwatered_crop_does_not_grow(self):
        g = make_game()
        g.farm.set_tile(5, 7, Tile.TILLED)
        g.farm.crops[(5, 7)] = CropState("parsnip")
        g.sleep()
        self.assertEqual(g.farm.crops[(5, 7)].growth, 0)

    def test_season_change_kills_crops_and_advances_year(self):
        g = make_game()
        g.farm.crops[(5, 7)] = CropState("parsnip")
        for _ in range(DAYS_PER_SEASON):
            g.sleep()
        self.assertEqual(g.calendar.season, Season.SUMMER)
        self.assertEqual(g.summary.died, 1)
        self.assertNotIn((5, 7), g.farm.crops)

    def test_sleep_resets_position_and_clock_even_after_midnight(self):
        g = make_game()
        g.calendar.advance(900)
        g.sleep()
        self.assertEqual((g.player.x, g.player.y), (5, 4))
        self.assertEqual(g.calendar.minutes, DAY_START)

    def test_real_time_flow_late_warning_and_passout(self):
        g = make_game()
        for _ in range(int((MIDNIGHT - DAY_START) * G.SECONDS_PER_MINUTE / 0.5) + 2):
            g.update(0.5)
        self.assertTrue(g.calendar.is_late)
        self.assertIn("Geç oldu", g.message[0])
        self.assertEqual(g.mode, G.PLAY)
        g.player.energy = 20
        for _ in range(int((PASSOUT - MIDNIGHT) * G.SECONDS_PER_MINUTE / 0.5) + 2):
            g.update(0.5)
        self.assertEqual(g.mode, G.SUMMARY)
        self.assertTrue(g.summary.passed_out)
        self.assertEqual(g.calendar.day, 2)
        self.assertEqual(g.player.energy, g.player.max_energy // 2)

    def test_time_paused_in_menus(self):
        g = make_game()
        g.handle_key("e")
        before = g.calendar.minutes
        g.update(100)
        self.assertEqual(g.calendar.minutes, before)

    def test_keys_and_modes(self):
        g = make_game()
        x, y = g.player.x, g.player.y
        g.handle_key("d")
        self.assertEqual((g.player.x, g.player.facing), (x + 1, Direction.RIGHT))
        g.handle_key("UP")
        self.assertEqual((g.player.y, g.player.facing), (y - 1, Direction.UP))
        g.handle_key("5")
        self.assertEqual(g.player.selected_slot().item_id, T.SCYTHE)
        for key, mode in (("e", G.INVENTORY), ("i", G.PLAY), ("p", G.SHOP), ("esc", G.PLAY), ("y", G.SLEEP), ("n", G.PLAY)):
            self.assertTrue(g.handle_key(key))
            self.assertEqual(g.mode, mode, key)

    def test_quit_keys(self):
        for k in ("q", "esc", "ctrl+c"):
            self.assertFalse(make_game().handle_key(k))

    def test_inventory_swap(self):
        g = make_game()
        g.handle_key("e")
        g.handle_key("enter")                               # slot 0 seç
        g.handle_key("down")
        g.handle_key("enter")                               # slot 1 ile yer değiştir
        self.assertEqual(g.player.inventory.slots[0].item_id, T.WATERING_CAN)
        self.assertEqual(g.player.inventory.slots[1].item_id, T.HOE)

    def test_shop_buy_and_sell_through_keys(self):
        g = make_game()
        g.handle_key("p")
        g.handle_key("enter")                               # en ucuz bahar tohumu (yaban havucu 20g)
        self.assertEqual(g.player.gold, 480)
        g.player.inventory.add("crop:potato", 3)
        g.handle_key("tab")
        rows = g._shop_rows()
        self.assertTrue(any(r[1] == "crop:potato" for r in rows))
        idx = [r[1] for r in rows].index("crop:potato")
        g.cursor = idx
        g.handle_key("a")
        self.assertEqual(g.player.inventory.count("crop:potato"), 0)
        self.assertEqual(g.player.gold, 480 + 3 * int(80 * 0.8))

    def test_fishing_flow_via_game(self):
        g = make_game()
        g.farm.set_tile(5, 7, Tile.POND)
        g.handle_key("6")
        g.handle_key("c")
        self.assertEqual(g.mode, G.FISHING)
        g.update(10)
        g.handle_key("space")
        self.assertEqual(g.fishing.phase, FishPhase.REEL)
        g.fishing.progress, g.fishing.fish_pos, g.fishing.bar = 0.999, 0.5, 0.4
        g.update(1 / 30)
        self.assertEqual(g.fishing.phase, FishPhase.CAUGHT)
        g.handle_key("space")                               # kilit süresi dolmadan kapanmaz
        self.assertEqual(g.mode, G.FISHING)
        g.update(1.0)
        g.handle_key("space")
        self.assertEqual(g.mode, G.PLAY)
        self.assertTrue(any(s and s.item_id.startswith("fish:") for s in g.player.inventory.slots))

    def test_harvest_by_interaction(self):
        g = make_game()
        g.farm.set_tile(5, 7, Tile.TILLED)
        g.farm.crops[(5, 7)] = CropState("parsnip", 4)
        g.handle_key("5")
        g.handle_key("c")                                   # elde tırpan olsa da hasat edilir
        self.assertEqual(g.player.inventory.count("crop:parsnip"), 1)


class TestRender(unittest.TestCase):
    def test_all_modes_render_without_error(self):
        g = make_game()
        g.farm.crops[(5, 7)] = CropState("tomato", 3)
        g.farm.set_tile(5, 7, Tile.WATERED)
        for w, h in ((SCREEN_W, SCREEN_H), (140, 40)):
            for mode in (G.PLAY, G.INVENTORY, G.SHOP, G.SLEEP):
                g.mode = mode
                buf = Buffer(w, h)
                render(g, buf, 1.5)
                self.assertTrue(any(c.char != " " for row in buf.cells for c in row))
        g.shop_tab = 1
        g.mode = G.SHOP
        render(g, Buffer(SCREEN_W, SCREEN_H), 0.0)
        g.sleep()
        buf = Buffer(SCREEN_W, SCREEN_H)
        render(g, buf, 0.0)
        self.assertIn("Gece Özeti", "\n".join(buf.to_lines()))
        g.mode = G.FISHING
        g.fishing = FishingGame(Season.SPRING, random.Random(1))
        for phase in ("wait", "bite", "reel"):
            if phase == "bite":
                g.fishing.update(10)
            if phase == "reel":
                g.fishing.press()
            render(g, Buffer(SCREEN_W, SCREEN_H), 0.0)

    def test_hud_text(self):
        g = make_game()
        buf = Buffer(SCREEN_W, SCREEN_H)
        render(g, buf, 0.0)
        text = "\n".join(buf.to_lines())
        for needle in ("Bahar 1, Yıl 1", "06:00", "500g", "270/270", "Çapa"):
            self.assertIn(needle, text)

    def test_hub_registration(self):
        import importlib
        hub = importlib.import_module("run_hub")
        item = next(i for i in hub.ITEMS if i["id"] == "stardew")
        self.assertEqual(item["num"], "10")
        self.assertTrue(os.path.isfile(item["path"]))


if __name__ == "__main__":
    unittest.main()
