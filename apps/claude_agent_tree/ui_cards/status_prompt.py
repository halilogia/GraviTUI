import tkinter as tk
from theme.colors import ThemeColors
from theme.typography import Typography
from state.store import AppStore

class StatusPrompt(tk.Frame):
    def __init__(self, master, store: AppStore):
        super().__init__(master, bg=ThemeColors.BG_CANVAS)
        self.store = store
        self.selected_target = "Claude Code CLI"
        self._build_ui()
        self.store.subscribe(self.update_state)

    def _build_ui(self):
        container = tk.Frame(self, bg=ThemeColors.BG_CANVAS)
        container.pack(fill=tk.X, padx=20, pady=(2, 14))

        # 1. Target Agent Selector & Quick Chips
        top_row = tk.Frame(container, bg=ThemeColors.BG_CANVAS)
        top_row.pack(fill=tk.X, pady=(0, 8))

        lbl_dispatch = tk.Label(
            top_row,
            text="Antigravity Hedef Ajan:",
            font=Typography.small_bold(),
            fg=ThemeColors.ANTIGRAVITY_ACCENT,
            bg=ThemeColors.BG_CANVAS
        )
        lbl_dispatch.pack(side=tk.LEFT, padx=(0, 8))

        # Target Selector Buttons
        self.btn_claude = tk.Button(
            top_row,
            text="🤖 Claude Code (Sonnet 3.7)",
            font=Typography.small_bold(),
            fg="#0b0f14",
            bg=ThemeColors.CLAUDE_ACCENT,
            relief=tk.FLAT,
            bd=0,
            padx=10,
            pady=2,
            cursor="hand2",
            command=lambda: self._set_target("Claude Code CLI")
        )
        self.btn_claude.pack(side=tk.LEFT, padx=3)

        self.btn_codex = tk.Button(
            top_row,
            text="💻 Codex (GPT-4o)",
            font=Typography.small(),
            fg=ThemeColors.TEXT_PRIMARY,
            bg=ThemeColors.LOG_BORDER,
            relief=tk.FLAT,
            bd=0,
            padx=10,
            pady=2,
            cursor="hand2",
            command=lambda: self._set_target("Codex CLI")
        )
        self.btn_codex.pack(side=tk.LEFT, padx=3)

        # Quick Actions
        quick_actions = [
            ("👋 Selamlaş", "Merhaba! Antigravity üzerinden bağlandım, hazır mısın?"),
            ("📂 Masaüstünü Listele", "Masaüstündeki dosyaları ve projeleri kısaca özetle."),
            ("🔍 Git Durumu", "Bulunduğumuz masaüstü dizini git reposu mu? Kontrol et."),
        ]

        for title, prompt_str in quick_actions:
            btn = tk.Button(
                top_row,
                text=title,
                font=Typography.small(),
                fg=ThemeColors.TEXT_SECONDARY,
                bg=ThemeColors.BG_CANVAS,
                activeforeground=ThemeColors.TEXT_PRIMARY,
                activebackground=ThemeColors.LOG_BORDER,
                relief=tk.FLAT,
                bd=0,
                padx=6,
                pady=2,
                cursor="hand2",
                command=lambda p=prompt_str: self._on_quick_chip(p)
            )
            btn.pack(side=tk.LEFT, padx=2)

        # 2. Interactive Input Box
        input_frame = tk.Frame(
            container,
            bg=ThemeColors.LOG_BG,
            highlightbackground=ThemeColors.LOG_BORDER,
            highlightthickness=1,
            padx=8,
            pady=4
        )
        input_frame.pack(fill=tk.X)

        self.lbl_chevron = tk.Label(
            input_frame,
            text="Antigravity ❯",
            font=Typography.small_bold(),
            fg=ThemeColors.ANTIGRAVITY_ACCENT,
            bg=ThemeColors.LOG_BG
        )
        self.lbl_chevron.pack(side=tk.LEFT, padx=(4, 8))

        self.entry_var = tk.StringVar()
        self.entry = tk.Entry(
            input_frame,
            textvariable=self.entry_var,
            font=Typography.small(),
            fg=ThemeColors.TEXT_PRIMARY,
            bg=ThemeColors.LOG_BG,
            insertbackground=ThemeColors.ANTIGRAVITY_ACCENT,
            relief=tk.FLAT,
            bd=0
        )
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=4)
        self.entry.bind("<Return>", lambda e: self._on_submit())

        self.entry_var.set("Seçili ajana iletilecek komutu buraya yazın (Örn: Masaüstünü tara)...")
        self.entry.bind("<FocusIn>", self._clear_placeholder)

        # Submit Button
        self.btn_submit = tk.Button(
            input_frame,
            text=" AJANA GÖNDER 🚀 ",
            font=Typography.small_bold(),
            fg="#0b0f14",
            bg=ThemeColors.ANTIGRAVITY_ACCENT,
            activeforeground="#0b0f14",
            activebackground=ThemeColors.SUBAGENT_PULSE,
            relief=tk.FLAT,
            bd=0,
            padx=12,
            pady=4,
            cursor="hand2",
            command=self._on_submit
        )
        self.btn_submit.pack(side=tk.RIGHT, padx=4)

        # Cancel / Stop Button (shown when agent is dispatching)
        self.btn_cancel = tk.Button(
            input_frame,
            text=" ⏹️ DURDUR ",
            font=Typography.small_bold(),
            fg="#ffffff",
            bg=ThemeColors.STATUS_ERROR,
            activeforeground="#ffffff",
            activebackground="#dc2626",
            relief=tk.FLAT,
            bd=0,
            padx=10,
            pady=4,
            cursor="hand2",
            command=self._on_cancel
        )


        # 3. Bottom Status Bar
        status_bar = tk.Frame(container, bg=ThemeColors.BG_CANVAS)
        status_bar.pack(fill=tk.X, pady=(6, 0))

        self.lbl_host_info = tk.Label(
            status_bar,
            text=f"◈ Host: {self.store.agent_state.host_name} ({self.store.agent_state.host_model})",
            font=Typography.small(),
            fg=ThemeColors.TEXT_MUTED,
            bg=ThemeColors.BG_CANVAS
        )
        self.lbl_host_info.pack(side=tk.LEFT, padx=(0, 16))

        self.lbl_target_info = tk.Label(
            status_bar,
            text=f"◈ Hedef: {self.selected_target} (Claude 3.7 Sonnet)",
            font=Typography.small(),
            fg=ThemeColors.TEXT_MUTED,
            bg=ThemeColors.BG_CANVAS
        )
        self.lbl_target_info.pack(side=tk.LEFT, padx=(0, 16))

        self.lbl_status = tk.Label(
            status_bar,
            text="● DURUM: ONLINE",
            font=Typography.small_bold(),
            fg=ThemeColors.STATUS_RUNNING,
            bg=ThemeColors.BG_CANVAS
        )
        self.lbl_status.pack(side=tk.RIGHT)

    def _set_target(self, target_name: str):
        self.selected_target = target_name
        if target_name == "Claude Code CLI":
            self.btn_claude.config(bg=ThemeColors.CLAUDE_ACCENT, fg="#0b0f14")
            self.btn_codex.config(bg=ThemeColors.LOG_BORDER, fg=ThemeColors.TEXT_PRIMARY)
            self.lbl_target_info.config(text=f"◈ Hedef: Claude Code CLI (Claude 3.7 Sonnet)")
        else:
            self.btn_codex.config(bg=ThemeColors.CODEX_ACCENT, fg="#0b0f14")
            self.btn_claude.config(bg=ThemeColors.LOG_BORDER, fg=ThemeColors.TEXT_PRIMARY)
            self.lbl_target_info.config(text=f"◈ Hedef: Codex CLI (Codex / GPT-4o)")

    def _clear_placeholder(self, event):
        if "Seçili ajana iletilecek komutu" in self.entry_var.get():
            self.entry_var.set("")

    def _on_quick_chip(self, prompt: str):
        self.entry_var.set(prompt)
        self._on_submit()

    def _on_submit(self):
        text = self.entry_var.get().strip()
        if not text or "Seçili ajana iletilecek" in text:
            return

        self.entry_var.set("")
        self.store.dispatch_prompt_async(text, target_agent=self.selected_target)

    def _on_cancel(self):
        self.store.cancel_current_task()

    def update_state(self):
        is_dispatching = (self.store.agent_state.status == "DISPATCHING")
        if is_dispatching:
            self.lbl_status.config(text="● DURUM: AJAN ÇALIŞIYOR...", fg=ThemeColors.STATUS_RUNNING)
            self.btn_submit.config(text=" ÇALIŞIYOR... ", state=tk.DISABLED, bg=ThemeColors.LINE_FLOW, fg=ThemeColors.TEXT_MUTED)
            if not self.btn_cancel.winfo_ismapped():
                self.btn_cancel.pack(side=tk.RIGHT, padx=4)
        else:
            self.lbl_status.config(text="● DURUM: ONLINE", fg=ThemeColors.STATUS_RUNNING)
            self.btn_submit.config(text=" AJANA GÖNDER 🚀 ", state=tk.NORMAL, bg=ThemeColors.ANTIGRAVITY_ACCENT, fg="#0b0f14")
            if self.btn_cancel.winfo_ismapped():
                self.btn_cancel.pack_forget()

