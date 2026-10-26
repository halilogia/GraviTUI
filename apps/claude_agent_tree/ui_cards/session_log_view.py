import tkinter as tk
from theme.colors import ThemeColors
from theme.typography import Typography
from state.store import AppStore
from models.session_log import LogEntry

class SessionLogView(tk.Frame):
    def __init__(self, master, store: AppStore):
        super().__init__(master, bg=ThemeColors.BG_CANVAS)
        self.store = store
        self.auto_scroll = True
        self._build_ui()
        self.store.subscribe(self.render_logs)

    def _build_ui(self):
        # Container frame
        self.container = tk.Frame(
            self,
            bg=ThemeColors.LOG_BG,
            highlightbackground=ThemeColors.LOG_BORDER,
            highlightthickness=1
        )
        self.container.pack(fill=tk.BOTH, expand=True, padx=20, pady=(4, 6))

        # Header bar of log view
        top_bar = tk.Frame(self.container, bg=ThemeColors.LOG_BG)
        top_bar.pack(fill=tk.X, padx=12, pady=(8, 4))

        lbl_title = tk.Label(
            top_bar,
            text="── 📟 CLAUDE CODE CANLI GÖREV & TERMİNAL GÜNLÜĞÜ ",
            font=Typography.small_bold(),
            fg=ThemeColors.MASTER_ACCENT,
            bg=ThemeColors.LOG_BG
        )
        lbl_title.pack(side=tk.LEFT)

        # Clear Button
        btn_clear = tk.Button(
            top_bar,
            text="Temizle",
            font=Typography.small(),
            fg=ThemeColors.TEXT_MUTED,
            bg=ThemeColors.LOG_BG,
            activeforeground=ThemeColors.TEXT_PRIMARY,
            activebackground=ThemeColors.LOG_BORDER,
            relief=tk.FLAT,
            bd=0,
            command=self._on_clear
        )
        btn_clear.pack(side=tk.RIGHT, padx=6)

        # Log Text Box with native scrollbar
        text_frame = tk.Frame(self.container, bg=ThemeColors.LOG_BG)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(2, 8))

        self.scrollbar = tk.Scrollbar(text_frame)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.text_area = tk.Text(
            text_frame,
            bg=ThemeColors.LOG_BG,
            fg=ThemeColors.TEXT_PRIMARY,
            font=Typography.small(),
            wrap=tk.WORD,
            height=12,
            bd=0,
            highlightthickness=0,
            yscrollcommand=self.scrollbar.set
        )
        self.text_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.config(command=self.text_area.yview)

        # Color Tags configuration
        self.text_area.tag_config("TIME", foreground=ThemeColors.TEXT_MUTED)
        self.text_area.tag_config("MASTER", foreground=ThemeColors.MASTER_ACCENT, font=Typography.small_bold())
        self.text_area.tag_config("STATUS", foreground=ThemeColors.STATUS_RUNNING, font=Typography.small_bold())
        self.text_area.tag_config("OUTPUT", foreground="#e2e8f0")
        self.text_area.tag_config("ENV", foreground=ThemeColors.EXPLORER_ACCENT)
        self.text_area.tag_config("ERROR", foreground=ThemeColors.STATUS_ERROR, font=Typography.small_bold())
        self.text_area.tag_config("LOG", foreground=ThemeColors.TEXT_SECONDARY)

        self.rendered_count = 0
        self.render_logs()

    def _on_clear(self):
        self.store.clear_logs()
        self.text_area.delete("1.0", tk.END)
        self.rendered_count = 0

    def render_logs(self):
        logs = self.store.logs
        if len(logs) == self.rendered_count:
            return

        # If logs cleared
        if len(logs) < self.rendered_count:
            self.text_area.delete("1.0", tk.END)
            self.rendered_count = 0

        # Append newly arrived logs only
        new_entries = logs[self.rendered_count:]
        for entry in new_entries:
            tag = entry.source.upper() if entry.source.upper() in ["MASTER", "STATUS", "OUTPUT", "ENV", "ERROR"] else "LOG"
            
            # Format: [HH:MM:SS] [SOURCE] Message
            self.text_area.insert(tk.END, f"[{entry.time}] ", "TIME")
            self.text_area.insert(tk.END, f"[{entry.source:<7}] ", tag)
            self.text_area.insert(tk.END, f"{entry.message}\n", tag if tag in ["STATUS", "ERROR"] else "OUTPUT")

        self.rendered_count = len(logs)

        # Auto-scroll to end
        if self.auto_scroll:
            self.text_area.see(tk.END)
