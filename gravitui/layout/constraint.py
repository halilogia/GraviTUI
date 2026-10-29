"""Layout kisit siniflari (Percentage, Length, Ratio, Min, Max, Fill)."""
from __future__ import annotations

from dataclasses import dataclass


class Constraint:
    """Taban sinif; alt siniflar `resolve(total)` ile istenen boyutu verir."""

    def resolve(self, total: int) -> int:
        raise NotImplementedError


@dataclass(frozen=True)
class Length(Constraint):
    value: int

    def resolve(self, total: int) -> int:
        return max(0, self.value)


@dataclass(frozen=True)
class Percentage(Constraint):
    value: int

    def resolve(self, total: int) -> int:
        return max(0, total * self.value // 100)


@dataclass(frozen=True)
class Ratio(Constraint):
    num: int
    den: int

    def resolve(self, total: int) -> int:
        return 0 if self.den == 0 else max(0, total * self.num // self.den)


@dataclass(frozen=True)
class Min(Constraint):
    """En az `value`; kalan alani paylasir."""
    value: int

    def resolve(self, total: int) -> int:
        return max(0, self.value)


@dataclass(frozen=True)
class Max(Constraint):
    """En fazla `value`; kalan alani paylasir ama `value`yu asmaz."""
    value: int

    def resolve(self, total: int) -> int:
        return max(0, self.value)


@dataclass(frozen=True)
class Fill(Constraint):
    """Kalan alanin `weight` oranli payi."""
    weight: int = 1

    def resolve(self, total: int) -> int:
        return 0
