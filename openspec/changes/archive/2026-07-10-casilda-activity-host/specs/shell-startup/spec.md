# shell-startup — Delta Spec

## ADDED Requirements

### Requirement: Exactly two startup modes
The shell SHALL support exactly two ways to start: **hosted** — launched as
a windowed application inside a GNOME session — and **standalone** —
launched as a client of a dedicated tiling Wayland session (Wayfire is the
reference compositor). Mode SHALL be detected by probing the compositor
actually serving the current Wayland connection for the
`zwlr_foreign_toplevel_manager_v1` protocol (present means standalone;
absent means hosted), not by reading an inherited environment variable —
with no mode-selection flags required. The shell's own layout, view
logic, and Frame behavior SHALL be identical in both modes; only the
window-observation adapter (see the `window-observation` spec) differs.

#### Scenario: Hosted launch from GNOME
- **WHEN** the user launches Sugar Next from a GNOME session via its
  desktop entry or `python -m sugar_next.shell.main`
- **THEN** the shell runs as a normal window, and the GNOME Shell
  extension adapter is active with no additional setup, nested compositor,
  or flags required

#### Scenario: Standalone session launch
- **WHEN** Sugar Next starts as a Wayfire session's shell client
- **THEN** it runs as a normal tiled client with the
  wlr-foreign-toplevel adapter active, behaving identically to hosted mode
  apart from adapter selection

### Requirement: No nested-compositor dev indirection
The shell SHALL NOT require or support running inside a nested compositor
(e.g. Wayfire-in-a-window, Hyprland-in-a-window) as a development mode. The
hosted mode inside GNOME is the primary development and window-management
verification environment; the standalone mode is exercised directly against
its target compositor (Wayfire).

#### Scenario: No nested Wayfire/Hyprland dev runner
- **WHEN** a developer sets up this project via `bootstrap.sh`
- **THEN** no nested-compositor runner script is installed, configured, or
  required to iterate on shell code

### Requirement: bootstrap.sh prepares the detected mode fully
`bootstrap.sh` SHALL detect the environment it runs in and leave that mode
fully ready with no manual follow-up: installing/enabling the GNOME Shell
extension when a GNOME session is detected, or pointing to the standalone
session template when it is not. It SHALL fail loudly with an actionable
message if a required piece (extension install, D-Bus interface) cannot be
set up automatically — per the workspace standard that environment
friction is a bug.

#### Scenario: Bootstrap on a GNOME dev machine
- **WHEN** `bootstrap.sh` runs on a machine with a GNOME session available
- **THEN** the GNOME Shell extension is installed/enabled as part of
  bootstrap, and no further manual step is needed before window tracking
  works

#### Scenario: Bootstrap failure is actionable
- **WHEN** `bootstrap.sh` cannot install or enable the GNOME Shell
  extension (e.g. unsupported GNOME Shell version)
- **THEN** it prints a clear, specific error identifying what failed and
  what to do, rather than silently continuing with no window tracking
