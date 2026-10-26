from dataclasses import dataclass, field
from typing import List

@dataclass
class ConfidenceMeter:
    label: str
    value: float
    tag: str = "sharp"
    total_blocks: int = 10

    @property
    def filled_blocks(self) -> int:
        return int(round(self.value * self.total_blocks))

@dataclass
class ForkMetrics:
    layer_name: str = "JEV · fork layer"
    forks_count: str = "1,320"
    meters: List[ConfidenceMeter] = field(default_factory=lambda: [
        ConfidenceMeter("which file", 0.94, "sharp"),
        ConfidenceMeter("which tool", 0.88, "sharp"),
        ConfidenceMeter("retry or stop", 0.85, "sharp"),
    ])
    footnote: str = "sharp -> runs in code   split -> Opus"
