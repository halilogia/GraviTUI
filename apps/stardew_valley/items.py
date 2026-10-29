"""Eşya kataloğu: alet, tohum, ürün, kaynak ve balık (tek kimlik -> ad / tür / satış fiyatı)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

from .crops import CROP_DATABASE
from .fishing import FISH_DATABASE
from .tools import COPPER_ORE, FIBER, STONE, TOOL_DATABASE, WOOD

TOOL, SEED, CROP, RESOURCE, FISH = "tool", "seed", "crop", "resource", "fish"
STACK_MAX = 999


@dataclass(frozen=True)
class ItemDef:
    id: str
    name: str
    kind: str
    sell_price: int = 0

    @property
    def stack(self) -> int:
        return 1 if self.kind == TOOL else STACK_MAX


def _build() -> Dict[str, ItemDef]:
    items = [ItemDef(t.id, t.name, TOOL) for t in TOOL_DATABASE.values()]
    for c in CROP_DATABASE.values():
        items.append(ItemDef(c.seed_item, c.seed_name, SEED, c.seed_price // 2))
        items.append(ItemDef(c.crop_item, c.name, CROP, c.sell_price))
    items += [ItemDef(WOOD, "Odun", RESOURCE, 2), ItemDef(STONE, "Taş", RESOURCE, 2),
              ItemDef(FIBER, "Lif", RESOURCE, 1), ItemDef(COPPER_ORE, "Bakır Cevheri", RESOURCE, 5)]
    items += [ItemDef(f.item_id, f.name, FISH, f.sell_price) for f in FISH_DATABASE.values()]
    return {i.id: i for i in items}


ITEMS: Dict[str, ItemDef] = _build()


def item(item_id: str) -> ItemDef:
    return ITEMS[item_id]


def item_name(item_id: str) -> str:
    return ITEMS[item_id].name


def sell_price(item_id: str) -> int:
    return ITEMS[item_id].sell_price


def is_tool(item_id: str) -> bool:
    return ITEMS[item_id].kind == TOOL
