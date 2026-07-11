# Tasks: unified-home-view

## 1. Dark/light theme toggle (Frame button)

- [x] 1.1 Add `dark_mode` (bool, default false) to settings_store.py defaults
- [x] 1.2 Add `set_dark_mode(bool)` to theme.py — swaps `--sn-*` token set
      between light and dark variants
- [x] 1.3 Add dark/light toggle button to Frame bar (right edge), icon
      changes between light/dark mode icons
- [x] 1.4 Wire button click → settings_store flip → theme_manager.set_dark_mode
- [x] 1.5 Manual test: toggle in Frame, confirm all chrome switches theme
      instantly; restart, confirm persisted
- [x] 1.6 BUG (found in explore): `sun-symbolic` does not exist in Adwaita, so
      the light-mode icon never renders (only the moon shows). Use
      `weather-clear-symbolic` (paired with `weather-clear-night-symbolic`)

## 2. Accent color auto-apply

- [x] 2.1 Remove hex Gtk.Entry and Apply button from settings.py Color tab
      (`custom_row` and `_on_custom_accent`)
- [x] 2.2 Confirm `_on_accent_chosen` already applies immediately (it does)
- [x] 2.3 Manual test: click swatch → accent changes instantly; no Apply
      button or hex entry visible

## 3. Icon hover tint (CSS)

- [x] 3.1 Add `.pie-menu-petal:hover image { -gtk-icon-filter: brightness(1.15)
      saturate(1.2); }` to pie_menu.py CSS
- [x] 3.2 Add `.app-grid-cell:hover image { -gtk-icon-filter: brightness(1.15)
      saturate(1.2); }` to app_grid.py CSS
- [x] 3.3 Add `transition: -gtk-icon-filter 150ms ease` to existing icon
      transition rules
- [x] 3.4 Manual test: hover over grid cell and pie petal, icon brightens
      smoothly; unhover, returns to state-based rendering

## 4. Unified Home View: mode (layout) axis

The Home View gains three *layout modes*, orthogonal to the *filter* axis
(section 5). A mode decides how icons are arranged; a filter decides which
icons appear.

- [x] 4.1 Create `UnifiedHomeView` widget that owns the modes (home_view.py).
      Spiral and grid subsume today's `SugarPieMenu`/`SugarAppGrid` via a new
      `populate(bundles)` on each; covered by tests/test_unified_home_view.py
- [x] 4.2 Spiral mode: radial layout that grows into concentric rings as the
      icon count exceeds one ring (ring_layout.py, tested in
      tests/test_ring_layout.py), so Spiral + "All apps" stays legible
- [x] 4.3 Grid mode: flow/grid layout (today's app grid), MRU-ordered
- [ ] 4.4 Free mode: manual x/y placement — DEFERRED to a follow-up change
      (most complex, least immediate value per design.md Risks)
- [x] 4.5 Default on shell start: Spiral mode
- [ ] 4.6 Manual test: switch modes, confirm the same filtered icon set
      re-lays-out in each (needs the shell wired + running — task 6/verify)

## 5. Filter axis (orthogonal to mode)

- [x] 5.1 Filter has four values: Favorites+Active (default), Favorites,
      Active, All (app_ordering.filter_apps). Sourced from favorites.json and
      `app_state` — no new bookkeeping; tested in tests/test_app_ordering.py
- [x] 5.2 Default filter on shell start: Favorites+Active (union) — the view
      subscribes to app_state so it stays live
- [ ] 5.3 Filter selector lives in the Frame (needs Frame wiring — task 7)
- [x] 5.4 Any mode × any filter is a valid combination (verified in
      tests/test_unified_home_view.py)
- [ ] 5.5 Manual test: each filter narrows the set (needs shell running)

## 6. Mode navigation via scroll / gesture (F-keys are dead on modern laptops)

- [ ] 6.1 Remove reliance on F1/F2 for mode switching — modern laptops remap
      the F-row to hardware keys, making them unreachable
- [ ] 6.2 Lateral scroll OR shift+scroll anywhere on the shell moves between
      modes; plain vertical scroll stays reserved for scrolling within grid
- [ ] 6.3 Scroll over the Frame also switches mode (the Frame has no scrollable
      content of its own)
- [ ] 6.4 Touch gesture equivalent (pinch or two-finger swipe) for
      touchscreens
- [ ] 6.5 Manual test on a laptop with an F-row remapped by firmware: modes
      switch by scroll/gesture with no F-key needed

## 7. Search moved to the Frame

- [ ] 7.1 Move the search entry out of `app_grid.py` and into the Frame bar
- [ ] 7.2 Search respects the active filter (searching in Favorites searches
      only favorites; switch to All explicitly to search everything)
- [ ] 7.3 Filtering applies across whichever mode is active (spiral/grid/free)
- [ ] 7.4 Manual test: type in Frame search → current mode filters live;
      change filter → search scope changes accordingly

## 8. Central menu (replaces direct Settings popup) + click-to-focus

- [x] 8.1 Spiral center button opens a popup MENU, not the Settings panel
      directly. Menu items: Settings; plus Logout (standalone mode) or Close
      Sugar Next (hosted mode), keyed off `self._standalone_mode`. Center is a
      Gtk.MenuButton + popover; covered by tests/test_pie_menu.py
- [x] 8.2 Clicking an app icon (spiral/grid/free) calls `focus_window()` if the
      app is already open (reuse `_on_frame_running_activated`'s logic), else
      launches — matching what the Frame's running list already does. Shared
      `_activate_app` in main.py; covered by tests/test_activate_app.py
- [x] 8.3 Manual test: click a running app's icon → its window raises instead
      of relaunching; center menu shows the mode-appropriate exit action

## 9. MRU ordering (grid mode)

- [x] 9.1 Add `mru_order` (list of str, default []) to settings_store.py
- [x] 9.2 Update MRU list on every app launch (in main.py:_on_app_launched)
- [x] 9.3 Grid mode orders by MRU: favorites first, then recently launched,
      then alphabetical (never-launched) — shared helper in app_ordering.py,
      covered by tests/test_app_ordering.py
- [x] 9.4 Manual test: launch Firefox, launch Calculator → Calculator appears
      before Firefox in grid; launch Firefox again → Firefox moves to top

## 10. Specs updates

- [ ] 10.1 Delta spec `frame-views`: single Home view; mode nav via
      scroll/gesture (not F1/F2); Frame gains filter selector, search entry,
      dark/light toggle; central menu replaces direct Settings popup
- [ ] 10.2 Delta spec `home-view`: three layout modes (spiral/grid/free),
      four-value filter axis, search-respects-filter, click-to-focus,
      dark/light toggle, accent auto-apply, hover tint
- [ ] 10.3 Update `semantic-color-system`: dark/light token set switching

## 11. Verification

- [ ] 11.1 Full manual walkthrough: start shell → Spiral + Favorites+Active →
      scroll to Grid → type in Frame search → change filter to All → scroll to
      Free, drag an icon → toggle dark/light → click a running app's icon
      (raises, not relaunches) → open center menu (correct exit action) →
      restart, confirm Free positions + theme persisted
- [ ] 11.2 Run existing test suite: `python -m pytest sugar-next/tests/`
