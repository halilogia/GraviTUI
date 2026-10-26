import tkinter as tk
import tkinter.font as tkfont

class Typography:
    _family: str = "Consolas"
    _initialized: bool = False

    @classmethod
    def init_fonts(cls, root: tk.Tk = None):
        """Discovers best available monospace font on the current operating system."""
        if cls._initialized:
            return
            
        try:
            available = set(tkfont.families(root))
            if "Cascadia Code" in available:
                cls._family = "Cascadia Code"
            elif "Consolas" in available:
                cls._family = "Consolas"
            elif "SF Mono" in available:
                cls._family = "SF Mono"
            elif "Menlo" in available:
                cls._family = "Menlo"
            else:
                cls._family = "Courier"
        except Exception as e:
            # Fallback to standard Consolas without crashing
            cls._family = "Consolas"
            
        cls._initialized = True

    @classmethod
    def family(cls) -> str:
        if not cls._initialized:
            cls.init_fonts()
        return cls._family

    @classmethod
    def title(cls) -> tuple:
        return (cls.family(), 11, "bold")

    @classmethod
    def section(cls) -> tuple:
        return (cls.family(), 10, "bold")

    @classmethod
    def body(cls) -> tuple:
        return (cls.family(), 9, "normal")

    @classmethod
    def body_bold(cls) -> tuple:
        return (cls.family(), 9, "bold")

    @classmethod
    def small(cls) -> tuple:
        return (cls.family(), 8, "normal")

    @classmethod
    def small_bold(cls) -> tuple:
        return (cls.family(), 8, "bold")

    @classmethod
    def code(cls) -> tuple:
        return (cls.family(), 9, "normal")

    @classmethod
    def header_tag(cls) -> tuple:
        return (cls.family(), 10, "bold")
