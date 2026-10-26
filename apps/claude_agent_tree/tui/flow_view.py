from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box
from rich.align import Align
from theme.colors import ThemeColors

def render_flow_tree(store) -> Table:
    """Renders the complete hierarchical Agent Tree flow layout."""
    grid = Table.grid(expand=True)
    grid.add_column()

    # 1. Top Card: Opus 5.5 Main Session
    opus_t = Text()
    opus_t.append(f"{store.agent_state.model_name} · {store.agent_state.session_title}  │  ", style=f"bold {ThemeColors.OPUS_ACCENT}")
    opus_t.append(f"{store.agent_state.role_description}  │  ", style=ThemeColors.TEXT_PRIMARY)
    opus_t.append("effort ", style=ThemeColors.TEXT_SECONDARY)
    opus_t.append("▮" * store.agent_state.effort_blocks, style=f"bold {ThemeColors.OPUS_ACCENT}")
    opus_t.append(f" {store.agent_state.effort_level}  │  context: ", style=ThemeColors.TEXT_SECONDARY)
    opus_t.append(f"{store.agent_state.context_window}", style=f"bold {ThemeColors.TEXT_PRIMARY}")
    
    opus_panel = Panel(
        Align.center(opus_t),
        border_style=ThemeColors.OPUS_BORDER,
        box=box.ROUNDED,
        padding=(0, 1)
    )
    grid.add_row(opus_panel)

    # Connector 1: Opus down to JEV
    c1 = Align.center(Text("│\n▼", style=f"bold {ThemeColors.LINE_FLOW}"))
    grid.add_row(c1)

    # 2. Middle Card: JEV · fork layer
    jev_table = Table.grid(expand=True)
    jev_table.add_column(justify="left", ratio=3)
    jev_table.add_column(justify="right", ratio=2)
    
    j_title = Text.assemble((store.fork_metrics.layer_name, f"bold {ThemeColors.JEV_ACCENT}"))
    j_forks = Text.assemble(("forks ", f"dim {ThemeColors.TEXT_SECONDARY}"), (store.fork_metrics.forks_count, f"bold {ThemeColors.JEV_ACCENT}"))
    jev_table.add_row(j_title, j_forks)
    
    for meter in store.fork_metrics.meters:
        filled = int(meter.value * 14)
        empty = 14 - filled
        bar = "█" * filled + "░" * empty
        pct = f"{int(meter.value * 100)}%"
        row_text = Text.assemble(
            (f"{meter.label:<14}", ThemeColors.TEXT_PRIMARY),
            (f" [{bar}] ", ThemeColors.JEV_ACCENT),
            (f"{pct:>4} ", f"bold {ThemeColors.TEXT_PRIMARY}"),
            (f"{meter.tag}", "dim green")
        )
        jev_table.add_row(row_text, Text(""))
    
    jev_footnote = Text(store.fork_metrics.footnote, style=f"italic dim {ThemeColors.TEXT_SECONDARY}")
    jev_table.add_row(jev_footnote, Text(""))
    
    jev_panel = Panel(
        jev_table,
        border_style=ThemeColors.JEV_BORDER,
        box=box.ROUNDED,
        padding=(0, 1)
    )
    grid.add_row(jev_panel)

    # Connector 2: Distribution Bus
    bus_text = Text()
    bus_text.append("             delegate to subagents · effort medium\n", style=f"dim {ThemeColors.TEXT_SECONDARY}")
    bus_text.append("             ┌───────────────────┼───────────────────┐\n", style=f"bold {ThemeColors.LINE_FLOW}")
    bus_text.append("             ▼                   ▼                   ▼", style=f"bold {ThemeColors.LINE_FLOW}")
    grid.add_row(Align.center(bus_text))

    # 3. Subagent Cards (worker, explorer, researcher)
    pulse_frames = ["◎", "◉", "●", "○"]
    pulse_char = pulse_frames[store.pulse_phase % len(pulse_frames)]
    if store.paused:
        pulse_char = "⏸"

    def make_subagent_panel(agent):
        st = Text()
        st.append(f"{agent.name}\n", style=f"bold {ThemeColors.SUBAGENT_ACCENT}")
        st.append(f"{agent.model} │ effort {'▮' * agent.effort_blocks} {agent.effort_level}\n", style=ThemeColors.TEXT_PRIMARY)
        st.append(f"{agent.role_description}\n", style=f"dim {ThemeColors.TEXT_SECONDARY}")
        
        status_color = ThemeColors.SUBAGENT_ACCENT if agent.status == "running" else "yellow"
        st.append(f"{pulse_char} {agent.status}", style=f"bold {status_color}")
        
        return Panel(
            Align.center(st),
            border_style=ThemeColors.SUBAGENT_BORDER,
            box=box.ROUNDED,
            padding=(0, 1)
        )

    sub_table = Table.grid(expand=True)
    for _ in store.subagents:
        sub_table.add_column(ratio=1)
        
    sub_panels = [make_subagent_panel(agent) for agent in store.subagents]
    sub_table.add_row(*sub_panels)
    grid.add_row(sub_table)

    # Connector 3: Convergence Bus
    ret_bus = Text()
    ret_bus.append("             ▲                   ▲                   ▲\n", style=f"bold {ThemeColors.LINE_FLOW}")
    ret_bus.append("             └───────────────────┼───────────────────┘\n", style=f"bold {ThemeColors.LINE_FLOW}")
    ret_bus.append("                                 ▼", style=f"bold {ThemeColors.LINE_FLOW}")
    grid.add_row(Align.center(ret_bus))

    # 4. Bottom Return Box: back to main session
    ret_t = Text()
    ret_t.append(f"{store.agent_state.return_title}  │  ", style=f"bold {ThemeColors.OPUS_ACCENT}")
    ret_t.append(f"{store.agent_state.return_action}", style=ThemeColors.TEXT_PRIMARY)
    
    ret_panel = Panel(
        Align.center(ret_t),
        border_style=ThemeColors.OPUS_BORDER,
        box=box.ROUNDED,
        padding=(0, 1)
    )
    grid.add_row(ret_panel)

    return grid
