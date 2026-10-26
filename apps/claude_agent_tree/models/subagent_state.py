from dataclasses import dataclass

@dataclass
class SubagentState:
    name: str
    model: str = "Opus 5.5"
    effort_level: str = "med"
    effort_blocks: int = 2
    role_description: str = ""
    status: str = "running"
    is_active: bool = True
