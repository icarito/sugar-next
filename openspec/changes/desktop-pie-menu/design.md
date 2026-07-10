# Desktop Pie Menu — Design

## Views (after the change)

| Key | View | Content |
|-----|------|---------|
| F1 | Desktop | Wallpaper + radial pie menu of pinned favorites. Settings in menu center |
| F2 | Apps | App Grid (Gtk.FlowBox + search). Unchanged from current |
| F3 | — | Reserved for future Groups/Neighborhood |
| F6 | Frame | View switcher [Desktop] [Apps] + running windows only |

## Pie menu widget

A new `shell/pie_menu.py` widget:

- Radial layout: favorite icons arranged in a circle around the cursor
  or screen center
- Click a petal → launch the app
- Right-click a petal → unpin from favorites
- Center button → Settings panel
- Empty state: "Pin apps from the Apps view to see them here" message
- Animation: fade-in on view activation, smooth petal reveal

## Frame simplification

- Remove `_favorites_box` and all favorites-related code from `frame.py`
- Remove Settings button (`_settings_button`) from Frame
- Retain: view switcher, running apps box

## Settings relocation

- Settings panel already exists (`shell/settings.py`)
- Remove `frame.set_settings_panel()` wiring in `main.py`
- Add settings-button in pie menu center calling `settings_panel.popup()`
- F10 keybinding can still toggle Settings

## Removals

| File | Action |
|------|--------|
| `shell/search_first.py` | Delete (Search view removed) |
| `shell/desktop_grid.py` | Delete (replaced by pie menu) |
| `examples/extensions/logger.js` | Keep (extension example, unrelated) |
| `favorites` in `frame.py` | Remove all favorites code |
| `settings_button` in `frame.py` | Remove |
