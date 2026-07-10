# Desktop Pie Menu — Tasks

## 1. Pie menu widget

- [ ] 1.1 Create `shell/pie_menu.py` — radial layout widget
- [ ] 1.2 Wire center button → Settings panel popup
- [ ] 1.3 Load favorites from `favorites.json` and populate petals
- [ ] 1.4 Wire petal click → launch app
- [ ] 1.5 Wire right-click on petal → unpin from favorites
- [ ] 1.6 Add animation (fade-in, smooth reveal)
- [ ] 1.7 Handle empty state (no favorites pinned)

## 2. Desktop view replacement

- [ ] 2.1 Replace `desktop_grid.py` usage in `HomeView` with `pie_menu.py`
- [ ] 2.2 Delete `shell/desktop_grid.py`
- [ ] 2.3 Verify wallpaper background still renders behind pie menu

## 3. Frame simplification

- [ ] 3.1 Remove `_favorites_box` and favorites code from `frame.py`
- [ ] 3.2 Remove Settings button from Frame
- [ ] 3.3 Remove `set_settings_panel()` and related wiring from `frame.py`

## 4. Settings relocation

- [ ] 4.1 Remove `frame.set_settings_panel()` call from `main.py`
- [ ] 4.2 Wire pie menu center → `settings_panel.popup()`
- [ ] 4.3 Ensure F10 keybinding still opens Settings

## 5. Search view removal

- [ ] 5.1 Remove `search-first` from views list in `main.py`
- [ ] 5.2 Delete `shell/search_first.py`
- [ ] 5.3 Update `_VIEW_KEYS` — F3 is no longer bound; document as reserved
- [ ] 5.4 Update view switcher in Frame (only [Desktop] [Apps])

## 6. Cleanup

- [ ] 6.1 Smoke test: navigate Desktop → Apps → Frame → Desktop
- [ ] 6.2 Smoke test: pin app in Apps view, verify it appears in pie menu
- [ ] 6.3 Smoke test: unpin from pie menu, verify it disappears
- [ ] 6.4 Smoke test: open Settings from pie menu center
- [ ] 6.5 Remove `home_view.py` if no longer needed (views are direct now)
- [ ] 6.6 Update tests
