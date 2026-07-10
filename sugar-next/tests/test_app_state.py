from sugar_next.shell.app_state import AppStateRegistry, normalize_app_id


def test_normalize_strips_desktop_and_lowercases():
    assert normalize_app_id("org.gnome.Calculator.desktop") == "org.gnome.calculator"
    assert normalize_app_id("org.gnome.Calculator") == "org.gnome.calculator"
    assert normalize_app_id(None) == ""


def test_wayland_and_desktop_ids_match():
    reg = AppStateRegistry()
    reg.add_open("org.gnome.Calculator")  # as reported by the compositor
    assert reg.is_open("org.gnome.Calculator.desktop")  # as keyed by a bundle


def test_open_and_close_notify_subscribers():
    reg = AppStateRegistry()
    calls = []
    reg.subscribe(lambda: calls.append(reg.open_app_ids))
    reg.add_open("a.desktop")
    reg.add_open("a.desktop")  # dedup: no second notification
    reg.remove_open("a.desktop")
    assert len(calls) == 2
    assert calls[0] == {"a"}
    assert calls[1] == set()


def test_focus_tracking():
    reg = AppStateRegistry()
    reg.add_open("a.desktop")
    reg.add_open("b.desktop")
    reg.set_focused("a.desktop")
    assert reg.is_focused("a.desktop")
    assert not reg.is_focused("b.desktop")
    reg.set_focused("b.desktop")
    assert reg.is_focused("b.desktop")
    assert not reg.is_focused("a.desktop")


def test_closing_focused_app_clears_focus():
    reg = AppStateRegistry()
    reg.add_open("a.desktop")
    reg.set_focused("a.desktop")
    reg.remove_open("a.desktop")
    assert reg.focused_app_id is None


def test_focus_defaults_to_none():
    reg = AppStateRegistry()
    reg.add_open("a.desktop")
    # No focus source: two-state world, nothing is focused.
    assert reg.focused_app_id is None
    assert not reg.is_focused("a.desktop")


def test_unsubscribe_stops_notifications():
    reg = AppStateRegistry()
    calls = []
    unsub = reg.subscribe(lambda: calls.append(1))
    reg.add_open("a.desktop")
    unsub()
    reg.add_open("b.desktop")
    assert len(calls) == 1
