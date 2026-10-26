from dataclasses import dataclass, field
from typing import List

@dataclass
class AdvisorState:
    name: str = "FABLE 5.1"
    subtitle: str = "advisor · on call"
    active_phase: str = "before a plan"
    active_desc: str = "reads the whole session, every\ntool call and every\nresult"
    advice_header: str = "last advice:"
    last_advice: List[str] = field(default_factory=lambda: [
        "plan skips auth",
        "split in 3 P"
    ])
    calls: int = 1
    tokens_read: str = "93k"
    routine_note: str = "silent on every\nroutine turn"
    error_phase: str = "error repeats"
    advice_rule: str = "never writes\ncode itself.\nOpus applies\nthe advice."
    final_phase: str = "before done"
