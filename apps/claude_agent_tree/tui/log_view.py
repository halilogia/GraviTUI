from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box
from theme.colors import ThemeColors

def get_tag_color(tag: str) -> str:
    t = tag.lower()
    if "fable" in t:
        return ThemeColors.FABLE_ACCENT
    if "jev" in t:
        return ThemeColors.JEV_ACCENT
    if "opus" in t:
        return ThemeColors.OPUS_ACCENT
    return ThemeColors.SUBAGENT_ACCENT

def render_session_logs(logs) -> Panel:
    """Renders the terminal session log panel."""
    grid = Table.grid(expand=True)
    grid.add_column()

    # Show the last 4 to 5 entries
    display_logs = logs[-4:] if len(logs) > 4 else logs
    
    for entry in display_logs:
        source_name = getattr(entry, "source", getattr(entry, "tag", "system"))
        meta_info = getattr(entry, "meta", getattr(entry, "detail", ""))
        col = get_tag_color(source_name)
        line = Text()
        line.append(f" {entry.time}  ", style=f"dim {ThemeColors.TEXT_MUTED}")
        line.append(f"[{source_name:<10}] ", style=f"bold {col}")
        line.append(f"{entry.message:<44} ", style=ThemeColors.TEXT_PRIMARY)
        if meta_info:
            line.append(f"({meta_info})", style="dim cyan")
        grid.add_row(line)

    return Panel(
        grid,
        title=f"[bold {ThemeColors.TEXT_SECONDARY}]── session log ─────────────────────────────────────────────────────────────[/]",
        border_style=ThemeColors.LOG_BORDER,
        box=box.ROUNDED,
        padding=(0, 1)
    )
