import json
import types

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk

import pytest

from sugar_next.shell.pie_menu import SugarPieMenu


@pytest.fixture(autouse=True)
def gtk_display():
    if not Gtk.init_check():
        pytest.skip("no display available for GTK")


def _stub_bundle(app_id):
    return types.SimpleNamespace(
        app_id=app_id, name=app_id, icon=None, launch=lambda: True
    )


def test_empty_state_shown_with_no_favorites(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    menu = SugarPieMenu()
    assert menu._empty_label.get_visible() is True
    assert len(menu._petals) == 0


def test_pin_persists_and_reloads(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    menu = SugarPieMenu()
    menu.pin_favorite(_stub_bundle("fake-app.desktop"))
    menu.pin_favorite(_stub_bundle("fake-app.desktop"))  # no duplicates

    favorites_file = tmp_path / "sugar-next" / "favorites.json"
    assert json.loads(favorites_file.read_text()) == ["fake-app.desktop"]

    # A fresh pie menu loads them back; the uninstalled app id is
    # skipped in the UI but kept in the list.
    menu2 = SugarPieMenu()
    assert menu2._favorite_ids == ["fake-app.desktop"]

    menu2._unpin(_stub_bundle("fake-app.desktop"))
    assert json.loads(favorites_file.read_text()) == []


def test_settings_callback_fires_on_center_click(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    called = []
    menu = SugarPieMenu(on_settings=lambda: called.append(True))
    menu._center_button.emit("clicked")
    assert called == [True]


def test_launch_notifies_on_launched():
    # Regression: launching from the pie menu must fire on_launched so the
    # shell marks the app open in the registry — otherwise its icon never
    # leaves greyscale (only the Apps grid was lighting icons up).
    launched = []
    menu = SugarPieMenu(on_launched=launched.append)
    bundle = _stub_bundle("x.desktop")
    menu._launch(bundle)
    assert launched == [bundle]


def test_petal_is_fully_constructed():
    # Regression: the icon-state binding must not truncate the petal's
    # constructor — the unpin menu button belongs to __init__.
    from sugar_next.shell.pie_menu import _Petal

    petal = _Petal(
        _stub_bundle("x.desktop"),
        on_activate=lambda b: None,
        on_unpin=lambda b: None,
    )
    # Launch button + menu button both appended.
    children = []
    child = petal.get_first_child()
    while child is not None:
        children.append(child)
        child = child.get_next_sibling()
    assert len(children) == 2
    assert hasattr(petal, "dispose_icon_state")
    petal.dispose_icon_state()  # must not raise
