from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box
from theme.colors import ThemeColors

def render_advisor(advisor_state) -> Panel:
    """Renders the left column FABLE 5.1 Advisor card with adaptive layout."""
    grid = Table.grid(expand=True)
    grid.add_column()

    # Header & Subtitle
    t_header = Text()
    t_header.append(f"{advisor_state.name}\n", style=f"bold {ThemeColors.FABLE_ACCENT}")
    t_header.append(f"{advisor_state.subtitle}\n", style=f"dim {ThemeColors.TEXT_SECONDARY}")
    grid.add_row(t_header)

    # Active Phase Badge (Nested mini-panel for clean auto-sizing)
    badge_text = Text(f"◆ {advisor_state.active_phase}", style=f"bold {ThemeColors.FABLE_TEXT_BRIGHT}")
    phase_badge = Panel(
        badge_text,
        border_style=ThemeColors.FABLE_ACCENT,
        box=box.ROUNDED,
        style=f"on {ThemeColors.FABLE_BADGE_BG}",
        padding=(0, 1)
    )
    grid.add_row(phase_badge)

    # Description & Body
    t_body = Text()
    t_body.append(f"{advisor_state.active_desc}\n\n", style=ThemeColors.TEXT_SECONDARY)
    
    t_body.append(f"{advisor_state.advice_header}\n", style=f"dim {ThemeColors.TEXT_SECONDARY}")
    for adv in advisor_state.last_advice:
        t_body.append(f"• {adv}\n", style=f"bold {ThemeColors.TEXT_PRIMARY}")
    t_body.append("\n")
    
    t_body.append("calls: ", style=ThemeColors.TEXT_SECONDARY)
    t_body.append(f"{advisor_state.calls}  ", style=f"bold {ThemeColors.TEXT_PRIMARY}")
    t_body.append("tokens: ", style=ThemeColors.TEXT_SECONDARY)
    t_body.append(f"{advisor_state.tokens_read}\n\n", style=f"bold {ThemeColors.FABLE_ACCENT}")
    
    t_body.append(f"{advisor_state.routine_note}\n\n", style=f"italic {ThemeColors.TEXT_MUTED}")
    t_body.append(f"◇ {advisor_state.error_phase}\n", style=ThemeColors.TEXT_SECONDARY)
    t_body.append(f"{advisor_state.advice_rule}\n", style=f"italic {ThemeColors.TEXT_MUTED}")
    t_body.append(f"◇ {advisor_state.final_phase}", style=ThemeColors.TEXT_SECONDARY)
    
    grid.add_row(t_body)

    return Panel(
        grid,
        title=f"[bold {ThemeColors.FABLE_ACCENT}]Advisor[/]",
        border_style=ThemeColors.FABLE_BORDER,
        box=box.ROUNDED,
        padding=(0, 1)
    )
