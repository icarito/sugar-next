# frame-views — Delta Spec

## MODIFIED Requirements

### Requirement: Views accessible from the Frame

The shell SHALL provide two views — Desktop, Apps — accessible from the
Frame (overlay bar at screen bottom / F6), NOT from Settings. The Frame
SHALL show a view switcher alongside running activities. Running entries
SHALL reflect embedded activity windows, sourced from the shell's own
compositor toplevel events: an entry appears when an activity's first
toplevel maps and disappears when its last toplevel closes. Activating a
running entry SHALL bring that embedded activity's page to the front
inside the shell window.

#### Scenario: Switching from Desktop to Apps view
- **WHEN** the learner presses F6 (Frame) and selects the "Apps" button
- **THEN** the shell switches to the App Grid view. The Frame closes.
  The same view is active next time the Frame is opened.

#### Scenario: Frame shows running activities AND view switcher
- **WHEN** the Frame opens (F6 or hot corner)
- **THEN** it shows: [Desktop] [Apps] buttons on the left, running
  embedded activities on the right. Favorites and Settings live in the
  Desktop pie menu, not the Frame.

#### Scenario: Activating a running entry switches to the activity
- **WHEN** the learner clicks a running activity's Frame entry
- **THEN** the shell shows that activity's embedded page frontmost and the
  Frame closes

#### Scenario: Closed activity leaves the Frame
- **WHEN** an embedded activity's last window closes
- **THEN** its Frame entry disappears without the learner reopening the
  Frame
