"""Regression coverage for _SHELL_APP_ID filtering in toplevel handlers.

SugarShell needs a full GTK activation (window, settings store, ...) to
construct normally, which is too heavy for testing this specific filter.
Instead these tests call the handler methods unbound against a minimal
stand-in carrying only the state they touch (_launched_bundles,
toplevel_tracker) — exercising the exact logic without the GTK setup.
"""

import types

import pytest

from sugar_next.shell import main as shell_main
from sugar_next.shell.app_state import AppStateRegistry


@pytest.fixture(autouse=True)
def fresh_app_state(monkeypatch):
    fresh = AppStateRegistry()
    monkeypatch.setattr(shell_main, "app_state", fresh)
    return fresh


def _fake_shell():
    return types.SimpleNamespace(
        _launched_bundles={},
        toplevel_tracker=None,
    )


def test_shell_app_id_is_normalized_sugarnext():
    assert shell_main._SHELL_APP_ID == "org.sugarlabs.sugarnext"


def test_on_toplevel_open_ignores_the_shells_own_window(fresh_app_state):
    shell = _fake_shell()
    shell_main.SugarShell._on_toplevel_open(
        shell, "org.sugarlabs.SugarNext", "Sugar Next"
    )
    assert not fresh_app_state.is_open("org.sugarlabs.SugarNext")
    assert shell._launched_bundles == {}


def test_on_toplevel_open_still_tracks_other_apps(fresh_app_state):
    shell = _fake_shell()
    shell_main.SugarShell._on_toplevel_open(
        shell, "org.gnome.Calculator", "Calculator"
    )
    assert fresh_app_state.is_open("org.gnome.Calculator")


def test_on_toplevel_close_ignores_the_shells_own_window(fresh_app_state):
    shell = _fake_shell()
    fresh_app_state.add_open("org.sugarlabs.SugarNext")

    shell_main.SugarShell._on_toplevel_close(
        shell, "org.sugarlabs.SugarNext", "Sugar Next"
    )
    # Still open: the close handler must have returned early rather than
    # calling app_state.remove_open for the shell's own id.
    assert fresh_app_state.is_open("org.sugarlabs.SugarNext")


def test_on_toplevel_focus_ignores_the_shells_own_window(fresh_app_state):
    shell = _fake_shell()
    fresh_app_state.set_focused("org.gnome.Calculator")

    shell_main.SugarShell._on_toplevel_focus(shell, "org.sugarlabs.SugarNext")
    # Focus must be unchanged — the shell's own window is not a
    # meaningful focus target for the Frame/icon views.
    assert fresh_app_state.focused_app_id == "org.gnome.calculator"


def test_on_toplevel_focus_none_still_clears_focus(fresh_app_state):
    shell = _fake_shell()
    fresh_app_state.set_focused("org.gnome.Calculator")

    shell_main.SugarShell._on_toplevel_focus(shell, None)
    assert fresh_app_state.focused_app_id is None
