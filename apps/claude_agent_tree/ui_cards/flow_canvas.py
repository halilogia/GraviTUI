import tkinter as tk
from theme.colors import ThemeColors
from theme.typography import Typography
from state.store import AppStore

class FlowCanvas(tk.Canvas):
    def __init__(self, master, store: AppStore):
        super().__init__(
            master,
            bg=ThemeColors.BG_CANVAS,
            highlightthickness=0,
            height=390
        )
        self.store = store
        self.store.subscribe(self.redraw)
        self.bind("<Configure>", lambda e: self.redraw())

    def redraw(self):
        self.delete("all")
        width = self.winfo_width()
        height = self.winfo_height()
        
        if width < 100:
            width = 800
        if height < 100:
            height = 390

        mid_x = width // 2

        # ══════════════════════════════════════════════════════════════════════
        # 1. ROOT NODE: ANTIGRAVITY (ANA SOHBET & SEÇİLİ MODELİ)
        # ══════════════════════════════════════════════════════════════════════
        host_w = min(600, width - 48)
        host_h = 104
        host_x1 = mid_x - (host_w // 2)
        host_x2 = mid_x + (host_w // 2)
        host_y1 = 16
        host_y2 = host_y1 + host_h

        is_dispatching = (self.store.agent_state.status == "DISPATCHING")
        pulse_color = ThemeColors.STATUS_RUNNING if is_dispatching else ThemeColors.ANTIGRAVITY_BORDER

        # Background Box
        self.create_rectangle(
            host_x1, host_y1, host_x2, host_y2,
            fill=ThemeColors.ANTIGRAVITY_BG,
            outline=ThemeColors.STATUS_RUNNING if is_dispatching else ThemeColors.ANTIGRAVITY_BORDER,
            width=2 if is_dispatching else 1
        )

        # Subtle glow effect if dispatching
        if is_dispatching:
            pulse_offset = (self.store.pulse_phase + 1) * 2
            self.create_rectangle(
                host_x1 - pulse_offset, host_y1 - pulse_offset,
                host_x2 + pulse_offset, host_y2 + pulse_offset,
                outline=ThemeColors.STATUS_RUNNING,
                width=1
            )

        # Host Title & Status Badge
        self.create_text(
            host_x1 + 18, host_y1 + 14,
            text="🌌 ANTIGRAVITY — ANA SOHBET (HOST ORCHESTRATOR)",
            font=Typography.small_bold(),
            fill=ThemeColors.ANTIGRAVITY_ACCENT,
            anchor="nw"
        )
        if getattr(self.store, "is_live", True):
            status_text = "🟢 LIVE (ÇALIŞIYOR)" if not is_dispatching else "🟢 AJAN YÖNETİYOR"
            status_color = ThemeColors.STATUS_RUNNING
        else:
            status_text = "🔴 OFFLINE"
            status_color = ThemeColors.STATUS_ERROR

        self.create_text(
            host_x2 - 18, host_y1 + 14,
            text=status_text,
            font=Typography.small_bold(),
            fill=status_color,
            anchor="ne"
        )

        # Host Selected Model Badge (Altın/Cyan vurgulu)
        model_pill_text = f"✦ Seçili Host Modeli : {self.store.agent_state.host_model}"
        self.create_text(
            host_x1 + 18, host_y1 + 38,
            text=model_pill_text,
            font=Typography.small_bold(),
            fill="#38bdf8",
            anchor="nw"
        )

        # Role & Workspace
        self.create_text(
            host_x1 + 18, host_y1 + 58,
            text=f"Çalışma Alanı : {self.store.agent_state.workspace}  •  Yetki: Tam Ajan Çağırma",
            font=Typography.small(),
            fill=ThemeColors.TEXT_SECONDARY,
            anchor="nw"
        )

        # Current Command banner
        last_cmd = self.store.agent_state.last_command
        if len(last_cmd) > 65:
            last_cmd = last_cmd[:62] + "..."
        self.create_text(
            host_x1 + 18, host_y1 + 78,
            text=f"❯ Delegasyon : {last_cmd}",
            font=Typography.small(),
            fill=ThemeColors.TEXT_PRIMARY,
            anchor="nw"
        )

        # ══════════════════════════════════════════════════════════════════════
        # 2. DELEGATION BUS (Antigravity'den Ajanlara İnen Dağıtım Hattı)
        # ══════════════════════════════════════════════════════════════════════
        bus_y1 = host_y2
        bus_y2 = bus_y1 + 30
        
        # Central spine down
        self.create_line(
            mid_x, bus_y1,
            mid_x, bus_y2,
            fill=pulse_color,
            width=2
        )

        # Horizontal bus
        card_w = (width - 48 - 32) // 3
        card_w = min(card_w, 240)

        card1_mid = mid_x - card_w - 16
        card2_mid = mid_x
        card3_mid = mid_x + card_w + 16

        self.create_line(
            card1_mid, bus_y2,
            card3_mid, bus_y2,
            fill=pulse_color,
            width=2
        )

        # Bus label
        self.create_text(
            mid_x, bus_y2 - 8,
            text="─── Antigravity CLI Ajanı Çağırıyor ───",
            font=Typography.small(),
            fill=ThemeColors.TEXT_MUTED,
            anchor="s"
        )

        # Connectors down to each agent
        for target_mid in [card1_mid, card2_mid, card3_mid]:
            self.create_line(
                target_mid, bus_y2,
                target_mid, bus_y2 + 18,
                fill=pulse_color,
                width=2,
                arrow=tk.LAST,
                arrowshape=(6, 8, 3)
            )

        # ══════════════════════════════════════════════════════════════════════
        # 3. DISPATCHED AGENTS (Claude Code CLI, Codex CLI, Shell Runner)
        # ══════════════════════════════════════════════════════════════════════
        sub_y1 = bus_y2 + 18
        sub_h = 142
        sub_y2 = sub_y1 + sub_h

        agents_data = [
            (card1_mid, self.store.subagents[0], ThemeColors.CLAUDE_ACCENT, ThemeColors.CLAUDE_BG, ThemeColors.CLAUDE_BORDER),
            (card2_mid, self.store.subagents[1], ThemeColors.CODEX_ACCENT, ThemeColors.CODEX_BG, ThemeColors.CODEX_BORDER),
            (card3_mid, self.store.subagents[2], ThemeColors.SHELL_ACCENT, ThemeColors.SHELL_BG, ThemeColors.SHELL_BORDER),
        ]

        for c_mid, agent, accent, bg, border in agents_data:
            c_x1 = c_mid - (card_w // 2)
            c_x2 = c_mid + (card_w // 2)

            is_active = (agent.status == "running")

            # Agent Card Background
            self.create_rectangle(
                c_x1, sub_y1, c_x2, sub_y2,
                fill=bg,
                outline=ThemeColors.STATUS_RUNNING if is_active else border,
                width=2 if is_active else 1
            )

            # Icon + Name
            self.create_text(
                c_x1 + 12, sub_y1 + 14,
                text=f"{agent.icon} {agent.name}",
                font=Typography.small_bold(),
                fill=accent,
                anchor="nw"
            )

            # Status Indicator
            badge_text = "● RUNNING" if is_active else "○ STANDBY"
            self.create_text(
                c_x2 - 12, sub_y1 + 14,
                text=badge_text,
                font=Typography.small(),
                fill=ThemeColors.STATUS_RUNNING if is_active else ThemeColors.TEXT_MUTED,
                anchor="ne"
            )

            # SEÇİLEN MODEL (VURGULU ÇERÇEVE İÇİNDE)
            model_box_y = sub_y1 + 38
            self.create_rectangle(
                c_x1 + 10, model_box_y, c_x2 - 10, model_box_y + 22,
                fill=ThemeColors.LOG_BG,
                outline=border,
                width=1
            )
            self.create_text(
                c_mid, model_box_y + 11,
                text=f"Model: {agent.selected_model}",
                font=Typography.small_bold(),
                fill=accent,
                anchor="center"
            )

            # Agent Type / Interface
            self.create_text(
                c_x1 + 12, sub_y1 + 68,
                text=f"Tip: {agent.agent_type}",
                font=Typography.small(),
                fill=ThemeColors.TEXT_PRIMARY,
                anchor="nw"
            )

            # Description (wrapped)
            self.create_text(
                c_x1 + 12, sub_y1 + 88,
                text=agent.role_description,
                font=Typography.small(),
                fill=ThemeColors.TEXT_SECONDARY,
                width=card_w - 24,
                anchor="nw"
            )

            # Effort Bar / Load Indicator
            bar_y = sub_y2 - 14
            bar_w = card_w - 24
            self.create_rectangle(
                c_x1 + 12, bar_y, c_x1 + 12 + bar_w, bar_y + 4,
                fill=ThemeColors.LINE_FLOW,
                outline=""
            )
            fill_w = (bar_w * agent.effort_blocks) // 4
            self.create_rectangle(
                c_x1 + 12, bar_y, c_x1 + 12 + fill_w, bar_y + 4,
                fill=accent,
                outline=""
            )

        # ══════════════════════════════════════════════════════════════════════
        # 4. TELEMETRY BAR
        # ══════════════════════════════════════════════════════════════════════
        telem_y = sub_y2 + 12
        dur_str = f"{self.store.agent_state.last_duration:.2f}s" if self.store.agent_state.last_duration > 0 else "0.00s"
        code_str = f"Kod: {self.store.agent_state.last_exit_code}"
        runs_str = f"Toplam Çağrı: {self.store.agent_state.total_runs}"
        
        telem_text = f"⏱️ Son Süre: {dur_str}  •  🚦 Çıkış: {code_str}  •  📊 {runs_str}  •  ⚡ Protokol: Antigravity ➔ CLI Pipe"
        self.create_text(
            mid_x, telem_y,
            text=telem_text,
            font=Typography.small(),
            fill=ThemeColors.TEXT_MUTED,
            anchor="n"
        )
