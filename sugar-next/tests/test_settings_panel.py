import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk

import pytest

from sugar_next.shell.home_view import HomeView
from sugar_next.shell.app_grid import SugarAppGrid
from sugar_next.shell.pie_menu import SugarPieMenu
from sugar_next.shell.settings import SettingsPanel
from sugar_next.shell.settings_store import SettingsStore


@pytest.fixture(autouse=True)
def gtk_display():
    if not Gtk.init_check():
        pytest.skip("no display available for GTK")


def test_builds_without_home_view(tmp_path):
    store = SettingsStore(tmp_path / "settings.json")
    panel = SettingsPanel(store=store)
    assert panel.get_child() is not None


def test_builds_with_home_view(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    store = SettingsStore(tmp_path / "settings.json")
    home_view = HomeView()
    home_view.add_view(SugarAppGrid(), set_active=True)
    home_view.add_view(SugarPieMenu())
    panel = SettingsPanel(home_view=home_view, store=store)
    assert panel.get_child() is not None


def test_settings_has_no_layout_selector(tmp_path, monkeypatch):
    # Views are chosen from the Frame, not Settings (frame-views spec):
    # the layout selector and its handler are gone.
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    store = SettingsStore(tmp_path / "settings.json")
    home_view = HomeView()
    home_view.add_view(SugarAppGrid(), set_active=True)
    home_view.add_view(SugarPieMenu())
    panel = SettingsPanel(home_view=home_view, store=store)
    assert not hasattr(panel, "_on_layout_changed")


def test_accent_choice_updates_store(tmp_path):
    store = SettingsStore(tmp_path / "settings.json")
    panel = SettingsPanel(store=store)
    panel._on_accent_chosen(None, "#123456")
    assert store.get("accent_color") == "#123456"


def test_color_tab_has_expanded_swatch_grid(tmp_path):
    store = SettingsStore(tmp_path / "settings.json")
    panel = SettingsPanel(store=store)
    # The curated grid is larger than the previous 8-color set.
    assert len(panel._swatch_buttons) > 8


def test_per_token_override_and_reset(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    from sugar_next.shell.theme import manager as theme_manager

    theme_manager.clear_override("--sn-surface")
    store = SettingsStore(tmp_path / "settings.json")
    panel = SettingsPanel(store=store)

    # A row exists for each overridable token, with a reset button.
    assert "--sn-surface" in panel._token_swatches
    reset = panel._token_resets["--sn-surface"]
    assert reset.get_sensitive() is False  # no override yet

    theme_manager.set_override("--sn-surface", "#112233")
    panel._refresh_token_swatch("--sn-surface")
    assert theme_manager.override_value("--sn-surface") == "#112233"

    panel._on_token_reset(reset, "--sn-surface")
    assert theme_manager.override_value("--sn-surface") is None
    assert reset.get_sensitive() is False


def test_extensions_list_shows_installed_extensions(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    extensions = tmp_path / "sugar-next" / "extensions"
    extensions.mkdir(parents=True)
    (extensions / "logger.py").write_text("")
    (extensions / "journal.py.disabled").write_text("")

    store = SettingsStore(tmp_path / "settings.json")
    panel = SettingsPanel(store=store)

    from sugar_next.api.hooks import list_extensions

    assert list_extensions(extensions) == [("journal", False), ("logger", True)]
    # Panel built without crashing and shows the extensions box.
    assert panel._extensions_box is not None


def test_toggling_extension_switch_persists_and_reloads(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    extensions = tmp_path / "sugar-next" / "extensions"
    extensions.mkdir(parents=True)
    (extensions / "logger.py").write_text("def on_shell_start(): pass\n")

    store = SettingsStore(tmp_path / "settings.json")
    panel = SettingsPanel(store=store)

    panel._on_extension_toggled(None, False, "logger")

    from sugar_next.api.hooks import list_extensions

    assert list_extensions(extensions) == [("logger", False)]
    assert (extensions / "logger.py").exists() is False
    assert (extensions / "logger.py.disabled").exists() is True

    panel._on_extension_toggled(None, True, "logger")
    assert list_extensions(extensions) == [("logger", True)]
