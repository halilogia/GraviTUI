"""Aletler (HOE, WATERING_CAN, AXE, PICKAXE, SCYTHE, FISHING_ROD) ve çiftlik eylemleri."""
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Callable, Dict, Optional

from .calendar import Season
from .crops import CropState, crop_by_seed
from .farm import Farm, Tile

HOE, WATERING_CAN, AXE, PICKAXE, SCYTHE, FISHING_ROD = (
    "hoe", "watering_can", "axe", "pickaxe", "scythe", "fishing_rod")
WOOD, STONE, FIBER, COPPER_ORE = "wood", "stone", "fiber", "copper_ore"
WATER_CAPACITY = 40
WOOD_HITS, ROCK_HITS = 3, 2


@dataclass(frozen=True)
class ToolDef:
    id: str
    name: str
    energy: int
    desc: str


TOOL_DATABASE: Dict[str, ToolDef] = {t.id: t for t in (
    ToolDef(HOE, "Çapa", 2, "Çimi işlenmiş toprağa çevirir"),
    ToolDef(WATERING_CAN, "Sulama Kabı", 2, "İşlenmiş toprağı sular; gölette dolar"),
    ToolDef(AXE, "Balta", 4, "Kütükleri keser, odun verir"),
    ToolDef(PICKAXE, "Kazma", 4, "Taşları kırar, taş ve maden verir"),
    ToolDef(SCYTHE, "Tırpan", 0, "Yabani otu keser, lif verir"),
    ToolDef(FISHING_ROD, "Olta", 3, "Gölette balık tutar"),
)}


@dataclass
class ToolResult:
    ok: bool
    msg: str
    action: Optional[str] = None   # "fish" -> oyun balıkçılık mini oyununu başlatır


TIRED = ToolResult(False, "Çok yorgunsun! Yatağa git ve uyu [Y].")
FULL = ToolResult(False, "Çanta dolu!")


def _pay(player, cost: int) -> bool:
    return player.energy >= cost and (cost == 0 or player.spend_energy(cost))


def _hoe(player, farm: Farm, x: int, y: int, rng) -> ToolResult:
    t = farm.tile(x, y)
    if t == Tile.GRASS:
        if not _pay(player, TOOL_DATABASE[HOE].energy):
            return TIRED
        farm.set_tile(x, y, Tile.TILLED)
        return ToolResult(True, "Toprak işlendi.")
    if t == Tile.WEED:
        return ToolResult(False, "Önce otları tırpanla temizle.")
    if t in (Tile.TILLED, Tile.WATERED):
        return ToolResult(False, "Toprak zaten işlenmiş.")
    return ToolResult(False, "Burası işlenemez.")


def _can(player, farm: Farm, x: int, y: int, rng) -> ToolResult:
    t = farm.tile(x, y)
    if t == Tile.POND:
        player.water = WATER_CAPACITY
        return ToolResult(True, f"Sulama kabı doldu ({WATER_CAPACITY}/{WATER_CAPACITY}).")
    if t != Tile.TILLED:
        return ToolResult(False, "Toprak zaten sulu." if t == Tile.WATERED else "Sulanacak işlenmiş toprak yok.")
    if player.water <= 0:
        return ToolResult(False, "Su bitti! Gölette doldur.")
    if not _pay(player, TOOL_DATABASE[WATERING_CAN].energy):
        return TIRED
    player.water -= 1
    farm.set_tile(x, y, Tile.WATERED)
    return ToolResult(True, f"Sulandı. Su: {player.water}/{WATER_CAPACITY}")


def _axe(player, farm: Farm, x: int, y: int, rng) -> ToolResult:
    if farm.tile(x, y) != Tile.WOOD:
        return ToolResult(False, "Balta ile kesilecek kütük yok.")
    if not player.inventory.can_add(WOOD):
        return FULL
    if not _pay(player, TOOL_DATABASE[AXE].energy):
        return TIRED
    if not farm.hit(x, y, WOOD_HITS):
        return ToolResult(True, "Kütüğe vurdun...")
    farm.set_tile(x, y, Tile.GRASS)
    n = rng.randint(3, 5)
    player.inventory.add(WOOD, n)
    return ToolResult(True, f"Kütük devrildi! +{n} Odun")


def _pickaxe(player, farm: Farm, x: int, y: int, rng) -> ToolResult:
    t = farm.tile(x, y)
    if t in (Tile.TILLED, Tile.WATERED):
        if not _pay(player, TOOL_DATABASE[PICKAXE].energy):
            return TIRED
        farm.set_tile(x, y, Tile.GRASS)
        farm.crops.pop((x, y), None)
        return ToolResult(True, "Toprak düzleştirildi.")
    if t != Tile.ROCK:
        return ToolResult(False, "Kazma ile kırılacak taş yok.")
    if not player.inventory.can_add(STONE):
        return FULL
    if not _pay(player, TOOL_DATABASE[PICKAXE].energy):
        return TIRED
    if not farm.hit(x, y, ROCK_HITS):
        return ToolResult(True, "Taş çatladı...")
    farm.set_tile(x, y, Tile.GRASS)
    n = rng.randint(2, 3)
    player.inventory.add(STONE, n)
    msg = f"Taş kırıldı! +{n} Taş"
    if rng.random() < 0.2:
        player.inventory.add(COPPER_ORE, 1)
        msg += ", +1 Bakır Cevheri"
    return ToolResult(True, msg)


def _scythe(player, farm: Farm, x: int, y: int, rng) -> ToolResult:
    if farm.tile(x, y) != Tile.WEED:
        return ToolResult(False, "Tırpanla kesilecek ot yok.")
    farm.set_tile(x, y, Tile.GRASS)       # enerji tüketmez
    if rng.random() < 0.6 and player.inventory.can_add(FIBER):
        player.inventory.add(FIBER, 1)
        return ToolResult(True, "Ot kesildi. +1 Lif")
    return ToolResult(True, "Ot kesildi.")


def _rod(player, farm: Farm, x: int, y: int, rng) -> ToolResult:
    if farm.tile(x, y) != Tile.POND:
        return ToolResult(False, "Olta atmak için göle bak.")
    if not _pay(player, TOOL_DATABASE[FISHING_ROD].energy):
        return TIRED
    return ToolResult(True, "Olta atıldı...", action="fish")


_HANDLERS: Dict[str, Callable] = {HOE: _hoe, WATERING_CAN: _can, AXE: _axe,
                                  PICKAXE: _pickaxe, SCYTHE: _scythe, FISHING_ROD: _rod}


def use_tool(tool_id: str, player, farm: Farm, rng: Optional[random.Random] = None) -> ToolResult:
    """Oyuncunun baktığı hücrede aleti kullanır. Enerjiyi yalnızca eylem başarılıysa harcar."""
    x, y = player.facing_pos()
    if not farm.in_bounds(x, y):
        return ToolResult(False, "Haritanın dışı.")
    return _HANDLERS[tool_id](player, farm, x, y, rng or random)


def plant_seed(item_id: str, player, farm: Farm, season: Season) -> ToolResult:
    crop = crop_by_seed(item_id)
    x, y = player.facing_pos()
    if crop is None or not farm.in_bounds(x, y):
        return ToolResult(False, "Buraya ekilemez.")
    if farm.tile(x, y) not in (Tile.TILLED, Tile.WATERED):
        return ToolResult(False, "Önce toprağı çapayla işle.")
    if (x, y) in farm.crops:
        return ToolResult(False, "Burada zaten bir ekin var.")
    if season not in crop.seasons:
        return ToolResult(False, f"{crop.name} bu mevsimde yetişmez.")
    player.inventory.remove(item_id, 1)
    farm.crops[(x, y)] = CropState(crop.id)
    return ToolResult(True, f"{crop.name} ekildi.")


def harvest_crop(player, farm: Farm, x: int, y: int) -> ToolResult:
    crop = farm.crops.get((x, y))
    if crop is None or not crop.harvestable:
        return ToolResult(False, "Hasada hazır ekin yok.")
    d = crop.definition
    if not player.inventory.can_add(d.crop_item):
        return FULL
    player.inventory.add(d.crop_item, 1)
    if not crop.harvest():
        del farm.crops[(x, y)]
    return ToolResult(True, f"Hasat: +1 {d.name}")
