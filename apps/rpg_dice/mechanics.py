"""RPG rules: DC, modifiers, advantage / disadvantage and check resolution (Baldur's Gate 3 / D&D 5e style)."""
from __future__ import annotations

import random
from dataclasses import dataclass, replace
from enum import Enum
from typing import List, Optional, Tuple

DICE_TYPES = (20, 12, 10, 8, 6, 4, 100)
DEFAULT_DC = {20: 15, 12: 8, 10: 6, 8: 5, 6: 4, 4: 3, 100: 50}
DC_MAX = 150


class RollMode(Enum):
    NORMAL = "Normal"
    ADVANTAGE = "Advantage"
    DISADVANTAGE = "Disadvantage"

    def next(self) -> "RollMode":
        order = list(RollMode)
        return order[(order.index(self) + 1) % len(order)]

    @property
    def dice_count(self) -> int:
        return 1 if self is RollMode.NORMAL else 2


@dataclass(frozen=True)
class ModifierRoll:
    name: str
    label: str
    value: int
    dice: Tuple[int, ...] = ()


@dataclass
class Modifier:
    """Flat bonus (dice_sides == 0) or bonus dice such as Guidance +1d4 / Bardic Inspiration +1d6."""
    name: str
    value: int = 0
    dice_sides: int = 0
    dice_count: int = 1
    enabled: bool = True

    @property
    def is_dice(self) -> bool:
        return self.dice_sides > 0

    @property
    def label(self) -> str:
        return f"+{self.dice_count}d{self.dice_sides}" if self.is_dice else f"{self.value:+d}"

    def adjust(self, delta: int) -> None:
        if self.is_dice:
            self.dice_count = max(1, min(4, self.dice_count + delta))
        else:
            self.value = max(-10, min(15, self.value + delta))

    def roll(self, rng: random.Random) -> ModifierRoll:
        if self.is_dice:
            dice = tuple(rng.randint(1, self.dice_sides) for _ in range(self.dice_count))
            return ModifierRoll(self.name, self.label, sum(dice), dice)
        return ModifierRoll(self.name, self.label, self.value)


def default_modifiers() -> List[Modifier]:
    return [
        Modifier("Ability Mod", value=3),
        Modifier("Proficiency", value=2),
        Modifier("Guidance", dice_sides=4, enabled=False),
        Modifier("Bardic Insp.", dice_sides=6, enabled=False),
        Modifier("Bless", dice_sides=4, enabled=False),
    ]


@dataclass(frozen=True)
class CheckResult:
    sides: int
    mode: RollMode
    rolls: Tuple[int, ...]
    kept_index: int
    parts: Tuple[ModifierRoll, ...]
    dc: int
    total: int
    success: bool
    crit: Optional[str]  # "success" (natural 20), "failure" (natural 1) or None

    @property
    def natural(self) -> int:
        return self.rolls[self.kept_index]

    @property
    def bonus(self) -> int:
        return sum(p.value for p in self.parts)

    @property
    def margin(self) -> int:
        return self.total - self.dc

    @property
    def verdict(self) -> str:
        if self.crit == "success":
            return "CRITICAL SUCCESS"
        if self.crit == "failure":
            return "CRITICAL FAILURE"
        return "SUCCESS" if self.success else "FAILURE"

    def with_dc(self, dc: int) -> "CheckResult":
        return replace(self, dc=dc, success=_succeeds(self.total, dc, self.crit))


def _succeeds(total: int, dc: int, crit: Optional[str]) -> bool:
    if crit == "success":
        return True
    if crit == "failure":
        return False
    return total >= dc


def roll_check(sides: int, dc: int, mode: RollMode, mods: List[Modifier],
               rng: random.Random, forced: Optional[int] = None) -> CheckResult:
    """Roll the die (twice with advantage/disadvantage), add enabled modifiers, compare against DC."""
    n = mode.dice_count
    rolls = tuple(forced if forced is not None else rng.randint(1, sides) for _ in range(n))
    if mode is RollMode.ADVANTAGE:
        kept = max(range(n), key=lambda i: rolls[i])
    elif mode is RollMode.DISADVANTAGE:
        kept = min(range(n), key=lambda i: rolls[i])
    else:
        kept = 0
    natural = rolls[kept]
    parts = tuple(m.roll(rng) for m in mods if m.enabled)
    total = natural + sum(p.value for p in parts)
    crit = None
    if sides == 20:
        crit = "success" if natural == 20 else "failure" if natural == 1 else None
    return CheckResult(sides, mode, rolls, kept, parts, dc, total, _succeeds(total, dc, crit), crit)


def format_formula(res: CheckResult, upto: Optional[int] = None) -> str:
    """'14 +3 +2 = 19' style string; `upto` limits how many modifier parts are shown."""
    parts = res.parts if upto is None else res.parts[:upto]
    s = f"{res.natural}" + "".join(f" {p.value:+d}" for p in parts)
    return s + f" = {res.natural + sum(p.value for p in parts)}"


def face_for_value(sides: int, value: int) -> int:
    """Index of the die face that must point at the camera for a given rolled value."""
    if sides == 100:
        return (value % 100) // 10
    return max(0, min(sides - 1, value - 1))
