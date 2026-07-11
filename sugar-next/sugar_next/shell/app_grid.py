# Sugar Next - App Grid View
# Copyright 2025 Sebastian Silva, Pliaget
# SPDX-License-Identifier: GPL-2.0-or-later

import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gio, GLib, Pango, Gdk

from sugar_next.shell.icon_state import icon_with_state


class AppGrid(Gtk.ScrolledWindow):
    def __init__(self):
        super().__init__()

        self._box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.set_child(self._box)

        self.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.set_vexpand(True)

        self._gtk_settings = Gtk.Settings.get_default()

        style = self.get_style_context()
        # Dark background for icon grid
        css_provider = Gtk.CssProvider()
        css_provider.load_from_string('''
            .app-grid-scroll {
                background: @window_bg_color;
            }
            .app-grid-flowbox {
                padding: 24px;
            }
            .app-grid-cell {
                background: transparent;
                border: none;
                padding: 8px;
                border-radius: 8px;
                min-width: 100px;
                min-height: 100px;
            }
            .app-grid-cell:hover {
                background: alpha(@accent_bg_color, 0.15);
            }
            .app-grid-cell label {
                font-size: 11px;
                color: @window_fg_color;
            }
            .app-grid-cell image {
                transition: -gtk-icon-filter 150ms ease;
            }
            .app-grid-cell:hover image {
                -gtk-icon-filter: brightness(1.15) saturate(1.2);
            }
            .app-grid-search {
                margin: 12px;
                margin-bottom: 0;
                min-height: 36px;
                border-radius: 18px;
            }
        ''')
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        self._search_entry = Gtk.SearchEntry()
        self._search_entry.set_placeholder_text("Search applications...")
        self._search_entry.add_css_class("app-grid-search")
        self._search_entry.connect("search_changed", self._on_search_changed)
        self._search_entry.connect("activate", self._on_search_activate)
        self._box.append(self._search_entry)

        self._flowbox = Gtk.FlowBox()
        self._flowbox.set_max_children_per_line(8)
        self._flowbox.set_min_children_per_line(3)
        self._flowbox.set_selection_mode(Gtk.SelectionMode.NONE)
        self._flowbox.set_homogeneous(True)
        self._flowbox.set_activate_on_single_click(True)
        self._flowbox.add_css_class("app-grid-flowbox")
        self._flowbox.connect("child_activated", self._on_app_activated)
        self._box.append(self._flowbox)

        self._apps = []

    def populate(self, apps):
        self._apps = apps
        child = self._flowbox.get_first_child()
        while child:
            next_child = child.get_next_sibling()
            self._flowbox.remove(child)
            child = next_child

        for appinfo in apps:
            btn = Gtk.Button()
            btn.add_css_class("app-grid-cell")
            btn.set_has_frame(False)

            vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
            vbox.set_halign(Gtk.Align.CENTER)

            icon = icon_with_state(appinfo)
            icon.set_pixel_size(48)
            vbox.append(icon)

            label = Gtk.Label(label=appinfo.get_display_name())
            label.set_justify(Gtk.Justification.CENTER)
            label.set_lines(2)
            label.set_wrap(True)
            label.set_ellipsize(Pango.EllipsizeMode.END)
            vbox.append(label)

            btn.set_child(vbox)
            btn.set_appinfo(appinfo)
            self._flowbox.append(btn)

    def _on_search_changed(self, entry):
        """Filter flowbox children based on search text."""
        search_text = entry.get_text().lower().strip()
        child = self._flowbox.get_first_child()
        while child:
            btn = child
            if search_text:
                name = btn.get_appinfo().get_display_name().lower()
                btn.set_visible(search_text in name)
            else:
                btn.set_visible(True)
            child = child.get_next_sibling()

    def _on_search_activate(self, entry):
        """Launch the first visible app on Enter."""
        search_text = entry.get_text().lower().strip()
        if not search_text:
            return
        child = self._flowbox.get_first_child()
        while child:
            if child.get_visible():
                appinfo = child.get_appinfo()
                if appinfo:
                    try:
                        ctx = GLib.AppLaunchContext()
                        Gio.AppInfo.launch_default_for_uri(
                            appinfo.get_id(), ctx
                        )
                    except Exception as e:
                        print(f"Error launching app: {e}")
                break
            child = child.get_next_sibling()

    def _on_app_activated(self, flowbox, child):
        appinfo = child.get_appinfo()
        if appinfo:
            try:
                ctx = GLib.AppLaunchContext()
                Gio.AppInfo.launch_default_for_uri(
                    appinfo.get_id(), ctx
                )
            except Exception as e:
                print(f"Error launching app: {e}")

    def focus_search(self):
        self._search_entry.grab_focus()
