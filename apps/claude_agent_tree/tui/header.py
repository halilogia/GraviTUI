from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box
from theme.colors import ThemeColors

def render_header(store) -> Panel:
    """Renders the top application header with title, status tags and color legend."""
    table = Table.grid(expand=True)
    table.add_column(justify="left", no_wrap=True)
    table.add_column(justify="right")
    
    left = Text.assemble(
        (" ⚡ ", "bold cyan"),
        ("CLAUDE CODE AGENT TREE", f"bold {ThemeColors.TEXT_PRIMARY}"),
        ("  [TUI Dashboard]", f"dim {ThemeColors.TEXT_SECONDARY}")
    )
    
    right = Text.assemble(
        ("● opus ", ThemeColors.OPUS_ACCENT),
        ("● subagents ", ThemeColors.SUBAGENT_ACCENT),
        ("● jev ", ThemeColors.JEV_ACCENT),
        ("● fable   ", ThemeColors.FABLE_ACCENT),
        ("│ [OPUS 5.5 WORKS] ", f"bold {ThemeColors.OPUS_ACCENT}"),
        ("◆ [FABLE 5.1 ON CALL]", f"bold {ThemeColors.FABLE_ACCENT}"),
        (" ", "")
    )
    table.add_row(left, right)
    
    return Panel(
        table,
        box=box.ROUNDED,
        border_style=ThemeColors.LINE_FLOW,
        padding=(0, 1)
    )
