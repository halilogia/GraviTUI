from rich.layout import Layout
from .header import render_header
from .advisor_view import render_advisor
from .flow_view import render_flow_tree
from .log_view import render_session_logs
from .prompt_view import render_prompt_bar

def build_dashboard_layout(store, console_width: int = 120, console_height: int = 38) -> Layout:
    """Builds the complete responsive Rich Layout for the Claude Code Agent Tree dashboard."""
    layout = Layout()
    
    # Calculate adaptive heights based on terminal vertical room
    header_size = 3
    footer_size = 3
    logs_size = 6 if console_height >= 34 else 5
    
    layout.split_column(
        Layout(name="header", size=header_size),
        Layout(name="main", ratio=1),
        Layout(name="logs", size=logs_size),
        Layout(name="footer", size=footer_size)
    )
    
    # Adaptive advisor panel width
    advisor_width = 30 if console_width >= 100 else 26
    layout["main"].split_row(
        Layout(name="advisor", size=advisor_width),
        Layout(name="tree", ratio=1)
    )
    
    layout["header"].update(render_header(store))
    layout["advisor"].update(render_advisor(store.advisor_state))
    layout["tree"].update(render_flow_tree(store))
    layout["logs"].update(render_session_logs(store.logs))
    layout["footer"].update(render_prompt_bar(store))
    
    return layout
