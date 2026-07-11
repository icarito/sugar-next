# frame-views

## ADDED Requirements

### Requirement: Single Home view accessible from the Frame

The shell SHALL present a single Home view (not separate Desktop/Apps views)
accessed from the Frame. Mode switching within the Home view SHALL be driven by
scroll/gesture (see the home-view spec), NOT by F1/F2 keybindings.

#### Scenario: Frame shows one view
- **WHEN** the learner opens the Frame (hot corner or reveal)
- **THEN** the Frame presents the single Home view alongside the running-windows
  list, the filter selector, the search entry, and the dark/light toggle

#### Scenario: Mode navigation is not on F-keys
- **WHEN** the learner switches Home view modes
- **THEN** it happens via scroll/gesture (including scroll over the Frame), not
  via F1/F2 — which are unreachable on laptops whose firmware maps the F-row to
  hardware keys

### Requirement: Filter selector in the Frame

The Frame SHALL provide a selector for the Home view's filter axis (Favorites+
Active, Favorites, Active, All). The Frame remains a hot-corner/reveal panel; it
is not promoted to a permanent command bar.

#### Scenario: Choosing a filter
- **WHEN** the learner selects a filter value in the Frame
- **THEN** the Home view's visible icon set updates to that filter while the
  current layout mode is preserved

### Requirement: Search entry in the Frame

The Frame SHALL host the search entry (moved out of the app grid). Search
respects the active filter (see the home-view spec).

#### Scenario: Search from the Frame
- **WHEN** the learner types in the Frame's search entry
- **THEN** the active Home view mode filters live within the active filter's set

### Requirement: Dark/light toggle in Frame

The Frame SHALL include a dark/light theme toggle button. The icon SHALL
reflect the current theme: `weather-clear-symbolic` when dark mode is active
(click to switch to light), `weather-clear-night-symbolic` when light mode is
active (click to switch to dark). Both icon names exist in Adwaita; the
previously specified `sun-symbolic` does not and must not be used.

#### Scenario: Toggling theme from Frame
- **WHEN** the learner clicks the theme toggle button in the Frame
- **THEN** the shell switches between light and dark theme instantly, persisted
  across restarts

#### Scenario: Both toggle icons render
- **WHEN** the shell is in either light or dark mode
- **THEN** the toggle shows a valid, visible icon for the opposite mode (no
  missing/broken icon in either state)

### Requirement: Central menu replaces direct Settings popup

The Home view's Spiral center button SHALL open a popup menu (Settings plus a
mode-appropriate exit action) rather than opening the Settings panel directly
(see the home-view spec for the menu contents).

#### Scenario: Center opens a menu
- **WHEN** the learner activates the Spiral center button
- **THEN** a popup menu appears rather than the Settings panel opening directly

### Requirement: Running list from shared registry

The Frame's running-windows list SHALL be sourced from the shared app-state
registry (unchanged from prior spec).

#### Scenario: Running list updates
- **WHEN** an app opens or closes
- **THEN** the Frame's running list updates to match, without maintaining its
  own separate bookkeeping
