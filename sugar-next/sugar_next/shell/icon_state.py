"""Render app icons to reflect open/focused state.

Color is meaningful in Sugar Next (HIG principle #4): an app's icon is
greyscale when the app is closed, full color when it is open, and gets a
saturated highlight when it is the focused app. Where the compositor
cannot report focus (see ``app_state``), ``focused_app_id`` stays ``None``
and icons only ever reach the open (color) state — a coherent two-state
fallback rather than a guess.

The three states are expressed as CSS ``-gtk-icon-filter`` rules (the
same GTK4 mechanism the Frame already uses to invert active-view icons),
applied by swapping a CSS class on the ``Gtk.Image``. A widget calls
:func:`bind_icon_state` once; it subscribes to the shared registry and
keeps the class in sync until the returned unsubscribe callable is run.
"""

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
from gi.repository import Gdk, Gtk

from sugar_next.shell.app_state import registry as app_state

_STATE_CLOSED = "sn-icon-closed"
_STATE_OPEN = "sn-icon-open"
_STATE_FOCUSED = "sn-icon-focused"
_ALL_STATE_CLASSES = (_STATE_CLOSED, _STATE_OPEN, _STATE_FOCUSED)

_CSS = """
    .sn-icon-closed {
        -gtk-icon-filter: grayscale(1) opacity(0.55);
        opacity: 0.75;
        transition: opacity 200ms ease, -gtk-icon-filter 200ms ease;
    }
    .sn-icon-open {
        -gtk-icon-filter: none;
        opacity: 1;
        transition: opacity 200ms ease, -gtk-icon-filter 200ms ease;
    }
    .sn-icon-focused {
        -gtk-icon-filter: saturate(1.35) brightness(1.05);
        opacity: 1;
        transition: opacity 200ms ease, -gtk-icon-filter 200ms ease;
    }
"""

_css_installed = False


def _ensure_css():
    global _css_installed
    if _css_installed:
        return
    display = Gdk.Display.get_default()
    if display is None:
        return
    provider = Gtk.CssProvider()
    provider.load_from_string(_CSS)
    Gtk.StyleContext.add_provider_for_display(
        display, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
    )
    _css_installed = True


def state_class_for(app_id) -> str:
    """The icon-state CSS class an app's icon should currently carry."""
    if app_state.is_focused(app_id):
        return _STATE_FOCUSED
    if app_state.is_open(app_id):
        return _STATE_OPEN
    return _STATE_CLOSED


def apply_icon_state(image: Gtk.Image, app_id):
    """Set *image*'s icon-state class to match *app_id*'s current state."""
    target = state_class_for(app_id)
    for cls in _ALL_STATE_CLASSES:
        if cls == target:
            image.add_css_class(cls)
        else:
            image.remove_css_class(cls)


def bind_icon_state(image: Gtk.Image, app_id):
    """Keep *image* rendering *app_id*'s open/focused state, live.

    Applies the current state immediately, then re-applies on every
    registry change. Returns an unsubscribe callable; call it when the
    icon widget is discarded so the registry does not keep it alive.
    """
    _ensure_css()
    apply_icon_state(image, app_id)
    return app_state.subscribe(lambda: apply_icon_state(image, app_id))
