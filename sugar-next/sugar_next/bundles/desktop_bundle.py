import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gio, GLib

from sugar_next.api.hooks import registry as hook_registry
from sugar_next.shell.app_state import normalize_app_id


def _watch_for_close(app_id, app_info, pid):
    """Fire on_app_close when *pid* exits.

    Fallback path (window-observation spec, design D4): the active
    window-observation adapter (GnomeWindowSource in hosted mode,
    TopLevelTracker in standalone mode) is the primary close-tracking
    mechanism and covers windows this shell did not launch too. This
    pid-watch only matters in the narrow window before the adapter's
    first event, or if no adapter is available (X11, missing extension) —
    and even then it cannot observe DBusActivatable apps (pid=0; see the
    call site).

    Note: Gio.AppInfo.launch() commonly reparents the launched process to
    the user's systemd instance (transient scope / portal activation)
    rather than forking it as our direct child, so the PID we watch is
    not our own child on those systems. GLib.child_watch_add() still
    fires reliably here because it falls back to polling /proc when
    waitpid() reports ECHILD — this works on Linux (Sugar Next's only
    target) but is not the "correct" parent-child watch mechanism. A
    fully correct implementation would track the systemd transient scope
    via org.freedesktop.systemd1 and watch its JobRemoved signal; that is
    unnecessary complexity for this v0.
    """

    def _on_exit(_pid, _status):
        hook_registry.call("on_app_close", app_id, app_info)
        GLib.spawn_close_pid(_pid)

    GLib.child_watch_add(GLib.PRIORITY_DEFAULT, pid, _on_exit)


class DesktopBundle:
    def __init__(self, app_info):
        self.app_info = app_info

    @property
    def app_id(self):
        return self.app_info.get_id()

    @property
    def name(self):
        return self.app_info.get_display_name()

    @property
    def description(self):
        return self.app_info.get_description() or ""

    @property
    def icon(self):
        icon = self.app_info.get_icon()
        if icon:
            return icon
        return None

    @property
    def category(self):
        """First XDG category from the .desktop file, if any."""
        categories = self.app_info.get_categories()
        if not categories:
            return None
        return categories.split(";")[0] or None

    def launch(self):
        # An on_app_launch hook may veto the launch by returning
        # {"cancel": True}; extensions that return nothing let it proceed.
        if hook_registry.call_is_cancelled(
            "on_app_launch", self.app_id, self.app_info
        ):
            return False
        launch_context = Gio.AppLaunchContext()
        launch_context.connect("launched", self._on_launched)
        return self.app_info.launch(None, launch_context)

    def _on_launched(self, context, app_info, platform_data):
        pid = dict(platform_data).get("pid") if platform_data else None
        # DBusActivatable apps (Nautilus, GNOME Connections, ...) are
        # launched via a D-Bus Activate call rather than fork+exec, and
        # report pid=0 — not a real process to watch. GLib.child_watch_add
        # on pid 0 never fires, so the app would stay stuck in the Frame
        # forever. Skip close-tracking for these; on_app_close simply
        # never fires for them under the fallback path (real window
        # tracking via wlr-foreign-toplevel-management, when available,
        # is unaffected — it tracks windows, not processes).
        if pid:
            _watch_for_close(self.app_id, self.app_info, pid)

    @staticmethod
    def iter_apps():
        for app_info in Gio.AppInfo.get_all():
            try:
                if app_info.should_show():
                    yield DesktopBundle(app_info)
            except Exception:
                continue

    @staticmethod
    def sorted_apps():
        apps = list(DesktopBundle.iter_apps())
        apps.sort(key=lambda a: a.name.lower())
        return apps

    @staticmethod
    def from_wm_class(wm_class):
        """Resolve a window-observation adapter's app id to a bundle.

        window-observation reports the Wayland ``wm_class``/``app_id`` of
        *any* window (window-observation spec: "external window is
        tracked"), not just ones this shell launched — so the Frame can
        show a real running-app entry for a terminal-launched app the
        same way it does for a shell-launched one. Returns ``None`` when
        no matching desktop entry exists (e.g. a window with no
        installed .desktop file), leaving the caller to fall back to
        icon-only tracking via app_state.

        Tries the direct id first (fast path: wm_class commonly matches
        the desktop file's own id, e.g. "org.gnome.Calculator"), then
        falls back to a normalized scan of all apps — wm_class and
        desktop-id casing/suffix can differ (see normalize_app_id).
        """
        for candidate in (wm_class, f"{wm_class}.desktop"):
            try:
                app_info = Gio.DesktopAppInfo.new(candidate)
            except TypeError:
                # Gio.DesktopAppInfo.new() raises (not returns None) when
                # no matching .desktop file exists — a GI binding quirk
                # around the underlying C API's NULL return.
                continue
            if app_info is not None:
                return DesktopBundle(app_info)

        target = normalize_app_id(wm_class)
        if not target:
            return None
        for bundle in DesktopBundle.iter_apps():
            if normalize_app_id(bundle.app_id) == target:
                return bundle
        return None
