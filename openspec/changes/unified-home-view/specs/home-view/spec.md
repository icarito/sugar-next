# home-view (MODIFIED)

## Requirements

### Requirement: Unified Home View with radial and grid modes

The Home View SHALL be a single view with two visual modes: a radial mode
showing pinned favorites arranged in a circle, and a grid mode showing all
installed applications in a scrollable grid. The transition between modes
SHALL be animated (slide up/down).

#### Scenario: Starting in radial mode
- **WHEN** the shell starts
- **THEN** the Home View shows pinned favorites in radial (pie menu) mode

#### Scenario: Switching to grid mode
- **WHEN** the learner presses F2 or clicks the zoom toggle
- **THEN** the view animates from radial to grid mode with a slide-up
  transition; all installed apps are visible

#### Scenario: Switching back to radial mode
- **WHEN** the learner presses F1 or clicks the zoom toggle again
- **THEN** the view animates from grid back to radial mode with a
  slide-down transition

### Requirement: Global type-to-search

Any printable character keypress that does not match a keyboard shortcut
SHALL activate a search overlay on the Home View. The search overlay filters
both radial and grid modes in real time. Escape or focus-loss dismisses the
overlay.

#### Scenario: Typing on Desktop activates search
- **WHEN** the learner presses a letter key while viewing the radial
  (favorites) mode
- **THEN** a search bar appears at the top of the Home View with that letter
  entered; non-matching petals are hidden

#### Scenario: Search persists across mode switch
- **WHEN** the learner has a search active in radial mode and switches to
  grid mode
- **THEN** the same search string and filter apply in grid mode

#### Scenario: Dismissing search
- **WHEN** the learner presses Escape or clicks outside the search bar
- **THEN** the search overlay is dismissed and all items become visible again

### Requirement: MRU ordering with pinned-at-top

The app grid SHALL order installed apps by most-recently-used, with pinned
favorites always appearing first. Never-launched apps appear in alphabetical
order after MRU apps.

#### Scenario: Launching an app moves it to top
- **WHEN** the learner launches an app from any view
- **THEN** that app moves to the top of the MRU list (right after pinned
  favorites)

#### Scenario: First launch order
- **WHEN** the learner opens the app grid for the first time with no history
- **THEN** pinned favorites appear first, followed by all other apps in
  alphabetical order

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

App icons in both radial and grid modes SHALL brighten and saturate slightly
on mouse hover, with a smooth transition.

#### Scenario: Hovering over an icon
- **WHEN** the learner hovers the mouse over an app icon
- **THEN** the icon brightens and saturates smoothly over ~150ms
