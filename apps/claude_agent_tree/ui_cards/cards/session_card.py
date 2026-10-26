import tkinter as tk
from theme.colors import ThemeColors
from theme.typography import Typography
from models.agent_state import AgentState

def render_session_card(canvas: tk.Canvas, x1: int, y1: int, x2: int, y2: int, state: AgentState):
    """Renders the top Opus 5.5 main session card."""
    canvas.create_rectangle(
        x1, y1, x2, y2,
        fill=ThemeColors.OPUS_BG,
        outline=ThemeColors.OPUS_BORDER,
        width=1
    )
    
    mid_x = (x1 + x2) // 2
    curr_y = y1 + 10
    
    # Title: Opus 5.5 · main session
    canvas.create_text(
        mid_x, curr_y,
        text=f"{state.model_name} · {state.session_title}",
        font=Typography.small_bold(),
        fill=ThemeColors.OPUS_ACCENT,
        anchor="n"
    )
    curr_y += 18
    
    # Subtitle: plans + decides
    canvas.create_text(
        mid_x, curr_y,
        text=state.role_description,
        font=Typography.small(),
        fill=ThemeColors.TEXT_PRIMARY,
        anchor="n"
    )
    curr_y += 18
    
    # Effort blocks: effort ▮▮▮▮ high
    effort_blocks = "▮" * state.effort_blocks
    effort_str = f"effort {effort_blocks} {state.effort_level}"
    canvas.create_text(
        mid_x, curr_y,
        text=effort_str,
        font=Typography.small(),
        fill=ThemeColors.OPUS_ACCENT,
        anchor="n"
    )
    curr_y += 18
    
    # Context info: context: 1M
    canvas.create_text(
        mid_x, curr_y,
        text=f"context: {state.context_window}",
        font=Typography.small(),
        fill=ThemeColors.TEXT_SECONDARY,
        anchor="n"
    )

def render_return_card(canvas: tk.Canvas, x1: int, y1: int, x2: int, y2: int, state: AgentState):
    """Renders the bottom return card 'back to main session · high'."""
    canvas.create_rectangle(
        x1, y1, x2, y2,
        fill=ThemeColors.OPUS_BG,
        outline=ThemeColors.OPUS_BORDER,
        width=1
    )
    
    mid_x = (x1 + x2) // 2
    curr_y = y1 + 10
    
    canvas.create_text(
        mid_x, curr_y,
        text=state.return_title,
        font=Typography.small_bold(),
        fill=ThemeColors.OPUS_ACCENT,
        anchor="n"
    )
    curr_y += 18
    
    canvas.create_text(
        mid_x, curr_y,
        text=state.return_action,
        font=Typography.small(),
        fill=ThemeColors.TEXT_PRIMARY,
        anchor="n"
    )
