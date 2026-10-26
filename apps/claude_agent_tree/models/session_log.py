from dataclasses import dataclass
from typing import Optional

@dataclass
class LogEntry:
    time: str
    source: str
    message: str
    meta: Optional[str] = None

    @property
    def tag(self) -> str:
        return self.source

    @property
    def detail(self) -> Optional[str]:
        return self.meta

