"""Shared registry of open and focused applications.

Sugar Next tracks "which apps are open" and "which app is focused" in one
place so every view — the Frame's running list, the Desktop pie menu, the
Apps grid — reads the same truth instead of each keeping its own copy
(the Frame historically kept a private ``_running_ids`` set). The shell
(``main.py``) owns the Wayland toplevel lifecycle and feeds this registry;
views subscribe to it and re-render on change.

Open tracking works on every compositor (it falls back to the shell's
``on_app_close`` hook when no toplevel protocol is available). Focus
tracking needs the wlroots ``activated`` toplevel state; where that is
unavailable, ``focused_app_id`` stays ``None`` forever and views degrade
to a two-state (closed/open) rendering rather than guessing focus.
"""


def normalize_app_id(app_id) -> str:
    """Normalize a desktop or Wayland app id for cross-source matching.

    A Wayland ``app_id`` (``org.gnome.Calculator``) and a ``.desktop`` id
    (``org.gnome.Calculator.desktop``) refer to the same app; views key
    icons off the desktop id while the compositor reports the Wayland one.
    Strips a trailing ``.desktop`` and lowercases so the two line up.
    """
    if not app_id:
        return ""
    text = str(app_id)
    if text.endswith(".desktop"):
        text = text[: -len(".desktop")]
    return text.lower()


class AppStateRegistry:
    """Single source of truth for open/focused apps, with subscribers.

    Ids are stored normalized (see :func:`normalize_app_id`) so callers
    may pass either a Wayland app id or a ``.desktop`` id interchangeably.
    """

    def __init__(self):
        self._open = set()
        self._focused = None
        self._subscribers = []

    # -- queries (used by views when rendering an icon) -------------------

    @property
    def open_app_ids(self) -> set:
        """Normalized ids of all currently-open apps."""
        return set(self._open)

    @property
    def focused_app_id(self):
        """Normalized id of the focused app, or ``None`` if unknown."""
        return self._focused

    def is_open(self, app_id) -> bool:
        return normalize_app_id(app_id) in self._open

    def is_focused(self, app_id) -> bool:
        norm = normalize_app_id(app_id)
        return norm != "" and norm == self._focused

    # -- mutation (used by the shell as toplevel events arrive) -----------

    def add_open(self, app_id):
        norm = normalize_app_id(app_id)
        if not norm or norm in self._open:
            return
        self._open.add(norm)
        self._notify()

    def remove_open(self, app_id):
        norm = normalize_app_id(app_id)
        changed = False
        if norm in self._open:
            self._open.discard(norm)
            changed = True
        # A closed app cannot remain the focused one.
        if self._focused == norm:
            self._focused = None
            changed = True
        if changed:
            self._notify()

    def set_focused(self, app_id):
        """Set (or clear, with ``None``) the focused app id."""
        norm = normalize_app_id(app_id) if app_id is not None else None
        if norm == self._focused:
            return
        self._focused = norm or None
        self._notify()

    # -- subscription -----------------------------------------------------

    def subscribe(self, callback):
        """Register *callback* (called with no args) on any state change.

        Returns an unsubscribe callable so a view can detach when it goes
        away.
        """
        self._subscribers.append(callback)

        def _unsubscribe():
            try:
                self._subscribers.remove(callback)
            except ValueError:
                pass

        return _unsubscribe

    def _notify(self):
        for callback in list(self._subscribers):
            callback()


#: Shared registry instance used by the shell and its views.
registry = AppStateRegistry()
