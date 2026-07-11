"""Home View container.

A **view** is a way of seeing your system — Desktop, Apps, Search — that
the learner navigates between from the Frame (not a layout selected in
Settings; see the frame-views spec). Each view is a ``Gtk.Widget`` that
declares a ``view_id`` class attribute and MAY define ``on_activate`` /
``on_deactivate`` methods, called when it becomes visible or is switched
away from. There is no base class or mixin to inherit: a view is anything
with a ``view_id`` — duck typing keeps the contract to one attribute.
"""

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk

from sugar_next.bundles.desktop_bundle import DesktopBundle
from sugar_next.shell.app_ordering import (
    FILTER_FAV_ACTIVE,
    FILTERS,
    filter_apps,
    load_favorites,
    order_apps,
)
from sugar_next.shell.settings_store import SettingsStore

#: The layout modes of the unified Home View. Mode is orthogonal to the
#: filter: mode decides how icons are arranged, filter decides which appear.
MODE_SPIRAL = "spiral"
MODE_GRID = "grid"
#: Free mode (manual x/y placement) is a planned follow-up; not yet here.
MODES = (MODE_SPIRAL, MODE_GRID)


class HomeView(Gtk.Stack):
    """Container that swaps between registered views."""

    __gtype_name__ = "SugarNextHomeView"

    def __init__(self):
        super().__init__()
        self.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self._views = {}
        self._active_id = None

    def add_view(self, view, set_active=False):
        view_id = getattr(view, "view_id", None)
        if view_id is None:
            raise ValueError("a view must declare a view_id")
        self._views[view_id] = view
        self.add_named(view, view_id)
        if set_active or self._active_id is None:
            self.set_active(view_id)

    def set_active(self, view_id):
        if view_id not in self._views:
            raise KeyError(f"unknown view {view_id!r}")
        if view_id == self._active_id:
            return
        previous = self._views.get(self._active_id)
        if previous is not None and hasattr(previous, "on_deactivate"):
            previous.on_deactivate()
        self._active_id = view_id
        self.set_visible_child_name(view_id)
        current = self._views[view_id]
        if hasattr(current, "on_activate"):
            current.on_activate()

    @property
    def active_id(self):
        return self._active_id

    def view_ids(self):
        return list(self._views.keys())

    def get_view(self, view_id):
        return self._views.get(view_id)


class UnifiedHomeView(Gtk.Stack):
    """One Home surface with orthogonal *mode* and *filter* axes.

    Wraps a spiral (pie menu) page and a grid page in a Gtk.Stack. The
    mode chooses which page is visible (animated OVER_UP/DOWN); the filter
    and search text choose which apps both pages render. The shell drives
    the axes via ``set_mode`` / ``set_filter`` / ``set_search`` and steps
    the mode with ``cycle_mode`` (bound to scroll/gesture in main.py).
    """

    __gtype_name__ = "SugarNextUnifiedHomeView"

    view_id = "home"
    view_name = "Home"

    def __init__(self, spiral, grid, app_state, mode=MODE_SPIRAL,
                 filter_value=FILTER_FAV_ACTIVE):
        super().__init__()
        self.set_transition_type(Gtk.StackTransitionType.OVER_UP_DOWN)
        self._spiral = spiral
        self._grid = grid
        self._app_state = app_state
        self._mode = mode if mode in MODES else MODE_SPIRAL
        self._filter = filter_value if filter_value in FILTERS else FILTER_FAV_ACTIVE
        self._search = ""

        self.add_named(spiral, MODE_SPIRAL)
        self.add_named(grid, MODE_GRID)
        self.set_visible_child_name(self._mode)

        # Re-derive the visible set whenever the open/focused set changes,
        # so Active / Favorites+Active filters stay live.
        app_state.subscribe(self._repopulate)

    @property
    def mode(self):
        return self._mode

    @property
    def filter_value(self):
        return self._filter

    def set_mode(self, mode):
        if mode not in MODES or mode == self._mode:
            return
        self._mode = mode
        self.set_visible_child_name(mode)
        self._repopulate()

    def cycle_mode(self, step):
        """Step the mode by *step* (+1/-1) along MODES, without wrapping."""
        i = MODES.index(self._mode) + step
        i = max(0, min(len(MODES) - 1, i))
        self.set_mode(MODES[i])

    def set_filter(self, filter_value):
        if filter_value not in FILTERS or filter_value == self._filter:
            return
        self._filter = filter_value
        self._repopulate()

    def set_search(self, text):
        self._search = text or ""
        # Search filters within the active filter's set: the grid filters
        # its cells live; the spiral re-derives (its petals are rebuilt).
        self._grid.set_search_text(self._search)
        if self._mode == MODE_SPIRAL:
            self._repopulate()

    def refresh(self):
        self._repopulate()

    def _visible_bundles(self):
        apps = DesktopBundle.sorted_apps()
        favorites = load_favorites()
        open_ids = self._app_state.open_app_ids
        subset = filter_apps(apps, self._filter, favorites, open_ids)
        store = SettingsStore()
        ordered = order_apps(subset, favorites, store.get("mru_order"))
        if self._search:
            needle = self._search.lower()
            ordered = [b for b in ordered if needle in b.name.lower()]
        return ordered

    def _repopulate(self):
        bundles = self._visible_bundles()
        # Only the visible page needs a rebuild; the hidden one refreshes
        # when it becomes visible via set_mode -> _repopulate.
        if self._mode == MODE_SPIRAL:
            self._spiral.populate(bundles)
        else:
            self._grid.populate(bundles)

    # -- view protocol (HomeView duck-types on view_id/on_activate) -------

    def on_activate(self):
        self._repopulate()

    def on_deactivate(self):
        pass
