# frame-views — Delta Spec

## MODIFIED Requirements

### Requirement: Views accessible from the Frame

The shell SHALL provide two views — Desktop, Apps — accessible from the
Frame (overlay bar at screen bottom / F6), NOT from Settings. The Frame
SHALL show a view switcher alongside running activities. Running entries
SHALL reflect real window state, sourced from the active window-observation
adapter (GNOME Shell extension in hosted mode, wlr-foreign-toplevel in
standalone mode — see the `window-observation` spec) via the shared
`app_state` contract: an entry appears when a window for that app opens
and disappears when its last window closes. Activating a running entry
SHALL ask the active adapter to focus that window on the host or session
compositor.

#### Scenario: Switching from Desktop to Apps view
- **WHEN** the learner presses F6 (Frame) and selects the "Apps" button
- **THEN** the shell switches to the App Grid view. The Frame closes.
  The same view is active next time the Frame is opened.

#### Scenario: Frame shows running activities AND view switcher
- **WHEN** the Frame opens (F6 or hot corner)
- **THEN** it shows: [Desktop] [Apps] buttons on the left, running
  activities on the right, sourced from the active adapter. Favorites and
  Settings live in the Desktop pie menu, not the Frame.

#### Scenario: Activating a running entry focuses the window
- **WHEN** the learner clicks a running activity's Frame entry
- **THEN** the shell asks the active adapter to focus that window (Mutter
  activation in hosted mode, the compositor's focus mechanism in
  standalone mode) and the Frame closes

#### Scenario: Closed activity leaves the Frame
- **WHEN** a tracked window's last instance closes
- **THEN** its Frame entry disappears without the learner reopening the
  Frame
