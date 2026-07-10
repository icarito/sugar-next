# Tasks: casilda-activity-host

> See design.md "Pivot note" — this change no longer embeds Casilda. Tasks
> below implement two window-observation adapters instead.

## 1. Spikes (de-risk before building)

- [x] 1.1 Spike: minimal GNOME Shell extension that logs
      `global.get_window_actors()` map/unmap and focus-window changes to
      verify the data Sugar Next needs is reachable without deprecated API.
      **Live-verified** (after a real session restart, task 8.4): a
      throwaway spike extension (since removed) confirmed `window-created`,
      per-window `unmanaged`, and
      `notify::focus-window` all fire with real data. Also surfaced that
      `window-created` fires *before* `wm_class`/title populate — carried
      into the real extension's design (see 8.4)
- [x] 1.2 Spike: expose that data over a session D-Bus interface from the
      extension; confirm a Python `Gio.DBusProxy` client in a throwaway
      script receives signals live. **Live-verified** via `gdbus monitor`
      against the real `sugar-next-windows` extension and
      `gnome_window_source.py`'s `Gio.DBusProxy` client (task 8.4) — no
      throwaway script needed once the real extension existed
- [x] 1.3 Spike: confirm `river-status-unstable-v1` (or the
      foreign-toplevel protocol alone) is sufficient to focus a specific
      window from outside river; note which call `toplevel_tracker.py`
      needs for the focus-follow path. **Resolved without needing
      river-status**: the vendored `zwlr_foreign_toplevel_handle_v1`
      binding (`sugar_next/_wayland_wlr/.../zwlr_foreign_toplevel_handle_v1.py:114`)
      already exposes `activate(seat)`, part of the foreign-toplevel
      protocol itself (v1+, no river-specific extension needed) — river
      implements this protocol, so focus-follow needs no new binding, just
      wiring `TopLevelTracker` to call `handle.activate(seat)` and to keep
      a `WlSeat` reference. `river-status-unstable-v1` is unnecessary for
      this change's scope
- [x] 1.4 Verify minimum GNOME Shell version the extension needs to
      support. Local dev machine runs **GNOME Shell 50.3**; the ESM
      extension format (`import ... from 'resource:///...'`,
      `export default class extends Extension`) is required from GNOME 45
      onward (pre-45 used the old `imports.misc.extensionUtils` CommonJS
      style) — `metadata.json` targets `["45", "46", "47", "48", "49", "50"]`

## 2. GNOME Shell extension (hosted-mode adapter)

- [x] 2.1 Create `extensions/gnome-shell/sugar-next-windows@sugarlabs.org/`:
      `metadata.json`, `extension.js` watching window map/unmap/focus
- [x] 2.2 Expose `org.sugarlabs.SugarNext.WindowSource` on the session bus:
      signals `WindowOpened(app_id, title)`, `WindowClosed(app_id)`,
      `WindowFocused(app_id)`; method `FocusWindow(app_id) -> bool`
- [x] 2.3 Added `sugar_next/shell/gnome_window_source.py`: `Gio.DBusProxy`
      client wrapping the interface, calling into `app_state` on each
      signal (design D2). Live-verified against the real extension (8.4)
- [x] 2.4 Wired adapter selection in `main.py`, removing the old
      `HyprlandIPC`-based branch entirely. **Revised after live testing**:
      initially used `_is_gnome_session()` checking `XDG_CURRENT_DESKTOP`,
      which gave a false "GNOME" reading for a shell launched into a
      nested Wayfire session from a GNOME terminal — the variable is
      inherited across the process chain, not tied to which compositor is
      actually serving the Wayland connection. Replaced with
      `_standalone_protocol_available()`: a throwaway Wayland connection
      probing for `zwlr_foreign_toplevel_manager_v1` directly (~30ms, one
      roundtrip), computed once per activate and cached on
      `self._standalone_mode`. See design.md D1's updated rationale.

## 3. Standalone adapter (keep, wire, verify)

- [x] 3.1 ~~Confirm `toplevel_tracker.py` / `_wayland_wlr/` need no code
      changes~~ — needed one addition (see 3.2), not a rewrite. Wired as
      the standalone-mode branch on `self._standalone_mode` (see 2.4)
- [x] 3.2 Implement focus-follow for standalone mode using the call
      identified in spike 1.3. Added `TopLevelTracker._seat` (bound
      alongside the manager in the same registry roundtrip) and
      `TopLevelTracker.focus(app_id)` calling `handle.activate(seat)`;
      wired into `main.py`'s `_on_frame_running_activated`
- [x] 3.3 Verified the `wlr-foreign-toplevel-management` protocol and
      `TopLevelTracker.focus()` end to end against real compositors, with
      an important finding about river specifically:
      - **river 0.4.5** (installed via pacman, `extra/river`) is a recent
        rewrite that separated compositor from window manager: it
        advertises `zwlr_foreign_toplevel_manager_v1` v3 correctly
        (confirmed via `wayland-info`) and `TopLevelTracker.available` is
        `True` against it, but **without an external WM implementing
        `river-window-management-v1`, river never completes its toplevel
        "manage sequence"** (`0 tracked configure(s)` in its own debug
        log) — so no `WindowOpened`/`WindowClosed` events are ever sent
        over the foreign-toplevel protocol, and windows render with no
        configured size (the reported "black screen" symptom has the same
        root cause). No WM for the new protocol was installable in this
        session (`rivercarro`, the reference layout generator on AUR,
        failed to build/install here). This is an environment gap, not a
        bug in `toplevel_tracker.py` — the protocol binding and connection
        logic are confirmed correct.
      - **Wayfire 0.10.1** (already installed, ships its own complete WM)
        was used to close the loop: a standalone script driving
        `TopLevelTracker` directly against a nested Wayfire session
        observed the full `OPEN → FOCUS → CLOSE → FOCUS(None)` sequence
        for a real app (`gtk4-demo`), and `tracker.focus('org.gtk.Demo4')`
        returned `True` and correctly moved compositor focus away from a
        second app (`gnome-calculator`) — confirming both the tracking
        and the new `activate(seat)`-based focus-follow (3.2) work
        end-to-end against a real wlroots compositor.
      - **Design implication**: `design.md`'s "river as reference
        standalone compositor" and `session/river-init` (which assumes
        the old `riverctl`/`rivertile` API) are now stale for river's
        current 0.4.x line — a WM for `river-window-management-v1` would
        need to be built/packaged before river is actually usable
        standalone. Not fixed in this task (out of scope for verification);
        flagged for a follow-up design update.

## 3b. Frame shows externally-opened apps too

- [x] 3b.1 Added `DesktopBundle.from_wm_class()`
      (`sugar_next/bundles/desktop_bundle.py`): resolves a window's
      `wm_class`/app id to an installed `.desktop` entry — direct
      `Gio.DesktopAppInfo.new()` lookup, falling back to a
      `normalize_app_id`-matched scan of `iter_apps()`. Returns `None`
      when no desktop entry exists (design D6)
- [x] 3b.2 Wired into `main.py`'s `_on_toplevel_open`: resolves lazily on
      first-seen app id and populates `_launched_bundles`, so the Frame's
      existing rendering code (`_sync_frame_running`) shows externally-
      opened apps with real icon/name, no separate code path needed
      (window-observation spec: "External windows get a real Frame entry
      when resolvable")
- [x] 3b.3 Added tests (`tests/test_desktop_bundle.py`):
      `test_from_wm_class_direct_match`, `_normalized_match`,
      `_no_match_returns_none`. Also fixed a real bug found writing
      these: `Gio.DesktopAppInfo.new()` raises `TypeError` (not
      `None`-return) when no matching desktop file exists — a GI binding
      quirk around the C API's NULL return
- [x] 3b.4 Verified live: launched `gnome-calculator` outside the shell
      (pointed at the standalone session's Wayland socket, simulating the
      terminal-launch scenario) — appeared in the Frame with its real
      icon and name, confirmed by the user visually

## 4. Cleanup: delete what the pivot obsoletes

- [x] 4.1 Delete `sugar_next/shell/hyprland_ipc.py` (and its test) and its
      wiring in `main.py` (`_poll_hyprland_state`, `_hyprland_*` state,
      IPC-based `_on_frame_running_activated` now routes through the
      active adapter instead)
- [x] 4.2 Delete `sugar_next/shell/layer_shell.py` (and its test), its
      `main.py` calls, and `LD_PRELOAD` handling — Sugar Next is a plain
      toplevel client in both modes
- [x] 4.3 Delete `dev/run-wayfire.sh`, `dev/wayfire.ini`,
      `dev/run-hyprland-nested.sh`, `dev/hyprland.lua`, and their
      VS Code tasks/launch entries (also removed the now-orphaned
      "Build/Install Casilda" tasks.json entries)
- [x] 4.4 Confirmed: `grep -rl casilda sugar-next/` returns nothing. The
      earlier design spike's C-level prototyping happened only in
      `repos/casilda`, which was reverted before this apply session

## 5. Standalone session template

- [x] 5.1 Replaced `session/hyprland.lua` with `session/wayfire.ini` (see
      design.md D3 for the river → Wayfire switch): autostart Sugar Next,
      traditional floating placement for other windows (no forced
      tiling — reversed an earlier version of this task that assumed it)
- [x] 5.2 Documented Wayfire as the reference standalone compositor inline
      in `session/wayfire.ini`'s header comment (install-as-session-entry
      instructions); README section is task 8.3
- [x] 5.3 Shell self-presentation (design D3 "session-owner exception"):
      Sugar Next fullscreens itself in standalone mode via
      `Gtk.Window.fullscreen()` called after `present()` in `main.py`.
      Two real bugs found and fixed getting here — see design.md D3 for
      full detail: (1) a `window-rules`-based approach (`on created` +
      `maximize`, the closest DSL action to fullscreen) rendered the
      window flat grey with no content, a known Wayfire/GTK4 interaction
      (upstream issues #957, #1094 — `created` fires before first paint,
      racing GTK4's configure/commit handshake); (2) calling
      `fullscreen()` *before* `present()` crashed a nested Wayfire dev
      session's output entirely (custom-mode renegotiation rejected by
      wlroots 0.19's nested Wayland backend). Verified live: fullscreen,
      no visible titlebar/border (native Wayland/GTK4 clients aren't
      decorated by Wayfire's `[decoration]` plugin to begin with), full
      UI rendering correctly, in a real nested Wayfire session

## 6. bootstrap.sh

- [x] 6.1 Detect a GNOME session at bootstrap time (`XDG_CURRENT_DESKTOP`
      — reliable here specifically because `bootstrap.sh` runs directly in
      the user's own terminal, no nested-compositor process chain to be
      inherited across; contrast with 2.4's `main.py` runtime detection,
      which needed a protocol probe instead for exactly that reason);
      install/enable the `sugar-next-windows` extension automatically
- [x] 6.2 Fail loudly with an actionable message if the extension install
      or enable step fails (spec: shell-startup "Bootstrap failure is
      actionable") — covers both missing `gnome-extensions` and the
      known "GNOME Shell hasn't discovered the new extension yet, log out
      and back in" case
- [x] 6.3 When no GNOME session is detected, point to the standalone
      session template (`session/river-init`) instead of attempting the
      extension install

## 7. Launch path

- [x] 7.1 Confirmed `desktop_bundle.py`'s `Gio.AppInfo.launch()` path is
      unchanged (never touched by the Casilda spike). Updated
      `_watch_for_close`'s docstring to document it as the fallback now
      that an adapter is the primary close-tracking mechanism (design D4)

## 8. Docs + verification

- [x] 8.1 Updated `specbook/docs/gtk-porting-standards.md`: added a note
      under "Why Wayfire, not Casilda" cross-referencing this change's
      independent rejection of Casilda for the same underlying reason (no
      tiling/window-management model)
- [x] 8.2 Updated HIG with a new "Startup modes and window observation"
      section (two modes, their data sources) and refreshed the XDG
      compliance list's `wlr-foreign-toplevel-management` line
- [x] 8.3 Updated README: replaced Development Runners / Nested Wayfire /
      Nested Hyprland with a "Startup Modes" section describing the two
      supported modes; kept the container runner
- [x] 8.4 (hosted mode done; standalone/river still blocked — river not
      installed, see below) End-to-end verification against a **real
      GNOME session** surfaced and fixed two real bugs, both confirmed
      live via `gdbus monitor` on `org.sugarlabs.SugarNext.WindowSource`
      and a full `sugar_next.shell.main` run:
      1. **Extension bug**: `WindowOpened` always emitted `('', '')` —
         `window-created` fires before Mutter populates `wm_class`/title
         from the client. Fixed in `extension.js`'s `_emitOpenedWhenReady`
         with a 100ms-spaced retry (up to 2s) rather than depending on a
         specific Mutter notify/first-frame signal (neither fired
         reliably in live testing on GNOME Shell 50).
      2. **main.py bug**: `_on_toplevel_close`'s availability guard
         (`if self.toplevel_tracker is None: return`) was written for the
         standalone adapter only, but ran unconditionally — in hosted
         mode `self.toplevel_tracker` is always `None`, so the guard made
         the whole method a no-op and every `WindowClosed` event from the
         GNOME extension was silently dropped. This is exactly the "icon
         stays lit in the Frame after closing the app" symptom reported
         live. Fixed by scoping the guard to `toplevel_tracker is not
         None`, falling through to `app_state.remove_open()` unconditionally
         for the hosted-mode case.
      Verified via `gdbus monitor` (WindowOpened/WindowClosed carry real
      data end to end) and an isolated repro of the exact
      `_on_toplevel_open`/`_on_toplevel_close` call sequence. Full
      GNOME-hosted flow (launch → Frame entry → close → entry gone) is
      confirmed. **Standalone/river leg still blocked**: river is not
      installed on this machine (`pacman -S river` not run — requires
      explicit go-ahead). The throwaway spike extension has been removed
      (`gnome-extensions disable` + directory deleted) now that the real
      `sugar-next-windows@sugarlabs.org` extension is the verified one.
- [x] 8.5 Checked `record-sugar-next-demo` skill: no references to the
      removed nested-compositor runners or Casilda; no changes needed
