import time

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gio, GLib

from sugar_next.bundles.desktop_bundle import DesktopBundle


def _marker_bundle(tmp_path):
    marker = tmp_path / "marker"
    desktop_file = tmp_path / "smoke.desktop"
    desktop_file.write_text(
        "[Desktop Entry]\n"
        "Type=Application\n"
        "Name=Smoke\n"
        f"Exec=touch {marker}\n"
        "NoDisplay=true\n"
    )
    info = Gio.DesktopAppInfo.new_from_filename(str(desktop_file))
    return DesktopBundle(info), marker


def test_scanner_finds_apps():
    apps = DesktopBundle.sorted_apps()
    assert len(apps) > 0
    names = [a.name for a in apps]
    assert names == sorted(names, key=str.lower)


def test_bundle_properties(tmp_path):
    bundle, _ = _marker_bundle(tmp_path)
    assert bundle.name == "Smoke"
    assert bundle.app_id == "smoke.desktop"
    assert bundle.description == ""


def test_launch_runs_exec_and_fires_hook(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "xdg"))
    bundle, marker = _marker_bundle(tmp_path)

    fired = []
    from sugar_next.api import hooks

    monkeypatch.setattr(
        hooks.registry,
        "call",
        lambda name, *args, **kw: fired.append((name, args[0])) or [],
    )

    assert bundle.launch() is True
    for _ in range(50):
        if marker.exists():
            break
        time.sleep(0.1)
    assert marker.exists()
    assert fired == [("on_app_launch", "smoke.desktop")]


def test_launch_fires_on_app_close_when_process_exits(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "xdg"))
    bundle, marker = _marker_bundle(tmp_path)

    fired = []
    from sugar_next.api import hooks

    monkeypatch.setattr(
        hooks.registry,
        "call",
        lambda name, *args, **kw: fired.append((name, args[0])) or [],
    )

    assert bundle.launch() is True

    loop = GLib.MainLoop()
    GLib.timeout_add(2000, lambda: loop.quit() or False)

    def _check_done():
        if any(name == "on_app_close" for name, _ in fired):
            loop.quit()
        return True

    GLib.timeout_add(50, _check_done)
    loop.run()

    assert ("on_app_close", "smoke.desktop") in fired


def test_pid_zero_does_not_register_a_close_watch(tmp_path, monkeypatch):
    # Regression: DBusActivatable apps (Nautilus, GNOME Connections, ...)
    # are launched via D-Bus Activate rather than fork+exec, and report
    # pid=0 in the "launched" signal's platform_data. GLib.child_watch_add
    # on pid 0 never fires, so on_app_close would never fire either —
    # leaving the app stuck in the Frame forever. _on_launched must skip
    # watch registration for pid=0 instead of treating it like a real PID.
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "xdg"))
    bundle, _ = _marker_bundle(tmp_path)

    from sugar_next import bundles

    watch_calls = []
    monkeypatch.setattr(
        bundles.desktop_bundle,
        "_watch_for_close",
        lambda app_id, app_info, pid: watch_calls.append(pid),
    )

    bundle._on_launched(None, bundle.app_info, {"pid": 0})
    assert watch_calls == []

    bundle._on_launched(None, bundle.app_info, {"pid": 12345})
    assert watch_calls == [12345]


def test_from_wm_class_direct_match(tmp_path, monkeypatch):
    # Fast path: Gio.DesktopAppInfo.new() finds the id directly. Uses the
    # real GIO desktop-file index (like Gio.DesktopAppInfo.new always
    # does), so exercise it against a real installed app rather than a
    # tmp_path fixture — XDG_DATA_HOME changes mid-process aren't
    # guaranteed to be picked up by GIO's cached app index.
    apps = DesktopBundle.sorted_apps()
    if not apps:
        return  # nothing installed in this environment to test against
    known = apps[0]
    bundle = DesktopBundle.from_wm_class(known.app_id.removesuffix(".desktop"))
    assert bundle is not None
    assert bundle.app_id == known.app_id


def test_from_wm_class_normalized_match(tmp_path, monkeypatch):
    # A window-observation adapter's wm_class doesn't always match the
    # .desktop id's exact casing/suffix (window-observation spec: "external
    # window is tracked") — from_wm_class must fall back to a normalized
    # scan (via iter_apps) when the direct Gio.DesktopAppInfo.new() lookup
    # misses. Mock iter_apps directly rather than depending on GIO's
    # desktop-file index picking up a tmp_path fixture mid-process.
    bundle, _ = _marker_bundle(tmp_path)
    from sugar_next import bundles

    monkeypatch.setattr(
        bundles.desktop_bundle.DesktopBundle, "iter_apps", lambda: iter([bundle])
    )

    found = DesktopBundle.from_wm_class("SMOKE")
    assert found is not None
    assert found.app_id == "smoke.desktop"


def test_from_wm_class_no_match_returns_none():
    assert DesktopBundle.from_wm_class("no.such.app.Anywhere") is None
