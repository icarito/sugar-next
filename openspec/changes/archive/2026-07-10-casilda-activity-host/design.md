# Design: casilda-activity-host

## Pivot note

This change originally proposed embedding a Casilda compositor widget so
Sugar Next would own placement/stacking/lifecycle of every activity it
launches, identically in a GNOME-hosted window and a future standalone
session. That approach was spiked (see below) and rejected during design
exploration — before any of it merged to `main` — in favor of a much
smaller change: Sugar Next stays a normal Wayland client in both modes and
gets two adapters for *observing* window state instead of one mechanism
for *owning* it. The name `casilda-activity-host` is kept for continuity
(all planning artifacts and history reference it); a rename is cosmetic
and can happen at archive time if useful.

### What the Casilda spike found

- `casilda_compositor_new()`'s `socket` argument is documented nullable in
  the C header but not annotated `(nullable)` in the generated GIR, so
  `Casilda.Compositor.new(None)` raises `TypeError` from Python — a private
  anonymous compositor (the common case for a per-activity page) isn't
  reachable from GI without a named socket workaround or an upstream fix.
- No GI-visible signal for toplevel mapped/unmapped (`g_signal_list_names`
  returns empty on `CasildaCompositorClass`); lifecycle would need a
  `spawn_async` + `GLib.child_watch_add` child-exit fallback, which *was*
  verified working (spawn a real client, kill it, watch fires) — but that
  only tracks process exit, not window close (loses the "dialog closes,
  activity's main window stays" distinction Casilda's own C code models
  internally via `toplevels` list per surface).
- Casilda's own source states it has "no workspace or stacking concept" —
  it centers/overlaps clients in one scene with no tiling model. It cannot
  deliver the tiling standalone-session behavior this design now targets;
  a per-activity-widget-in-a-Gtk.Stack scheme (the original D1) sidesteps
  tiling by only ever showing one activity at a time, which conflicts with
  wanting real tiled windows in standalone mode.
- Fundamentally: embedding solves "the shell needs native window data it
  otherwise can't get." But the shell *can* get that data non-natively in
  both target environments (GNOME Shell extension; wlr-foreign-toplevel in
  a wlroots session) without taking on compositor ownership, GTK-on-GTK
  input quirks, or a wlroots build dependency.

## Context

Sugar Next is a `Gtk.Application` with one window. Apps launch via
`Gio.AppInfo.launch()`. The shell has always needed a way to know when a
launched app's window closes (to update the Frame), and ideally to know
about windows it didn't launch (a terminal-opened app, anything a
collaboration feature surfaces). Two mechanisms already exist for pieces of
this:

- `desktop_bundle.py` watches the launch PID via `GLib.child_watch_add`.
  DBusActivatable apps (~14% of desktop files, including GNOME core apps)
  report `pid=0` and are never tracked this way.
- `toplevel_tracker.py` speaks `zwlr_foreign_toplevel_management_unstable_v1`
  over a vendored pywayland binding. This protocol is wlroots-specific;
  Mutter deliberately does not implement it, so under GNOME — the primary
  dev environment — this tracker is silently inert.
- `hyprland_ipc.py` polls `hyprctl -j clients` every 500 ms, working only
  inside a Hyprland session (the now-removed nested-Hyprland dev mode).

None of these cover "real window data while developing inside GNOME",
which is the environment this project is actually developed in day to day.

## Goals / Non-Goals

**Goals:**

- Reliable window open/close/focus tracking for *all* windows relevant to
  the shell — launched by Sugar Next or not — in both supported startup
  modes.
- The GNOME-hosted mode is a first-class dev/verification environment: it
  must exercise the Frame's real window-management logic (running list,
  focus-follow) against live data, not a stub.
- One internal event contract (`on_window_open/close/focus`) that the
  Frame and lifecycle hooks consume, regardless of which adapter is
  active underneath.
- Exactly two startup modes, no nested-compositor indirection for dev
  iteration.
- Standalone mode supports real window tiling via the session compositor
  — Sugar Next does not own layout in either mode.
- `bootstrap.sh` leaves whichever mode is detected fully ready — installing
  the GNOME Shell extension when GNOME is present, with no manual step.

**Non-Goals:**

- Owning window placement, stacking, or compositing in any mode (this is
  the point of the pivot away from Casilda).
- Standalone session *packaging* (kiosk display-manager entry, distro
  integration) — a separate future change.
- X11 support beyond "launch still works, no window tracking" — documented
  fallback, not a design target.
- Supporting arbitrary standalone compositors — Wayfire is the one verified
  target; other wlroots compositors likely work via the same protocol but
  are untested by this change (river was tried and is currently unusable
  standalone without a packaged `river-window-management-v1` WM — see D3).
- Real-time collaboration or Zeitgeist-backed analysis features — this
  change wires the data sources (window events, D-Bus surface) that such
  features would consume later; it does not build them.

## Decisions

### D1. Two adapters, one internal event contract

`main.py` selects an adapter at startup by probing the compositor
directly: a throwaway Wayland connection checks whether
`zwlr_foreign_toplevel_manager_v1` is advertised (~30ms, one roundtrip) —
present → standalone; absent → hosted. This replaced an earlier
`XDG_CURRENT_DESKTOP`-based heuristic, rejected after it gave a false
"GNOME" reading live: the variable is inherited across the process chain
from wherever the shell was launched (e.g. a GNOME terminal), not from
which compositor is actually serving the current Wayland socket, so a
shell launched into a nested Wayfire session from a GNOME terminal
detected itself as hosted and skipped the standalone adapter entirely.
Probing the protocol directly has no such inheritance problem — it asks
the compositor actually being connected to. Both adapters call the
same three methods on `app_state` (already the shell's single source of
truth for open apps — see `frame-views` spec): `add_open`, `remove_open`,
`set_focused`. The Frame, hooks, and every consumer of `app_state` are
unchanged by which adapter is active.

- *Why not unify into one mechanism, as the original D7 required?* The
  fork is already physical: GNOME and a standalone wlroots session are
  different processes with different capabilities. Forcing one mechanism
  meant either building a GNOME Shell extension AND running it identically
  in standalone (impossible — no GNOME Shell there), or building a wlroots
  compositor client and hoping GNOME would run it (impossible — Mutter
  refuses the protocol). Embedding (Casilda) was the only way to truly
  unify, and D5 below explains why that cost isn't worth it. Two adapters
  behind one contract gets the same simplicity where it matters (the
  Frame's code) without the compositor-ownership cost.

### D2. Hosted mode: GNOME Shell extension over D-Bus

A GNOME Shell extension (`extensions/gnome-shell/sugar-next-windows@sugarlabs.org/`)
watches `global.get_window_actors()` for map/unmap and
`global.display.focus-window` for focus changes, and exposes them on a
session-bus interface (e.g. `org.sugarlabs.SugarNext.WindowSource`) with
signals `WindowOpened(app_id, title)`, `WindowClosed(app_id)`,
`WindowFocused(app_id)`. `sugar_next/shell/gnome_window_source.py` is a
thin `Gio.DBusProxy` client that subscribes to these signals and calls into
`app_state`.

- *Why an extension and not polling `wmctrl`/`xdotool`-equivalents*: those
  don't exist for Wayland/Mutter; GNOME Shell extensions are the
  documented, supported way to read Mutter's compositor state from
  outside GNOME Shell itself.
- *Why this counts as a dev tool, not just a runtime dependency*: it is
  the only way to exercise Sugar Next's window-management code (Frame
  running-list rendering, focus-follow, close-triggered hook firing)
  against real desktop windows without standing up a nested compositor.
  Every dev iterating inside GNOME gets this for free once `bootstrap.sh`
  installs it.
- *Cost*: GNOME Shell extension APIs are not guaranteed stable across GNOME
  versions; `bootstrap.sh` should pin/document a tested GNOME version range
  and fail loudly (environment friction is a bug, workspace standard) if
  the extension fails to load.
- Focus-follow (`_on_frame_running_activated` in `main.py`) calls a method
  on the same D-Bus interface (e.g. `FocusWindow(app_id)`) that asks Mutter
  to activate the window — bidirectional, not just event consumption.

### D3. Standalone mode: keep `toplevel_tracker.py` as-is

`toplevel_tracker.py` and `_wayland_wlr/` are **not deleted** (reversing
the original proposal's D5). They were dead code under GNOME, but they are
exactly the right client for `wlr-foreign-toplevel-management` on a
wlroots-based standalone session compositor. **Wayfire** is the recommended
reference compositor: wlroots-based (implements the protocol), ships a
complete window manager (tiling/floating plugins configurable), and is
already used elsewhere in this workspace for GTK4-port verification (see
`specbook/docs/gtk-porting-standards.md`).

- *Why Wayfire, not river*: river was the original choice for its minimal,
  externally-scriptable design (`riverctl` / `rivertile`) — but river 0.4.x
  (the version packaged today, `extra/river` 0.4.5) rewrote its
  architecture to separate compositor from window manager: it now requires
  an external process implementing `river-window-management-v1` to
  complete its toplevel lifecycle at all. Live verification (see tasks.md
  3.3) confirmed river advertises `zwlr_foreign_toplevel_manager_v1`
  correctly and `TopLevelTracker` connects successfully, but **without a
  compatible WM, river never completes its "manage sequence"** — no
  toplevel ever gets configured or reported over the foreign-toplevel
  protocol, and windows render unconfigured (no size). No packaged WM for
  the new protocol was available to install (the reference layout
  generator, `rivercarro` on AUR, failed to build). Wayfire has no such
  gap — a full `OPEN → FOCUS → CLOSE` cycle plus `activate(seat)`-based
  focus-follow were verified working end-to-end against it. River may
  become viable again once a WM for `river-window-management-v1` is
  packaged; revisit then.
- `session/hyprland.lua` is replaced with `session/wayfire.ini`: autostart
  Sugar Next, traditional floating placement (not tiled) for other
  windows — no automatic tiling plugin. Revised from an earlier version of
  this design that assumed forced tiling for everything.
- **Session-owner exception**: as the session owner in standalone mode,
  Sugar Next *does* manage what it reasonably can about its own
  presentation — it calls GTK4's `Gtk.Window.fullscreen()` on itself,
  after `present()`, at startup — like the old Hyprland template's
  fullscreen window-rule did. This does not contradict "Sugar Next does
  not own window placement" (the goal is about *other* windows — apps the
  learner launches, which stay ordinary floating windows placed by
  Wayfire); it only concerns how the shell presents *itself* when it is
  the thing that owns the session. In hosted mode no equivalent call is
  made — Sugar Next is a guest inside GNOME and does not ask for special
  treatment.
  - *Why in-app, not a Wayfire `window-rules` entry*: tried first, and a
    `on created if app_id is "org.sugarlabs.SugarNext" then maximize`
    rule (the closest available — `window-rules`' action DSL has no
    `fullscreen` verb at all, only `maximize`/`minimize`/`sticky`/
    `always-on-top`, confirmed against `libwindow-rules.so`) *did* apply
    without error, and did maximize the window — but rendered it as flat
    grey with no application content. This matches known upstream Wayfire
    issues (#957, #1094): `window-rules`' only lifecycle event,
    `created`, fires before the client's first paint, and requesting a
    size change that early races GTK4's configure/commit handshake
    (Wayfire's incomplete `gtk_shell` v3 implementation doesn't send
    `configure_edges`, which GTK4 depends on more than GTK3 did). No
    Wayfire-native hook exists later than `created` (confirmed against
    the upstream wiki) — window-rules cannot avoid this race by
    configuration alone.
  - `Gtk.Window.fullscreen()` sidesteps the render race by construction
    (called after `present()`, once the window is already mapped and has
    painted) — but calling it *before* `present()` hit a second, distinct
    bug: it made a nested Wayfire dev session try to renegotiate the
    output to a custom mode and fail (`Couldn't find matching mode
    1280x720@0 ... disabling output`, wlroots 0.19's nested Wayland
    backend), tearing down the whole nested session. Both issues needed
    fixing — event ordering (which race) and call ordering relative to
    `present()` (which failure mode) are independent axes.
- Focus-follow in standalone mode uses
  `ZwlrForeignToplevelHandleV1.activate(seat)` — part of the
  foreign-toplevel protocol itself, verified against Wayfire (no
  Wayfire-specific IPC needed).

### D4. No embedding; `Gio.AppInfo.launch()` unchanged

The original proposal's D3 (exec `Exec=` directly via a compositor's
`spawn_async` to avoid D-Bus activation escaping to the host) is dropped.
There is no "host" to escape to avoid — the host *is* the destination in
both modes now. `Gio.AppInfo.launch()` remains the one launch path; its
existing `pid`-based close-watch in `desktop_bundle.py` becomes a fallback
that mostly stops mattering once an adapter is active (the adapter's
window-close signal fires `on_app_close` reliably, including for
DBusActivatable apps where the pid-watch never could).

- *Migration*: keep the pid-watch as a defensive fallback for the narrow
  window before an adapter's first event, or if an adapter is unavailable
  (X11 fallback, extension not installed) — but it is no longer the
  primary mechanism, and its documented DBusActivatable gap is now covered
  by D2.

### D5. Why Casilda is out of scope entirely (not "deferred")

Recorded for anyone revisiting this: Casilda was not rejected for being
hard to build, but because it solves a problem this design no longer has.
Once Sugar Next accepts that it does not own window placement in either
mode (D-goals above), there is nothing left for an embedding compositor to
do — GNOME already places windows; Wayfire already tiles them. Re-opening
Casilda only makes sense if a future change wants Sugar Next to own
layout again (e.g. reintroducing a fullscreen one-activity-at-a-time model)
— at which point re-read the spike findings above before re-adopting it.

### D6. External windows get real Frame entries, not just icon state

Both adapters already reported every window, not just shell-launched
ones (`app_state.add_open`/`remove_open` never distinguished the source —
D1's "one internal event contract" made this automatic). The Frame,
however, only rendered entries for apps it had a `DesktopBundle` for,
which `_on_app_launched` only populated for shell-initiated launches — so
externally-opened windows updated icon state everywhere but never got a
Frame entry. This was inherited, unexamined, from the pre-this-change
Frame (its own docstring called it out as matching "prior behavior").

Closed the gap: `DesktopBundle.from_wm_class()` resolves a window's
`wm_class`/app id to an installed `.desktop` entry (direct
`Gio.DesktopAppInfo.new()` lookup first, falling back to a
`normalize_app_id`-matched scan of `iter_apps()` for casing/suffix
mismatches — the same normalization `app_state` already uses to key
windows). `_on_toplevel_open` in `main.py` calls this lazily, once per
newly-seen app id, and populates `_launched_bundles` with the result
alongside shell-launched bundles — the Frame's rendering code
(`_sync_frame_running`) needed no changes, since it already iterates
`_launched_bundles` without caring how an entry got there.

- *Why lazy, not eager*: resolving every installed app's `.desktop` entry
  upfront would be wasted work — most installed apps are never opened in
  a given session. Resolving on first-seen window open is O(1) extra
  lookups per actually-relevant app.
- *Why "no entry" instead of a placeholder for unresolvable windows*: a
  window with no installed `.desktop` file has no name or icon to render
  a meaningful Frame item from. `app_state` still tracks it (open/focus
  state used elsewhere), but the Frame silently omits it rather than
  showing an item with no identity.

## Risks / Trade-offs

- [GNOME Shell extension API stability across versions] → `bootstrap.sh`
  documents a tested version range and fails loudly with a clear message
  if the extension doesn't load, rather than silently degrading to
  pid-watch-only tracking.
- [Wayfire is less minimal than river's original design goal] → accepted:
  Wayfire's complete built-in WM is exactly what's missing from river
  0.4.x today. Document Wayfire as the *reference* target, not an
  exclusivity requirement — other wlroots compositors implementing the
  foreign-toplevel protocol likely work too, just unverified by this
  change. Revisit river once a `river-window-management-v1` WM is
  packaged (see D3).
- [Two adapters instead of one mechanism means two code paths to maintain]
  → mitigated by the shared `app_state` contract (D1): the Frame and hooks
  have exactly one code path; only adapter selection and the two small
  adapter modules differ.
- [Extension install is host-side friction, same category of risk flagged
  against the rejected GNOME-extension-for-production idea in the earlier
  explore session] → different here because it's explicitly a *dev-mode*
  install handled by `bootstrap.sh`, not a requirement for the shipped
  standalone session (which needs no GNOME anything).

## Migration Plan

1. Land the two adapters and the shared `app_state` contract; keep
   `desktop_bundle.py`'s pid-watch as fallback throughout (never a
   breaking removal).
2. Delete `hyprland_ipc.py`, `layer_shell.py`, and the nested dev runners
   in the same change, once the GNOME extension adapter is confirmed
   working end to end (no window with zero working tracking mechanism).
3. Replace `session/hyprland.lua` with the Wayfire config once the
   standalone adapter (existing `toplevel_tracker.py`, unmodified) is
   confirmed working against Wayfire specifically.
4. Docs updated in-change: `gtk-porting-standards.md` gains the
   Casilda-rejected note; HIG gains the two-mode description.
5. Rollback: the pid-watch fallback means reverting either adapter alone
   degrades functionality (DBusActivatable tracking, external-window
   visibility) without breaking the shell.

## Open Questions

- ~~Exact D-Bus interface shape for the GNOME Shell extension~~ — resolved:
  `org.sugarlabs.SugarNext.WindowSource` with `WindowOpened(app_id, title)`,
  `WindowClosed(app_id)`, `WindowFocused(app_id)` signals and a
  `FocusWindow(app_id) -> bool` method; live-verified.
- ~~Does `river-status-unstable-v1` or the foreign-toplevel protocol alone
  suffice for focus-follow~~ — resolved: the foreign-toplevel protocol's
  own `activate(seat)` request is sufficient, verified against Wayfire; no
  river-specific IPC needed (moot for river anyway per D3).
- ~~Minimum supported GNOME Shell version~~ — resolved: GNOME Shell 45+
  (ESM extension format requirement); live-tested against 50.3.
- **New**: is there a packaged, maintained window manager for river's
  `river-window-management-v1` protocol? None was found/installable during
  this change's verification (D3) — worth rechecking before recommending
  river again for anything.
