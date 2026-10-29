"""Balıkçılık: mevsimlik balık kataloğu ve ısırma + makaralama mini oyunu."""
from __future__ import annotations

import random
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional, Tuple

from .calendar import Season

SP, SU, FA, WI = Season.SPRING, Season.SUMMER, Season.FALL, Season.WINTER


@dataclass(frozen=True)
class FishDef:
    id: str
    name: str
    sell_price: int
    difficulty: float            # 0..1 — balığın hareket hızı / zıplaması
    seasons: Tuple[Season, ...]

    @property
    def item_id(self) -> str:
        return f"fish:{self.id}"


FISH_DATABASE: Dict[str, FishDef] = {f.id: f for f in (
    FishDef("carp", "Sazan", 30, 0.25, (SP, SU, FA)),
    FishDef("bream", "Çipura", 45, 0.35, (SP, WI)),
    FishDef("sunfish", "Güneş Balığı", 30, 0.30, (SP, SU)),
    FishDef("trout", "Alabalık", 65, 0.50, (SU,)),
    FishDef("bass", "Levrek", 100, 0.65, (SU, FA)),
    FishDef("salmon", "Somon", 75, 0.55, (FA,)),
    FishDef("walleye", "Uskumru", 105, 0.70, (FA, WI)),
    FishDef("perch", "Tatlı Su Levreği", 55, 0.40, (WI,)),
    FishDef("sturgeon", "Mersin", 200, 0.90, (SU, WI)),
)}


def fish_for_season(season: Season, rng: random.Random) -> FishDef:
    pool = [f for f in FISH_DATABASE.values() if season in f.seasons]
    return rng.choice(pool)


class FishPhase(Enum):
    WAIT = "wait"      # olta suda, balık bekleniyor
    BITE = "bite"      # balık yemi kaptı — hızlı tepki ver
    REEL = "reel"      # makaralama mini oyunu
    CAUGHT = "caught"
    LOST = "lost"


BITE_WINDOW = 1.0
BAR_SIZE = 0.30
GRAVITY = 1.2
TAP_LIFT = 0.60
START_PROGRESS = 0.30


class FishingGame:
    """Zamana dayalı, terminalden bağımsız (headless test edilebilir) balıkçılık durum makinesi.

    REEL aşamasında yeşil çubuk `press()` ile yükselir, yoksa yerçekimiyle düşer; balığın
    işaretçisi çubuğun içinde kaldıkça ilerleme artar, dışında azalır.
    """

    def __init__(self, season: Season, rng: Optional[random.Random] = None) -> None:
        self.rng = rng or random.Random()
        self.fish = fish_for_season(season, self.rng)
        self.phase = FishPhase.WAIT
        self.timer = self.rng.uniform(1.5, 4.0)
        self.message = "Olta suda... balık bekleniyor"
        self.bar = 0.35        # çubuğun alt ucu (0..1-BAR_SIZE)
        self.vel = 0.0
        self.fish_pos = 0.5
        self.target = 0.5
        self.retarget = 0.0
        self.progress = START_PROGRESS

    @property
    def done(self) -> bool:
        return self.phase in (FishPhase.CAUGHT, FishPhase.LOST)

    @property
    def bar_range(self) -> Tuple[float, float]:
        return self.bar, self.bar + BAR_SIZE

    def press(self) -> None:
        if self.phase == FishPhase.WAIT:
            self._lose("Çok erken çektin, balık kaçtı!")
        elif self.phase == FishPhase.BITE:
            self.phase = FishPhase.REEL
            self.message = "Çubuğu balığın üstünde tut! [Boşluk]"
        elif self.phase == FishPhase.REEL:
            self.vel = TAP_LIFT

    def update(self, dt: float) -> None:
        if self.phase == FishPhase.WAIT:
            self.timer -= dt
            if self.timer <= 0:
                self.phase, self.timer = FishPhase.BITE, BITE_WINDOW
                self.message = "BALIK YEMİ KAPTI!  [Boşluk]"
        elif self.phase == FishPhase.BITE:
            self.timer -= dt
            if self.timer <= 0:
                self._lose("Geç kaldın, balık yemi alıp gitti.")
        elif self.phase == FishPhase.REEL:
            self._reel(dt)

    def _reel(self, dt: float) -> None:
        self.vel -= GRAVITY * dt
        self.bar += self.vel * dt
        top = 1.0 - BAR_SIZE
        if self.bar <= 0.0:
            self.bar, self.vel = 0.0, max(0.0, self.vel * -0.3)
        elif self.bar >= top:
            self.bar, self.vel = top, 0.0
        d = self.fish.difficulty
        self.retarget -= dt
        if self.retarget <= 0:
            self.target = self.rng.random()
            self.retarget = self.rng.uniform(0.6, 1.6) * (1.2 - 0.6 * d)
        speed = 0.18 + 0.40 * d
        step = speed * dt
        self.fish_pos += max(-step, min(step, self.target - self.fish_pos))
        lo, hi = self.bar_range
        inside = lo <= self.fish_pos <= hi
        self.progress += (0.24 if inside else -(0.12 + 0.10 * d)) * dt
        if self.progress >= 1.0:
            self.progress, self.phase = 1.0, FishPhase.CAUGHT
            self.message = f"{self.fish.name} yakaladın! ({self.fish.sell_price}g)"
        elif self.progress <= 0.0:
            self._lose(f"{self.fish.name} kaçtı...")

    def _lose(self, msg: str) -> None:
        self.phase, self.message = FishPhase.LOST, msg
