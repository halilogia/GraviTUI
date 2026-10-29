"""Oyuncu: konum, bakış yönü, enerji, para, 12 slotluk çanta ve hotbar seçimi."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Tuple

from .farm import SPAWN
from .items import ITEMS
from .tools import (AXE, FISHING_ROD, HOE, PICKAXE, SCYTHE, WATER_CAPACITY, WATERING_CAN)

MAX_ENERGY = 270
START_GOLD = 500
INVENTORY_SIZE = 12
HOTBAR_SIZE = 9


class Direction(Enum):
    UP = (0, -1)
    DOWN = (0, 1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)

    @property
    def dx(self) -> int:
        return self.value[0]

    @property
    def dy(self) -> int:
        return self.value[1]


@dataclass
class Slot:
    item_id: str
    qty: int = 1


class Inventory:
    def __init__(self, size: int = INVENTORY_SIZE) -> None:
        self.slots: List[Optional[Slot]] = [None] * size

    def count(self, item_id: str) -> int:
        return sum(s.qty for s in self.slots if s and s.item_id == item_id)

    def _room(self, item_id: str) -> int:
        cap = ITEMS[item_id].stack
        return sum(cap - s.qty for s in self.slots if s and s.item_id == item_id) + \
            sum(cap for s in self.slots if s is None)

    def can_add(self, item_id: str, qty: int = 1) -> bool:
        return self._room(item_id) >= qty

    def add(self, item_id: str, qty: int = 1) -> int:
        """Eşyayı önce mevcut yığınlara, sonra boş slotlara ekler. Sığmayan miktarı döndürür."""
        cap = ITEMS[item_id].stack
        for s in self.slots:
            if qty and s and s.item_id == item_id and s.qty < cap:
                n = min(qty, cap - s.qty)
                s.qty += n
                qty -= n
        for i, s in enumerate(self.slots):
            if qty and s is None:
                n = min(qty, cap)
                self.slots[i] = Slot(item_id, n)
                qty -= n
        return qty

    def remove(self, item_id: str, qty: int = 1) -> bool:
        if self.count(item_id) < qty:
            return False
        for i in range(len(self.slots) - 1, -1, -1):
            s = self.slots[i]
            if qty and s and s.item_id == item_id:
                n = min(qty, s.qty)
                s.qty -= n
                qty -= n
                if s.qty == 0:
                    self.slots[i] = None
        return True

    def swap(self, a: int, b: int) -> None:
        self.slots[a], self.slots[b] = self.slots[b], self.slots[a]

    @property
    def free_slots(self) -> int:
        return sum(1 for s in self.slots if s is None)


class Player:
    def __init__(self) -> None:
        self.x, self.y = SPAWN
        self.facing = Direction.UP
        self.max_energy = MAX_ENERGY
        self.energy = MAX_ENERGY
        self.gold = START_GOLD
        self.water = WATER_CAPACITY
        self.hotbar_index = 0
        self.inventory = Inventory()
        for tool in (HOE, WATERING_CAN, AXE, PICKAXE, SCYTHE, FISHING_ROD):
            self.inventory.add(tool)
        self.inventory.add("seed:parsnip", 15)

    # ------------------------------------------------------------ konum
    def facing_pos(self) -> Tuple[int, int]:
        return self.x + self.facing.dx, self.y + self.facing.dy

    def move(self, direction: Direction, farm) -> bool:
        """Yöne döner; hedef yürünebilirse adım atar."""
        self.facing = direction
        nx, ny = self.x + direction.dx, self.y + direction.dy
        if farm.walkable(nx, ny):
            self.x, self.y = nx, ny
            return True
        return False

    # ------------------------------------------------------------ enerji
    @property
    def exhausted(self) -> bool:
        return self.energy <= 0

    def spend_energy(self, n: int) -> bool:
        if self.energy < n:
            return False
        self.energy -= n
        return True

    def restore_energy(self, fraction: float = 1.0) -> None:
        self.energy = max(self.energy, round(self.max_energy * fraction))

    # ------------------------------------------------------------ hotbar
    def select(self, number: int) -> None:
        """1-9 tuşuna karşılık gelen hotbar slotunu seçer."""
        if 1 <= number <= HOTBAR_SIZE:
            self.hotbar_index = number - 1

    def selected_slot(self) -> Optional[Slot]:
        return self.inventory.slots[self.hotbar_index]
