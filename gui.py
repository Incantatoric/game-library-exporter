import threading
import subprocess
import sys
from pathlib import Path

import customtkinter as ctk
from tkinter import filedialog

from core.gog import export_gog
from core.steam import parse_steam_paste
from core.output import write_output
from core import config

ctk.set_appearance_mode("system")
ctk.set_default_color_theme("blue")

CHECKBOX_ACTIVE_COLOR = "#2d8a4e" # fg_color
CHECKBOX_HOVER_COLOR = "#236e3e"
CHECKBOX_CHECKMARK_COLOR = "white"

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Game Library Exporter")

        # Load saved config on launch
        self.cfg = config.load()

        self.geometry(f"{self.cfg['window_width']}x{self.cfg['window_height']}")
        self.resizable(True, True)
        self.minsize(700, 700)

        # Save config when window is closed
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self._build_ui()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        padding = {"padx": 20, "pady": 10}

        # ── GOG SECTION ──────────────────────────────────────────────
        gog_frame = ctk.CTkFrame(self)
        gog_frame.grid(row=0, column=0, sticky="ew", **padding)
        gog_frame.grid_columnconfigure(1, weight=1)

        gog_header = ctk.CTkFrame(gog_frame, fg_color="transparent")
        gog_header.grid(row=0, column=0, columnspan=3, sticky="w", padx=15, pady=(12, 4))

        self.gog_enabled_var = ctk.BooleanVar(value=self.cfg["gog_enabled"])
        ctk.CTkCheckBox(
            gog_header, text="Export GOG (via Heroic)",
            font=ctk.CTkFont(size=14, weight="bold"),
            checkmark_color=CHECKBOX_CHECKMARK_COLOR,
            fg_color=CHECKBOX_ACTIVE_COLOR,
            hover_color=CHECKBOX_HOVER_COLOR,
            variable=self.gog_enabled_var,
            command=self._toggle_gog_section,
        ).pack(side="left")

        ctk.CTkLabel(gog_frame, text="auth.json path:", anchor="w").grid(
            row=1, column=0, padx=15, pady=6, sticky="w"
        )
        self.gog_path_var = ctk.StringVar(value=self.cfg["gog_auth_path"])
        self.gog_path_entry = ctk.CTkEntry(gog_frame, textvariable=self.gog_path_var, state="readonly")
        self.gog_path_entry.grid(row=1, column=1, padx=6, pady=6, sticky="ew")

        self.gog_browse_btn = ctk.CTkButton(gog_frame, text="Browse", width=80, command=self._browse_gog_path)
        self.gog_browse_btn.grid(row=1, column=2, padx=(0, 15), pady=6)

        self.gog_hint = ctk.CTkLabel(
            gog_frame,
            text="Open Heroic Launcher before exporting — it refreshes your GOG token on launch.\nTokens expire after 1 hour.",
            text_color="gray",
            font=ctk.CTkFont(size=11),
            justify="left",
            anchor="w",
        )
        self.gog_hint.grid(row=2, column=0, columnspan=3, padx=15, pady=(0, 12), sticky="w")

        # ── STEAM SECTION ─────────────────────────────────────────────
        steam_frame = ctk.CTkFrame(self)
        steam_frame.grid(row=1, column=0, sticky="ew", **padding)
        steam_frame.grid_columnconfigure(0, weight=1)

        steam_header = ctk.CTkFrame(steam_frame, fg_color="transparent")
        steam_header.grid(row=0, column=0, sticky="w", padx=15, pady=(12, 4))

        self.steam_enabled_var = ctk.BooleanVar(value=self.cfg["steam_enabled"])
        ctk.CTkCheckBox(
            steam_header, text="Export Steam (manual paste)",
            font=ctk.CTkFont(size=14, weight="bold"),
            checkmark_color=CHECKBOX_CHECKMARK_COLOR,
            fg_color=CHECKBOX_ACTIVE_COLOR,
            hover_color=CHECKBOX_HOVER_COLOR,
            variable=self.steam_enabled_var,
            command=self._toggle_steam_section,
        ).pack(side="left")

        self.steam_hint = ctk.CTkLabel(
            steam_frame,
            text="1. Go to your Steam profile games page while logged in\n"
                 "2. Open browser console (F12 → Console)\n"
                 "3. Paste and run the snippet from README.md\n"
                 "4. Paste the copied result into the box below",
            text_color="gray",
            font=ctk.CTkFont(size=11),
            justify="left",
            anchor="w",
        )
        self.steam_hint.grid(row=1, column=0, padx=15, pady=(0, 6), sticky="w")

        self.steam_textbox = ctk.CTkTextbox(steam_frame, height=140)
        self.steam_textbox.grid(row=2, column=0, padx=15, pady=(0, 12), sticky="ew")
        self.steam_textbox.insert("end", "Paste your Steam games list here...")
        self.steam_textbox.bind("<FocusIn>", self._clear_steam_placeholder)

        # ── OUTPUT SECTION ────────────────────────────────────────────
        output_frame = ctk.CTkFrame(self)
        output_frame.grid(row=2, column=0, sticky="ew", **padding)
        output_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(output_frame, text="Output", font=ctk.CTkFont(size=14, weight="bold")).grid(
            row=0, column=0, columnspan=3, sticky="w", padx=15, pady=(12, 4)
        )
        ctk.CTkLabel(output_frame, text="Save to:", anchor="w").grid(
            row=1, column=0, padx=15, pady=6, sticky="w"
        )
        self.output_dir_var = ctk.StringVar(value=self.cfg["output_dir"])
        ctk.CTkEntry(output_frame, textvariable=self.output_dir_var, state="readonly").grid(
            row=1, column=1, padx=6, pady=6, sticky="ew"
        )
        ctk.CTkButton(output_frame, text="Browse", width=80, command=self._browse_output_dir).grid(
            row=1, column=2, padx=(0, 15), pady=6
        )
        ctk.CTkLabel(output_frame, text="Format:", anchor="w").grid(
            row=2, column=0, padx=15, pady=(0, 12), sticky="w"
        )
        self.format_var = ctk.StringVar(value=self.cfg["format"])
        ctk.CTkSegmentedButton(output_frame, values=["txt", "json"], variable=self.format_var).grid(
            row=2, column=1, padx=6, pady=(0, 12), sticky="w"
        )

        # ── EXPORT BUTTON ─────────────────────────────────────────────
        self.export_btn = ctk.CTkButton(
            self, text="Export", height=44,
            font=ctk.CTkFont(size=15, weight="bold"),
            command=self._run_export,
        )
        self.export_btn.grid(row=3, column=0, padx=20, pady=(0, 10), sticky="ew")

        # ── STATUS AREA ───────────────────────────────────────────────
        self.status_box = ctk.CTkTextbox(self, height=100, state="disabled")
        self.status_box.grid(row=4, column=0, padx=20, pady=(0, 10), sticky="ew")

        # Configure text colors for status messages
        self.status_box._textbox.tag_config("error", foreground="red")
        self.status_box._textbox.tag_config("success", foreground="green")

        # ── OPEN FOLDER BUTTON (hidden until export succeeds) ─────────
        self.open_btn = ctk.CTkButton(
            self, text="Open output folder", command=self._open_output_folder
        )

        # Apply initial toggle states
        self._toggle_gog_section()
        self._toggle_steam_section()

    # ── TOGGLE SECTION STATES ─────────────────────────────────────────

    def _toggle_gog_section(self):
        """Gray out GOG section widgets when checkbox is unchecked."""
        state = "normal" if self.gog_enabled_var.get() else "disabled"
        self.gog_path_entry.configure(state="readonly" if self.gog_enabled_var.get() else "disabled")
        self.gog_browse_btn.configure(state=state)

    def _toggle_steam_section(self):
        """Gray out Steam section widgets when checkbox is unchecked."""
        state = "normal" if self.steam_enabled_var.get() else "disabled"
        self.steam_textbox.configure(state=state)

    # ── HELPERS ───────────────────────────────────────────────────────

    def _clear_steam_placeholder(self, event):
        if self.steam_textbox.get("1.0", "end").strip() == "Paste your Steam games list here...":
            self.steam_textbox.delete("1.0", "end")

    def _browse_gog_path(self):
        path = filedialog.askopenfilename(
            title="Select Heroic auth.json",
            filetypes=[("JSON files", "*.json")],
        )
        if path:
            self.gog_path_var.set(path)

    def _browse_output_dir(self):
        path = filedialog.askdirectory(title="Select output folder")
        if path:
            self.output_dir_var.set(path)

    def _log(self, message: str, level: str = "normal"):
        """
        Append a line to the status box.
        level: "normal", "error", "success"
        """
        self.status_box.configure(state="normal")
        self.status_box._textbox.insert("end", message + "\n", level)
        self.status_box.see("end")
        self.status_box.configure(state="disabled")

    def _clear_log(self):
        self.status_box.configure(state="normal")
        self.status_box.delete("1.0", "end")
        self.status_box.configure(state="disabled")

    def _open_output_folder(self):
        folder = self.output_dir_var.get()
        if sys.platform == "win32":
            subprocess.Popen(["explorer", folder])
        elif sys.platform == "darwin":
            subprocess.Popen(["open", folder])
        else:
            subprocess.Popen(["xdg-open", folder])

    def _on_close(self):
        """Save config before closing the window."""
        config.save({
            "gog_enabled": self.gog_enabled_var.get(),
            "steam_enabled": self.steam_enabled_var.get(),
            "gog_auth_path": self.gog_path_var.get(),
            "output_dir": self.output_dir_var.get(),
            "format": self.format_var.get(),
            "window_width": self.winfo_width(),
            "window_height": self.winfo_height(),
        })
        self.destroy()

    # ── EXPORT ────────────────────────────────────────────────────────

    def _run_export(self):
        """Validate selections before starting export thread."""
        gog_wanted = self.gog_enabled_var.get()
        steam_wanted = self.steam_enabled_var.get()

        # Nothing selected at all
        if not gog_wanted and not steam_wanted:
            self._clear_log()
            self._log("Nothing selected. Please check at least one platform.", "error")
            return

        # Steam checked but nothing pasted
        if steam_wanted:
            raw = self.steam_textbox.get("1.0", "end").strip()
            placeholder = "Paste your Steam games list here..."
            if not raw or raw == placeholder:
                self._clear_log()
                self._log("Steam is checked but no games list was pasted.", "error")
                return

        self.export_btn.configure(state="disabled", text="Exporting...")
        self.open_btn.grid_remove()
        self._clear_log()
        threading.Thread(target=self._export_worker, daemon=True).start()

    def _export_worker(self):
        gog_games = []
        steam_games = []

        # GOG
        if self.gog_enabled_var.get():
            self._log("Fetching GOG library...")
            try:
                gog_games = export_gog(auth_path=Path(self.gog_path_var.get()))
                self._log(f"GOG: {len(gog_games)} games found.", "success")
            except (FileNotFoundError, PermissionError) as e:
                # GOG was explicitly requested but failed — halt and tell the user
                self._log(f"GOG error: {e}", "error")
                self._log("Export halted. Fix the GOG issue or uncheck GOG to export Steam only.", "error")
                self.export_btn.configure(state="normal", text="Export")
                return
            except Exception as e:
                self._log(f"GOG unexpected error: {e}", "error")
                self.export_btn.configure(state="normal", text="Export")
                return

        # Steam
        if self.steam_enabled_var.get():
            raw_steam = self.steam_textbox.get("1.0", "end").strip()
            steam_games = parse_steam_paste(raw_steam)
            self._log(f"Steam: {len(steam_games)} games found.", "success")

        # Write output
        try:
            gog_path, steam_path = write_output(
                gog_games=gog_games,
                steam_games=steam_games,
                output_dir=Path(self.output_dir_var.get()),
                format=self.format_var.get(),
            )
            if gog_path:
                self._log(f"Saved: {gog_path}", "success")
            if steam_path:
                self._log(f"Saved: {steam_path}", "success")
            self._log("Done!", "success")
            self.open_btn.grid(row=5, column=0, padx=20, pady=(0, 20), sticky="ew")
        except Exception as e:
            self._log(f"Output error: {e}", "error")

        self.export_btn.configure(state="normal", text="Export")


if __name__ == "__main__":
    app = App()
    app.mainloop()