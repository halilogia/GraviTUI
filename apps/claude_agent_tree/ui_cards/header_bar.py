import tkinter as tk
from theme.colors import ThemeColors
from theme.typography import Typography
from state.store import AppStore

class HeaderBar(tk.Frame):
    def __init__(self, master, store: AppStore = None):
        super().__init__(master, bg=ThemeColors.BG_CANVAS)
        self.store = store
        self._build_ui()
        if self.store:
            self.store.subscribe(self.update_ui)

    def _build_ui(self):
        # Top title row
        top_row = tk.Frame(self, bg=ThemeColors.BG_CANVAS)
        top_row.pack(fill=tk.X, padx=20, pady=(10, 4))
        
        # Left: App Title
        title = tk.Label(
            top_row,
            text="◈ ANTIGRAVITY AGENT ORCHESTRATION STUDIO ◈",
            font=Typography.title(),
            fg=ThemeColors.TEXT_PRIMARY,
            bg=ThemeColors.BG_CANVAS
        )
        title.pack(side=tk.LEFT)
        
        # Right indicators (Live LED & Model badge)
        right_box = tk.Frame(top_row, bg=ThemeColors.BG_CANVAS)
        right_box.pack(side=tk.RIGHT)
        
        # 🟢 LIVE / 🔴 OFFLINE indicator
        self.tag_live = tk.Label(
            right_box,
            text="🟢 LIVE",
            font=Typography.small_bold(),
            fg=ThemeColors.STATUS_RUNNING,
            bg=ThemeColors.BG_CANVAS
        )
        self.tag_live.pack(side=tk.RIGHT, padx=(14, 0))
        
        # Active Model text
        model_name = self.store.agent_state.host_model if self.store else "GEMINI 3.8 FLASH HIGH"
        self.tag_model = tk.Label(
            right_box,
            text=f"MODEL: {model_name.upper()}",
            font=Typography.small_bold(),
            fg=ThemeColors.CODEX_ACCENT,
            bg=ThemeColors.BG_CANVAS
        )
        self.tag_model.pack(side=tk.RIGHT)

        # Divider line
        divider = tk.Frame(self, bg=ThemeColors.LINE_SEPARATOR, height=1)
        divider.pack(fill=tk.X, padx=20, pady=(6, 8))

        # Legend Row
        legend_row = tk.Frame(self, bg=ThemeColors.BG_CANVAS)
        legend_row.pack(fill=tk.X, padx=20, pady=(0, 4))
        
        legends = [
            ("Host · Antigravity", ThemeColors.ANTIGRAVITY_ACCENT),
            ("Ajan 1 · Claude Code", ThemeColors.CLAUDE_ACCENT),
            ("Ajan 2 · Codex CLI", ThemeColors.CODEX_ACCENT),
            ("Yürütücü · PowerShell", ThemeColors.SHELL_ACCENT),
        ]
        
        for text, color in legends:
            item = tk.Frame(legend_row, bg=ThemeColors.BG_CANVAS)
            item.pack(side=tk.LEFT, padx=(0, 18))
            
            dot = tk.Label(
                item,
                text="■",
                font=Typography.small(),
                fg=color,
                bg=ThemeColors.BG_CANVAS
            )
            dot.pack(side=tk.LEFT, padx=(0, 5))
            
            lbl = tk.Label(
                item,
                text=text,
                font=Typography.small(),
                fg=ThemeColors.TEXT_SECONDARY,
                bg=ThemeColors.BG_CANVAS
            )
            lbl.pack(side=tk.LEFT)

    def update_ui(self):
        if not self.store:
            return
        
        # Update Model label
        current_model = self.store.agent_state.host_model
        self.tag_model.config(text=f"MODEL: {current_model.upper()}")
        
        # Update LIVE / OFFLINE light
        if getattr(self.store, "is_live", True):
            self.tag_live.config(text="🟢 LIVE", fg=ThemeColors.STATUS_RUNNING)
        else:
            self.tag_live.config(text="🔴 OFFLINE", fg=ThemeColors.STATUS_ERROR)
