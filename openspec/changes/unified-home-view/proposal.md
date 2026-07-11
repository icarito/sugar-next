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

A single Home View that *is* both — a zoomable, animatable surface where
favorites sit at the center and the full app catalog fans out on demand —
would make the shell feel like one continuous space rather than two rooms
with a door. The transition between "just favorites" and "everything" becomes
a fluid animation instead of a stack page flip.

Beyond layout: the Home View currently has no built-in search mechanism
beyond the App Grid's SearchEntry. A global "type to search" mode — active
in any view state — means the learner never has to click into a search bar
before typing. And the app ordering (most-recently-used first, with manual
rearrangement) makes the grid feel alive and personal rather than a static
alphabetical catalogue.

## What Changes

- **Unified Home View widget**: a single canvas (`Gtk.Widget` with custom
  drawing / `Gtk.Fixed`-like positioning) that has two *modes* — a compact
  radial mode showing only pinned favorites (current pie menu behavior) and
  an expanded grid mode showing all installed apps, filterable by search. The
  transition between modes is animated (scale/rotate/fade via CSS transitions
  or a brief Cairo animation).
- **Global type-to-search**: any keypress that is not a keybinding shortcut
  activates search. The Frame / Home View enters a search overlay that filters
  apps in real time regardless of which mode is active. No explicit search bar
  click needed.
- **MRU + manual ordering**: the app grid orders by most-recently-used, with
  drag-to-reorder. Pinned favorites are always first.
- **Dark/light toggle in Frame** (moved from Jules task to spec): a single
  button in the Frame toggles between light and dark theme, instantly.
- **Accent color applies immediately** (moved from Jules task to spec):
  swatch click = instant apply, no hex entry, no Apply button.
- **Icon hover tint** (moved from Jules task to spec): icons brighten/saturate
  on mouse hover in both radial and grid modes.

## Capabilities

### New Capabilities

- `unified-home-view`: the Home View becomes a single zoomable surface with
  radial (favorites) and grid (all apps) modes, animated transitions, global
  type-to-search, MRU ordering with manual drag-reorder.

### Modified Capabilities

- `frame-views`: the view switcher simplifies to one view ("Home") with a
  zoom toggle inside the view itself rather than two separate frame buttons.
  The Frame keeps the toggle button in its bar but removes the [Desktop]
  [Apps] switcher — or keeps them as "Zoom out" / "Zoom in" actions.
- `home-view`: adds dark/light toggle, accent swatch auto-apply, icon hover
  tint. Removes hex entry and Apply button from color picker.
- `semantic-color-system`: adds the dark/light theme token set toggle.

## Impact

- `sugar-next/sugar_next/shell/pie_menu.py` — becomes the radial-mode
  rendering of the unified view, or is subsumed into a new widget.
- `sugar-next/sugar_next/shell/app_grid.py` — becomes the grid-mode rendering
  of the unified view, or is subsumed.
- `sugar-next/sugar_next/shell/home_view.py` — gains mode switching, search
  overlay, animation logic, MRU tracking.
- `sugar-next/sugar_next/shell/frame.py` — view switcher simplified; dark/light
  toggle button added.
- `sugar-next/sugar_next/shell/main.py` — passes dark/light toggle callback,
  connects global keypress-to-search.
- `sugar-next/sugar_next/shell/settings.py` — color picker loses hex entry and
  Apply button; accent swatches apply immediately.
- `sugar-next/sugar_next/shell/settings_store.py` — adds `dark_mode` boolean
  default, MRU order list.
- `sugar-next/sugar_next/shell/theme.py` — adds dark/light token set switching.
