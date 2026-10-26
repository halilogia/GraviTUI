import tkinter as tk
from theme.colors import ThemeColors
from theme.typography import Typography
from models.advisor_state import AdvisorState

def render_advisor_card(canvas: tk.Canvas, x1: int, y1: int, x2: int, y2: int, state: AdvisorState):
    """Renders the FABLE 5.1 advisor left panel card with proportional spacing."""
    # Outer rectangle with subtle Fable purple border
    canvas.create_rectangle(
        x1, y1, x2, y2,
        fill=ThemeColors.FABLE_BG,
        outline=ThemeColors.FABLE_BORDER,
        width=1
    )
    
    pad_x = x1 + 14
    badge_w = (x2 - x1) - 26
    
    # 1. Header & Subtitle
    canvas.create_text(
        pad_x, y1 + 14,
        text=state.name,
        font=Typography.section(),
        fill=ThemeColors.FABLE_ACCENT,
        anchor="nw"
    )
    
    canvas.create_text(
        pad_x, y1 + 34,
        text=state.subtitle,
        font=Typography.small(),
        fill=ThemeColors.TEXT_SECONDARY,
        anchor="nw"
    )
    
    # 2. Active Phase Badge (◆ before a plan)
    badge_y = y1 + 56
    badge_h = 24
    canvas.create_rectangle(
        pad_x - 3, badge_y,
        pad_x - 3 + badge_w, badge_y + badge_h,
        fill=ThemeColors.FABLE_BADGE_BG,
        outline=ThemeColors.FABLE_ACCENT,
        width=1
    )
    canvas.create_text(
        pad_x + 5, badge_y + 4,
        text=f"◆ {state.active_phase}",
        font=Typography.small_bold(),
        fill=ThemeColors.FABLE_TEXT_BRIGHT,
        anchor="nw"
    )
    
    # 3. Phase description
    canvas.create_text(
        pad_x, y1 + 88,
        text=state.active_desc,
        font=Typography.small(),
        fill=ThemeColors.TEXT_SECONDARY,
        anchor="nw",
        width=badge_w
    )
    
    # 4. Last advice section
    canvas.create_text(
        pad_x, y1 + 150,
        text=state.advice_header,
        font=Typography.small(),
        fill=ThemeColors.TEXT_SECONDARY,
        anchor="nw"
    )
    
    adv_y = y1 + 170
    for adv in state.last_advice:
        canvas.create_text(
            pad_x, adv_y,
            text=f"• {adv}",
            font=Typography.small(),
            fill=ThemeColors.TEXT_PRIMARY,
            anchor="nw"
        )
        adv_y += 18
        
    # 5. Calls & Tokens read metrics
    canvas.create_text(
        pad_x, y1 + 226,
        text=f"calls          {state.calls}",
        font=Typography.small(),
        fill=ThemeColors.TEXT_SECONDARY,
        anchor="nw"
    )
    
    canvas.create_text(
        pad_x, y1 + 250,
        text="tokens read",
        font=Typography.small(),
        fill=ThemeColors.TEXT_SECONDARY,
        anchor="nw"
    )
    canvas.create_text(
        pad_x + 14, y1 + 268,
        text=state.tokens_read,
        font=Typography.small_bold(),
        fill=ThemeColors.TEXT_PRIMARY,
        anchor="nw"
    )
    
    # 6. Routine turn note
    canvas.create_text(
        pad_x, y1 + 306,
        text=state.routine_note,
        font=Typography.small(),
        fill=ThemeColors.TEXT_MUTED,
        anchor="nw",
        width=badge_w
    )
    
    # 7. Error repeats (Inactive diamond)
    canvas.create_text(
        pad_x, y1 + 358,
        text=f"◇ {state.error_phase}",
        font=Typography.small(),
        fill=ThemeColors.TEXT_SECONDARY,
        anchor="nw"
    )
    
    # 8. Never writes code itself rule
    canvas.create_text(
        pad_x, y1 + 392,
        text=state.advice_rule,
        font=Typography.small(),
        fill=ThemeColors.TEXT_MUTED,
        anchor="nw",
        width=badge_w
    )
    
    # 9. Before done (Inactive diamond at bottom)
    canvas.create_text(
        pad_x, y1 + 468,
        text=f"◇ {state.final_phase}",
        font=Typography.small(),
        fill=ThemeColors.TEXT_SECONDARY,
        anchor="nw"
    )
