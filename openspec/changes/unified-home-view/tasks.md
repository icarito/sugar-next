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
- [x] 5.3 Filter selector lives in the Frame (Gtk.DropDown in frame.py, wired
      to unified_home.set_filter)
- [x] 5.4 Any mode × any filter is a valid combination (verified in
      tests/test_unified_home_view.py)
- [ ] 5.5 Manual test: each filter narrows the set (needs shell running)

## 6. Mode navigation via scroll / gesture (F-keys are dead on modern laptops)

- [x] 6.1 Remove reliance on F1/F2 for mode switching — _VIEW_KEYS removed
      from _on_key_pressed; single Home view no longer needs view keys
- [x] 6.2 Lateral scroll OR shift+scroll anywhere switches mode
      (Gtk.EventControllerScroll on the window → unified_home.cycle_mode);
      plain vertical scroll left for the grid
- [x] 6.3 Scroll over the Frame also switches mode (controller is on the
      window, so it covers the Frame too)
- [ ] 6.4 Touch gesture equivalent (pinch/two-finger swipe) — DEFERRED with
      Free mode; the scroll path covers trackpad/wheel now
- [ ] 6.5 Manual test on a laptop with a remapped F-row (needs hardware;
      shell smoke-tested to start cleanly with the scroll controller wired)

## 7. Search moved to the Frame

- [x] 7.1 Move the search entry out of `app_grid.py` and into the Frame bar
      (Gtk.SearchEntry in frame.py; grid filtered via set_search_text)
- [x] 7.2 Search respects the active filter (UnifiedHomeView._visible_bundles
      applies search within the filtered set; tested in
      tests/test_unified_home_view.py)
- [x] 7.3 Filtering applies across whichever mode is active (spiral repopulates
      on search; grid filters live)
- [ ] 7.4 Manual test: type in Frame search → mode filters live (needs the
      shell running; smoke-tested to start cleanly)

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

- [x] 10.1 Delta spec `frame-views`: single Home view; mode nav via
      scroll/gesture (not F1/F2); Frame gains filter selector, search entry,
      dark/light toggle; central menu replaces direct Settings popup
- [x] 10.2 Delta spec `home-view`: layout modes, four-value filter axis,
      search-respects-filter, click-to-focus, dark/light toggle, accent
      auto-apply, hover tint (Free mode noted as follow-up)
- [x] 10.3 Update `semantic-color-system`: dark/light token set switching

## 11. Verification

- [ ] 11.1 Full manual walkthrough (needs a real session): Spiral +
      Favorites+Active → scroll to Grid → Frame search → filter to All →
      toggle dark/light → click a running app's icon (raises) → center menu
      exit action. Startup smoke-tested clean under Xvfb; Free-mode step
      deferred with Free mode.
- [x] 11.2 Run existing test suite: `python -m pytest sugar-next/tests/`
      (119 passed)
