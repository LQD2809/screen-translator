"""Windows desktop UI for translating visible text."""

from __future__ import annotations

import os
import threading
import tkinter as tk
from tkinter import filedialog, ttk

import mss
import pytesseract
from PIL import Image

from translator import create_translator


BG = "#101318"
PANEL = "#191e26"
PANEL_ALT = "#202732"
TEXT = "#f4f6fb"
MUTED = "#99a4b5"
ACCENT = "#8b7bff"
GREEN = "#3dd6a3"
ORANGE = "#f1bb66"


class RegionSelector(tk.Toplevel):
    def __init__(self, master, on_select):
        super().__init__(master)
        self.on_select = on_select
        self.start_point = None
        self.attributes("-fullscreen", True)
        self.attributes("-topmost", True)
        self.attributes("-alpha", 0.3)
        self.configure(background="#000000", cursor="crosshair")
        self.canvas = tk.Canvas(self, bg="#000000", highlightthickness=0, cursor="crosshair")
        self.canvas.pack(fill="both", expand=True)
        self.canvas.create_text(
            28, 28, anchor="nw", text="Drag to select text  ·  Esc to cancel",
            fill="white", font=("Segoe UI", 16, "bold")
        )
        self.canvas.bind("<ButtonPress-1>", self._begin)
        self.canvas.bind("<B1-Motion>", self._drag)
        self.canvas.bind("<ButtonRelease-1>", self._finish)
        self.bind("<Escape>", lambda _event: self._cancel())
        self.focus_force()

    def _begin(self, event):
        self.start_point = (event.x_root, event.y_root)
        self.rect = self.canvas.create_rectangle(
            event.x, event.y, event.x, event.y, outline=ACCENT, width=3
        )

    def _drag(self, event):
        if self.start_point:
            x1 = self.start_point[0] - self.winfo_rootx()
            y1 = self.start_point[1] - self.winfo_rooty()
            self.canvas.coords(self.rect, x1, y1, event.x, event.y)

    def _finish(self, event):
        if not self.start_point:
            self.destroy()
            return
        x1, y1 = self.start_point
        x2, y2 = event.x_root, event.y_root
        self.destroy()
        if abs(x2 - x1) >= 8 and abs(y2 - y1) >= 8:
            self.on_select({
                "left": min(x1, x2), "top": min(y1, y2),
                "width": abs(x2 - x1), "height": abs(y2 - y1),
            })
        else:
            self.on_select(None)

    def _cancel(self):
        self.destroy()
        self.on_select(None)


class TranslationCard(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.attributes("-alpha", 0.94)
        self.configure(bg=PANEL)
        self.geometry("410x190+40+100")
        self.offset = (0, 0)
        self.card = tk.Frame(self, bg=PANEL, highlightbackground="#303947", highlightthickness=1)
        self.card.pack(fill="both", expand=True)
        header = tk.Frame(self.card, bg=PANEL)
        header.pack(fill="x", padx=14, pady=(12, 4))
        tk.Label(header, text="✦", fg=ACCENT, bg=PANEL, font=("Segoe UI", 14, "bold")).pack(side="left")
        tk.Label(header, text="TRANSLATION", fg=MUTED, bg=PANEL, font=("Segoe UI", 9, "bold")).pack(side="left", padx=7)
        tk.Label(header, text="DRAG TO MOVE", fg="#647184", bg=PANEL, font=("Segoe UI", 8)).pack(side="right")
        tk.Button(
            header, text="×", command=self.withdraw, fg=MUTED, bg=PANEL,
            activeforeground=TEXT, activebackground=PANEL_ALT, relief="flat",
            borderwidth=0, font=("Segoe UI", 12), cursor="hand2",
        ).pack(side="right", padx=(8, 4))
        self.output = tk.Label(
            self.card, text="Your translation will appear here.",
            fg=TEXT, bg=PANEL, justify="left", anchor="nw",
            wraplength=370, font=("Segoe UI", 13), padx=14, pady=10,
        )
        self.output.pack(fill="both", expand=True)
        self.opacity = ttk.Scale(self.card, from_=0.4, to=1.0, command=self._set_opacity)
        self.opacity.set(0.94)
        self.opacity.pack(fill="x", padx=14, pady=(0, 10))
        for widget in (self, self.card, header, self.output):
            widget.bind("<ButtonPress-1>", self._start_move)
            widget.bind("<B1-Motion>", self._move)

    def _start_move(self, event):
        self.offset = (event.x_root - self.winfo_x(), event.y_root - self.winfo_y())

    def _move(self, event):
        self.geometry(f"+{event.x_root - self.offset[0]}+{event.y_root - self.offset[1]}")

    def _set_opacity(self, value):
        self.attributes("-alpha", float(value))

    def display(self, text):
        self.output.configure(text=text or "No text detected.")
        self.deiconify()


class ScreenTranslatorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Screen Translator")
        self.geometry("760x700")
        self.minsize(650, 600)
        self.configure(bg=BG)
        self.option_add("*Font", "Segoe UI 10")
        self.region = None
        self.refresh_id = None
        self._style()
        self.card = TranslationCard(self)
        self._build()

    def _style(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TFrame", background=BG)
        style.configure("Panel.TFrame", background=PANEL)
        style.configure("TLabel", background=BG, foreground=TEXT)
        style.configure("Muted.TLabel", background=BG, foreground=MUTED)
        style.configure("Panel.TLabel", background=PANEL, foreground=TEXT)
        style.configure("TEntry", fieldbackground=PANEL_ALT, foreground=TEXT, insertcolor=TEXT, borderwidth=0, padding=8)
        style.configure("TCombobox", fieldbackground=PANEL_ALT, foreground=TEXT, padding=7)
        style.map("TCombobox", fieldbackground=[("readonly", PANEL_ALT)], foreground=[("readonly", TEXT)])
        style.configure("TButton", background=PANEL_ALT, foreground=TEXT, padding=(12, 9), borderwidth=0)
        style.map("TButton", background=[("active", "#303a49")])
        style.configure("Accent.TButton", background=ACCENT, foreground="white", padding=(14, 10), borderwidth=0)
        style.map("Accent.TButton", background=[("active", "#7564f0")])
        style.configure("TCheckbutton", background=PANEL, foreground=TEXT)
        style.configure("Horizontal.TProgressbar", troughcolor=PANEL_ALT, background=ACCENT, borderwidth=0)

    def _build(self):
        root = tk.Frame(self, bg=BG, padx=26, pady=22)
        root.pack(fill="both", expand=True)

        top = tk.Frame(root, bg=BG)
        top.pack(fill="x")
        tk.Label(top, text="◈", fg=ACCENT, bg=BG, font=("Segoe UI", 25, "bold")).pack(side="left")
        title_block = tk.Frame(top, bg=BG)
        title_block.pack(side="left", padx=10)
        tk.Label(title_block, text="Screen Translator", fg=TEXT, bg=BG, font=("Segoe UI", 21, "bold")).pack(anchor="w")
        tk.Label(title_block, text="Translate what you see, right where you see it.", fg=MUTED, bg=BG).pack(anchor="w")
        tk.Label(top, text="●  WINDOWS DESKTOP", fg=GREEN, bg=BG, font=("Segoe UI", 8, "bold")).pack(side="right", anchor="n", pady=9)

        self._section_label(root, "01  ·  LANGUAGES")
        language_panel = tk.Frame(root, bg=PANEL, padx=16, pady=14)
        language_panel.pack(fill="x", pady=(8, 18))
        self.source = tk.StringVar(value="en")
        self.target = tk.StringVar(value="vi")
        self.provider = tk.StringVar(value="Local (Argos)")
        tk.Label(language_panel, text="SOURCE", fg=MUTED, bg=PANEL, font=("Segoe UI", 8, "bold")).grid(row=0, column=0, sticky="w")
        tk.Label(language_panel, text="TARGET", fg=MUTED, bg=PANEL, font=("Segoe UI", 8, "bold")).grid(row=0, column=2, sticky="w")
        self.source_box = ttk.Combobox(language_panel, textvariable=self.source, values=("en", "vi", "ja", "ko", "zh", "fr", "de", "es"), width=15)
        self.source_box.grid(row=1, column=0, sticky="ew", pady=(6, 0))
        tk.Label(language_panel, text="→", fg=ACCENT, bg=PANEL, font=("Segoe UI", 17, "bold")).grid(row=1, column=1, padx=15)
        self.target_box = ttk.Combobox(language_panel, textvariable=self.target, values=("vi", "en", "ja", "ko", "zh", "fr", "de", "es"), width=15)
        self.target_box.grid(row=1, column=2, sticky="ew", pady=(6, 0))
        ttk.Combobox(language_panel, textvariable=self.provider, values=("Local (Argos)", "LibreTranslate"), state="readonly", width=18).grid(row=1, column=3, sticky="e", padx=(18, 0), pady=(6, 0))
        language_panel.columnconfigure(0, weight=1)
        language_panel.columnconfigure(2, weight=1)
        tk.Label(language_panel, text="Translation engine", fg=MUTED, bg=PANEL, font=("Segoe UI", 8)).grid(row=0, column=3, sticky="e")

        self._section_label(root, "02  ·  CAPTURE")
        action_panel = tk.Frame(root, bg=PANEL, padx=14, pady=14)
        action_panel.pack(fill="x", pady=(8, 18))
        ttk.Button(action_panel, text="▣  Capture screen region", style="Accent.TButton", command=self.select_region).pack(side="left")
        ttk.Button(action_panel, text="▧  Open image", command=self.open_image).pack(side="left", padx=8)
        self.refresh = tk.BooleanVar(value=False)
        ttk.Checkbutton(action_panel, text="Refresh every 2s (video subtitles)", variable=self.refresh, command=self.toggle_refresh).pack(side="right")

        self._section_label(root, "03  ·  SOURCE TEXT")
        text_panel = tk.Frame(root, bg=PANEL, padx=14, pady=12)
        text_panel.pack(fill="both", expand=True, pady=(8, 10))
        self.input = tk.Text(
            text_panel, height=8, wrap="word", bg=PANEL, fg=TEXT, insertbackground=TEXT,
            selectbackground=ACCENT, relief="flat", borderwidth=0, padx=8, pady=8,
            font=("Segoe UI", 11), undo=True,
        )
        self.input.pack(fill="both", expand=True)
        self.input.insert("1.0", "Paste or type text here, or capture a screen region / open an image.")
        self.input.bind("<FocusIn>", self._clear_placeholder)
        footer = tk.Frame(root, bg=BG)
        footer.pack(fill="x")
        self.status = tk.StringVar(value="Ready · OCR runs on your device")
        tk.Label(footer, textvariable=self.status, fg=MUTED, bg=BG, anchor="w").pack(side="left", fill="x", expand=True)
        ttk.Button(footer, text="Translate  →", style="Accent.TButton", command=self.translate).pack(side="right")
        tk.Label(root, text="Images and screen captures stay on this device. Audio / speech is not translated.", fg="#778395", bg=BG, font=("Segoe UI", 8)).pack(anchor="w", pady=(12, 0))

    def _section_label(self, parent, text):
        tk.Label(parent, text=text, fg="#c1c9d6", bg=BG, font=("Segoe UI", 9, "bold")).pack(anchor="w")

    def _clear_placeholder(self, _event):
        if self.input.get("1.0", "end-1c") == "Paste or type text here, or capture a screen region / open an image.":
            self.input.delete("1.0", "end")
            self.input.unbind("<FocusIn>")

    def select_region(self):
        self.stop_refresh()
        self.withdraw()
        self.after(350, lambda: RegionSelector(self, self._region_selected))

    def _region_selected(self, region):
        self.deiconify()
        if not region:
            self.status.set("Screen capture cancelled.")
            return
        self.region = region
        self._capture_and_ocr(refresh=self.refresh.get())

    def open_image(self):
        path = filedialog.askopenfilename(
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp *.tif *.tiff"), ("All files", "*.*")]
        )
        if path:
            self._run_ocr(lambda: Image.open(path).convert("RGB"))

    def _capture_and_ocr(self, refresh=False):
        if not self.region:
            return
        self.card.withdraw()

        def capture():
            with mss.mss() as screen:
                shot = screen.grab(self.region)
                return Image.frombytes("RGB", shot.size, shot.rgb)

        self._run_ocr(capture, refresh=refresh)

    def _run_ocr(self, image_factory, refresh=False):
        self.status.set("Reading text from image…")

        def worker():
            try:
                result = pytesseract.image_to_string(
                    image_factory(), lang=os.environ.get("TESSERACT_LANG", "eng")
                ).strip()
                self.after(0, lambda value=result: self._ocr_done(value, refresh))
            except Exception as exc:
                self.after(0, lambda error=str(exc): self._show_error(f"OCR failed: {error}", refresh))

        threading.Thread(target=worker, daemon=True).start()

    def _ocr_done(self, result, refresh=False):
        if result:
            self.input.delete("1.0", "end")
            self.input.insert("1.0", result)
            self.translate(refresh=refresh)
        else:
            self.status.set("No text detected · try a larger or clearer region")
            self._schedule_refresh(refresh)

    def translate(self, refresh=False):
        text = self.input.get("1.0", "end").strip()
        if not text or text.startswith("Paste or type text here"):
            self.status.set("Enter or capture some text first.")
            return
        try:
            provider = "local" if self.provider.get() == "Local (Argos)" else "libretranslate"
            engine = create_translator(provider)
        except (ValueError, RuntimeError) as exc:
            self._show_error(str(exc), refresh)
            return
        source = self.source.get().strip()
        target = self.target.get().strip()
        if not source or not target:
            self.status.set("Enter source and target language codes.")
            return
        self.status.set("Translating…")

        def worker():
            try:
                result = engine.translate(text, source, target)
                self.after(0, lambda value=result: self._translated(value, refresh))
            except Exception as exc:
                self.after(0, lambda error=str(exc): self._show_error(f"Translation failed: {error}", refresh))

        threading.Thread(target=worker, daemon=True).start()

    def _translated(self, result, refresh=False):
        self.card.display(result)
        self.status.set("Translation ready · shown in floating card")
        self._schedule_refresh(refresh)

    def _schedule_refresh(self, refresh):
        if refresh and self.refresh.get() and self.region:
            self.refresh_id = self.after(2000, lambda: self._capture_and_ocr(refresh=True))

    def toggle_refresh(self):
        if self.refresh.get():
            if self.region:
                self._capture_and_ocr(refresh=True)
            else:
                self.status.set("Capture a screen region first to refresh video subtitles.")
                self.refresh.set(False)
        else:
            self.stop_refresh()

    def stop_refresh(self):
        if self.refresh_id is not None:
            self.after_cancel(self.refresh_id)
            self.refresh_id = None

    def _show_error(self, message, refresh=False):
        self.status.set(message)
        self._schedule_refresh(refresh)


if __name__ == "__main__":
    ScreenTranslatorApp().mainloop()
