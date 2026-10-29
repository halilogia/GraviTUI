"""Oyun durumu ve girdi yönlendirme (terminalden bağımsız; headless test edilebilir)."""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from .calendar import GameCalendar
from .farm import SPAWN, Farm, Tile
from .fishing import FishingGame, FishPhase
from .items import ITEMS, SEED, TOOL, is_tool, item_name
from .player import Direction, Player
from .shipping import ShippingBin, ShippingReport
from .tools import harvest_crop, plant_seed, use_tool
from . import town

SECONDS_PER_MINUTE = 0.7      # gerçek saniye / oyun dakikası (06:00 -> 02:00 ≈ 14 dk)
RESULT_LOCK = 0.6             # balıkçılık sonucu hemen kapanmasın
PLAY, INVENTORY, SHOP, SUMMARY, FISHING, SLEEP = (
    "play", "inventory", "shop", "summary", "fishing", "sleep")
MOVES = {"up": Direction.UP, "w": Direction.UP, "down": Direction.DOWN, "s": Direction.DOWN,
         "left": Direction.LEFT, "a": Direction.LEFT, "right": Direction.RIGHT, "d": Direction.RIGHT}
CONFIRM = ("enter", "space", "c")
QUIT = ("q", "esc", "ctrl+c")


@dataclass
class NightSummary:
    date_before: str
    date_after: str
    report: ShippingReport
    grown: int = 0
    ready: int = 0
    died: int = 0
    season_changed: bool = False
    passed_out: bool = False
    events: List[str] = field(default_factory=list)


class Game:
    def __init__(self, seed: Optional[int] = None) -> None:
        self.rng = random.Random(seed)
        self.calendar = GameCalendar()
        self.farm = Farm(seed)
        self.player = Player()
        self.bin = ShippingBin()
        self.mode = PLAY
        self.cursor = 0
        self.shop_tab = 0              # 0 = satın al, 1 = sat
        self.pick: Optional[int] = None   # envanterde taşınmak üzere seçilen slot
        self.fishing: Optional[FishingGame] = None
        self.summary: Optional[NightSummary] = None
        self.message: Tuple[str, bool] = ("Günaydın! Çapa ile toprağı işle, tohum ek.", True)
        self.msg_t = 6.0
        self._clock_acc = 0.0
        self._lock = 0.0

    # ------------------------------------------------------------ mesaj
    def flash(self, text: str, ok: bool = True, secs: float = 4.0) -> None:
        self.message, self.msg_t = (text, ok), secs

    def _apply(self, res) -> None:
        self.flash(res.msg, res.ok)

    # ------------------------------------------------------------ girdi
    def handle_key(self, key: str) -> bool:
        """False dönerse oyundan çıkılır."""
        key = key.lower()
        handler = {PLAY: self._key_play, INVENTORY: self._key_inventory, SHOP: self._key_shop,
                   SUMMARY: self._key_summary, FISHING: self._key_fishing, SLEEP: self._key_sleep}
        return handler[self.mode](key)

    def _key_play(self, key: str) -> bool:
        p = self.player
        if key in QUIT:
            return False
        if key in MOVES:
            p.move(MOVES[key], self.farm)
        elif key.isdigit() and key != "0":
            p.select(int(key))
            slot = p.selected_slot()
            self.flash(item_name(slot.item_id) if slot else "(boş slot)")
        elif key in ("c", "space"):
            self.use_selected()
        elif key in ("e", "i"):
            self.mode, self.cursor, self.pick = INVENTORY, p.hotbar_index, None
        elif key == "p":
            self.mode, self.cursor, self.shop_tab = SHOP, 0, 0
        elif key == "y":
            self.mode = SLEEP
        return True

    def _key_inventory(self, key: str) -> bool:
        n = len(self.player.inventory.slots)
        if key == "ctrl+c":
            return False
        if key in ("esc", "q", "e", "i"):
            self.mode = PLAY
        elif key in ("up", "w"):
            self.cursor = (self.cursor - 1) % n
        elif key in ("down", "s"):
            self.cursor = (self.cursor + 1) % n
        elif key in CONFIRM:
            if self.pick is None:
                self.pick = self.cursor
            else:
                self.player.inventory.swap(self.pick, self.cursor)
                self.pick = None
        return True

    def _shop_rows(self) -> list:
        return town.stock(self.calendar.season) if self.shop_tab == 0 else town.sellable(self.player)

    def _key_shop(self, key: str) -> bool:
        if key == "ctrl+c":
            return False
        if key in ("esc", "q", "p"):
            self.mode = PLAY
            return True
        if key == "tab":
            self.shop_tab, self.cursor = 1 - self.shop_tab, 0
            return True
        rows = self._shop_rows()
        if not rows:
            return True
        self.cursor = min(self.cursor, len(rows) - 1)
        if key in ("up", "w"):
            self.cursor = (self.cursor - 1) % len(rows)
        elif key in ("down", "s"):
            self.cursor = (self.cursor + 1) % len(rows)
        elif key in ("enter", "space", "a"):
            if self.shop_tab == 0:
                ok, msg = town.buy_seed(self.player, rows[self.cursor].id, 5 if key == "a" else 1,
                                        self.calendar.season)
            else:
                _, item_id, qty = rows[self.cursor]
                ok, msg = town.sell_item(self.player, item_id, qty if key == "a" else 1)
            self.flash(msg, ok)
            self.cursor = min(self.cursor, max(0, len(self._shop_rows()) - 1))
        return True

    def _key_summary(self, key: str) -> bool:
        if key == "ctrl+c":
            return False
        if key in CONFIRM or key in ("esc", "q"):
            self.mode = PLAY
        return True

    def _key_sleep(self, key: str) -> bool:
        if key == "ctrl+c":
            return False
        if key in ("y", "enter"):
            self.sleep()
        elif key in ("n", "esc", "q"):
            self.mode = PLAY
        return True

    def _key_fishing(self, key: str) -> bool:
        fg = self.fishing
        if key == "ctrl+c":
            return False
        if fg is None or (key == "esc" and not fg.done):
            self.fishing, self.mode = None, PLAY
            self.flash("Oltayı geri çektin.", False)
        elif fg.done:
            if key in CONFIRM + ("esc",) and self._lock <= 0:
                self._finish_fishing()
        elif key in CONFIRM:
            fg.press()
        return True

    # ------------------------------------------------------------ eylemler
    def use_selected(self) -> None:
        """C / Space: baktığın hücreyle etkileşime gir (hasat, sevkiyat, alet, tohum)."""
        p, farm = self.player, self.farm
        x, y = p.facing_pos()
        if not farm.in_bounds(x, y):
            return self.flash("Haritanın kenarı.", False)
        crop = farm.crops.get((x, y))
        if crop is not None and crop.harvestable:
            return self._apply(harvest_crop(p, farm, x, y))
        tile, slot = farm.tile(x, y), p.selected_slot()
        if tile == Tile.FARMHOUSE:
            return self.flash("Evin kapısı. Uyumak için [Y] tuşuna bas.")
        if slot is None:
            return self.flash("Elin boş. Bir eşya seç [1-9].", False)
        if tile == Tile.SHIPPING_BIN:
            if is_tool(slot.item_id):
                return self.flash("Aleti kutuya koyamazsın.", False)
            qty, name = slot.qty, item_name(slot.item_id)
            self.bin.ship(slot.item_id, qty)
            p.inventory.remove(slot.item_id, qty)
            return self.flash(f"{qty}x {name} sevkiyat kutusuna bırakıldı.")
        kind = ITEMS[slot.item_id].kind
        if kind == TOOL:
            res = use_tool(slot.item_id, p, farm, self.rng)
            if res.ok and res.action == "fish":
                self.fishing, self.mode = FishingGame(self.calendar.season, self.rng), FISHING
            return self._apply(res)
        if kind == SEED:
            return self._apply(plant_seed(slot.item_id, p, farm, self.calendar.season))
        self.flash(f"{item_name(slot.item_id)}: sevkiyat kutusuna bırak veya Pierre'e sat [P].", False)

    def _finish_fishing(self) -> None:
        fg, self.fishing, self.mode = self.fishing, None, PLAY
        if fg.phase == FishPhase.CAUGHT:
            if self.player.inventory.can_add(fg.fish.item_id):
                self.player.inventory.add(fg.fish.item_id)
                self.flash(f"+1 {fg.fish.name}")
            else:
                self.flash("Çanta dolu, balık kaçtı!", False)
        else:
            self.flash(fg.message, False)

    def sleep(self, passed_out: bool = False) -> NightSummary:
        """Yatağa girer: ekinler büyür, topraklar kurur, kutu satılır, enerji yenilenir, gün +1."""
        cal, p = self.calendar, self.player
        before = cal.date_str
        grown, ready = self.farm.advance_night()
        report = self.bin.settle()
        p.gold += report.total
        changed = cal.next_day()
        died = self.farm.kill_out_of_season(cal.season) if changed else 0
        self.farm.spawn_weeds(self.rng.randint(2, 5))
        p.restore_energy(0.5 if passed_out else 1.0)
        p.x, p.y, p.facing = SPAWN[0], SPAWN[1], Direction.UP
        events = []
        if passed_out:
            events.append("Gece 02:00'de yorgunluktan bayıldın; enerjin yarıya kadar yenilendi.")
        if changed:
            events.append(f"Mevsim değişti: {cal.season_name}!")
        if died:
            events.append(f"{died} ekin yeni mevsimde yetişemeyip soldu.")
        self.summary = NightSummary(before, cal.date_str, report, grown, ready, died,
                                    changed, passed_out, events)
        self.mode, self._clock_acc = SUMMARY, 0.0
        return self.summary

    # ------------------------------------------------------------ zaman
    def update(self, dt: float) -> None:
        if self.msg_t > 0:
            self.msg_t -= dt
        if self._lock > 0:
            self._lock -= dt
        if self.mode == FISHING and self.fishing is not None:
            was_done = self.fishing.done
            self.fishing.update(dt)
            if self.fishing.done and not was_done:
                self._lock = RESULT_LOCK
            return
        if self.mode != PLAY:
            return
        self._clock_acc += dt
        while self._clock_acc >= SECONDS_PER_MINUTE and self.mode == PLAY:
            self._clock_acc -= SECONDS_PER_MINUTE
            for ev in self.calendar.advance(1):
                if ev == "late":
                    self.flash("Geç oldu! Yatağa gitmelisin [Y].", False, 8.0)
                elif ev == "passout":
                    self.sleep(passed_out=True)
