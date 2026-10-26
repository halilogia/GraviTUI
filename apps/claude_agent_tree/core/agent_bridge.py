import os
import sys
import subprocess
import time
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(BASE_DIR, "live_feed.log")
CLAUDE_BIN = os.path.expanduser("~/.local/bin/claude.exe")

CURRENT_PROC = None

def log_to_feed(text: str):
    """Appends text immediately to the live stream log for the console window and UI."""
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(text + "\n")
        f.flush()

def stop_current_task() -> bool:
    """Terminates any currently running agent process."""
    global CURRENT_PROC
    if CURRENT_PROC and CURRENT_PROC.poll() is None:
        try:
            CURRENT_PROC.kill()
            log_to_feed(f"\n[{datetime.now().strftime('%H:%M:%S')}] ⏹️ [İŞLEM KULLANICI TARAFINDAN DURDURULDU]")
            return True
        except Exception as e:
            log_to_feed(f"❌ [DURDURMA HATASI]: {e}")
    return False

def run_claude_prompt(prompt: str, cwd: str = None) -> tuple[int, float, str]:
    """Runs a prompt through Claude Code CLI headlessly and streams output directly to feed."""
    global CURRENT_PROC
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    target_cwd = cwd or os.path.expanduser("~/Desktop")
    
    log_to_feed(f"\n[{now_str}] 🚀 [CLAUDE ÇAĞRILDI]: {prompt}")
    log_to_feed(f"📂 Dizin : {target_cwd}")
    log_to_feed("─" * 65)
    
    start_time = time.time()
    all_output = []
    
    try:
        CURRENT_PROC = subprocess.Popen(
            [CLAUDE_BIN, "-p", prompt],
            cwd=target_cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            text=True,
            encoding="utf-8",
            errors="replace"
        )
        
        for line in CURRENT_PROC.stdout:
            clean_line = line.rstrip()
            all_output.append(clean_line)
            log_to_feed(f"   │ {clean_line}")
            print(clean_line)
            
        CURRENT_PROC.wait()
        elapsed = time.time() - start_time
        exit_code = CURRENT_PROC.returncode
        
        log_to_feed("─" * 65)
        status_icon = "✅" if exit_code == 0 else "❌"
        log_to_feed(f"[{datetime.now().strftime('%H:%M:%S')}] {status_icon} [İŞLEM BİTTİ]: Kod: {exit_code} | Süre: {elapsed:.2f}s")
        log_to_feed("═" * 65 + "\n")
        
        CURRENT_PROC = None
        return exit_code, elapsed, "\n".join(all_output)
    except Exception as e:
        err_msg = f"❌ [HATA]: {e}"
        log_to_feed(err_msg)
        CURRENT_PROC = None
        return 1, 0.0, err_msg

if __name__ == "__main__":
    if len(sys.argv) > 1:
        prompt_text = " ".join(sys.argv[1:])
    else:
        prompt_text = "Merhaba! Codex motoru ile hazir misin?"
        
    code, dur, out = run_claude_prompt(prompt_text)
    sys.exit(code)
