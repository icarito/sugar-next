# Design: unified-home-view

## Context

Sugar Next's Home View is a `Gtk.Stack` with two pages: the pie menu
(`SugarPieMenu`, view_id `desktop-grid`) and the app grid (`SugarAppGrid`,
view_id `app-grid`). The Frame provides [Desktop] [Apps] buttons that switch
between them. This works but treats two aspects of the same thing — "my apps"
— as separate destinations.

The pie menu uses `Gtk.Fixed` for radial positioning of _Petal widgets. The
app grid uses `Gtk.FlowBox` inside a `Gtk.ScrolledWindow` with a
`Gtk.SearchEntry`. Both use `bind_icon_state` from `icon_state.py` for
open/focused rendering.

The frame-views spec currently mandates two views (Desktop, Apps) with F1/F2
direct keybindings. This change reduces the frame-views requirement to one
view (Home) and moves F1/F2 to zoom-in/zoom-out within that view.

## Goals / Non-Goals

**Goals:**

- Replace the two-view stack with a single Home view that has a radial
  "favorites" mode and a grid "all apps" mode, animated transition between
  them.
- Any keypress that is not a kb shortcut triggers search overlay instantly.
- Apps ordered by MRU; manual drag-reorder; pinned favorites always first.
- Dark/light toggle from the Frame (one click, instant).
- Accent color picker applies on swatch click (no Apply button, no hex entry).
- Icon hover tint in both radial and grid modes.

**Non-Goals:**

- Fancy GPU shaders — animations use GTK4 built-in transitions and Cairo,
  matching the project's existing rendering approach.
- Full touch rework — the interactive areas already work on touch (pie menu
  petals, grid cells); this change does not redesign for touch first.
- Activity workspaces (future change).

## Decisions

### D1. Unified Home View wraps both modes in a single widget

A new `UnifiedHomeView(Gtk.Widget)` (or extending `Gtk.Overlay`) that owns
the pie menu and app grid as internal children. It manages two `Gtk.Stack`
pages internally, but presents them as one conceptual view to the shell.

- *Why not keep two separate views in HomeView's stack?* Because the
  transition between "just favorites" and "full grid" is not a page flip — it
  is a zoom/scale animation. A wrapper can orchestrate that animation.
- The Frame's view switcher shows one button ("Home") instead of two.
  Internal mode switching happens via a zoom toggle button within the Home
  view itself (or F1/F2), not via the Frame.

### D2. Animation via Gtk.Stack with OVER_UP/DOWN transition

The simplest approach that works: when the learner zooms in (favorites →
grid), the pie menu page slides up and out while the grid page slides up and
in (`OVER_UP`). Zoom out (grid → favorites) reverses with `OVER_DOWN`. This
reuses existing GTK4 stack transitions, requires no custom Cairo animation,
and looks polished.

- *Fallback if more visual drama is wanted:* chain two crossfades with a
  scale transform via a Gtk.Transition or a custom Gtk.Widget do_snapshot.
  For now, OVER_UP/DOWN is zero new code and good enough.

### D3. Global type-to-search via EventControllerKey on the shell window

A single `Gtk.EventControllerKey` on the shell window (already exists in
`main.py:_on_key_pressed`). When a printable character is pressed and it is
not a keybinding, focus the search entry (which lives in the Home view, not
the App Grid) and insert the character.

- The search overlay is a `Gtk.SearchEntry` positioned over the Home view,
  shown when any printable key is pressed and hidden on Escape or when the
  entry loses focus.
- Filtering: in grid mode, the existing `_filter_func` applies. In radial
  mode, petals that don't match the search term are hidden (opacity 0).
- The same search state persists across mode switches.

### D4. MRU order via a LRU list in SettingsStore

A new `mru_order` list in `SettingsStore` (list of normalized app ids,
most-recently-launched first). Updated on every app launch. The app grid
renders in this order (favorites first, then MRU, then alphabetical for
never-launched apps).

- Manual drag-reorder: `Gtk.FlowBox` does not natively support drag-reorder.
  Implement via `Gtk.DragSource` + `Gtk.DropTarget` on each cell, or switch
  to a `Gtk.ListView` with `Gtk.SingleSelection` for built-in drag-reorder.
  Prefer `Gtk.ListView` for future-proofing; `Gtk.FlowBox` was a simpler
  initial choice but lacks reorder support.
- *Note:* this is the most complex sub-task. Could be deferred to a follow-up
  if the animation + search + dark/light toggle are enough for this change.

### D5. Dark/light toggle: one button in the Frame

A `Gtk.Button` with `weather-clear-night-symbolic` / `sun-symbolic` icon at
the right edge of the Frame bar. Clicking toggles `dark_mode` in
SettingsStore, then calls `theme_manager.set_dark_mode(bool)` which swaps the
`--sn-*` token set between light and dark variants. No restart needed.

### D6. Accent picker auto-apply

`_on_accent_chosen` already calls `theme_manager.set_accent_tint()` and
`store.set("accent_color", ...)` — it just needs the hex entry row (lines
399-408 in settings.py) and `_on_custom_accent` removed. Each swatch click
persists and applies immediately.

### D7. Icon hover tint: CSS-only

```css
.pie-menu-petal:hover,
.app-grid-cell:hover image {
    -gtk-icon-filter: brightness(1.15) saturate(1.2);
    transition: -gtk-icon-filter 150ms ease;
}
```

Applied via the existing CSS providers in `pie_menu.py` and `app_grid.py`.
Open/focused state classes (`sn-icon-closed/open/focused`) take precedence
over hover when both apply (CSS specificity; hover adds to the same element).

## Risks / Trade-offs

- [Gtk.FlowBox lacks drag-reorder] → switch to `Gtk.ListView` for the grid
  mode; this is a significant refactor of `SugarAppGrid`. Mitigation: defer
  drag-reorder to a follow-up change, ship MRU-only ordering first.
- [Global type-to-search may conflict with keybindings] → the key controller
  already handles this: known shortcuts return True, unknown printable chars
  fall through to search. Test with accented characters and IME.
- [OVER_UP/DOWN may feel too simple for a "zoom" metaphor] → acceptable for
  v1; replace with a custom scale animation in a later cycle if feedback says
  it looks cheap.

## Migration Plan

1. Implement dark/light toggle, accent auto-apply, hover tint first
   (delegated to Jules) — these are independent improvements.
2. Refactor `UnifiedHomeView` wrapper, mode switching, OVER_UP/DOWN animation.
3. Add global type-to-search.
4. Add MRU ordering (Gtk.ListView refactor, drag-reorder deferred).
5. Simplify Frame view switcher to one button.
6. Archive `desktop-pie-menu` and `frame-views` changes' implemented parts.

## Open Questions

- Should the Frame keep two view-switcher buttons that zoom in/out instead of
  one button? "Zoom out" / "Zoom in" text labels are clearer than a single
  toggle icon. Ask Sebastian.
- Is MRU + drag-reorder in scope for this change, or deferred? The design
  includes it; the first implementation round may skip drag-reorder.
- Should the radial mode show *only* pinned favorites, or also recent apps
  that aren't pinned (a "recents" ring around the pin circle)? This would make
  the radial mode useful even with zero pinned apps.
