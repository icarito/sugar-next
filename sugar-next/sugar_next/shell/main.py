#!/usr/bin/env python3
import cairo
import sys
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
gi.require_version("GdkPixbuf", "2.0")
from gi.repository import Gdk, GdkPixbuf, Gtk, GLib

from sugar_next.api.hooks import registry as hook_registry
from sugar_next.bundles.desktop_bundle import DesktopBundle
from sugar_next.shell.app_state import registry as app_state, normalize_app_id
from sugar_next.shell.app_grid import SugarAppGrid
from sugar_next.shell.pie_menu import SugarPieMenu
from sugar_next.shell.frame import SugarFrame
from sugar_next.shell.gnome_window_source import GnomeWindowSource
from sugar_next.shell.home_view import HomeView
from sugar_next.shell.theme import manager as theme_manager
from sugar_next.shell.palette import dominant_color_hex
from sugar_next.shell.settings import SettingsPanel
from sugar_next.shell.settings_store import SettingsStore, icon_size_px
from sugar_next.shell.toplevel_tracker import TopLevelTracker

#: The shell's own application id (matches SugarShell.__init__'s
#: Gtk.Application id below). Both window-observation adapters report
#: every window they see, including the shell's own toplevel — without
#: filtering this out, Sugar Next would show itself as a "running app" in
#: its own Frame, and clicking that entry would try to focus/launch a
#: second instance of itself.
_SHELL_APP_ID = normalize_app_id("org.sugarlabs.SugarNext")


def _standalone_protocol_available() -> bool:
    """Standalone-mode detection (shell-startup spec): probe the compositor.

    Checks whether wlr-foreign-toplevel-management is actually advertised
    on the current WAYLAND_DISPLAY — a direct compositor capability check,
    not an environment-variable heuristic. XDG_CURRENT_DESKTOP was tried
    first and rejected: it is inherited across the process chain from
    wherever the shell was launched (a terminal, a session's autostart
    script, ...) rather than reflecting which compositor is actually
    serving the current Wayland socket, and was observed live giving a
    false "GNOME" reading for a shell running under a nested Wayfire
    session launched from a GNOME terminal.

    A throwaway connection + one roundtrip (~30ms measured locally) is
    cheap enough to do unconditionally at startup, before picking an
    adapter. GNOME/Mutter never advertises this protocol (by design, see
    toplevel_tracker.py); any compositor that does is standalone-capable.
    """
    try:
        from pywayland.client import Display
    except ImportError:
        return False

    found = False
    try:
        display = Display()
        display.connect()
        try:
            registry = display.get_registry()

            def _on_global(_registry, _name, interface, _version):
                nonlocal found
                if interface == "zwlr_foreign_toplevel_manager_v1":
                    found = True

            registry.dispatcher["global"] = _on_global
            display.roundtrip()
        finally:
            display.disconnect()
    except Exception:
        return False
    return found


class SugarShell(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="org.sugarlabs.SugarNext")
        self.connect("activate", self._on_activate)
        self.connect("shutdown", self._on_shutdown)

    def _on_activate(self, app):
        hook_registry.load()
        hook_registry.call("on_shell_start")
        # Computed once and cached: startup-mode detection (shell-startup
        # spec) probes the compositor over Wayland (see
        # _standalone_protocol_available's docstring for why), so it's
        # worth avoiding a second roundtrip for the same answer later in
        # this method.
        self._standalone_mode = _standalone_protocol_available()
        self.window = Gtk.ApplicationWindow(
            application=app,
            title="Sugar Next — A Learning Shell for Everyday Computing",
            default_width=1024,
            default_height=768,
        )
        self.settings_store = SettingsStore()
        is_dark = self.settings_store.get("dark_mode")
        theme_manager.set_dark_mode(is_dark)
        theme_manager.apply(self.window.get_display())
        if self.settings_store.get("accent_color"):
            theme_manager.set_accent_tint(self.settings_store.get("accent_color"))
        theme_manager.set_contrast(self.settings_store.get("contrast"))

        base_css = Gtk.CssProvider()
        base_css.load_from_string(
            """
            window {
                background-color: var(--sn-bg);
                color: var(--sn-text);
            }
            button {
                border-radius: 10px;
                box-shadow: 0 1px 0 rgba(255,255,255,0.12);
            }
            button:hover {
                box-shadow: 0 1px 0 rgba(255,255,255,0.18),
                            0 2px 6px rgba(0,0,0,0.12);
            }
            searchbar, entry {
                border-radius: 12px;
                border: 1px solid rgba(0,0,0,0.1);
                background: linear-gradient(180deg,
                    rgba(0,0,0,0.03) 0%,
                    rgba(0,0,0,0.01) 100%
                );
                box-shadow:
                    inset 0 1px 2px rgba(0,0,0,0.06),
                    0 1px 0 rgba(255,255,255,0.08);
            }
            .sn-dropdown {
                border: none;
                box-shadow: none;
                background: none;
                margin: 0;
                padding: 0 4px;
                min-height: 28px;
            }
            .sn-dropdown > button {
                border-radius: 8px;
                border: 1px solid rgba(0,0,0,0.12);
                background: linear-gradient(180deg,
                    rgba(255,255,255,0.08) 0%,
                    rgba(0,0,0,0.02) 100%
                );
                box-shadow: 0 1px 0 rgba(255,255,255,0.08);
                padding: 2px 10px;
            }
            .sn-dropdown > button:hover {
                border-color: rgba(0,0,0,0.20);
            }
            .sn-dropdown > popover {
                border-radius: 10px;
                border: 1px solid rgba(0,0,0,0.12);
                box-shadow: 0 3px 12px rgba(0,0,0,0.18);
                padding: 4px 0;
            }
            .sn-dropdown > popover contents > row {
                padding: 4px 12px;
            }
            .sn-dropdown > popover contents > row:hover {
                background: var(--sn-accent);
                color: white;
            }
            .frame-handle {
                min-width: 52px;
                min-height: 14px;
                padding: 0;
                margin-top: 0;
                border: none;
                border-radius: 0 0 8px 8px;
                background: var(--sn-accent);
                opacity: 0.6;
                box-shadow: 0 1px 3px rgba(0,0,0,0.35);
                transition: opacity 150ms ease;
            }
            .frame-handle:hover {
                opacity: 0.95;
            }
            """
        )
        Gtk.StyleContext.add_provider_for_display(
            self.window.get_display(),
            base_css,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )

        self.frame = SugarFrame()

        # Bundles for apps this shell launched, so the Frame can render a
        # rich item (icon + palette) when the registry reports them open.
        # Keyed by normalized app id. Apps opened outside the shell have no
        # bundle here and are tracked as ids only.
        self._launched_bundles = {}
        # Window refcounts per normalized app id. In hosted mode (GNOME)
        # each window triggers its own open/close event; this prevents
        # closing one of multiple windows from marking the app closed.
        self._toplevel_refcounts = {}
        # Keep the Frame's rendered running-list in sync with the shared
        # registry — the registry is the single source of truth for what
        # is open (frame-views spec); the Frame only renders it.
        app_state.subscribe(self._sync_frame_running)

        # Window-observation adapter (shell-startup / window-observation
        # specs): exactly one of the two is active, selected by startup
        # mode. Both feed the same app_state contract (add_open/
        # remove_open/set_focused) so the Frame and lifecycle hooks below
        # do not know or care which one is running.
        self.toplevel_tracker = None
        self.gnome_window_source = None
        if self._standalone_mode:
            self.toplevel_tracker = TopLevelTracker(
                on_open=self._on_toplevel_open,
                on_close=self._on_toplevel_close,
                on_focus=self._on_toplevel_focus,
            )
            self.toplevel_tracker.start()
        else:
            self.gnome_window_source = GnomeWindowSource(
                on_open=self._on_toplevel_open,
                on_close=self._on_toplevel_close,
                on_focus=self._on_toplevel_focus,
            )
            self.gnome_window_source.start()
        hook_registry.subscribe(
            "on_app_close", lambda app_id, app_info: self._on_app_process_closed(app_id)
        )

        icon_size = icon_size_px(self.settings_store.get("icon_size"))
        self.pie_menu = SugarPieMenu(
            on_settings=self._on_settings_requested,
            on_launched=self._activate_app,
            icon_size=icon_size,
            on_exit=self._on_exit_requested,
            exit_label="Logout" if self._standalone_mode else "Close Sugar Next",
        )
        self.app_grid = SugarAppGrid(
            on_launched=self._activate_app,
            on_pin=self.pie_menu.pin_favorite,
            icon_size=icon_size,
        )

        self.home_view = HomeView()
        self.home_view.add_view(self.app_grid)
        self.home_view.add_view(self.pie_menu, set_active=True)

        # Views are navigated from the Frame (Desktop / Apps), not selected
        # in Settings. Map the user-facing view onto the underlying layout
        # id. Order here is the Frame button order. Search view is removed
        # (desktop-pie-menu change); F3 is reserved for a future
        # Groups/Neighborhood view.
        self._views = [
            ("desktop-grid", "Desktop"),
            ("app-grid", "Apps"),
        ]

        # Restore the last active view, or start in Desktop on first run.
        saved_layout = self.settings_store.get("home_view_layout")
        if saved_layout in self.home_view.view_ids():
            self.home_view.set_active(saved_layout)
        else:
            self.home_view.set_active("desktop-grid")

        self._background_picture = Gtk.Picture()
        self._background_picture.set_content_fit(Gtk.ContentFit.COVER)
        self._background_picture.set_can_shrink(True)
        bg_path = self.settings_store.get("background_path")
        if bg_path:
            self._background_picture.set_filename(bg_path)
            self._bg_grey_pixbuf = self._build_grey_pixbuf(bg_path)
        self._background_picture.add_css_class("home-view-bg")

        # Background adjustment overlay. A single flat wash drawn over the
        # wallpaper and *under* the Home View, so every view (app-grid,
        # desktop-grid pie menu) sees the same treatment.
        #   brightness: -1.0 (black) .. 0 (none) .. +1.0 (white)
        #   contrast:    0.0 (none)  .. 1.0 (flat mid-grey veil)
        self._bg_brightness = float(self.settings_store.get("bg_brightness"))
        self._bg_contrast = float(self.settings_store.get("bg_contrast"))
        self._bg_saturation = float(self.settings_store.get("bg_saturation"))
        self._bg_vignette = float(self.settings_store.get("bg_vignette"))

        self._bg_overlay = Gtk.DrawingArea()
        self._bg_overlay.set_hexpand(True)
        self._bg_overlay.set_vexpand(True)
        self._bg_overlay.set_can_target(False)
        self._bg_overlay.add_css_class("home-view-bg-overlay")
        self._bg_overlay.set_draw_func(self._draw_bg_overlay)

        home_overlay = Gtk.Overlay()
        home_overlay.set_child(self._background_picture)
        home_overlay.add_overlay(self._bg_overlay)
        home_overlay.add_overlay(self.home_view)

        shell_overlay = Gtk.Overlay()
        shell_overlay.set_child(home_overlay)
        shell_overlay.add_overlay(self.frame)
        self.window.set_child(shell_overlay)
        shell_overlay._frame = self.frame

        # Visible pull-down handle at the top-center — a small accent pill
        # that reveals the Frame on click or hover. Centered so it never
        # overlaps the Frame's settings button at the right edge. It hides
        # itself while the Frame is open (the Frame's own top edge takes
        # over) and reappears when the Frame is dismissed.
        self._hot_corner = Gtk.Button()
        self._hot_corner.add_css_class("frame-handle")
        self._hot_corner.set_halign(Gtk.Align.CENTER)
        self._hot_corner.set_valign(Gtk.Align.START)
        self._hot_corner.set_tooltip_text("Click or hover to reveal the Frame")
        self._hot_corner.connect("clicked", self._on_handle_clicked)
        shell_overlay.add_overlay(self._hot_corner)

        # Keep the handle out of the way whenever the Frame is showing.
        self.frame.connect(
            "notify::child-revealed", self._on_frame_reveal_changed
        )

        # Classic-Sugar auto-Frame: reveal the Frame when the shell loses
        # focus (an activity has taken the screen, so the user always has a
        # way back). It is NOT hidden when the window regains focus — the
        # Frame lives inside the shell window, so regaining window focus is
        # not the same as leaving the Frame. Instead it hides when the
        # pointer leaves the Frame's own area (see the motion controller on
        # ``self.frame`` below). A manual dismiss is respected until the
        # next focus change.
        self._frame_manually_dismissed = False
        # Clicking the handle *pins* the Frame open: a deliberate act, so
        # it must not close just because the pointer moves into the window.
        # Only another click on the handle (toggle), F6, or a background
        # click dismisses a pinned Frame. Hovering the handle still reveals
        # a transient, unpinned Frame that hides on pointer-leave.
        self._frame_pinned = False
        # Monotonic time (µs) until which a spurious pointer `leave` right
        # after revealing the Frame must be ignored. Revealing slides the
        # Frame out from under the pointer, which fires `leave` immediately
        # and would otherwise snap it shut so a click "does nothing".
        self._frame_leave_guard_until = 0
        self.window.connect("notify::is-active", self._on_window_active_changed)

        # Hide the Frame once the pointer leaves it (but not while the shell
        # is unfocused — then an activity owns the screen and the Frame
        # should stay put as the way back).
        frame_motion = Gtk.EventControllerMotion()
        frame_motion.connect("leave", self._on_frame_pointer_left)
        self.frame.add_controller(frame_motion)

        # Click outside the Frame closes it.
        close_gesture = Gtk.GestureClick()
        close_gesture.connect("pressed", self._on_background_pressed)
        home_overlay.add_controller(close_gesture)

        self.settings_panel = SettingsPanel(
            home_view=self.home_view, store=self.settings_store, shell=self
        )
        self.frame.set_view_switcher(
            self._views,
            self._on_view_selected,
            active_id=self.home_view.active_id,
        )
        self.frame.set_running_activated_callback(self._on_frame_running_activated)
        self.frame.set_theme_toggle_callback(self._on_theme_toggle)
        self.frame.set_dark_mode(self.settings_store.get("dark_mode"))

        key_controller = Gtk.EventControllerKey()
        key_controller.connect("key-pressed", self._on_key_pressed)
        self.window.add_controller(key_controller)

        # Motion on the hot corner itself (keeping the old behavior).
        motion = Gtk.EventControllerMotion()
        motion.connect("motion", self._on_motion)
        self._hot_corner.add_controller(motion)

        self.window.present()
        if self._standalone_mode:
            # Standalone mode: Sugar Next is the session owner, not a
            # guest — it manages its own presentation (design.md D3's
            # "session-owner exception"), like any DE's shell process.
            # In hosted mode no equivalent call is made — Sugar Next is a
            # guest inside GNOME and does not ask for special treatment.
            #
            # Done in-app (Gtk.Window.fullscreen()), not via a Wayfire
            # window-rule: window-rules' only lifecycle event, `created`,
            # races GTK4's first paint under Wayfire — a created-time
            # maximize/fullscreen rule renders the client as flat grey
            # with no content (upstream Wayfire issues #957, #1094; no
            # later hook exists in Wayfire's config surface, confirmed
            # against the wiki). Calling fullscreen() here, after
            # present() has already mapped and painted the window, avoids
            # that race.
            #
            # Also avoids a second, distinct nested-session bug: calling
            # fullscreen() *before* present() (on an unmapped toplevel)
            # made a nested Wayfire dev session negotiate a custom output
            # mode and reject it (wlroots 0.19's nested Wayland backend —
            # "Couldn't find matching mode 1280x720@0 ... disabling
            # output", verified live), tearing down the whole nested
            # session. After present(), fullscreen only requests state on
            # the existing output — no mode renegotiation.
            self.window.fullscreen()

    def _on_window_active_changed(self, window, _pspec):
        # Focus changed: this is a fresh context, so any earlier manual
        # dismiss no longer applies.
        self._frame_manually_dismissed = False
        if not window.get_property("is-active"):
            # Shell lost focus (an activity took over) — surface the Frame
            # as the user's way back. Regaining focus does *not* hide it;
            # that is left to the pointer leaving the Frame.
            self.frame.reveal()

    def _reveal_frame(self):
        # Guard against the `leave` that fires as the Frame slides out from
        # under the pointer, so it doesn't immediately close again.
        self._frame_leave_guard_until = GLib.get_monotonic_time() + 400_000
        self.frame.reveal()

    def _on_handle_clicked(self, _button):
        # Clicking toggles a pinned Frame: pin it open, or unpin+close if
        # it is already pinned.
        if self._frame_pinned and self.frame.get_reveal_child():
            self._frame_pinned = False
            self.frame.set_reveal_child(False)
        else:
            self._frame_pinned = True
            self._reveal_frame()

    def _on_frame_pointer_left(self, _controller):
        # A pinned Frame (opened by clicking the handle) stays put no
        # matter where the pointer goes; only an explicit dismiss closes it.
        if self._frame_pinned:
            return
        # Ignore the spurious leave right after a reveal (see _reveal_frame).
        if GLib.get_monotonic_time() < self._frame_leave_guard_until:
            return
        # Keep the Frame open while an item palette is up — the palette
        # extends below the Frame, so the pointer "leaves" the Frame to
        # use it; hiding now would make the palette unusable.
        if self.frame.has_open_palette():
            return
        # Pointer left the Frame. Tuck it away — unless the shell is
        # unfocused, in which case an activity owns the screen and the
        # Frame must remain as the way back.
        if self.window.get_property("is-active"):
            self.frame.set_reveal_child(False)

    def _on_background_pressed(self, gesture, n_press, x, y):
        # Explicit dismiss: unpin and remember it so auto-Frame does not
        # immediately re-open while the shell stays unfocused.
        self._frame_pinned = False
        if not self.window.get_property("is-active"):
            self._frame_manually_dismissed = True
        self.frame.set_reveal_child(False)

    #: Direct keybindings to views (frame-views spec): F1/F2. F3 is
    #: reserved for a future Groups/Neighborhood view (desktop-pie-menu
    #: change removed Search, which previously used F3).
    _VIEW_KEYS = {
        Gdk.KEY_F1: "desktop-grid",
        Gdk.KEY_F2: "app-grid",
    }

    def _on_key_pressed(self, controller, keyval, keycode, state):
        if keyval == Gdk.KEY_F6:
            # F6 is a deliberate act, like clicking the handle: it pins the
            # Frame open, or unpins+closes it if already open.
            if self.frame.get_reveal_child():
                self._frame_pinned = False
                if not self.window.get_property("is-active"):
                    self._frame_manually_dismissed = True
                self.frame.set_reveal_child(False)
            else:
                self._frame_pinned = True
                self._reveal_frame()
            return True
        if keyval in self._VIEW_KEYS:
            self._activate_view(self._VIEW_KEYS[keyval])
            return True
        if keyval == Gdk.KEY_F10:
            if self.settings_panel.is_visible():
                self.settings_panel.popdown()
            else:
                self.settings_panel.popup()
            return True
        return False

    def _on_settings_requested(self):
        # Chosen from the center menu's "Settings" item.
        self.settings_panel.popup()

    def _on_exit_requested(self):
        # Center-menu exit action. In standalone mode this is "Logout"
        # (Sugar owns the session); when hosted it is "Close Sugar Next"
        # (the host session keeps running). Both quit this application;
        # standalone session teardown, when integrated with a session
        # manager, would hook in here.
        self.quit()

    def _activate_view(self, view_id):
        """Switch to *view_id*, persist it, and sync the Frame switcher."""
        if view_id not in self.home_view.view_ids():
            return
        self.home_view.set_active(view_id)
        self.frame.set_active_view(view_id)
        self.settings_store.set("home_view_layout", view_id)

    def _on_view_selected(self, view_id):
        # Called when a Frame view button is clicked. The Frame closes
        # after selection (handled in frame.py), so drop any pin.
        self._frame_pinned = False
        self._activate_view(view_id)

    def _on_theme_toggle(self):
        is_dark = not self.settings_store.get("dark_mode")
        self.settings_store.set("dark_mode", is_dark)
        theme_manager.set_dark_mode(is_dark)
        self.frame.set_dark_mode(is_dark)

    def _on_motion(self, controller, x, y):
        if y <= 3:
            self._reveal_frame()

    def _on_frame_reveal_changed(self, frame, _pspec):
        # Fade the pull-down handle out while the Frame is visible instead
        # of hiding it: set_visible(False) collapses the overlay child and
        # forces a re-layout mid-animation, which makes the Frame "jump".
        # Opacity + can_target keeps its slot reserved, so no reflow.
        revealed = frame.get_child_revealed()
        self._hot_corner.set_opacity(0.0 if revealed else 1.0)
        self._hot_corner.set_can_target(not revealed)

    def _on_shutdown(self, app):
        if self.toplevel_tracker is not None:
            self.toplevel_tracker.stop()
        if self.gnome_window_source is not None:
            self.gnome_window_source.stop()

    def _on_app_launched(self, bundle):
        self._launched_bundles[normalize_app_id(bundle.app_id)] = bundle
        app_state.add_open(bundle.app_id)
        self._record_mru(bundle.app_id)
        if self.settings_store.get("accent_color"):
            return
        color = dominant_color_hex(bundle.icon)
        theme_manager.set_accent_tint(color)

    def _record_mru(self, app_id):
        # Promote *app_id* to the front of the most-recently-used list.
        norm = normalize_app_id(app_id)
        order = [a for a in self.settings_store.get("mru_order") if a != norm]
        order.insert(0, norm)
        self.settings_store.set("mru_order", order)

    def _draw_bg_overlay(self, area, cr, width, height):
        # Saturation: cross-fade a greyscale copy over the color image.
        if self._bg_saturation < 1.0 and self._bg_grey_pixbuf is not None:
            cr.save()
            cr.scale(
                width / GdkPixbuf.Pixbuf.get_width(self._bg_grey_pixbuf),
                height / GdkPixbuf.Pixbuf.get_height(self._bg_grey_pixbuf),
            )
            Gdk.cairo_set_source_pixbuf(cr, self._bg_grey_pixbuf, 0, 0)
            cr.paint_with_alpha(1.0 - self._bg_saturation)
            cr.restore()
        # Vignette: radial gradient, transparent at center, dark at edges.
        if self._bg_vignette > 0:
            cx, cy = width / 2, height / 2
            r = max(cx, cy)
            gradient = cairo.RadialGradient(cx, cy, r * 0.25, cx, cy, r)
            gradient.add_color_stop_rgba(0, 0, 0, 0, 0)
            gradient.add_color_stop_rgba(1, 0, 0, 0, self._bg_vignette)
            cr.set_source(gradient)
            cr.paint()
        # Contrast: a flat mid-grey veil that mutes the wallpaper toward
        # grey so foreground labels/icons keep their footing.
        if self._bg_contrast > 0:
            cr.set_source_rgba(0.5, 0.5, 0.5, self._bg_contrast)
            cr.paint()
        # Brightness: push toward white (positive) or black (negative).
        b = self._bg_brightness
        if b > 0:
            cr.set_source_rgba(1, 1, 1, min(b, 1.0))
            cr.paint()
        elif b < 0:
            cr.set_source_rgba(0, 0, 0, min(-b, 1.0))
            cr.paint()

    def _build_grey_pixbuf(self, path):
        if path:
            pixbuf = GdkPixbuf.Pixbuf.new_from_file(path)
            grey = GdkPixbuf.Pixbuf.new(
                GdkPixbuf.Pixbuf.get_colorspace(pixbuf),
                GdkPixbuf.Pixbuf.get_has_alpha(pixbuf),
                GdkPixbuf.Pixbuf.get_bits_per_sample(pixbuf),
                GdkPixbuf.Pixbuf.get_width(pixbuf),
                GdkPixbuf.Pixbuf.get_height(pixbuf),
            )
            pixbuf.saturate_and_pixelate(grey, 0.0, False)
            return grey
        return None

    def set_background(self, path):
        if path:
            self._background_picture.set_filename(path)
            self._bg_grey_pixbuf = self._build_grey_pixbuf(path)
        else:
            self._background_picture.set_filename(None)
            self._bg_grey_pixbuf = None

    def set_bg_brightness(self, value):
        self._bg_brightness = float(value)
        self._bg_overlay.queue_draw()

    def set_bg_contrast(self, value):
        self._bg_contrast = float(value)
        self._bg_overlay.queue_draw()

    def set_bg_saturation(self, value):
        self._bg_saturation = float(value)
        self._bg_overlay.queue_draw()

    def set_bg_vignette(self, value):
        self._bg_vignette = float(value)
        self._bg_overlay.queue_draw()

    def _on_toplevel_open(self, wayland_app_id, title):
        if normalize_app_id(wayland_app_id) == _SHELL_APP_ID:
            # The shell's own window — see _SHELL_APP_ID's comment. Never
            # tracked, never shown as a running app in its own Frame.
            return
        # A window opened for an app we did not launch (or a second window):
        # record it open so its icon lights up everywhere.
        norm_id = normalize_app_id(wayland_app_id)
        if not norm_id:
            return
        self._toplevel_refcounts[norm_id] = self._toplevel_refcounts.get(norm_id, 0) + 1
        app_state.add_open(wayland_app_id)
        # window-observation spec's "external window is tracked": show a
        # real Frame entry for apps opened outside the shell too, not
        # just icon state. Resolve lazily here (not eagerly for every
        # installed app) since this only matters for apps that actually
        # open a window; skip if we already have a bundle (shell-launched
        # apps keep using the richer one from _on_app_launched).
        if norm_id not in self._launched_bundles:
            bundle = DesktopBundle.from_wm_class(wayland_app_id)
            if bundle is not None:
                self._launched_bundles[norm_id] = bundle

    def _on_toplevel_close(self, wayland_app_id, title):
        if normalize_app_id(wayland_app_id) == _SHELL_APP_ID:
            return
        norm_id = normalize_app_id(wayland_app_id)
        if not norm_id:
            return
        # Decrement the window refcount for this app. Only remove from
        # app_state when its *last* window closes — an app may have
        # multiple windows (especially in hosted/GNOME mode, where the
        # extension reports per-window events).
        if self._toplevel_refcounts.get(norm_id, 0) > 0:
            self._toplevel_refcounts[norm_id] -= 1
        if self._toplevel_refcounts.get(norm_id, 0) > 0:
            return
        # The availability guard only applies to the standalone adapter
        # (toplevel_tracker): the protocol may be unavailable on a given
        # compositor, in which case its close events are unreliable and
        # the pid-watch fallback (desktop_bundle.py) should be the only
        # source of truth. The hosted adapter (gnome_window_source) has no
        # such availability gate — a bug here previously made this whole
        # method a no-op in hosted mode (self.toplevel_tracker is always
        # None there), silently dropping every WindowClosed event from the
        # GNOME Shell extension and leaving closed apps' icons stuck "open".
        if self.toplevel_tracker is not None:
            if self.toplevel_tracker.available is not True:
                return
            # Only drop the app once its *last* window is gone.
            if self._has_open_toplevel(wayland_app_id):
                return
        app_state.remove_open(wayland_app_id)

    def _on_toplevel_focus(self, wayland_app_id):
        # Fired only where the compositor exposes the `activated` state;
        # otherwise focus stays None and views degrade to two states.
        # wayland_app_id is None when focus left every tracked toplevel —
        # that's a real, meaningful state and must pass through; only the
        # shell's own id (see _SHELL_APP_ID) is filtered.
        if wayland_app_id is not None and normalize_app_id(wayland_app_id) == _SHELL_APP_ID:
            return
        app_state.set_focused(wayland_app_id)

    def _has_open_toplevel(self, wayland_app_id):
        return any(
            state.get("app_id") == wayland_app_id
            for state in self.toplevel_tracker._toplevels.values()
        )

    def _on_frame_running_activated(self, bundle):
        return self._focus_window(bundle)

    def _focus_window(self, bundle):
        # Ask whichever window-observation adapter is active to focus the
        # window natively on the host or session compositor (window-
        # observation spec: "Activating a running entry focuses the
        # window"). Neither adapter owns placement — this only requests
        # activation, same as clicking a taskbar entry would.
        #
        # bundle.app_id may end in ".desktop" (desktop-file id), but the
        # compositor/adapter compares against WM_CLASS / Wayland app_id
        # values that omit the suffix. Normalize so the two match.
        normalized = normalize_app_id(bundle.app_id)
        if self.gnome_window_source is not None:
            return self.gnome_window_source.focus_window(normalized)
        if self.toplevel_tracker is not None:
            return self.toplevel_tracker.focus(normalized)
        return False

    def _activate_app(self, bundle):
        # Clicking an app icon (pie menu / grid) focuses the existing
        # window if the app is already open, and launches otherwise —
        # matching what the Frame's running list already does. Post-launch
        # bookkeeping stays in _on_app_launched, called only on a launch.
        if app_state.is_open(bundle.app_id):
            self._focus_window(bundle)
            return
        bundle.launch()
        self._on_app_launched(bundle)

    def _on_app_process_closed(self, app_id):
        # Always remove from app_state when the process exits — the
        # toplevel tracker augments this with windows opened outside the
        # shell, but it does not replace the shell's own process tracking.
        app_state.remove_open(app_id)
        self._launched_bundles.pop(normalize_app_id(app_id), None)

    def _sync_frame_running(self):
        """Render the Frame's running list from the shared registry.

        Adds a Frame item for each open app we have a bundle for and are
        not already showing; removes items whose app is no longer open.
        _launched_bundles holds both shell-launched apps (from
        _on_app_launched) and externally-opened ones resolved lazily in
        _on_toplevel_open (window-observation spec: "external window is
        tracked") — an app with no installed .desktop entry has no bundle
        and is tracked in the registry for icon state only, not shown as
        a Frame item (nothing to render a name/icon from).
        """
        open_ids = app_state.open_app_ids
        for norm_id, bundle in self._launched_bundles.items():
            if norm_id in open_ids:
                self.frame.add_running(bundle)
            else:
                self.frame.remove_running(bundle.app_id)


def main():
    app = SugarShell()
    return app.run(sys.argv)


if __name__ == "__main__":
    main()
