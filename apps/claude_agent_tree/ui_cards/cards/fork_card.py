import tkinter as tk
from theme.colors import ThemeColors
from theme.typography import Typography
from models.fork_metrics import ForkMetrics

def render_fork_card(canvas: tk.Canvas, x1: int, y1: int, x2: int, y2: int, metrics: ForkMetrics):
    """Renders the JEV · fork layer card with meters and confidence indicators."""
    canvas.create_rectangle(
        x1, y1, x2, y2,
        fill=ThemeColors.JEV_BG,
        outline=ThemeColors.JEV_BORDER,
        width=1
    )
    
    pad_x = x1 + 14
    curr_y = y1 + 10
    
    # 1. Header: 'JEV · fork layer' on left, 'forks 1,320' on right
    canvas.create_text(
        pad_x, curr_y,
        text=metrics.layer_name,
        font=Typography.small_bold(),
        fill=ThemeColors.JEV_ACCENT,
        anchor="nw"
    )
    
    right_x = x2 - 14
    canvas.create_text(
        right_x, curr_y,
        text=f"forks    {metrics.forks_count}",
        font=Typography.small_bold(),
        fill=ThemeColors.JEV_ACCENT,
        anchor="ne"
    )
    curr_y += 24
    
    # 2. Three Confidence Meters
    bar_width = 86
    bar_height = 10
    
    for meter in metrics.meters:
        # Label on left (e.g. 'which file')
        canvas.create_text(
            pad_x, curr_y,
            text=f"{meter.label:<14}",
            font=Typography.small(),
            fill=ThemeColors.TEXT_PRIMARY,
            anchor="nw"
        )
        
        # Vector Bar in center
        bar_x1 = pad_x + 108
        bar_y1 = curr_y + 2
        bar_x2 = bar_x1 + bar_width
        bar_y2 = bar_y1 + bar_height
        
        # Bar background container
        canvas.create_rectangle(
            bar_x1, bar_y1, bar_x2, bar_y2,
            fill=ThemeColors.JEV_BAR_BG,
            outline=ThemeColors.JEV_BORDER,
            width=1
        )
        
        # Bar fill based on score
        fill_w = int(bar_width * meter.value)
        if fill_w > 0:
            canvas.create_rectangle(
                bar_x1 + 1, bar_y1 + 1, bar_x1 + fill_w, bar_y2 - 1,
                fill=ThemeColors.JEV_BAR_FILL,
                outline="",
            )
            
        # Value & Tag on right (e.g. '0.94 sharp')
        val_x = bar_x2 + 12
        canvas.create_text(
            val_x, curr_y,
            text=f"{meter.value:.2f} {meter.tag}",
            font=Typography.small(),
            fill=ThemeColors.JEV_ACCENT,
            anchor="nw"
        )
        
        curr_y += 20
        
    curr_y += 4
    
    # 3. Footnote: 'sharp -> runs in code   split -> Opus'
    canvas.create_text(
        pad_x, curr_y,
        text=metrics.footnote,
        font=Typography.small(),
        fill=ThemeColors.TEXT_MUTED,
        anchor="nw"
    )
