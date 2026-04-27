import threading
import subprocess
import sys
from pathlib import Path

import customtkinter as ctk
from tkinter import filedialog

from core.gog import export_gog, get_heroic_auth_path
from core.epic import export_epic, get_legendary_config_path
from core.steam import parse_steam_paste
from core.output import write_output
from core import config

ctk.set_appearance_mode("system")
ctk.set_default_color_theme("blue")

# ── THEME ─────────────────────────────────────────────────────────────
CHECKBOX_ACTIVE_COLOR = "#2d8a4e"
CHECKBOX_HOVER_COLOR = "#236e3e"
CHECKBOX_CHECKMARK_COLOR = "white"

# ── PLATFORM DEFINITIONS ──────────────────────────────────────────────
# To add a new platform, add an entry here and a corresponding
# exporter function in EXPORTERS below. No other GUI code needs changing.
PLATFORMS = [
    {
        "key": "gog",
        "label": "Export GOG (via Heroic)",
        "path_label": "auth.json path:",
        "hint": "Open Heroic Launcher before exporting — it refreshes your GOG token on launch.\nTokens expire after 1 hour.",
        "browse_type": "file",
        "config_path_key": "gog_auth_path",
    },
    {
        "key": "epic",
        "label": "Export Epic (via Heroic)",
        "path_label": "Legendary path:",
        "hint": "Open Heroic Launcher before exporting — it refreshes your Epic token on launch.\nTokens expire after 36 hours.",
        "browse_type": "dir",
        "config_path_key": "epic_legendary_path",
    },
]

# Maps platform key to its export function.
# Each function takes a path string and returns list[str].
EXPORTERS = {
    "gog": lambda path: export_gog(auth_path=Path(path)),
    "epic": lambda path: export_epic(legendary_path=Path(path)),
}


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Game Library Exporter")

        self.cfg = config.load()

        self.geometry(f"{self.cfg['window_width']}x{self.cfg['window_height']}")
        self.resizable(True, True)
        self.minsize(700, 900)

        self.protocol("WM_DELETE_WINDOW", self._on_close)

        # Stores per-platform widget references keyed by platform key
        # e.g. self.platform_vars["gog"]["enabled"] -> BooleanVar
        self.platform_vars: dict[str, dict] = {}

        self._build_ui()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        padding = {"padx": 20, "pady": 10}

        # ── PLATFORM SECTIONS (GOG, Epic, ...) ───────────────────────
        for row, platform in enumerate(PLATFORMS):
            self._build_platform_section(row, platform, padding)

        steam_row = len(PLATFORMS)
        output_row = steam_row + 1
        export_row = output_row + 1
        status_row = export_row + 1
        open_row = status_row + 1

        # ── STEAM SECTION ─────────────────────────────────────────────
        # Steam is hand-coded because it uses a textbox instead of a
        # path entry — structurally different from GOG/Epic.
        steam_frame = ctk.CTkFrame(self)
        steam_frame.grid(row=steam_row, column=0, sticky="ew", **padding)
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

        ctk.CTkLabel(
            steam_frame,
            text="1. Go to your Steam profile games page while logged in\n"
                 "2. Open browser console (F12 → Console)\n"
                 "3. Paste and run the snippet from README.md\n"
                 "4. Paste the copied result into the box below",
            text_color="gray",
            font=ctk.CTkFont(size=11),
            justify="left",
            anchor="w",
        ).grid(row=1, column=0, padx=15, pady=(0, 6), sticky="w")

        self.steam_textbox = ctk.CTkTextbox(steam_frame, height=140)
        self.steam_textbox.grid(row=2, column=0, padx=15, pady=(0, 12), sticky="ew")
        self.steam_textbox.insert("end", "Paste your Steam games list here...")
        self.steam_textbox.bind("<FocusIn>", self._clear_steam_placeholder)

        # ── OUTPUT SECTION ────────────────────────────────────────────
        output_frame = ctk.CTkFrame(self)
        output_frame.grid(row=output_row, column=0, sticky="ew", **padding)
        output_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(output_frame, text="Output",
                     font=ctk.CTkFont(size=14, weight="bold")).grid(
            row=0, column=0, columnspan=3, sticky="w", padx=15, pady=(12, 4)
        )
        ctk.CTkLabel(output_frame, text="Save to:", anchor="w").grid(
            row=1, column=0, padx=15, pady=6, sticky="w"
        )
        self.output_dir_var = ctk.StringVar(value=self.cfg["output_dir"])
        ctk.CTkEntry(output_frame, textvariable=self.output_dir_var,
                     state="readonly").grid(
            row=1, column=1, padx=6, pady=6, sticky="ew"
        )
        ctk.CTkButton(output_frame, text="Browse", width=80,
                      command=self._browse_output_dir).grid(
            row=1, column=2, padx=(0, 15), pady=6
        )
        ctk.CTkLabel(output_frame, text="Format:", anchor="w").grid(
            row=2, column=0, padx=15, pady=(0, 12), sticky="w"
        )
        self.format_var = ctk.StringVar(value=self.cfg["format"])
        ctk.CTkSegmentedButton(output_frame, values=["txt", "json"],
                               variable=self.format_var).grid(
            row=2, column=1, padx=6, pady=(0, 12), sticky="w"
        )

        # ── EXPORT BUTTON ─────────────────────────────────────────────
        self.export_btn = ctk.CTkButton(
            self, text="Export", height=44,
            font=ctk.CTkFont(size=15, weight="bold"),
            command=self._run_export,
        )
        self.export_btn.grid(row=export_row, column=0, padx=20,
                             pady=(0, 10), sticky="ew")

        # ── STATUS AREA ───────────────────────────────────────────────
        self.status_box = ctk.CTkTextbox(self, height=100, state="disabled")
        self.status_box.grid(row=status_row, column=0, padx=20,
                             pady=(0, 10), sticky="ew")
        self.status_box._textbox.tag_config("error", foreground="red")
        self.status_box._textbox.tag_config("success", foreground="green")

        # ── OPEN FOLDER BUTTON (hidden until export succeeds) ─────────
        self.open_btn = ctk.CTkButton(
            self, text="Open output folder",
            command=self._open_output_folder
        )
        self._open_btn_row = open_row

        # Apply initial toggle states
        for platform in PLATFORMS:
            self._toggle_platform_section(platform["key"])
        self._toggle_steam_section()

    def _build_platform_section(self, row: int, platform: dict, padding: dict):
        """
        Builds a standard platform section (checkbox + path entry + browse + hint).
        Used for GOG, Epic, and any future platforms added to PLATFORMS.
        Steam is excluded because it uses a textbox instead of a path entry.
        """
        key = platform["key"]

        frame = ctk.CTkFrame(self)
        frame.grid(row=row, column=0, sticky="ew", **padding)
        frame.grid_columnconfigure(1, weight=1)

        header = ctk.CTkFrame(frame, fg_color="transparent")
        header.grid(row=0, column=0, columnspan=3, sticky="w",
                    padx=15, pady=(12, 4))

        enabled_var = ctk.BooleanVar(value=self.cfg.get(f"{key}_enabled", True))
        ctk.CTkCheckBox(
            header, text=platform["label"],
            font=ctk.CTkFont(size=14, weight="bold"),
            checkmark_color=CHECKBOX_CHECKMARK_COLOR,
            fg_color=CHECKBOX_ACTIVE_COLOR,
            hover_color=CHECKBOX_HOVER_COLOR,
            variable=enabled_var,
            command=lambda k=key: self._toggle_platform_section(k),
        ).pack(side="left")

        ctk.CTkLabel(frame, text=platform["path_label"], anchor="w").grid(
            row=1, column=0, padx=15, pady=6, sticky="w"
        )

        path_var = ctk.StringVar(
            value=self.cfg.get(platform["config_path_key"], "")
        )
        path_entry = ctk.CTkEntry(frame, textvariable=path_var,
                                  state="readonly")
        path_entry.grid(row=1, column=1, padx=6, pady=6, sticky="ew")

        browse_btn = ctk.CTkButton(
            frame, text="Browse", width=80,
            command=lambda k=key: self._browse_platform_path(k),
        )
        browse_btn.grid(row=1, column=2, padx=(0, 15), pady=6)

        ctk.CTkLabel(
            frame, text=platform["hint"],
            text_color="gray",
            font=ctk.CTkFont(size=11),
            justify="left",
            anchor="w",
        ).grid(row=2, column=0, columnspan=3, padx=15,
               pady=(0, 12), sticky="w")

        # Store widget references for toggling and value retrieval
        self.platform_vars[key] = {
            "enabled": enabled_var,
            "path": path_var,
            "path_entry": path_entry,
            "browse_btn": browse_btn,
            "browse_type": platform["browse_type"],
        }

    # ── TOGGLE SECTION STATES ─────────────────────────────────────────

    def _toggle_platform_section(self, key: str):
        """Gray out platform section widgets when checkbox is unchecked."""
        widgets = self.platform_vars[key]
        enabled = widgets["enabled"].get()
        widgets["path_entry"].configure(
            state="readonly" if enabled else "disabled"
        )
        widgets["browse_btn"].configure(
            state="normal" if enabled else "disabled"
        )

    def _toggle_steam_section(self):
        state = "normal" if self.steam_enabled_var.get() else "disabled"
        self.steam_textbox.configure(state=state)

    # ── HELPERS ───────────────────────────────────────────────────────

    def _clear_steam_placeholder(self, event):
        if self.steam_textbox.get("1.0", "end").strip() == \
                "Paste your Steam games list here...":
            self.steam_textbox.delete("1.0", "end")

    def _browse_platform_path(self, key: str):
        """Opens file or folder picker depending on platform browse_type."""
        widgets = self.platform_vars[key]
        if widgets["browse_type"] == "file":
            path = filedialog.askopenfilename(
                title=f"Select {key} auth file",
                filetypes=[("JSON files", "*.json")],
            )
        else:
            path = filedialog.askdirectory(
                title=f"Select {key} config folder"
            )
        if path:
            widgets["path"].set(path)

    def _browse_output_dir(self):
        path = filedialog.askdirectory(title="Select output folder")
        if path:
            self.output_dir_var.set(path)

    def _log(self, message: str, level: str = "normal"):
        """Append a line to the status box. level: normal, error, success."""
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
        """Save config before closing."""
        data = {
            "steam_enabled": self.steam_enabled_var.get(),
            "output_dir": self.output_dir_var.get(),
            "format": self.format_var.get(),
            "window_width": self.winfo_width(),
            "window_height": self.winfo_height(),
        }
        # Save per-platform enabled state and path
        for platform in PLATFORMS:
            key = platform["key"]
            widgets = self.platform_vars[key]
            data[f"{key}_enabled"] = widgets["enabled"].get()
            data[platform["config_path_key"]] = widgets["path"].get()

        config.save(data)
        self.destroy()

    # ── EXPORT ────────────────────────────────────────────────────────

    def _run_export(self):
        """Validate selections before starting export thread."""
        any_platform = any(
            self.platform_vars[p["key"]]["enabled"].get()
            for p in PLATFORMS
        )
        steam_wanted = self.steam_enabled_var.get()

        if not any_platform and not steam_wanted:
            self._clear_log()
            self._log("Nothing selected. Please check at least one platform.",
                      "error")
            return

        if steam_wanted:
            raw = self.steam_textbox.get("1.0", "end").strip()
            if not raw or raw == "Paste your Steam games list here...":
                self._clear_log()
                self._log("Steam is checked but no games list was pasted.",
                          "error")
                return

        self.export_btn.configure(state="disabled", text="Exporting...")
        self.open_btn.grid_remove()
        self._clear_log()
        threading.Thread(target=self._export_worker, daemon=True).start()

    def _export_worker(self):
        libraries = {}

        # Platform exports (GOG, Epic, ...) — driven by PLATFORMS + EXPORTERS
        for platform in PLATFORMS:
            key = platform["key"]
            widgets = self.platform_vars[key]

            if not widgets["enabled"].get():
                continue

            self._log(f"Fetching {key.upper()} library...")
            try:
                games = EXPORTERS[key](widgets["path"].get())
                libraries[key] = games
                self._log(f"{key.upper()}: {len(games)} games found.",
                          "success")
            except (FileNotFoundError, PermissionError) as e:
                self._log(f"{key.upper()} error: {e}", "error")
                self._log(
                    f"Export halted. Fix the {key.upper()} issue or "
                    f"uncheck {key.upper()} to continue.",
                    "error"
                )
                self.export_btn.configure(state="normal", text="Export")
                return
            except Exception as e:
                self._log(f"{key.upper()} unexpected error: {e}", "error")
                self.export_btn.configure(state="normal", text="Export")
                return

        # Steam
        if self.steam_enabled_var.get():
            raw = self.steam_textbox.get("1.0", "end").strip()
            games = parse_steam_paste(raw)
            libraries["steam"] = games
            self._log(f"Steam: {len(games)} games found.", "success")

        if not libraries:
            self._log("Nothing to export.", "error")
            self.export_btn.configure(state="normal", text="Export")
            return

        try:
            written = write_output(
                libraries=libraries,
                output_dir=Path(self.output_dir_var.get()),
                format=self.format_var.get(),
            )
            for platform, path in written.items():
                self._log(f"Saved: {path}", "success")
            self._log("Done!", "success")
            self.open_btn.grid(
                row=self._open_btn_row, column=0,
                padx=20, pady=(0, 20), sticky="ew"
            )
        except Exception as e:
            self._log(f"Output error: {e}", "error")

        self.export_btn.configure(state="normal", text="Export")


if __name__ == "__main__":
    app = App()
    app.mainloop()