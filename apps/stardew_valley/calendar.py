"""4 mevsimli takvim ve gün saati (her mevsim 28 gün, gün 06:00'da başlar)."""
from __future__ import annotations

from enum import IntEnum
from typing import List


class Season(IntEnum):
    SPRING = 0
    SUMMER = 1
    FALL = 2
    WINTER = 3


SEASON_NAMES = ("Bahar", "Yaz", "Sonbahar", "Kış")
WEEKDAYS = ("Pzt", "Sal", "Çar", "Per", "Cum", "Cmt", "Paz")
DAYS_PER_SEASON = 28
DAY_START = 6 * 60      # 06:00
MIDNIGHT = 24 * 60      # 00:00 -> "Geç oldu!"
PASSOUT = 26 * 60       # 02:00 -> yorgunluktan bayılma


class GameCalendar:
    def __init__(self, year: int = 1, season: Season = Season.SPRING, day: int = 1) -> None:
        self.year = year
        self.season = Season(season)
        self.day = day
        self.minutes = DAY_START  # 00:00'dan itibaren dakika; 1440+ = gece yarısından sonrası

    # ------------------------------------------------------------ zaman
    def advance(self, minutes: int = 1) -> List[str]:
        """Saati ilerletir; geçilen eşikler için 'late' / 'passout' olaylarını döndürür."""
        old = self.minutes
        self.minutes = min(self.minutes + minutes, PASSOUT)
        events: List[str] = []
        if old < MIDNIGHT <= self.minutes:
            events.append("late")
        if old < PASSOUT <= self.minutes:
            events.append("passout")
        return events

    def next_day(self) -> bool:
        """Yeni güne geçer, saati 06:00 yapar. Mevsim değiştiyse True."""
        self.minutes = DAY_START
        self.day += 1
        if self.day <= DAYS_PER_SEASON:
            return False
        self.day = 1
        self.season = Season((self.season + 1) % 4)
        if self.season == Season.SPRING:
            self.year += 1
        return True

    # ------------------------------------------------------------ durum
    @property
    def is_late(self) -> bool:
        return self.minutes >= MIDNIGHT

    @property
    def is_passout(self) -> bool:
        return self.minutes >= PASSOUT

    @property
    def weekday(self) -> str:
        return WEEKDAYS[(self.day - 1) % 7]

    @property
    def season_name(self) -> str:
        return SEASON_NAMES[self.season]

    @property
    def clock_str(self) -> str:
        return f"{(self.minutes // 60) % 24:02d}:{self.minutes % 60:02d}"

    @property
    def date_str(self) -> str:
        return f"{self.season_name} {self.day}, Yıl {self.year}"

    @property
    def daylight(self) -> float:
        """0 (gündüz) .. 1 (gece) — renderer tonlaması için."""
        return max(0.0, min(1.0, (self.minutes - 18 * 60) / (6 * 60)))
