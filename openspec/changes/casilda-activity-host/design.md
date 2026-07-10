# Design: casilda-activity-host

## Context

Sugar Next is a `Gtk.Application` with one window. Apps launch via
`Gio.AppInfo.launch()` and their windows belong to the host desktop; the shell
observes them only indirectly:

- `desktop_bundle.py` watches the launch PID (`GLib.child_watch_add`), with a
  documented caveat that systemd reparents launched processes and the watch
  survives only via a `/proc`-polling fallback; DBusActivatable apps report
  `pid=0` and are never tracked.
- `toplevel_tracker.py` speaks `zwlr_foreign_toplevel_management_unstable_v1`
  over a vendored pywayland binding — a protocol Mutter deliberately does not
  implement, so it is dead code in the very environment used for development.

The `casilda-embedded-widget-demo` change (archived, validated 2026-07-08)
proved a Wayland client renders inside a `CasildaCompositor` widget, and
explicitly disclaimed shell-level hosting as unproven. Casilda (vendored at
`repos/casilda`, LGPL-2.1, wlroots 0.20, GTK 4.22) is a GTK4 widget that *is*
a compositor: it implements `xdg_shell`, spawns clients with
`WAYLAND_DISPLAY`/`WAYLAND_SOCKET`/`GDK_BACKEND` forced, imports buffers via
dmabuf, and exposes toplevels to the embedding process natively.

Constraint from the exploration that motivated this change: the same code must
behave identically when Sugar Next runs as a window inside GNOME (fast dev
iteration) and as a future standalone session. No GNOME-specific APIs, no
capability forks between the two tiers.

## Goals / Non-Goals

**Goals:**

- Launched apps render inside the shell window; Sugar Next owns their
  placement, stacking, and lifecycle.
- One launch pipeline and one lifecycle-tracking mechanism, identical in
  GNOME-hosted and standalone tiers.
- The Frame lists exactly the activities that have an open embedded window.
- External clients (Flatpak apps, a kid with a terminal) can join the shell by
  pointing `WAYLAND_DISPLAY` at a named socket.
- Delete the pid-watch and wlr-protocol workarounds.

**Non-Goals:**

- Standalone session packaging (kiosk compositor, `wayland-sessions` entry,
  logind wiring) — a separate future change.
- XWayland support (upstream Casilda work; X11-only apps use the escape
  hatch).
- Multi-seat/multi-user, window tiling, or any WM features beyond
  one-activity-at-a-time with switching.
- Migrating classic Sugar activities or the jarabe shell.

## Decisions

### D1. One `CasildaCompositor` widget per activity, in a `Gtk.Stack`

Each launched activity gets its own `CasildaCompositor` instance, added as a
page of a `Gtk.Stack` layered under the Frame overlay. Switching activities =
`stack.set_visible_child()`. Closing = removing the page.

- *Why not one shared compositor for all activities?* A single Casilda has no
  workspace or stacking concept — all clients composite into one scene
  (Casilda centers windows; overlapping toplevels would need real WM code in
  wlroots). Per-activity widgets turn window management into ordinary GTK
  widget navigation: zero wlroots WM code, and the Frame's "switch to
  activity" is a stack-page flip. Sugar's model is fullscreen
  one-activity-at-a-time anyway.
- *Cost*: one `wl_display` + socket per activity. Acceptable for the expected
  handful of concurrent activities; revisit if profiling says otherwise.
- Apps that open multiple toplevels (dialogs, secondary windows) stay
  contained in their own compositor page — a free isolation win.

### D2. Named socket for the *ambient* join path; per-activity sockets stay private

The shell exposes one well-known named socket (`sugar-next-<n>` in
`XDG_RUNTIME_DIR`, collision-scanned like Wayland's own `wayland-<n>`)
attached to an "ambient" compositor page for externally-joining clients —
Flatpak launches and manual `WAYLAND_DISPLAY=sugar-next-0 <app>` redirects.
Activities the shell spawns itself use their private per-activity compositor
(`casilda_compositor_new(NULL)` + `spawn_async`, which passes a connected fd
via `WAYLAND_SOCKET`).

- *Why*: private-fd spawning is hermetic and needs no socket-name bookkeeping,
  while the named socket preserves the low-floor property (redirect any app
  into the shell with one env var) and gives Flatpak a socket path it can
  bind. Each external toplevel arriving on the ambient socket is surfaced in
  the Frame like any activity.
- *Alternative rejected*: only a named socket shared by everything —
  simpler, but couples all spawns to one compositor page, contradicting D1.

### D3. Launch by exec'ing `Exec=`, not `Gio.AppInfo.launch()`

`DesktopBundle.launch()` parses the desktop file's `Exec=` line
(`Gio.DesktopAppInfo.get_commandline()`, field codes stripped per the Desktop
Entry spec) and passes the argv to `casilda_compositor_spawn_async()`.

- *Why*: `Gio.AppInfo.launch()` honors `DBusActivatable=true` (~14% of
  desktop files on a stock system, incl. GNOME core apps) by activating via
  the session bus — the app spawns with the *host* environment and its window
  escapes to the host compositor regardless of what env we set. The Desktop
  Entry spec requires `Exec=` even for DBusActivatable entries, so exec'ing it
  directly is always available and is exactly what `spawn_async` wraps.
- `on_app_launch` (veto) and `on_app_close` hooks keep firing at the same
  points; only the mechanism between them changes.

### D4. "Open outside" escape hatch keeps the old path

A secondary launch action (context menu on grid/pie items) uses the existing
`Gio.AppInfo.launch()` unchanged, handing the window to the host desktop.
Offered only in cooperative mode (detected by `WAYLAND_DISPLAY`/host session
present at startup); in a standalone session there is no "outside".
X11-only apps, and single-instance apps the user wants unified with an
already-running host instance, go through this hatch.

- Externally-launched windows are *not* tracked (that is what the deleted
  `toplevel_tracker.py` failed to do portably); the Frame simply doesn't list
  them. This is an accepted, documented limitation of the escape hatch.

### D5. Lifecycle from compositor events; delete the workarounds

The per-activity compositor reports its toplevels to the embedding process
(wlroots `xdg_shell.events.new_toplevel` / destroy, surfaced through Casilda).
An activity is "running" while its compositor page has ≥1 mapped toplevel;
when the last toplevel closes, the shell fires `on_app_close`, removes the
Frame entry, and disposes the stack page. `desktop_bundle.py`'s pid-watch,
`toplevel_tracker.py`, the vendored `_wayland_wlr/` bindings, and the optional
`pywayland` dependency are all deleted.

- *Note*: if Casilda's public GI API does not yet expose toplevel
  mapped/closed signals, the fallback is child-pid exit from `spawn_async`
  (a real fork+exec child this time — no systemd reparenting, no pid=0), and
  a small upstream Casilda contribution adds the signal. Verify first (see
  Open Questions).

### D6. Casilda acquired from `repos/casilda` via Meson; documented, not automated away

Bootstrap docs gain a "build Casilda" section (`meson setup` +
`ninja install` to `~/.local`, `GI_TYPELIB_PATH`/`LD_LIBRARY_PATH` notes).
`bootstrap.sh` checks for the `Casilda` typelib and prints the doc pointer if
missing — environment friction is a bug (workspace standard), so the check
must fail loudly and helpfully, but this change does not take on packaging.

## Risks / Trade-offs

- [No XWayland in Casilda] → X11-only apps cannot embed. Mitigation: escape
  hatch (D4) + document; upstream XWayland support is future work.
- [Nested rendering cost — every activity's buffers composite through the
  GTK scene graph] → dmabuf import (Casilda ≥1.4) keeps it GPU-side; test on
  weak hardware early (task), keep the demo recording skill as a smoke test.
- [Single-instance apps (e.g. Firefox with a running host instance) may IPC
  to the host instance and open there despite the embedded spawn] → detect
  nothing; document, and offer the escape hatch. Per-app instance flags
  (e.g. `--new-instance`) can come later as extension-provided launch
  overrides.
- [Flatpak + named socket unverified — `--socket=wayland` binds the socket
  named by `WAYLAND_DISPLAY`, believed to work with a custom name in
  `XDG_RUNTIME_DIR`] → spike task before building the Flatpak-facing docs;
  if it fails, fallback is `flatpak run --env=WAYLAND_DISPLAY=… --filesystem=xdg-run/sugar-next-0`.
- [Casilda is a small single-maintainer upstream] → LGPL, vendored, active
  (1.4.0, 2026-05); budget for upstream contributions (toplevel signals,
  XWayland) rather than forking.
- [GTK-on-GTK input quirks (focus, IM, shortcuts crossing the compositor
  boundary)] → the embedded-widget demo already exercised basic input; add a
  keyboard-focus scenario to verification tasks.
- [Per-activity compositors multiply wl_displays] → fine at classroom scale
  (≤ ~10 concurrent); profile before optimizing.

## Migration Plan

1. Land the launch-path change behind the existing UI (grid/pie click =
   embedded launch; context-menu = open outside). No config flag: the
   behavior change *is* the feature, and the escape hatch is the rollback for
   any individual app.
2. Delete `toplevel_tracker.py` / `_wayland_wlr/` in the same change as the
   compositor-event tracking lands, so there is never a window with two
   tracking mechanisms.
3. Docs updated in-change: `gtk-porting-standards.md` boundary note replaced
   with the validated result; HIG XDG list gains the socket contract.
4. Rollback: revert the change; the old `Gio.AppInfo.launch()` path is
   preserved as the escape hatch, so a revert is a small diff.

## Open Questions

- Does Casilda's GI API expose per-toplevel mapped/closed signals today, or
  only render them? Determines whether D5 needs an upstream patch first
  (spike task at the top of tasks.md).
- Socket naming: is one ambient socket enough, or should each external
  Flatpak launch get its own compositor page for D1 symmetry? Start with one
  ambient page; split later if external clients overlap confusingly.
- How does the Frame represent an embedded activity's *title* (per-toplevel
  `xdg_toplevel.title` vs. the desktop entry name)? Default to desktop entry
  name; revisit when multi-window apps arrive.
