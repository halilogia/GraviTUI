import datetime
from typing import List, Callable, Dict
from models.agent_state import AgentState
from models.advisor_state import AdvisorState
from models.fork_metrics import ForkMetrics, ConfidenceMeter
from models.subagent_state import SubagentState
from models.session_log import LogEntry

class AppStore:
    def __init__(self):
        self.agent_state = AgentState()
        self.advisor_state = AdvisorState()
        self.fork_metrics = ForkMetrics()
        
        self.subagents: List[SubagentState] = [
            SubagentState(
                name="worker",
                model="Opus 5.5",
                effort_level="med",
                effort_blocks=2,
                role_description="edits + runs tests",
                status="running"
            ),
            SubagentState(
                name="explorer",
                model="Opus 5.5",
                effort_level="med",
                effort_blocks=2,
                role_description="reads the code",
                status="running"
            ),
            SubagentState(
                name="researcher",
                model="Opus 5.5",
                effort_level="med",
                effort_blocks=2,
                role_description="pulls the docs",
                status="running"
            ),
        ]
        
        self.logs: List[LogEntry] = [
            LogEntry("23:48:00", "fable", "before a plan · reading full session"),
            LogEntry("23:48:07", "jev", "retry or stop -> stop + ask", "p=0.85 sharp -> code"),
            LogEntry("23:48:09", "researcher", "found 3 doc pages"),
            LogEntry("23:48:09", "jev", "which tool -> grep", "p=0.88 sharp -> code"),
        ]
        
        self.status_pills: Dict[str, str] = {
            "effort": "high/medium",
            "subagents": "3/3",
            "fable": "advising",
            "jev": "1,320 forks",
        }
        
        self.prompt_text: str = "claude --advisor fable"
        self.cursor_visible: bool = True
        self.pulse_phase: int = 0
        self.paused: bool = False
        
        self._listeners: List[Callable[[], None]] = []
        self._sim_counter: int = 0

    def subscribe(self, callback: Callable[[], None]):
        self._listeners.append(callback)

    def notify(self):
        for listener in self._listeners:
            try:
                listener()
            except Exception as e:
                import sys
                sys.stderr.write(f"[AppStore Error] Listener notification failed: {e}\n")

    def toggle_cursor(self):
        self.cursor_visible = not self.cursor_visible
        self.notify()

    def tick_pulse(self):
        if not self.paused:
            self.pulse_phase = (self.pulse_phase + 1) % 4
            self._sim_counter += 1
            # Add dynamic simulation events every few seconds
            if self._sim_counter % 12 == 0:
                self._generate_simulated_event()
        self.notify()

    def toggle_pause(self):
        self.paused = not self.paused
        status = "paused" if self.paused else "running"
        for sub in self.subagents:
            sub.status = status
        self.notify()

    def add_log(self, tag: str, message: str, detail: str = ""):
        now_str = datetime.datetime.now().strftime("%H:%M:%S")
        self.logs.append(LogEntry(now_str, tag, message, detail))
        if len(self.logs) > 8:
            self.logs.pop(0)
        self.notify()

    def cycle_advisor_phase(self):
        phases = [
            ("before a plan", "reads the whole session, every\ntool call and result"),
            ("analyzing AST", "deep AST structure verification\nacross 14 files"),
            ("error repeats", "detected repeated exception,\nguiding fallback branch"),
            ("before done", "pre-flight checks passing,\nverifying unit tests")
        ]
        curr_phase = self.advisor_state.active_phase
        curr_idx = 0
        for idx, (p_name, _) in enumerate(phases):
            if p_name == curr_phase:
                curr_idx = idx
                break
        next_idx = (curr_idx + 1) % len(phases)
        new_name, new_desc = phases[next_idx]
        self.advisor_state.active_phase = new_name
        self.advisor_state.active_desc = new_desc
        self.advisor_state.calls += 1
        self.add_log("fable", f"transitioned phase -> {new_name}")

    def trigger_mock_fork(self):
        import random
        base_forks = 1320 + self._sim_counter * 3
        self.fork_metrics.forks_count = f"{base_forks:,}"
        self.status_pills["jev"] = f"{base_forks:,} forks"
        # slightly tweak confidence values
        for meter in self.fork_metrics.meters:
            delta = random.choice([-0.02, -0.01, 0.0, 0.01, 0.02])
            meter.value = max(0.70, min(0.99, round(meter.value + delta, 2)))
        self.add_log("jev", f"fork evaluation batch completed", f"total={base_forks}")

    def _generate_simulated_event(self):
        import random
        events = [
            ("worker", "verified test suite: 18 passed, 0 failed", ""),
            ("explorer", "scanned directory tree for imports", "28 modules"),
            ("researcher", "cached documentation embeddings", "tokens: 4.2k"),
            ("jev", "branch pruned: zero-confidence path", "p=0.12 discarded"),
            ("fable", "advisory check: no security regressions", "clean"),
        ]
        tag, msg, det = random.choice(events)
        self.add_log(tag, msg, det)
        self.fork_metrics.forks_count = f"{1320 + self._sim_counter * 2:,}"
        self.status_pills["jev"] = f"{self.fork_metrics.forks_count} forks"
