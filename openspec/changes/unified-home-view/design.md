# Design: unified-home-view

## Context

Sugar Next's Home View is a `Gtk.Stack` with two pages: the pie menu
(`SugarPieMenu`, view_id `desktop-grid`) and the app grid (`SugarAppGrid`,
view_id `app-grid`). The Frame provides [Desktop] [Apps] buttons that switch
between them. This works but treats two aspects of the same thing — "my apps"
— as separate destinations, and it navigates via F1/F2, which are unreachable
on laptops whose firmware maps the F-row to hardware keys.

The pie menu uses `Gtk.Fixed` for radial positioning of _Petal widgets. The
app grid uses `Gtk.FlowBox` inside a `Gtk.ScrolledWindow` with a
`Gtk.SearchEntry`. Both use `bind_icon_state` from `icon_state.py` for
open/focused rendering. The Frame already has a `_running_box` (open apps) and
a working `focus_window()` path (`_on_frame_running_activated`), and the shell
already distinguishes standalone vs hosted mode (`self._standalone_mode`).

## Goals / Non-Goals

**Goals:**

- One Home view with two orthogonal axes: a **mode** (layout: Spiral / Grid /
  Free) and a **filter** (set: Favorites+Active / Favorites / Active / All).
- Mode navigation by scroll/gesture, not F-keys.
- Search lives in the Frame and respects the active filter.
- The spiral center opens a menu (Settings + standalone/hosted exit action),
  not the Settings panel directly.
- Clicking a running app's icon focuses its window instead of relaunching.
- Dark/light toggle, accent auto-apply, hover tint (done; specced here).

**Non-Goals:**

- GPU shaders — animations use GTK4 built-in transitions and Cairo.
- Journal / knowledge-graph object model — separate future change
  (`specbook/docs/journal-graph-vision.md`).
- F6/F10 replacement — same dead-key problem, deferred to a separate change.

## Two orthogonal axes

The central mental model. Mode = layout (how). Filter = set (which). They cross
freely; every cell is valid.

```
                │  Favorites+Active  │  Favorites  │  Active  │  All
  ──────────────┼────────────────────┼─────────────┼──────────┼─────────
  Spiral (rings)│  DEFAULT on start  │  pie menu    │ open now │ all, in
                │                    │  of today    │ radially │ rings
  Grid  (flow)  │  favs ∪ open, grid │  small grid  │ open now │ app grid
                │                    │  of favs     │ in grid  │ of today
  Free  (x/y)   │  favs ∪ open,      │  favs, freely│ open now │ all,
                │  placed            │  placed      │  placed  │ placed
```

## Decisions

### D1. Mode axis: Spiral / Grid / Free

`UnifiedHomeView` owns three layout strategies over one filtered icon set.

- **Spiral** grows into concentric rings as the icon count exceeds one ring's
  capacity (classic Sugar `RingLayout`), so Spiral + All stays legible instead
  of one enormous circle. Subsumes today's `SugarPieMenu`.
- **Grid** is today's `SugarAppGrid` flow layout, MRU-ordered.
- **Free** is manual x/y placement: each icon draggable anywhere, position
  persisted per app id. New; no prior equivalent.
- Default on start: **Spiral**.

*Why a mode axis at all, vs. just the pie/grid split of today?* Because the
learner should re-arrange the *same* set of things, not travel to a different
place with a different set. Mode changes the arrangement; the set is the
filter's job.

### D2. Filter axis: Favorites+Active / Favorites / Active / All

Four values over existing data — no new bookkeeping:

- **Favorites** = pinned in favorites.json (today's pie-menu set).
- **Active** = `app_state.is_open()` (today's Frame running-list set).
- **All** = every installed app (today's app-grid set).
- **Favorites+Active** = the union, and the **default on start** — so the
  screen is never empty even before anything is launched, and open-but-unpinned
  apps show up next to pinned ones. `icon_state.py` already distinguishes their
  visual state (`sn-icon-open` vs `sn-icon-closed`), so mixing them reads
  cleanly.

The filter selector lives in the Frame. The Frame is **not** promoted to a
permanent command bar — it still appears via hot-corner / reveal as today; it
just carries more inside when open.

### D3. Mode navigation via scroll / gesture (F-keys are dead)

Modern laptops map the F-row to hardware keys, so F1/F2 are out.

- **Lateral scroll** (trackpad two-finger horizontal) or **shift+scroll**
  (wheel) anywhere on the shell moves between modes. Plain **vertical** scroll
  stays reserved for scrolling within a grid, so the two never collide (they
  are different axes, not the same axis overloaded).
- Scroll over the **Frame** also switches mode — the Frame has no scrollable
  content of its own, so any scroll there is unambiguous.
- Touch: a pinch or two-finger vertical swipe as the gesture equivalent.
- Mode order for the scroll cycle and whether it wraps is an implementation
  detail to tune during apply (see Open Questions).

### D4. Search in the Frame, respecting the active filter

The `Gtk.SearchEntry` moves out of `app_grid.py` into the Frame bar. Typing
filters whichever mode is active. Search **respects the active filter**:
searching under Favorites searches only favorites; to search everything the
learner switches the filter to All explicitly. Predictable over "magic" — the
search never silently changes the visible set behind the learner's back.

### D5. Central menu, not a direct Settings popup

The spiral center button currently calls `settings_panel.popup()` directly. It
instead opens a **popup menu**:

- **Settings** — opens the Settings panel (today's behavior, now one item).
- **Logout** when `self._standalone_mode` (Sugar owns the session — logging out
  ends it), or **Close Sugar Next** when hosted (Sugar runs inside a host
  GNOME — closing leaves the host alive).

### D6. Click-to-focus for running apps

Clicking an app icon (spiral/grid/free) should focus an already-open window
rather than relaunch. The path already exists — `_on_frame_running_activated`
calls `gnome_window_source.focus_window()` / `toplevel_tracker.focus()`. The
per-icon click handler becomes: `if app_state.is_open(app_id): focus_window()
else: launch()`. Pass this as the icons' activate callback instead of a blind
`bundle.launch()`.

### D7. Dark/light toggle, accent auto-apply, hover tint (done)

Already implemented (recovered from the Jules branches). One bug found in
explore: the light-mode icon name `sun-symbolic` does not exist in Adwaita, so
only the moon ever renders. Use `weather-clear-symbolic` (the freedesktop pair
of `weather-clear-night-symbolic`). Hover tint is CSS-only, present in both
`pie_menu.py` and `app_grid.py`, and open/focused state classes take
precedence over hover by specificity.

### D8. Free-mode placement persistence

Free mode stores an x/y per app id. Options: store normalized (0..1) fractions
so positions survive resolution changes, keyed by app id in SettingsStore.
Apps never placed have no stored position and fall back to an auto-layout
(grid snapshot) until first dragged. Drag via `Gtk.DragSource` +
`Gtk.DropTarget` on a `Gtk.Fixed` canvas.

## Risks / Trade-offs

- [Spiral + All with 50+ apps] → ring-growth layout (D1); needs a capacity
  formula per ring. Mitigation: cap visible count or add an outer "more" ring
  if it gets absurd.
- [Scroll-to-switch vs. scroll-within-grid] → resolved by using different axes
  (lateral/shift = mode, vertical = grid scroll). Test trackpad vs. wheel vs.
  touch to confirm the axis split feels natural on each.
- [Free-mode is the most complex sub-task] → could ship Spiral + Grid first and
  land Free in a follow-up if scope pressures. MRU + filter + scroll-nav are
  the higher-value core.
- [Search moving to Frame] → the Frame is normally hidden; typing must reveal
  it (or the search must be reachable without the Frame open). Decide during
  apply whether type-to-search auto-reveals the Frame.

## Migration Plan

1. Fix `sun-symbolic` → `weather-clear-symbolic` (trivial, unblocks the toggle
   the learner already sees half-broken).
2. `UnifiedHomeView`: mode axis (Spiral rings / Grid / Free), filter axis,
   default Spiral + Favorites+Active.
3. Scroll/gesture mode navigation; retire F1/F2 for modes.
4. Move search to the Frame; wire filter-respecting search.
5. Central menu (standalone/hosted exit) + click-to-focus.
6. MRU ordering in grid mode.
7. Write delta specs; run suite.

## Open Questions

- Mode scroll order and wrap: Spiral → Grid → Free → (wrap to Spiral)? Or is
  Free a deliberate, less-frequent destination reached differently?
- Should type-to-search auto-reveal the Frame (so the learner can search
  without opening it first), or is search only available once the Frame is up?
- Free mode: per-app normalized positions vs. absolute px — confirm during
  apply against multi-monitor / resolution-change behavior.
