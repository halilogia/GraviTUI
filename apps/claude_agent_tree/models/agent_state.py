from dataclasses import dataclass

@dataclass
class AgentState:
    model_name: str = "Opus 5.5"
    session_title: str = "main session"
    role_description: str = "plans + decides"
    effort_level: str = "high"
    effort_blocks: int = 4
    context_window: str = "1M"
    return_title: str = "back to main session · high"
    return_action: str = "review + verify"
