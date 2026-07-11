# Proposal: unified-home-view

## Why

Sugar Next currently has two separate views — Desktop (pie menu of pinned
favorites) and Apps (scrollable grid of all installed apps) — switched via
the Frame. This split reflects an earlier design where the Desktop was a
static grid and the pie menu replaced it. Now that both exist and work, the
split feels like a mode switch rather than a unified experience: the learner
moves between "my stuff" and "everything" through two different widgets with
different layouts, different interaction models (radial vs. grid), and no
visible connection between them.

A single Home View that *is* both — one surface whose icons can be arranged
radially, in a grid, or placed freely — makes the shell feel like one
continuous space rather than two rooms with a door. Two independent axes make
this coherent instead of a pile of modes:

- **Mode (layout)** decides *how* icons are arranged: Spiral, Grid, or Free.
- **Filter (set)** decides *which* icons appear: Favorites+Active, Favorites,
  Active, or All.

Any mode combines with any filter, so "the pie menu of favorites" and "the
grid of all apps" become two cells of one matrix rather than two apps.

Beyond layout, the current navigation model is broken on real hardware. The
shell binds mode/view switching to F1/F2 (and F6/F10 for Frame/Settings), but
modern laptops remap the F-row to hardware functions (brightness, volume),
making those keys unreachable without `Fn`. Navigation must move to
scroll/gesture, which also makes the "zoom between levels" metaphor literal.

## What Changes

- **Three layout modes**: Spiral (radial, growing into concentric rings as the
  icon count grows — classic Sugar RingLayout), Grid (flow layout, MRU
  ordered), and Free (manual x/y placement, persisted per app). Default on
  start: Spiral.
- **Four-value filter axis**, orthogonal to mode: Favorites+Active (default,
  never an empty screen), Favorites, Active, All. Backed by existing data
  (favorites.json + `app_state`), no new bookkeeping.
- **Mode navigation via scroll/gesture, not F-keys**: lateral scroll or
  shift+scroll anywhere on the shell (including over the Frame) moves between
  modes; plain vertical scroll stays reserved for scrolling within a grid.
  Touch pinch/swipe equivalent.
- **Search moves to the Frame** and respects the active filter (searching in
  Favorites searches only favorites; switch to All to search everything).
- **Central menu replaces the direct Settings popup**: the spiral center
  button opens a popup menu — Settings, plus Logout (standalone mode) or Close
  Sugar Next (hosted mode).
- **Click-to-focus**: clicking a running app's icon raises its window instead
  of relaunching, matching what the Frame's running list already does.
- **Dark/light toggle in Frame**, **accent color applies immediately**, **icon
  hover tint** — already implemented (were delegated to Jules); folded into
  this change's spec. One follow-up: the light-mode icon name `sun-symbolic`
  does not exist in Adwaita and must be `weather-clear-symbolic`.

## Capabilities

### New Capabilities

- `unified-home-view`: the Home View becomes a single surface with two
  orthogonal axes — three layout modes (spiral/grid/free) and a four-value
  filter (favorites+active/favorites/active/all) — navigated by scroll/gesture,
  searched from the Frame, with click-to-focus for running apps.

### Modified Capabilities

- `frame-views`: the view switcher becomes a single Home view. Mode navigation
  moves off F1/F2 to scroll/gesture. The Frame gains the filter selector, the
  search entry, and the dark/light toggle; the spiral center opens a menu
  (Settings + mode-appropriate exit) rather than the Settings panel directly.
- `home-view`: three layout modes, four-value filter, search-respects-filter,
  click-to-focus, dark/light toggle, accent auto-apply, icon hover tint.
  Removes the hex entry and Apply button from the color picker.
- `semantic-color-system`: adds the dark/light theme token set toggle.

## Out of Scope (noted debt)

- **F6 (Frame pin) and F10 (Settings)** share the dead-F-key problem but are
  left to a separate change; only the Home View's own mode navigation is
  addressed here. F6 already has a partial alternative (hot-corner reveal);
  F10 has none yet.
- **Journal / knowledge-graph** (the constructionist object model, folder-as-
  graph, filesystem observation, Zeitgeist/indexer) is a separate future
  change. Its north star is captured in
  `specbook/docs/journal-graph-vision.md`. This change is only the app
  launcher surface.

## Impact

- `sugar-next/sugar_next/shell/pie_menu.py` — becomes the spiral-mode
  rendering of the unified view (with ring-growth layout).
- `sugar-next/sugar_next/shell/app_grid.py` — becomes the grid-mode rendering;
  loses its own SearchEntry (moves to Frame).
- `sugar-next/sugar_next/shell/home_view.py` — gains the mode axis, the filter
  axis, scroll/gesture navigation, Free-mode placement, MRU ordering.
- `sugar-next/sugar_next/shell/frame.py` — hosts the filter selector, search
  entry, dark/light toggle; scroll over the Frame switches mode.
- `sugar-next/sugar_next/shell/main.py` — routes scroll/gesture to mode
  changes; central menu wiring (standalone vs hosted); click-to-focus reuse of
  `_on_frame_running_activated`; MRU update on launch. Fix `sun-symbolic` →
  `weather-clear-symbolic`.
- `sugar-next/sugar_next/shell/settings.py` — color picker without hex entry /
  Apply button (already done).
- `sugar-next/sugar_next/shell/settings_store.py` — `dark_mode` (done),
  `mru_order` list, Free-mode per-app positions.
- `sugar-next/sugar_next/shell/theme.py` — dark/light token set switching
  (done).
