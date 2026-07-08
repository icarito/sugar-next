## Purpose

Equip this Sugar workspace with AI-assisted development tooling that
understands GTK4's widget hierarchy, Sugar's shell architecture,
Wayland/Wayfire debugging, and common Sugar development workflows — so
that an AI agent (running in VS Code or CLI) can navigate the codebase
and make correct changes without rediscovering its structure from scratch
each session.

## Requirements

### Requirement: Skills for GTK4 introspection are available to AI agents
The system SHALL provide agent skills that describe GTK4 widget class
hierarchies, how `Gtk.Widget`/`Gtk.Window`/`Gtk.Application` compose, and
how PyGObject's GObject Introspection binding conventions differ from
pure Python libraries.

#### Scenario: Agent identifies correct GTK4 container replacement
- **WHEN** an AI agent is asked to port a `Gtk.EventBox`-wrapping pattern
  from the GTK3 codebase
- **THEN** the skill directs it to use `gtk3compat.Alignment` (if
  centralized) or a direct `Gtk.Box`/`Gtk.Overlay` layout, instead of
  guessing or reverting to a pre-gtk4-port pattern

#### Scenario: Agent distinguishes GTK4 from GTK3 API usage
- **WHEN** an agent reads code calling `pack_start()`, `get_children()`,
  or `Gdk.Screen.width()`
- **THEN** the skill recognizes these as `sugar4.gtk3compat` shims and
  does not treat them as real GTK4 APIs that would imply incorrect
  porting

### Requirement: Skills for Sugar shell navigation are available to AI agents
The system SHALL provide agent skills describing jarabe's architecture:
the Gtk.Application lifecycle (`ShellModel`/`HomeWindow`/`FrameWindow`),
activity launching via `activityfactory`, the Sugar profile/onboarding
flow, and the GTK4 port's relationship to `sugar-toolkit-gtk4`.

#### Scenario: Agent traces the shell startup path
- **WHEN** an agent needs to understand why a window renders as blank
- **THEN** the skill explains `ShellModel.add_window()`'s compositor
  fallback behavior and the `'activate'` signal path through
  `jarabe/main.py`, so the agent can bisect without reading every file

#### Scenario: Agent knows which modules are stubbed vs. real
- **WHEN** an agent encounters `sugar4.ext.clipboard_set_with_data`
- **THEN** the skill points to the `NOT_IMPLEMENTED` stub convention and
  the real GTK4 equivalents (`Gdk.Clipboard`/`Gdk.ContentProvider`)
  documented in the `sugar4-ext-module` spec

### Requirement: Skills for Wayland/Wayfire debugging are available
The system SHALL provide agent skills covering the Wayfire nested-session
setup validated in this workspace, common GTK4-on-Wayland failure modes
(blank surfaces, missing protocols, ABI conflicts), and how to
introspect running Wayland clients.

#### Scenario: Agent debugs a compositor/surface mismatch
- **WHEN** a widget renders as a blank gray box inside nested Wayfire
- **THEN** the skill suggests checking `ShellModel.add_window()`'s child
  replacement logic (the root cause documented in
  `jarabe-gtk4-integration`), D-Bus/`$WAYLAND_DISPLAY` connectivity, and
  whether the widget has a child already set before the compositor
  fallback fires

#### Scenario: Agent interprets Wayland protocol errors
- **WHEN** a GTK4 client logs protocol-level errors or warnings
- **THEN** the skill maps common messages (`xdg_wm_base`, `wl_surface`)
  to likely causes at the Sugar/code level rather than requiring raw
  protocol knowledge

### Requirement: Agent workflows for common Sugar dev tasks are documented
The system SHALL provide workflow definitions for the most common Sugar
development tasks: porting a GTK3 widget to GTK4, adding a new sugar4
toolkit module, debugging jarabe startup failures, and validating changes
in the nested Wayfire session.

#### Scenario: Porting a GTK3 widget to GTK4
- **WHEN** an agent starts a GTK3→GTK4 port
- **THEN** the workflow directs it to: (1) check `gtk3compat` for
  centralized shims, (2) apply direct GTK4 equivalents for one-off
  patterns documented in `sugar4-gtk3compat-module` and
  `jarabe-gtk4-integration` specs, (3) run jarabe in windowed mode to
  visually verify, (4) update `specbook/docs/gtk-porting-standards.md`
  with any new patterns discovered

#### Scenario: Adding a new sugar4 module
- **WHEN** new toolkit functionality is needed
- **THEN** the workflow directs the agent to: (1) add the module under
  `repos/sugar-toolkit-gtk4/src/sugar4/`, (2) write `make test` covering
  it, (3) verify jarabe can import it before any jarabe-side changes, (4)
  update the relevant spec if it introduces new architecture

### Requirement: Tool integration with VS Code is configured
The system SHALL provide a VS Code workspace configuration that registers
the above skills as workspace-level AI context, configures Python
debugging (`debugpy`) against the nested Wayfire session, and surfaces
the task automation commands.

#### Scenario: AI agent context is active in VS Code
- **WHEN** a developer opens this workspace in VS Code with a compatible
  AI extension (Copilot, Cody, Kilo, etc.)
- **THEN** the agent has access to the Sugar skills for GTK4
  introspection, shell navigation, and Wayland debugging as context
  without extra setup

#### Scenario: Debugging jarabe from VS Code
- **WHEN** a developer attaches the VS Code debugger
- **THEN** breakpoints in `sugar-toolkit-gtk4` and `jarabe` source files
  are hit, even when jarabe is running inside the nested Wayfire session
  (Wayland/Wayfire does not block `debugpy`'s local TCP connection)

## Design Decisions

**D1 — Skills are prose documents, not formal grammars.**
Rationale: The existing specs (`jarabe-gtk4-integration`,
`sugar4-ext-module`, etc.) already document the architecture in prose.
Skills should reference and reinforce those specs, not duplicate them in
a machine-parseable format that would drift. The AI agent reads the
skills alongside the specs at session start.

**D2 — Workflows are imperative checklists, not declarative automations.**
Rationale: The most common failure mode for Sugar dev is skipping the
verification step (visual confirmation in nested Wayfire). Workflows
should enforce that step explicitly rather than assuming the agent will
guess to do it.

## Not Yet Implemented

This spec is aspirational. No skills, workflows, or VS Code
configuration exist in the workspace as of 2026-07-08. The existing
specs (`jarabe-gtk4-integration`, `sugar4-ext-module`,
`sugar4-gtk3compat-module`, `windowed-jarabe-mode`,
`nested-wayfire-dev-session`) serve as the knowledge foundation. This
spec defines what agent-accessible tooling should be built on top of
them.
