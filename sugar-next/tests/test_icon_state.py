import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk

import pytest

from sugar_next.shell import icon_state
from sugar_next.shell.app_state import AppStateRegistry


@pytest.fixture(autouse=True)
def gtk_display():
    if not Gtk.init_check():
        pytest.skip("no display available for GTK")


@pytest.fixture
def fresh_registry(monkeypatch):
    reg = AppStateRegistry()
    monkeypatch.setattr(icon_state, "app_state", reg)
    return reg


def test_state_class_closed_open_focused(fresh_registry):
    assert icon_state.state_class_for("a.desktop") == "sn-icon-closed"
    fresh_registry.add_open("a.desktop")
    assert icon_state.state_class_for("a.desktop") == "sn-icon-open"
    fresh_registry.set_focused("a.desktop")
    assert icon_state.state_class_for("a.desktop") == "sn-icon-focused"


def test_two_state_fallback_without_focus(fresh_registry):
    # No focus source ever sets focused_app_id: an open app stays "open",
    # it never reaches the focused (full-saturation) class.
    fresh_registry.add_open("a.desktop")
    assert fresh_registry.focused_app_id is None
    assert icon_state.state_class_for("a.desktop") == "sn-icon-open"


def test_apply_icon_state_swaps_class(fresh_registry):
    image = Gtk.Image()
    fresh_registry.add_open("a.desktop")
    icon_state.apply_icon_state(image, "a.desktop")
    assert image.has_css_class("sn-icon-open")
    assert not image.has_css_class("sn-icon-closed")
    fresh_registry.remove_open("a.desktop")
    icon_state.apply_icon_state(image, "a.desktop")
    assert image.has_css_class("sn-icon-closed")
    assert not image.has_css_class("sn-icon-open")


def test_bind_updates_on_registry_change_and_unbinds(fresh_registry):
    image = Gtk.Image()
    unbind = icon_state.bind_icon_state(image, "a.desktop")
    assert image.has_css_class("sn-icon-closed")
    fresh_registry.add_open("a.desktop")
    assert image.has_css_class("sn-icon-open")
    unbind()
    fresh_registry.remove_open("a.desktop")
    # After unbind the class is frozen at its last value.
    assert image.has_css_class("sn-icon-open")
