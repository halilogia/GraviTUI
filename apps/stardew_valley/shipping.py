"""Sevkiyat Kutusu: bırakılan ürünler ve gece uyurken hesaplanan gelir dökümü."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from .items import sell_price


@dataclass
class ShipLine:
    item_id: str
    qty: int
    unit: int

    @property
    def total(self) -> int:
        return self.qty * self.unit


@dataclass
class ShippingReport:
    lines: List[ShipLine] = field(default_factory=list)

    @property
    def total(self) -> int:
        return sum(line.total for line in self.lines)


class ShippingBin:
    def __init__(self) -> None:
        self.items: Dict[str, int] = {}

    def ship(self, item_id: str, qty: int = 1) -> bool:
        if qty <= 0 or sell_price(item_id) <= 0:
            return False
        self.items[item_id] = self.items.get(item_id, 0) + qty
        return True

    @property
    def is_empty(self) -> bool:
        return not self.items

    def pending_value(self) -> int:
        return sum(q * sell_price(i) for i, q in self.items.items())

    def settle(self) -> ShippingReport:
        """Kutuyu boşaltır ve gelir dökümünü (değere göre azalan) döndürür."""
        lines = [ShipLine(i, q, sell_price(i)) for i, q in self.items.items()]
        lines.sort(key=lambda ln: ln.total, reverse=True)
        self.items.clear()
        return ShippingReport(lines)
