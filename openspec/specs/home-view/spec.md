## Purpose

Define the Sugar Next Home View — its Settings panel, color/theming model,
and desktop-environment citizenship (XDG paths and FreeDesktop
integration) — so the shell's presentation layer is configurable,
themeable, and a well-behaved Linux desktop citizen. View selection
(Desktop, Apps, Search) is defined in the `frame-views` capability, not
here.

## Requirements

### Requirement: Settings panel
The shell SHALL provide a Settings panel accessible from the Frame or a
keybinding, exposing background image, accent color, contrast, icon size,
and extension management controls.

#### Scenario: Changing accent color
- **WHEN** the learner picks a new accent color in Settings
- **THEN** the shell chrome updates to use that color without restarting

### Requirement: Color token system
The shell SHALL define its chrome colors as `--sn-*` CSS custom
properties set from the system `prefers-color-scheme`, and SHALL allow
user overrides via `~/.config/sugar-next/colors.css` or the Settings
panel.

#### Scenario: User override file present
- **WHEN** `~/.config/sugar-next/colors.css` exists and defines `--sn-accent`
- **THEN** the shell uses that value instead of the computed default

### Requirement: Active-app palette tint
The shell chrome SHALL subtly tint toward the focused application's icon
palette, falling back to the static accent color when a dominant color
cannot be determined.

#### Scenario: Focus changes
- **WHEN** the learner focuses a different application window
- **THEN** the Frame and Home View background tint shift toward that
  app's icon color within a short, unobtrusive transition

### Requirement: XDG Base Directory compliance
The shell SHALL store configuration under `~/.config/sugar-next/` and
data under `~/.local/share/sugar-next/`, per the XDG Base Directory
specification.

#### Scenario: Fresh install
- **WHEN** the shell starts with no existing config or data directories
- **THEN** it creates them under the XDG-specified paths, not elsewhere

### Requirement: FreeDesktop desktop citizenship
The shell SHALL register the `org.sugarlabs.SugarNext` D-Bus name,
associate MIME types with Journal entries, and expose a
StatusNotifierItem for background services.

#### Scenario: Background service running
- **WHEN** a background service (e.g. presence bus) is active
- **THEN** a StatusNotifierItem icon is visible in the system tray
