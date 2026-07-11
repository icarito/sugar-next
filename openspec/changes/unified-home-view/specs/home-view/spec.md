# home-view (MODIFIED)

## Requirements

### Requirement: Unified Home View with orthogonal mode and filter axes

The Home View SHALL be a single view governed by two independent axes: a
**mode** (layout) and a **filter** (set). The mode SHALL be one of Spiral
(radial, growing into concentric rings as the icon count grows), Grid (flow
layout), or Free (manual x/y placement). The filter SHALL be one of
Favorites+Active, Favorites, Active, or All. Any mode SHALL be combinable with
any filter.

#### Scenario: Default on start
- **WHEN** the shell starts
- **THEN** the Home View shows Spiral mode with the Favorites+Active filter (the
  union of pinned favorites and currently-open apps), so the view is never
  empty even before anything has been launched

#### Scenario: Mode changes the layout, not the set
- **WHEN** the learner changes the mode while a filter is active
- **THEN** the same filtered set of icons is re-laid-out in the new mode
  (spiral rings, grid flow, or free positions) without changing which icons
  appear

#### Scenario: Filter changes the set, not the layout
- **WHEN** the learner changes the filter while a mode is active
- **THEN** the visible icon set narrows or widens (favorites, active, all, or
  the union) while the current layout mode is preserved

#### Scenario: Spiral grows into rings
- **WHEN** the filtered set has more icons than fit in one ring
- **THEN** Spiral mode arranges them in concentric rings rather than a single
  oversized circle, keeping Spiral + All legible

#### Scenario: Free-mode positions persist
- **WHEN** the learner drags an icon to a position in Free mode and restarts
- **THEN** that icon returns to the placed position; never-placed icons fall
  back to an auto-layout

### Requirement: Mode navigation via scroll or gesture

The Home View SHALL switch between modes via lateral scroll, shift+scroll, or a
touch gesture — NOT via F1/F2 (which are unreachable on laptops whose firmware
maps the F-row to hardware keys). Plain vertical scroll SHALL remain reserved
for scrolling within a grid.

#### Scenario: Scroll switches mode
- **WHEN** the learner performs a lateral scroll or shift+scroll anywhere on
  the shell, including over the Frame
- **THEN** the Home View switches to the adjacent layout mode

#### Scenario: Vertical scroll still scrolls the grid
- **WHEN** the learner scrolls vertically while in Grid mode with more icons
  than fit on screen
- **THEN** the grid scrolls its contents; the mode does not change

### Requirement: Search in the Frame respects the active filter

The search entry SHALL live in the Frame (not inside the app grid). Typing
SHALL filter whichever mode is active, restricted to the active filter's set.

#### Scenario: Searching within the active filter
- **WHEN** the filter is Favorites and the learner types in the Frame search
- **THEN** only favorites matching the search text remain visible; apps outside
  the favorites set are not surfaced by the search

#### Scenario: Widening the search scope
- **WHEN** the learner switches the filter to All and continues searching
- **THEN** the search now matches across all installed apps

### Requirement: Clicking a running app focuses its window

Clicking an app icon in any mode SHALL focus the app's existing window if it is
already open, and launch the app only if it is not.

#### Scenario: Click focuses instead of relaunching
- **WHEN** the learner clicks an app icon whose app is already open
- **THEN** the shell requests focus/raise of the existing window rather than
  starting a second instance

#### Scenario: Click launches when closed
- **WHEN** the learner clicks an app icon whose app is not open
- **THEN** the app launches

### Requirement: Central menu replaces direct Settings popup

The Spiral center button SHALL open a popup menu rather than opening the
Settings panel directly. The menu SHALL contain Settings and a
mode-appropriate exit action: Logout in standalone mode, Close Sugar Next in
hosted mode.

#### Scenario: Central menu in standalone mode
- **WHEN** the learner activates the center button and the shell owns the
  session (standalone)
- **THEN** the menu offers Settings and Logout

#### Scenario: Central menu in hosted mode
- **WHEN** the learner activates the center button and the shell runs inside a
  host GNOME (hosted)
- **THEN** the menu offers Settings and Close Sugar Next (the host session is
  unaffected)

### Requirement: Dark/light theme

The shell SHALL support switching between light and dark theme instantly
without restart. The setting SHALL persist in SettingsStore.

#### Scenario: Switching to dark mode
- **WHEN** the learner toggles dark mode in the Frame
- **THEN** all shell chrome switches to dark theme tokens immediately

### Requirement: Accent color applies instantly

The Settings Color tab SHALL apply the accent color immediately when a swatch
is clicked, without requiring a separate Apply action or hex entry.

#### Scenario: Swatch click applies instantly
- **WHEN** the learner clicks a color swatch in Settings
- **THEN** the accent color changes immediately and is persisted

### Requirement: Icon hover tint

App icons in all modes SHALL brighten and saturate slightly on mouse hover,
with a smooth transition. Open/focused state rendering SHALL take precedence
over the hover tint.

#### Scenario: Hovering over an icon
- **WHEN** the learner hovers the mouse over an app icon
- **THEN** the icon brightens and saturates smoothly over ~150ms
