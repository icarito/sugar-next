"""Coverage for click-to-focus: _activate_app focuses an open app's window
instead of relaunching, and launches only when the app is closed.

Like test_main_toplevel_filtering, this calls the handler unbound against a
minimal stand-in rather than constructing a full GTK shell.
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


def _bundle(app_id):
    launched = []
    b = types.SimpleNamespace(
        app_id=app_id,
        launch=lambda: launched.append(True) or True,
        _launched=launched,
    )
    return b


def _fake_shell():
    focused = []
    relaunched = []
    return types.SimpleNamespace(
        _focus_calls=focused,
        _launch_calls=relaunched,
        _focus_window=lambda bundle: focused.append(bundle),
        _on_app_launched=lambda bundle: relaunched.append(bundle),
    )


def test_activate_focuses_when_open(fresh_app_state):
    fresh_app_state.add_open("firefox.desktop")
    shell = _fake_shell()
    bundle = _bundle("firefox.desktop")

    shell_main.SugarShell._activate_app(shell, bundle)

    assert shell._focus_calls == [bundle]
    assert shell._launch_calls == []  # did not relaunch
    assert bundle._launched == []     # bundle.launch not called


def test_activate_launches_when_closed(fresh_app_state):
    shell = _fake_shell()
    bundle = _bundle("gimp.desktop")

    shell_main.SugarShell._activate_app(shell, bundle)

    assert shell._focus_calls == []
    assert bundle._launched == [True]        # launched
    assert shell._launch_calls == [bundle]   # post-launch bookkeeping ran
