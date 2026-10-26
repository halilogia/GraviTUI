import tkinter as tk
from theme.colors import ThemeColors

class WindowBar(tk.Frame):
    def __init__(self, master, close_callback=None, minimize_callback=None, maximize_callback=None):
        super().__init__(master, bg=ThemeColors.BG_TITLEBAR, height=36)
        self.pack_propagate(False)
        self.close_callback = close_callback
        self.minimize_callback = minimize_callback
        self.maximize_callback = maximize_callback
        
        self._drag_start_x = 0
        self._drag_start_y = 0
        
        self._build_ui()
        self._bind_drag()

    def _build_ui(self):
        # Canvas for window traffic light control buttons
        self.dots_canvas = tk.Canvas(
            self,
            width=80,
            height=36,
            bg=ThemeColors.BG_TITLEBAR,
            highlightthickness=0,
            cursor="hand2"
        )
        self.dots_canvas.pack(side=tk.LEFT, padx=(14, 0))
        
        # Red, Yellow, Green circles
        self.btn_close = self.dots_canvas.create_oval(4, 12, 16, 24, fill=ThemeColors.BTN_CLOSE, outline="")
        self.btn_min = self.dots_canvas.create_oval(24, 12, 36, 24, fill=ThemeColors.BTN_MINIMIZE, outline="")
        self.btn_max = self.dots_canvas.create_oval(44, 12, 56, 24, fill=ThemeColors.BTN_ZOOM, outline="")
        
        self.dots_canvas.tag_bind(self.btn_close, "<Button-1>", lambda e: self.close_callback and self.close_callback())
        self.dots_canvas.tag_bind(self.btn_min, "<Button-1>", lambda e: self.minimize_callback and self.minimize_callback())
        self.dots_canvas.tag_bind(self.btn_max, "<Button-1>", lambda e: self.maximize_callback and self.maximize_callback())

    def _bind_drag(self):
        self.bind("<ButtonPress-1>", self._on_drag_start)
        self.bind("<B1-Motion>", self._on_drag_motion)

    def _on_drag_start(self, event):
        self._drag_start_x = event.x_root
        self._drag_start_y = event.y_root

    def _on_drag_motion(self, event):
        dx = event.x_root - self._drag_start_x
        dy = event.y_root - self._drag_start_y
        
        root = self.winfo_toplevel()
        new_x = root.winfo_x() + dx
        new_y = root.winfo_y() + dy
        root.geometry(f"+{new_x}+{new_y}")
        
        self._drag_start_x = event.x_root
        self._drag_start_y = event.y_root
