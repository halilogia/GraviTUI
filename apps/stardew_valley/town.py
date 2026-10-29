"""Pierre'in Mağazası: mevsime uygun tohum satın alma ve anında ürün satma."""
from __future__ import annotations

from typing import List, Tuple

from .calendar import Season
from .crops import CROP_DATABASE, CropDef
from .items import ITEMS, TOOL, item_name, sell_price

SELL_RATE = 0.8   # Pierre anında öder ama kutudan %20 az; kutu gece tam fiyatla öder


def stock(season: Season) -> List[CropDef]:
    """Bu mevsimde ekilebilen tohumlar (fiyata göre artan)."""
    return sorted((c for c in CROP_DATABASE.values() if season in c.seasons),
                  key=lambda c: c.seed_price)


def buy_seed(player, crop_id: str, qty: int, season: Season) -> Tuple[bool, str]:
    crop = CROP_DATABASE.get(crop_id)
    if crop is None or season not in crop.seasons:
        return False, "Bu tohum bu mevsimde satılmıyor."
    cost = crop.seed_price * qty
    if player.gold < cost:
        return False, f"Yetersiz altın ({cost}g gerekli)."
    if not player.inventory.can_add(crop.seed_item, qty):
        return False, "Çanta dolu!"
    player.gold -= cost
    player.inventory.add(crop.seed_item, qty)
    return True, f"{qty}x {crop.seed_name} alındı (-{cost}g)"


def sell_value(item_id: str) -> int:
    return int(sell_price(item_id) * SELL_RATE)


def sellable(player) -> List[Tuple[int, str, int]]:
    """Satılabilir slotlar: (slot indeksi, eşya kimliği, adet)."""
    return [(i, s.item_id, s.qty) for i, s in enumerate(player.inventory.slots)
            if s and ITEMS[s.item_id].kind != TOOL and sell_value(s.item_id) > 0]


def sell_item(player, item_id: str, qty: int) -> Tuple[bool, str]:
    qty = min(qty, player.inventory.count(item_id))
    unit = sell_value(item_id)
    if qty <= 0 or unit <= 0:
        return False, "Satılacak bir şey yok."
    player.inventory.remove(item_id, qty)
    player.gold += unit * qty
    return True, f"{qty}x {item_name(item_id)} satıldı (+{unit * qty}g)"
