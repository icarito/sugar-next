# Proposal: casilda-activity-host

> **Note:** this change no longer uses Casilda. It kept its original name
> across a design pivot (see design.md "Pivot" note) rather than fork a new
> change mid-exploration; a future rename is cosmetic only.

## Why

Sugar Next currently launches apps as sibling windows on the host desktop,
and can only reliably track the ones it launched itself: `desktop_bundle.py`
watches the launch PID, which fails for `DBusActivatable` apps (pid=0,
~14% of desktop files), and the shell has no way to know about windows it
didn't spawn. Two prior workarounds chased this from different angles —
`toplevel_tracker.py` speaks `wlr-foreign-toplevel-management`, a protocol
Mutter deliberately does not implement, so it is dead code under GNOME (the
primary dev environment); `hyprland_ipc.py` polls `hyprctl` every 500 ms, a
Hyprland-specific IPC that only exists for the (now-removed) nested-Hyprland
dev mode.

An embedded-compositor approach (Casilda) was explored and prototyped: make
Sugar Next own a `CasildaCompositor` widget and render launched apps inside
it, so it always has native toplevel data. This was rejected after spiking
it (see design.md "Pivot"): Casilda has no tiling/stacking model of its own
(a plain widget, not a session compositor), its GI bindings have real gaps
(`Compositor.new(NULL)` isn't marked nullable, no toplevel-mapped/unmapped
signals — only a `spawn_async` + child-exit fallback verified to work), and
— the decisive point — **it solves a problem Sugar Next doesn't have**.
Sugar Next doesn't need to *own* window placement in either environment: in
GNOME, Mutter already places windows; in a standalone tiling session, the
session compositor already does. Sugar Next's job is to *observe* windows
and act as a launcher with metadata, analysis, and (future) collaboration
features on top — Zeitgeist, D-Bus, and the compositor's own status
protocol are data sources, not something to replace.

This change deletes the pid-watch and the Hyprland IPC poller, and gives
Sugar Next exactly two window-observation adapters — one per supported
startup mode — feeding one internal event contract.

## What Changes

- **Two startup modes only**: hosted (windowed app inside GNOME, the
  primary dev/launcher environment) and standalone (a dedicated Wayland
  session, tiling, non-GNOME). No nested-compositor dev modes, no
  GNOME-in-a-window-in-Wayfire indirection.
- **Hosted mode**: a GNOME Shell extension (`extensions/gnome-shell/`,
  installed by `bootstrap.sh`) reads Mutter's window list
  (`global.get_window_actors()`) and exposes open/close/focus events over a
  session D-Bus interface. This is a **dev/verification tool as much as a
  runtime dependency** — it is how Sugar Next's window-management code (the
  Frame's running list, focus switching) gets exercised against real
  desktop data without a nested compositor. `Gio.AppInfo.launch()` stays
  the launch mechanism (unchanged); the extension only supplies lifecycle
  data the pid-watch cannot (DBusActivatable apps, windows opened outside
  Sugar Next).
- **Standalone mode**: keep and rely on the existing
  `toplevel_tracker.py` / `_wayland_wlr` `wlr-foreign-toplevel-management`
  client — it was dead code under GNOME but is exactly the right adapter
  for a wlroots-based standalone session compositor. Recommend **Wayfire**
  (wlroots, tiling, scriptable) as the reference standalone compositor;
  document it as the target, not a hard dependency of Sugar Next itself.
- **One internal contract**: both adapters feed the same
  `on_window_open(app_id) / on_window_close(app_id) / on_window_focus(app_id)`
  surface already implicit in `main.py`'s `app_state` registry. The Frame,
  lifecycle hooks, and focus-follow logic do not know or care which adapter
  is active.
- **Delete**: `hyprland_ipc.py` and its polling loop in `main.py`;
  `layer_shell.py` and `LD_PRELOAD` handling (no longer needed — Sugar Next
  is a plain toplevel client in both modes, never a background layer under
  sibling windows); the nested dev runners (`dev/run-wayfire.sh` +
  `wayfire.ini`, `dev/run-hyprland-nested.sh` + `dev/hyprland.lua`) and
  their `SUGAR_NEXT_*` env knobs; the Casilda runtime dependency explored
  during this change's design (never merged into `main`, so nothing to
  revert in shipped code).
- **Simplify** `session/hyprland.lua` → a Wayfire config (or equivalent):
  autostart Sugar Next, no bespoke tiling rules beyond what the compositor
  provides by default.
- **No embedding, no compositor ownership.** Sugar Next is a normal Wayland
  client in both modes. Activities launch as independent windows; the host
  or session compositor places and tiles them.

Out of scope: standalone session *packaging* (`wayland-sessions` desktop
entry, distro integration); a Sway/Hyprland/labwc adapter (Wayfire is the one
target for this change; the wlr-foreign-toplevel adapter is compositor
family-generic in principle but only verified against Wayfire); real-time
collaboration and Zeitgeist-backed analysis features themselves (this
change wires the data sources, not the features built on them); X11
support (documented as an unsupported fallback: `Gio.AppInfo.launch()`
still works, but no window lifecycle tracking without a Wayland
compositor).

## Capabilities

### New Capabilities

- `window-observation`: the shell tracks open/close/focus for windows it
  did and did not launch, via one of two adapters selected by startup mode
  (GNOME Shell extension in hosted mode, wlr-foreign-toplevel-management in
  standalone mode), feeding one internal event contract that the Frame and
  lifecycle hooks consume without knowing which adapter is active.
- `shell-startup`: exactly two supported startup modes (hosted window on
  GNOME; standalone Wayland session on a tiling wlroots compositor), no
  nested-compositor dev indirection, `bootstrap.sh` prepares whichever mode
  is detected.

### Modified Capabilities

- `frame-views`: the Frame's running-apps list changes at requirement level
  — entries reflect real window state from whichever adapter is active
  (not launch-PID heuristics), and activating a running entry asks the
  active adapter to focus that window (compositor-native focus, not a
  shell-owned page flip).

## Impact

- **Code**: `sugar_next/bundles/desktop_bundle.py` (drop the pid-watch,
  keep `Gio.AppInfo.launch()`), `sugar_next/shell/main.py` (adapter
  selection at startup, drop Hyprland-IPC and layer-shell wiring), new
  `sugar_next/shell/gnome_window_source.py` (D-Bus client for the
  extension); **deleted**: `sugar_next/shell/hyprland_ipc.py`,
  `sugar_next/shell/layer_shell.py`, `dev/run-wayfire.sh`,
  `dev/wayfire.ini`, `dev/run-hyprland-nested.sh`, `dev/hyprland.lua`;
  **kept as-is**: `sugar_next/shell/toplevel_tracker.py`,
  `sugar_next/_wayland_wlr/`; **new**: `extensions/gnome-shell/` (GJS
  extension + D-Bus service), `session/wayfire.ini` (or equivalent)
  replacing `session/hyprland.lua`.
- **Dependencies**: no new runtime dependency for `sugar_next` itself. The
  GNOME Shell extension is a dev-environment install (`bootstrap.sh`
  handles it when GNOME is detected). Standalone mode documents Wayfire as
  the reference compositor but does not vendor or require it at import
  time — `wlr-foreign-toplevel-management` is a protocol, not a library
  dependency, so `toplevel_tracker.py` degrades gracefully on compositors
  that lack it (already its documented behavior). Casilda is fully dropped
  — no `repos/casilda` build step in `bootstrap.sh`.
- **Behavior**: launching an app opens it as a normal window on whichever
  compositor is active (host or session); Sugar Next never embeds or
  repositions it. The Frame's running list becomes accurate for
  externally-opened windows too (previously invisible in hosted mode,
  since `toplevel_tracker.py` is inert under Mutter).
- **Docs**: `specbook/docs/gtk-porting-standards.md` gets a note that
  embedding (Casilda) was evaluated and rejected in favor of observation
  adapters, with the reasoning; HIG gains a description of the two startup
  modes and their data sources.
- **Extensions**: `on_app_launch`/`on_app_close` hook semantics are
  preserved; `on_app_close` now fires reliably for DBusActivatable apps
  under hosted mode (previously silent) via the GNOME Shell extension.
