"""Terminal: boyut, VT100/UTF-8 modu, alt-screen, imlec ve ham klavye (msvcrt)."""
from __future__ import annotations

import os
import shutil
import sys
from typing import Optional, Tuple

ALT_ON = "\x1b[?1049h"
ALT_OFF = "\x1b[?1049l"
CURSOR_HIDE = "\x1b[?25l"
CURSOR_SHOW = "\x1b[?25h"

_SPECIAL = {
    # msvcrt: 0x00/0xE0 oneki + kod
    "H": "up", "P": "down", "K": "left", "M": "right",
    "G": "home", "O": "end", "I": "pageup", "Q": "pagedown",
    "S": "delete", "R": "insert",
}
_PLAIN = {"\r": "enter", "\n": "enter", "\t": "tab", "\x1b": "esc",
          "\x08": "backspace", "\x7f": "backspace", " ": "space"}


def enable_windows_vt() -> bool:
    """Windows konsolunda ANSI/VT isleme + UTF-8 cikis. Diger OS'te True."""
    if os.name != "nt":
        return True
    ok = False
    try:
        import ctypes
        k32 = ctypes.windll.kernel32
        k32.SetConsoleOutputCP(65001)
        k32.SetConsoleCP(65001)
        handle = k32.GetStdHandle(-11)
        mode = ctypes.c_ulong()
        if k32.GetConsoleMode(handle, ctypes.byref(mode)):
            # ENABLE_PROCESSED_OUTPUT | ENABLE_VIRTUAL_TERMINAL_PROCESSING
            ok = bool(k32.SetConsoleMode(handle, mode.value | 0x0001 | 0x0004))
    except Exception:
        ok = False
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    return ok


def terminal_size() -> Tuple[int, int]:
    s = shutil.get_terminal_size((80, 24))
    return s.columns, s.lines


def translate_key(first: str, second: Optional[str] = None) -> str:
    """msvcrt tus kodunu okunur ada cevirir (test edilebilir saf fonksiyon)."""
    if first in ("\x00", "\xe0"):
        return _SPECIAL.get(second or "", f"key:{ord(second) if second else 0}")
    if first in _PLAIN:
        return _PLAIN[first]
    if first == "\x03":
        return "ctrl+c"
    if len(first) == 1 and ord(first) < 32:
        return "ctrl+" + chr(ord(first) + 96)
    return first


class Terminal:
    def __init__(self, out=None):
        self.out = out or sys.stdout
        self._active = False

    def size(self) -> Tuple[int, int]:
        return terminal_size()

    def write(self, data: str) -> None:
        self.out.write(data)
        self.out.flush()

    def enter(self) -> None:
        enable_windows_vt()
        self.write(ALT_ON + CURSOR_HIDE + "\x1b[2J\x1b[H")
        self._active = True

    def leave(self) -> None:
        if self._active:
            self._active = False
            try:
                self.write("\x1b[0m" + CURSOR_SHOW + ALT_OFF)
            except OSError:
                pass  # stdout kapandi (boru koptu); geri yuklenecek bir sey yok

    def move_cursor(self, x: int, y: int) -> None:
        self.write(f"\x1b[{y + 1};{x + 1}H")

    def show_cursor(self, visible: bool = True) -> None:
        self.write(CURSOR_SHOW if visible else CURSOR_HIDE)

    def __enter__(self) -> "Terminal":
        self.enter()
        return self

    def __exit__(self, *exc) -> None:
        self.leave()

    def poll_key(self) -> Optional[str]:
        """Bloklamadan tek tus okur; yoksa None."""
        if os.name == "nt":
            import msvcrt
            if not msvcrt.kbhit():
                return None
            ch = msvcrt.getwch()
            if ch in ("\x00", "\xe0"):
                return translate_key(ch, msvcrt.getwch())
            return translate_key(ch)
        import select
        if not select.select([sys.stdin], [], [], 0)[0]:
            return None
        return translate_key(sys.stdin.read(1))
