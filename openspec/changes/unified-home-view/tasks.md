# Tasks: unified-home-view

## 1. Dark/light theme toggle (Frame button)

- [ ] 1.1 Add `dark_mode` (bool, default false) to settings_store.py defaults
- [ ] 1.2 Add `set_dark_mode(bool)` to theme.py — swaps `--sn-*` token set
      between light and dark variants
- [ ] 1.3 Add dark/light toggle button to Frame bar (right edge), icon
      changes between `sun-symbolic` and `weather-clear-night-symbolic`
- [ ] 1.4 Wire button click → settings_store flip → theme_manager.set_dark_mode
- [ ] 1.5 Manual test: toggle in Frame, confirm all chrome switches theme
      instantly; restart, confirm persisted

## 2. Accent color auto-apply

- [ ] 2.1 Remove hex Gtk.Entry and Apply button from settings.py Color tab
      (lines 399-408, `custom_row` and `_on_custom_accent`)
- [ ] 2.2 Confirm `_on_accent_chosen` already applies immediately (it does)
- [ ] 2.3 Manual test: click swatch → accent changes instantly; no Apply
      button or hex entry visible

## 3. Icon hover tint (CSS)

- [ ] 3.1 Add `.pie-menu-petal:hover { -gtk-icon-filter: brightness(1.15)
      saturate(1.2); }` to pie_menu.py CSS
- [ ] 3.2 Add `.app-grid-cell:hover image { -gtk-icon-filter: brightness(1.15)
      saturate(1.2); }` to app_grid.py CSS
- [ ] 3.3 Add `transition: -gtk-icon-filter 150ms ease` to existing icon
      transition rules
- [ ] 3.4 Manual test: hover over grid cell and pie petal, icon brightens
      smoothly; unhover, returns to state-based rendering

## 4. Unified Home View wrapper + mode switching

- [ ] 4.1 Create `UnifiedHomeView` widget that wraps pie menu and app grid as
      internal children in a Gtk.Stack with OVER_UP/DOWN transitions
- [ ] 4.2 Set "favorites" (radial, pie menu) as default visible page
- [ ] 4.3 Add zoom toggle: F1 = zoom out (radial), F2 = zoom in (grid).
      Also a small button at the Home view's top-right
- [ ] 4.4 Wire zoom toggle to HomeView.set_active() with OVER_UP/DOWN
- [ ] 4.5 Replace HomeView's two-view registration with single
      UnifiedHomeView in main.py
- [ ] 4.6 Manual test: F1/F2 switches between radial and grid with slide
      animation; button reflects current mode

## 5. Global type-to-search

- [ ] 5.1 Add a Gtk.SearchEntry overlay to the UnifiedHomeView (hidden by
      default, positioned at top)
- [ ] 5.2 In main.py:_on_key_pressed, catch printable chars that don't match
      any keybinding — show the search overlay, focus entry, insert char
- [ ] 5.3 Escape or focus-loss hides the search overlay, clears filter
- [ ] 5.4 Filtering: in grid mode, existing _filter_func applies. In radial
      mode, match petal names against search text (opacity 0 for non-matches)
- [ ] 5.5 Manual test: press any letter key on Desktop → search bar appears
      with that letter; radial mode filters petals; switch to grid mode,
      filter persists; Esc dismisses

## 6. MRU ordering

- [ ] 6.1 Add `mru_order` (list of str, default []) to settings_store.py
- [ ] 6.2 Update MRU list on every app launch (in main.py:_on_app_launched)
- [ ] 6.3 Refactor SugarAppGrid to order by MRU: favorites first, then
      recently launched, then alphabetical (never-launched)
- [ ] 6.4 Manual test: launch Firefox, launch Calculator → Calculator appears
      before Firefox in grid; launch Firefox again → Firefox moves to top

## 7. Frame simplification

- [ ] 7.1 Replace [Desktop] [Apps] view switcher with a single Home button
      (or keep both but map to zoom directions)
- [ ] 7.2 Update _VIEW_KEYS: F1 = zoom out, F2 = zoom in (both within
      the single Home view)
- [ ] 7.3 Manual test: Frame shows one view button; F1/F2 zoom within Home

## 8. Specs updates

- [ ] 8.1 Write delta spec for `frame-views`: view switcher simplified to one
      Home view, F1/F2 as zoom actions, Frame gains dark/light toggle
- [ ] 8.2 Write delta spec for `home-view`: unified single view, global
      type-to-search, MRU ordering, dark/light toggle, accent auto-apply,
      hover tint
- [ ] 8.3 Update `semantic-color-system`: add dark/light token set switching

## 9. Verification

- [ ] 9.1 Full manual walkthrough: start shell → radial mode → type a letter
      → search appears → F2 → grid mode with filter → F1 → back to radial →
      toggle dark/light → click accent swatch → launch app → confirm MRU
      updated → close app → confirm icon state
- [ ] 9.2 Run existing test suite: `python -m pytest sugar-next/tests/`
