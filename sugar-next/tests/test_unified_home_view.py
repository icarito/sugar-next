import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk

import pytest

from sugar_next.shell.app_ordering import (
    FILTER_ALL,
    FILTER_FAV_ACTIVE,
    FILTER_FAVORITES,
)
from sugar_next.shell.app_state import AppStateRegistry
from sugar_next.shell.home_view import (
    MODE_GRID,
    MODE_SPIRAL,
    UnifiedHomeView,
)


@pytest.fixture(autouse=True)
def gtk_display():
    if not Gtk.init_check():
        pytest.skip("no display available for GTK")


class _StubPage(Gtk.Box):
    """A stand-in page recording what it was told to render."""

    def __init__(self):
        super().__init__()
        self.populated = None
        self.search = None

    def populate(self, bundles):
        self.populated = list(bundles)

    def set_search_text(self, text):
        self.search = text


def _make(monkeypatch, apps, favorites, mru=None):
    # Isolate the data sources the view reads.
    import sugar_next.shell.home_view as hv

    monkeypatch.setattr(hv, "load_favorites", lambda: favorites)

    class _Bundle:
        def __init__(self, app_id, name):
            self.app_id = app_id
            self.name = name

    bundles = [_Bundle(a, a.split(".")[0].title()) for a in apps]
    monkeypatch.setattr(
        hv, "DesktopBundle", type("D", (), {"sorted_apps": staticmethod(lambda: bundles)})
    )
    monkeypatch.setattr(
        hv, "SettingsStore", type("S", (), {"get": lambda self, k: (mru or [])})
    )
    return bundles


def test_default_mode_and_filter():
    spiral, grid = _StubPage(), _StubPage()
    reg = AppStateRegistry()
    view = UnifiedHomeView(spiral, grid, reg)
    assert view.mode == MODE_SPIRAL
    assert view.filter_value == FILTER_FAV_ACTIVE


def test_cycle_mode_does_not_wrap():
    spiral, grid = _StubPage(), _StubPage()
    view = UnifiedHomeView(spiral, grid, AppStateRegistry())
    view.cycle_mode(-1)  # already at first mode
    assert view.mode == MODE_SPIRAL
    view.cycle_mode(1)
    assert view.mode == MODE_GRID
    view.cycle_mode(1)  # past the end, clamps
    assert view.mode == MODE_GRID


def test_filter_favorites_populates_only_favorites(monkeypatch):
    _make(monkeypatch, ["a.desktop", "b.desktop"], favorites=["a.desktop"])
    spiral, grid = _StubPage(), _StubPage()
    view = UnifiedHomeView(spiral, grid, AppStateRegistry())
    view.set_filter(FILTER_FAVORITES)
    # Spiral is the visible page by default; it renders only the favorite.
    assert [b.app_id for b in spiral.populated] == ["a.desktop"]


def test_filter_all_populates_everything(monkeypatch):
    _make(monkeypatch, ["a.desktop", "b.desktop"], favorites=["a.desktop"])
    spiral, grid = _StubPage(), _StubPage()
    view = UnifiedHomeView(spiral, grid, AppStateRegistry())
    view.set_filter(FILTER_ALL)
    assert {b.app_id for b in spiral.populated} == {"a.desktop", "b.desktop"}


def test_active_filter_reacts_to_open_state(monkeypatch):
    _make(monkeypatch, ["a.desktop", "b.desktop"], favorites=[])
    reg = AppStateRegistry()
    spiral, grid = _StubPage(), _StubPage()
    view = UnifiedHomeView(spiral, grid, reg, filter_value=FILTER_FAV_ACTIVE)
    # Nothing pinned or open yet -> empty.
    view.refresh()
    assert spiral.populated == []
    # Opening an app makes it appear under Favorites+Active, live.
    reg.add_open("b.desktop")
    assert [b.app_id for b in spiral.populated] == ["b.desktop"]


def test_search_filters_within_filter(monkeypatch):
    _make(monkeypatch, ["apple.desktop", "banana.desktop"], favorites=None or [])
    spiral, grid = _StubPage(), _StubPage()
    view = UnifiedHomeView(spiral, grid, AppStateRegistry())
    view.set_filter(FILTER_ALL)
    view.set_search("app")
    assert [b.app_id for b in spiral.populated] == ["apple.desktop"]
    # Grid always receives the raw search text too (it filters live).
    assert grid.search == "app"
