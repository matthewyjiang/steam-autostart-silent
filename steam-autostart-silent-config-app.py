#!/usr/bin/env python3

from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gtk  # noqa: E402


CONFIG_FILE = Path("/etc/steam-autostart-silent/config.conf")
TARGET_FILE = Path("/etc/xdg/autostart/steam.desktop")
APPLY_HELPER = Path("/usr/lib/steam-autostart-silent/apply-config")
SOURCE_PATHS = {
    "steam": Path("/usr/share/applications/steam.desktop"),
    "steam-native": Path("/usr/share/applications/steam-native.desktop"),
}
SOURCE_LABELS = ["Auto", "Steam", "Steam (native)"]
SOURCE_VALUES = ["auto", "steam", "steam-native"]
INVALID_FLAG_CHARS = re.compile(r"[\n;|&`]|\$\(")


@dataclass
class Config:
    enabled: bool = True
    silent: bool = True
    extra_flags: str = ""
    source: str = "auto"

    def serialize(self) -> str:
        return (
            f"ENABLED={str(self.enabled).lower()}\n"
            f"SILENT={str(self.silent).lower()}\n"
            f'EXTRA_FLAGS="{self.extra_flags}"\n'
            f"SOURCE={self.source}\n"
        )


def read_key_values(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key] = value.strip().strip('"')
    return values


def read_config() -> Config:
    values = read_key_values(CONFIG_FILE)
    source = values.get("SOURCE", "auto")
    if source not in SOURCE_VALUES:
        source = "auto"
    return Config(
        enabled=values.get("ENABLED", "true") == "true",
        silent=values.get("SILENT", "true") == "true",
        extra_flags=" ".join(values.get("EXTRA_FLAGS", "").split()),
        source=source,
    )


def desktop_exec(path: Path) -> str:
    if not path.exists():
        return ""
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("Exec="):
            return line[5:]
    return ""


def resolve_source(config: Config) -> Path | None:
    if config.source in SOURCE_PATHS:
        path = SOURCE_PATHS[config.source]
        return path if path.exists() else None
    for path in SOURCE_PATHS.values():
        if path.exists():
            return path
    return None


def validate_flags(flags: str) -> str | None:
    if INVALID_FLAG_CHARS.search(flags):
        return "Extra flags cannot contain shell operators or newlines."
    return None


def apply_config(config: Config) -> subprocess.CompletedProcess[str]:
    fd, path = tempfile.mkstemp(prefix="steam-autostart-silent-", suffix=".conf")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(config.serialize())
        os.chmod(path, 0o600)
        return subprocess.run(
            ["pkexec", str(APPLY_HELPER), path],
            text=True,
            capture_output=True,
            check=False,
        )
    finally:
        try:
            os.unlink(path)
        except FileNotFoundError:
            pass


class ConfigWindow(Adw.ApplicationWindow):
    def __init__(self, app: Adw.Application) -> None:
        super().__init__(application=app, title="Steam Autostart")
        self.set_default_size(560, 620)
        Gtk.Window.set_default_icon_name("steam")

        self.config = read_config()
        self.loading = False

        self.toast_overlay = Adw.ToastOverlay()
        self.set_content(self.toast_overlay)

        toolbar = Adw.ToolbarView()
        self.toast_overlay.set_child(toolbar)

        header = Adw.HeaderBar()
        toolbar.add_top_bar(header)

        self.apply_button = Gtk.Button(label="Apply")
        self.apply_button.add_css_class("suggested-action")
        self.apply_button.connect("clicked", self.on_apply_clicked)
        header.pack_end(self.apply_button)

        refresh_button = Gtk.Button(label="Refresh")
        refresh_button.connect("clicked", self.on_refresh_clicked)
        header.pack_start(refresh_button)

        page = Adw.PreferencesPage()
        toolbar.set_content(page)

        status_group = Adw.PreferencesGroup(title="Status")
        page.add(status_group)

        self.steam_row = Adw.ActionRow(title="Steam desktop file")
        status_group.add(self.steam_row)

        self.managed_row = Adw.ActionRow(title="Managed autostart file")
        status_group.add(self.managed_row)

        self.exec_row = Adw.ActionRow(title="Current Exec=")
        status_group.add(self.exec_row)

        self.source_row = Adw.ActionRow(title="Source Exec=")
        status_group.add(self.source_row)

        behavior_group = Adw.PreferencesGroup(title="Behavior")
        page.add(behavior_group)

        self.enabled_row = Adw.SwitchRow(title="Enable Steam autostart")
        self.enabled_row.set_subtitle("Create and maintain /etc/xdg/autostart/steam.desktop")
        self.enabled_row.connect("notify::active", self.on_changed)
        behavior_group.add(self.enabled_row)

        self.silent_row = Adw.SwitchRow(title="Launch silently (-silent)")
        self.silent_row.connect("notify::active", self.on_changed)
        behavior_group.add(self.silent_row)

        self.flags_row = Adw.EntryRow(title="Extra Steam flags")
        self.flags_row.set_text(self.config.extra_flags)
        self.flags_row.connect("notify::text", self.on_changed)
        behavior_group.add(self.flags_row)

        self.flags_help_row = Adw.ActionRow(title="Flag examples")
        self.flags_help_row.set_subtitle("-nochatui -nofriendsui -noverifyfiles")
        behavior_group.add(self.flags_help_row)

        self.source_combo = Adw.ComboRow(title="Source desktop file")
        self.source_combo.set_model(Gtk.StringList.new(SOURCE_LABELS))
        self.source_combo.connect("notify::selected", self.on_changed)
        behavior_group.add(self.source_combo)

        actions_group = Adw.PreferencesGroup(title="Actions")
        page.add(actions_group)

        resync_row = Adw.ActionRow(title="Re-sync now")
        resync_row.set_subtitle("Refresh the managed desktop entry from current settings")
        resync_button = Gtk.Button(label="Re-sync")
        resync_button.set_valign(Gtk.Align.CENTER)
        resync_button.connect("clicked", self.on_resync_clicked)
        resync_row.add_suffix(resync_button)
        actions_group.add(resync_row)

        reset_row = Adw.ActionRow(title="Reset to defaults")
        reset_row.set_subtitle("Enable autostart, enable -silent, use auto source, clear extra flags")
        reset_button = Gtk.Button(label="Reset")
        reset_button.set_valign(Gtk.Align.CENTER)
        reset_button.connect("clicked", self.on_reset_clicked)
        reset_row.add_suffix(reset_button)
        actions_group.add(reset_row)

        self.load_config(self.config)
        self.refresh_status()

    def selected_config(self) -> Config:
        return Config(
            enabled=self.enabled_row.get_active(),
            silent=self.silent_row.get_active(),
            extra_flags=" ".join(self.flags_row.get_text().split()),
            source=SOURCE_VALUES[self.source_combo.get_selected()],
        )

    def load_config(self, config: Config) -> None:
        self.loading = True
        self.enabled_row.set_active(config.enabled)
        self.silent_row.set_active(config.silent)
        self.flags_row.set_text(config.extra_flags)
        self.source_combo.set_selected(SOURCE_VALUES.index(config.source))
        self.loading = False
        self.update_apply_state()

    def on_changed(self, *_args: object) -> None:
        if not self.loading:
            self.update_apply_state()

    def update_apply_state(self) -> None:
        config = self.selected_config()
        error = validate_flags(config.extra_flags)
        self.apply_button.set_sensitive(error is None and config != self.config)
        self.flags_help_row.set_subtitle(error or "-nochatui -nofriendsui -noverifyfiles")

    def refresh_status(self) -> None:
        config = self.selected_config()
        source = resolve_source(config)
        source_exec = desktop_exec(source) if source else ""
        target_exec = desktop_exec(TARGET_FILE)

        self.steam_row.set_subtitle(str(source) if source else "Not found")
        self.managed_row.set_subtitle(str(TARGET_FILE) if TARGET_FILE.exists() else "Missing")
        self.exec_row.set_subtitle(target_exec or "No managed Exec= line")
        self.source_row.set_subtitle(source_exec or "No source Exec= line")

    def show_result(self, result: subprocess.CompletedProcess[str], success_text: str) -> bool:
        if result.returncode == 0:
            self.toast_overlay.add_toast(Adw.Toast(title=success_text))
            return True
        message = result.stderr.strip() or result.stdout.strip() or "Authentication cancelled or command failed."
        self.toast_overlay.add_toast(Adw.Toast(title=message[:160]))
        return False

    def on_apply_clicked(self, _button: Gtk.Button) -> None:
        config = self.selected_config()
        error = validate_flags(config.extra_flags)
        if error:
            self.toast_overlay.add_toast(Adw.Toast(title=error))
            return
        result = apply_config(config)
        if self.show_result(result, "Settings applied"):
            self.config = read_config()
            self.load_config(self.config)
            self.refresh_status()

    def on_resync_clicked(self, _button: Gtk.Button) -> None:
        result = apply_config(self.selected_config())
        if self.show_result(result, "Re-sync complete"):
            self.config = read_config()
            self.load_config(self.config)
            self.refresh_status()

    def on_reset_clicked(self, _button: Gtk.Button) -> None:
        self.load_config(Config())

    def on_refresh_clicked(self, _button: Gtk.Button) -> None:
        self.config = read_config()
        self.load_config(self.config)
        self.refresh_status()


class ConfigApplication(Adw.Application):
    def __init__(self) -> None:
        super().__init__(application_id="io.github.matthewyjiang.steam-autostart-silent")

    def do_activate(self) -> None:
        window = self.props.active_window
        if window is None:
            window = ConfigWindow(self)
        window.present()


def main() -> int:
    app = ConfigApplication()
    return app.run(sys.argv)


if __name__ == "__main__":
    raise SystemExit(main())
