"""Ekin kataloğu (CROP_DATABASE), büyüme aşamaları ve ekin durumu."""
from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from typing import Dict, Optional, Tuple

from .calendar import Season


class Stage(IntEnum):
    SEED = 0         # Tohum
    SPROUT = 1       # Filiz
    VEGETATIVE = 2   # Büyüme
    BLOOM = 3        # Çiçeklenme
    HARVESTABLE = 4  # Hasata Hazır


STAGE_NAMES = {
    Stage.SEED: "Tohum",
    Stage.SPROUT: "Filiz",
    Stage.VEGETATIVE: "Büyüme",
    Stage.BLOOM: "Çiçeklenme",
    Stage.HARVESTABLE: "Hasata Hazır",
}

SP, SU, FA = Season.SPRING, Season.SUMMER, Season.FALL


@dataclass(frozen=True)
class CropDef:
    id: str
    name: str                      # ekin / hasat ürünü adı
    days_to_grow: int
    seed_price: int
    sell_price: int
    seasons: Tuple[Season, ...]
    regrow_days: int               # 0 = tek hasat; >0 = hasattan sonra N günde yeniden olgunlaşır
    color: Tuple[int, int, int]    # hasat ürünü rengi (renderer)

    @property
    def seed_item(self) -> str:
        return f"seed:{self.id}"

    @property
    def crop_item(self) -> str:
        return f"crop:{self.id}"

    @property
    def seed_name(self) -> str:
        return f"{self.name} Tohumu"


CROP_DATABASE: Dict[str, CropDef] = {c.id: c for c in (
    CropDef("parsnip", "Yaban Havucu", 4, 20, 35, (SP,), 0, (240, 230, 170)),
    CropDef("potato", "Patates", 6, 50, 80, (SP,), 0, (190, 150, 90)),
    CropDef("cauliflower", "Karnabahar", 12, 80, 175, (SP,), 0, (245, 245, 235)),
    CropDef("strawberry", "Çilek", 8, 100, 120, (SP,), 4, (235, 50, 70)),
    CropDef("tomato", "Domates", 11, 50, 60, (SU,), 4, (230, 60, 40)),
    CropDef("corn", "Mısır", 14, 150, 50, (SU, FA), 4, (250, 210, 60)),
    CropDef("pumpkin", "Balkabağı", 13, 100, 320, (FA,), 0, (240, 130, 30)),
    CropDef("blue_jazz", "Mavi Caz", 7, 30, 50, (SP,), 0, (90, 140, 250)),
)}


def crop_by_seed(item_id: str) -> Optional[CropDef]:
    return CROP_DATABASE.get(item_id[5:]) if item_id.startswith("seed:") else None


def stage_of(crop: CropDef, growth: int) -> Stage:
    """Büyüme gününe göre aşama: gün 0 tohum, sonra %35 / %70 eşikleri, tamamlanınca hasat."""
    if growth >= crop.days_to_grow:
        return Stage.HARVESTABLE
    if growth <= 0:
        return Stage.SEED
    frac = growth / crop.days_to_grow
    if frac < 0.35:
        return Stage.SPROUT
    return Stage.VEGETATIVE if frac < 0.7 else Stage.BLOOM


@dataclass
class CropState:
    crop_id: str
    growth: int = 0

    @property
    def definition(self) -> CropDef:
        return CROP_DATABASE[self.crop_id]

    @property
    def stage(self) -> Stage:
        return stage_of(self.definition, self.growth)

    @property
    def harvestable(self) -> bool:
        return self.stage == Stage.HARVESTABLE

    def grow(self) -> None:
        if not self.harvestable:
            self.growth += 1

    def harvest(self) -> bool:
        """Hasat eder. Yeniden hasat edilebilirse True (ekin yerinde kalır), değilse False."""
        d = self.definition
        if d.regrow_days > 0:
            self.growth = d.days_to_grow - d.regrow_days
            return True
        return False
