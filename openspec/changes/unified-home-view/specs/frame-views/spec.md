# frame-views (MODIFIED)

## Requirements

### Requirement: Single Home view accessible from the Frame

The shell SHALL present a single Home view (not separate Desktop/Apps views)
accessed from the Frame. The Frame shows one view button ("Home"). Internal
mode switching between radial (favorites) and grid (all apps) is controlled
by F1/F2 keybindings or a zoom toggle within the Home view itself.

#### Scenario: Frame shows one view button
- **WHEN** the learner opens the Frame (F6 or hot corner)
- **THEN** the view switcher shows a single "Home" button alongside the
  running-windows list and the dark/light toggle button

#### Scenario: Zooming within Home view
- **WHEN** the learner presses F1
- **THEN** the Home view zooms out to radial (favorites) mode
- **WHEN** the learner presses F2
- **THEN** the Home view zooms in to grid (all apps) mode

### Requirement: Dark/light toggle in Frame

The Frame SHALL include a dark/light theme toggle button at its right edge.
The icon SHALL reflect the current theme: `sun-symbolic` when dark mode is
active (click to switch to light), `weather-clear-night-symbolic` when light
mode is active (click to switch to dark).

#### Scenario: Toggling theme from Frame
- **WHEN** the learner clicks the theme toggle button in the Frame
- **THEN** the shell switches between light and dark theme instantly,
  persisted across restarts

### Requirement: Running list from shared registry

The Frame's running-windows list SHALL be sourced from the shared app-state
registry (unchanged from prior spec).

#### Scenario: Running list updates
- **WHEN** an app opens or closes
- **THEN** the Frame's running list updates to match, without maintaining
  its own separate bookkeeping
