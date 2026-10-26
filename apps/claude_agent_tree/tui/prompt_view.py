from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box
from theme.colors import ThemeColors

def render_prompt_bar(store) -> Panel:
    """Renders the bottom prompt line with blinking cursor and status capsules."""
    grid = Table.grid(expand=True)
    grid.add_column(justify="left", no_wrap=True)
    grid.add_column(justify="right", no_wrap=True)
    
    cur_char = "█" if store.cursor_visible else " "
    prompt = Text.assemble(
        (" ❯ ", f"bold {ThemeColors.JEV_ACCENT}"),
        (f"{store.prompt_text} ", f"bold {ThemeColors.TEXT_PRIMARY}"),
        (cur_char, f"bold {ThemeColors.CURSOR_COLOR}")
    )
    
    pills = Text.assemble(
        ("effort ", f"dim {ThemeColors.TEXT_SECONDARY}"),
        (f"[{store.status_pills.get('effort', 'high/med')}]  ", f"bold {ThemeColors.OPUS_ACCENT}"),
        ("subagents ", f"dim {ThemeColors.TEXT_SECONDARY}"),
        (f"[{store.status_pills.get('subagents', '3/3')}]  ", f"bold {ThemeColors.SUBAGENT_ACCENT}"),
        ("fable ", f"dim {ThemeColors.TEXT_SECONDARY}"),
        (f"[{store.status_pills.get('fable', 'advising')}]  ", f"bold {ThemeColors.FABLE_ACCENT}"),
        ("jev ", f"dim {ThemeColors.TEXT_SECONDARY}"),
        (f"[{store.status_pills.get('jev', '1,320 forks')}]  ", f"bold {ThemeColors.JEV_ACCENT}"),
        ("[Q: quit]", f"bold {ThemeColors.TEXT_WHITE}")
    )
    
    grid.add_row(prompt, pills)
    
    return Panel(
        grid,
        box=box.ROUNDED,
        border_style=ThemeColors.LINE_FLOW,
        padding=(0, 1)
    )
