import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk

import pytest

from sugar_next.shell.app_grid import SugarAppGrid
from sugar_next.shell.pie_menu import SugarPieMenu
from sugar_next.shell.home_view import HomeView


@pytest.fixture(autouse=True)
def gtk_display():
    if not Gtk.init_check():
        pytest.skip("no display available for GTK")


def test_add_and_switch_layouts(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    home_view = HomeView()
    app_grid = SugarAppGrid()
    pie_menu = SugarPieMenu()

    home_view.add_view(app_grid, set_active=True)
    home_view.add_view(pie_menu)

    assert home_view.active_id == "app-grid"
    assert set(home_view.view_ids()) == {"app-grid", "desktop-grid"}

    home_view.set_active("desktop-grid")
    assert home_view.active_id == "desktop-grid"

    home_view.set_active("app-grid")
    assert home_view.active_id == "app-grid"


def test_switching_preserves_app_grid_search_state(tmp_path, monkeypatch):
    # Views preserve their own state across switches (frame-views spec).
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    home_view = HomeView()
    app_grid = SugarAppGrid()
    pie_menu = SugarPieMenu()
    home_view.add_view(app_grid, set_active=True)
    home_view.add_view(pie_menu)

    app_grid._search_entry.set_text("firefox")
    home_view.set_active("desktop-grid")
    home_view.set_active("app-grid")

    assert app_grid._search_entry.get_text() == "firefox"


def test_unknown_layout_raises():
    home_view = HomeView()
    app_grid = SugarAppGrid()
    home_view.add_view(app_grid, set_active=True)
    with pytest.raises(KeyError):
        home_view.set_active("does-not-exist")
