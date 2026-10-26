import os
import sys
import time

# 1. Force UTF-8 encoding across Windows console & standard streams
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
    if hasattr(sys.stderr, "reconfigure"):
        try:
            sys.stderr.reconfigure(encoding="utf-8")
        except Exception:
            pass

# Add project root directory to sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from rich.console import Console
from rich.live import Live

from config import (
    APP_TITLE,
    TICK_INTERVAL_SEC,
    CURSOR_BLINK_SEC,
)
from state.store import AppStore
from tui.dashboard import build_dashboard_layout

# Windows non-blocking keyboard listener
try:
    import msvcrt
    HAS_MSVCRT = True
except ImportError:
    HAS_MSVCRT = False


def run_tui():
    """Runs the Claude Code Agent Tree live TUI dashboard."""
    console = Console(force_terminal=True, color_system="truecolor")
    store = AppStore()
    
    last_tick_time = time.time()
    last_cursor_time = time.time()
    
    # Run inside alternate screen buffer for a true native TUI application feel
    with Live(
        build_dashboard_layout(store, console.width, console.height),
        console=console,
        screen=True,
        auto_refresh=False
    ) as live:
        
        running = True
        while running:
            current_time = time.time()
            needs_update = False
            
            # 1. Cursor blink interval
            if current_time - last_cursor_time >= CURSOR_BLINK_SEC:
                store.toggle_cursor()
                last_cursor_time = current_time
                needs_update = True
                
            # 2. Agent pulse and simulation interval
            if current_time - last_tick_time >= TICK_INTERVAL_SEC:
                store.tick_pulse()
                last_tick_time = current_time
                needs_update = True
                
            # 3. Handle non-blocking keyboard inputs
            if HAS_MSVCRT:
                while msvcrt.kbhit():
                    ch = msvcrt.getwch()
                    # Exit keys: q, Q, or ESC (\x1b)
                    if ch in ('q', 'Q', '\x1b'):
                        running = False
                        break
                    elif ch == ' ':
                        store.toggle_pause()
                        needs_update = True
                    elif ch in ('a', 'A'):
                        store.cycle_advisor_phase()
                        needs_update = True
                    elif ch in ('f', 'F'):
                        store.trigger_mock_fork()
                        needs_update = True
                    elif ch in ('l', 'L'):
                        store._generate_simulated_event()
                        needs_update = True
            
            # 4. Redraw layout if state changed
            if needs_update:
                layout = build_dashboard_layout(store, console.width, console.height)
                live.update(layout, refresh=True)
                
            # Small sleep to keep CPU usage near 0%
            time.sleep(0.04)


def main():
    try:
        run_tui()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        sys.stderr.write(f"\n[Error] {e}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
