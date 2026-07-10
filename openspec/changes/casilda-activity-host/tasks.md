# Tasks: casilda-activity-host

## 1. Spikes (de-risk before building)

- [ ] 1.1 Verify Casilda's GI API exposes toplevel mapped/closed information
      to the embedding process (design D5); if not, prototype the
      `spawn_async` child-exit fallback and file/draft the upstream Casilda
      signal patch
- [ ] 1.2 Spike: spawn a real app (e.g. gtk4-demo, then a browser) into a
      `CasildaCompositor` from Python/GI inside the Sugar Next window; note
      input focus, keyboard shortcuts, and rendering behavior
- [ ] 1.3 Spike: point a Flatpak app at a custom-named socket in
      `XDG_RUNTIME_DIR` (`WAYLAND_DISPLAY=sugar-next-0`); record whether
      `--socket=wayland` suffices or `--filesystem=xdg-run/...` is needed

## 2. Environment / bootstrap

- [ ] 2.1 Document building Casilda from `repos/casilda` (meson setup, ninja
      install, `GI_TYPELIB_PATH`/`LD_LIBRARY_PATH`) in sugar-next docs
- [ ] 2.2 Make `bootstrap.sh` detect the Casilda typelib and fail loudly with
      a pointer to the build doc when missing

## 3. Activity hosting core

- [ ] 3.1 Add an `ActivityHost` module: per-activity `CasildaCompositor`
      pages in a `Gtk.Stack` layered under the Frame overlay (design D1),
      with add/switch/dispose operations
- [ ] 3.2 Rewrite `DesktopBundle.launch()`: strip `Exec=` field codes, spawn
      via the activity's compositor (design D3); keep the `on_app_launch`
      veto hook before spawn
- [ ] 3.3 Wire lifecycle: activity running while ≥1 toplevel mapped; on last
      toplevel closed fire `on_app_close`, remove Frame entry, dispose page
      (design D5)
- [ ] 3.4 Delete `shell/toplevel_tracker.py`, `_wayland_wlr/`, the pid-watch
      in `bundles/desktop_bundle.py`, and the `pywayland` optional dependency
      in the same commit as 3.3

## 4. Frame integration

- [ ] 4.1 Feed the Frame's running list from ActivityHost events; entry
      appears on first toplevel map, disappears on last close
- [ ] 4.2 Clicking a running entry switches to that activity's page and
      closes the Frame

## 5. Ambient socket + escape hatch

- [ ] 5.1 Bind a collision-scanned `sugar-next-<n>` named socket in
      `XDG_RUNTIME_DIR` attached to an ambient compositor page; external
      toplevels gain Frame entries (design D2)
- [ ] 5.2 Add "Open outside" secondary action on grid/pie items using
      `Gio.AppInfo.launch()`; offer it only when a host desktop session is
      detected (design D4)

## 6. Docs + verification

- [ ] 6.1 Update `specbook/docs/gtk-porting-standards.md`: replace the
      "shell inside Casilda unproven" boundary note with this change's
      validated result
- [ ] 6.2 Update HIG XDG-compliance list with the named-socket contract and
      document the escape hatch's untracked-window limitation
- [ ] 6.3 End-to-end verification: launch two apps embedded, switch via
      Frame, close one (entry disappears, hook fires), redirect a terminal
      app via `WAYLAND_DISPLAY`, open one outside; run in both a GNOME
      session and a nested bare compositor
- [ ] 6.4 Update the `record-sugar-next-demo` skill script if the launch
      flow it records changed
