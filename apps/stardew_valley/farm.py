"""2D çiftlik haritası (32x18): hücre tipleri, ekin yerleşimi ve gece döngüsü."""
from __future__ import annotations

import random
from enum import IntEnum
from typing import Dict, List, Optional, Tuple

from .calendar import Season
from .crops import CropState

FARM_W, FARM_H = 32, 18


class Tile(IntEnum):
    GRASS = 0
    TILLED = 1
    WATERED = 2
    ROCK = 3
    WOOD = 4
    WEED = 5
    POND = 6
    FARMHOUSE = 7
    SHIPPING_BIN = 8


WALKABLE = frozenset({Tile.GRASS, Tile.TILLED, Tile.WATERED, Tile.WEED})
HOUSE_RECT = (2, 1, 6, 3)   # x, y, w, h
BIN_POS = (9, 3)
SPAWN = (5, 4)
CLEAR_ZONE = (1, 0, 12, 8)  # kaya/kütük çıkmayan başlangıç bölgesi (x, y, w, h)
POND_CENTER = (25.0, 12.0)


class Farm:
    def __init__(self, seed: Optional[int] = None, generate: bool = True) -> None:
        self.rng = random.Random(seed)
        self.width, self.height = FARM_W, FARM_H
        self.tiles: List[List[Tile]] = [[Tile.GRASS] * FARM_W for _ in range(FARM_H)]
        self.crops: Dict[Tuple[int, int], CropState] = {}
        self.hp: Dict[Tuple[int, int], int] = {}   # kaya / kütük için aldığı vuruş
        if generate:
            self._generate()

    # ------------------------------------------------------------ erişim
    def in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    def tile(self, x: int, y: int) -> Tile:
        return self.tiles[y][x]

    def set_tile(self, x: int, y: int, t: Tile) -> None:
        self.tiles[y][x] = t
        self.hp.pop((x, y), None)

    def walkable(self, x: int, y: int) -> bool:
        return self.in_bounds(x, y) and self.tiles[y][x] in WALKABLE

    def count(self, t: Tile) -> int:
        return sum(row.count(t) for row in self.tiles)

    def hit(self, x: int, y: int, max_hp: int) -> bool:
        """Kaya/kütüğe vuruş ekler; tamamen kırıldıysa True döner."""
        n = self.hp.get((x, y), 0) + 1
        if n >= max_hp:
            self.hp.pop((x, y), None)
            return True
        self.hp[(x, y)] = n
        return False

    # ------------------------------------------------------------ üretim
    def _in_zone(self, x: int, y: int, zone: Tuple[int, int, int, int]) -> bool:
        zx, zy, zw, zh = zone
        return zx <= x < zx + zw and zy <= y < zy + zh

    def _generate(self) -> None:
        cx, cy = POND_CENTER
        for y in range(self.height):
            for x in range(self.width):
                if ((x - cx) / 6.0) ** 2 + ((y - cy) / 3.4) ** 2 <= 1.0:
                    self.tiles[y][x] = Tile.POND
        hx, hy, hw, hh = HOUSE_RECT
        for y in range(hy, hy + hh):
            for x in range(hx, hx + hw):
                self.tiles[y][x] = Tile.FARMHOUSE
        self.tiles[BIN_POS[1]][BIN_POS[0]] = Tile.SHIPPING_BIN
        for t, n, clear in ((Tile.ROCK, 24, True), (Tile.WOOD, 16, True), (Tile.WEED, 28, False)):
            self._scatter(t, n, avoid_start=clear)

    def _free_grass(self, avoid_start: bool = False) -> List[Tuple[int, int]]:
        return [(x, y) for y in range(self.height) for x in range(self.width)
                if self.tiles[y][x] == Tile.GRASS and (x, y) != SPAWN
                and not (avoid_start and self._in_zone(x, y, CLEAR_ZONE))]

    def _scatter(self, t: Tile, n: int, avoid_start: bool = False) -> int:
        spots = self._free_grass(avoid_start)
        self.rng.shuffle(spots)
        for x, y in spots[:n]:
            self.tiles[y][x] = t
        return min(n, len(spots))

    def spawn_weeds(self, n: int) -> int:
        return self._scatter(Tile.WEED, n)

    # ------------------------------------------------------------ gece döngüsü
    def advance_night(self) -> Tuple[int, int]:
        """Sulanmış topraktaki ekinleri 1 gün büyütür, tüm toprağı kurutur. (büyüyen, hasada hazır)."""
        grown = ready = 0
        for (x, y), crop in self.crops.items():
            if self.tiles[y][x] == Tile.WATERED and not crop.harvestable:
                crop.grow()
                grown += 1
            ready += crop.harvestable
        for y in range(self.height):
            for x in range(self.width):
                if self.tiles[y][x] == Tile.WATERED:
                    self.tiles[y][x] = Tile.TILLED
        return grown, ready

    def kill_out_of_season(self, season: Season) -> int:
        """Yeni mevsimde yetişmeyen ekinleri kurutur (toprak işlenmiş kalır)."""
        dead = [pos for pos, c in self.crops.items() if season not in c.definition.seasons]
        for pos in dead:
            del self.crops[pos]
        return len(dead)
