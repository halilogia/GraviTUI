import tkinter as tk
from theme.colors import ThemeColors
from theme.typography import Typography
from models.subagent_state import SubagentState

def render_subagent_card(
    canvas: tk.Canvas,
    x1: int,
    y1: int,
    x2: int,
    y2: int,
    agent: SubagentState,
    pulse_phase: int = 0
):
    """Renders an individual subagent card (worker, explorer, researcher)."""
    # Card outer container
    canvas.create_rectangle(
        x1, y1, x2, y2,
        fill=ThemeColors.SUBAGENT_BG,
        outline=ThemeColors.SUBAGENT_BORDER,
        width=1
    )
    
    mid_x = (x1 + x2) // 2
    curr_y = y1 + 10
    
    # 1. Agent Name (worker, explorer, researcher)
    canvas.create_text(
        mid_x, curr_y,
        text=agent.name,
        font=Typography.small_bold(),
        fill=ThemeColors.SUBAGENT_ACCENT,
        anchor="n"
    )
    curr_y += 18
    
    # 2. Model: Opus 5.5
    canvas.create_text(
        mid_x, curr_y,
        text=agent.model,
        font=Typography.small(),
        fill=ThemeColors.TEXT_PRIMARY,
        anchor="n"
    )
    curr_y += 18
    
    # 3. Effort: effort ▮▮ med
    effort_blocks = "▮" * agent.effort_blocks
    effort_str = f"effort {effort_blocks} {agent.effort_level}"
    canvas.create_text(
        mid_x, curr_y,
        text=effort_str,
        font=Typography.small(),
        fill=ThemeColors.SUBAGENT_ACCENT,
        anchor="n"
    )
    curr_y += 18
    
    # 4. Role description (edits + runs tests, etc.)
    canvas.create_text(
        mid_x, curr_y,
        text=agent.role_description,
        font=Typography.small(),
        fill=ThemeColors.TEXT_SECONDARY,
        anchor="n"
    )
    curr_y += 20
    
    # 5. Status: '◎ running' with animated pulsing dot
    status_y = curr_y + 4
    dot_radius = 4
    dot_center_x = mid_x - 30
    
    # Outer ring
    canvas.create_oval(
        dot_center_x - dot_radius, status_y - dot_radius,
        dot_center_x + dot_radius, status_y + dot_radius,
        outline=ThemeColors.SUBAGENT_PULSE,
        fill="",
        width=1
    )
    
    # Inner dot (subtle pulse based on pulse_phase)
    inner_r = 2 if (pulse_phase % 2 == 0) else 1
    canvas.create_oval(
        dot_center_x - inner_r, status_y - inner_r,
        dot_center_x + inner_r, status_y + inner_r,
        outline="",
        fill=ThemeColors.SUBAGENT_ACCENT
    )
    
    canvas.create_text(
        dot_center_x + 10, status_y,
        text=agent.status,
        font=Typography.small(),
        fill=ThemeColors.SUBAGENT_ACCENT,
        anchor="w"
    )
