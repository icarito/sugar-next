# Proposal: casilda-activity-host

## Why

Sugar Next currently launches apps as sibling windows on the host desktop, which
leaves it powerless as a shell: it cannot list windows it didn't spawn (Mutter
refuses `wlr-foreign-toplevel-management` by design), cannot place or manage
them, and had to grow two fragile workarounds — a pid-watch that polls `/proc`
(`desktop_bundle.py`) and a wlr protocol client that only works on wlroots
compositors (`toplevel_tracker.py`). Embedding a Casilda compositor makes Sugar
Next *the compositor for its own activities*: launched apps render inside the
shell window, identically whether Sugar Next runs as a GNOME-hosted app (dev
iteration) or as a future standalone session. This dissolves the
cooperative-vs-standalone fork without depending on any GNOME-specific or
host-compositor-specific API. The `casilda-embedded-widget-demo` change already
validated the toolchain; this is the shell-level step it explicitly left open.

## What Changes

- Add a runtime dependency on Casilda (`repos/casilda`, LGPL, wlroots-based
  GTK4 compositor widget) and embed one or more `CasildaCompositor` widgets in
  the shell window as the surface where launched apps render.
- Route app launches through Casilda: exec the desktop file's `Exec=` line via
  Casilda's spawn (with `WAYLAND_DISPLAY`/`GDK_BACKEND` forced), **not**
  `Gio.AppInfo.launch()` — DBusActivatable apps (~14% of desktop files) escape
  environment-based redirection via session-bus activation.
- Embed by default in both cooperative (GNOME-hosted) and standalone tiers; a
  per-launch "open outside" escape hatch uses the existing
  `Gio.AppInfo.launch()` path when a host desktop exists.
- Listen on a named Wayland socket in `XDG_RUNTIME_DIR` (e.g. `sugar-next-0`)
  so Flatpak apps can be pointed at it and users can redirect any app into
  Sugar Next from a terminal (low floor: the shell is hackable with one env
  var).
- Track activity lifecycle from Casilda's toplevel events. **Removes** the
  pid-watch close-tracking in `desktop_bundle.py` and the entire
  `toplevel_tracker.py` wlr-foreign-toplevel client (and its vendored
  `_wayland_wlr/` protocol bindings) — embedded windows are observed natively.
- The Frame's running list is fed by Casilda toplevel events; clicking a
  running entry brings that activity's surface to the front inside the shell.

Out of scope: standalone session packaging (cage/kiosk compositor +
`wayland-sessions` desktop entry) is a separate future change; XWayland
support in Casilda; migrating classic Sugar activities.

## Capabilities

### New Capabilities

- `activity-hosting`: launched apps render embedded inside the shell window
  via a Casilda compositor — launch routing (Exec-based spawn, embed by
  default, "open outside" escape hatch), the named Wayland socket contract,
  activity lifecycle tracking from compositor toplevel events, and switching
  between running embedded activities.

### Modified Capabilities

- `frame-views`: the Frame's running-apps list changes at requirement level —
  entries now reflect embedded activity windows (opened/closed via compositor
  events, not launch/pid heuristics), and activating a running entry switches
  to that embedded activity instead of relying on the host desktop to raise
  the window.

## Impact

- **Code**: `sugar_next/bundles/desktop_bundle.py` (launch path rewrite),
  `sugar_next/shell/main.py` (compositor widget(s) in the shell layout,
  activity switching), `sugar_next/shell/frame.py` (running list source);
  **deleted**: `sugar_next/shell/toplevel_tracker.py`,
  `sugar_next/_wayland_wlr/`.
- **Dependencies**: adds Casilda (GI-importable, built from `repos/casilda`
  via Meson; not yet packaged by most distros — bootstrap/docs must cover
  building it). Drops the optional `pywayland` dependency.
- **Behavior**: launching an app from the Home View now opens it inside the
  Sugar Next window (classic-Sugar feel) instead of as a separate host window.
  X11-only apps cannot embed (no XWayland in Casilda) and must fall back to
  the escape-hatch path.
- **Docs**: `specbook/docs/gtk-porting-standards.md` boundary note (shell
  inside Casilda "unproven") gets updated by this change's results; HIG's
  XDG-compliance list gains the socket contract.
- **Extensions**: `on_app_launch`/`on_app_close` hook semantics are preserved;
  close events become reliable (window-based, not pid-based).
