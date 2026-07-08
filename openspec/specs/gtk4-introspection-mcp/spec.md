## Purpose

Provide MCP (Model Context Protocol) servers that give AI agents
programmatic access to GTK4/GObject widget class hierarchies,
GObject Introspection documentation for Python `gi.repository` usage,
a live D-Bus-accessible widget tree inspector, GTK CSS theme inspection,
and runtime widget state snapshots — all specific to the Sugar GTK4
codebase.

## Requirements

### Requirement: GTK4/GObject class hierarchy browser MCP
The system SHALL provide an MCP server that exposes the GTK4 and GObject
class hierarchy (class → parent → interfaces → properties → signals) so
an AI agent can look up API surface without leaving the editing context
to browse `developer.gnome.org`.

#### Scenario: Agent queries a widget's inheritance chain
- **WHEN** an agent needs to know what `Gtk.Window` inherits and what
  properties its parent chain adds
- **THEN** the MCP returns `Gtk.Window : Gtk.Widget : GObject.InitiallyUnowned
  : GObject.Object`, listing each class's key properties (`default-width`,
  `child`, `title`, etc.) and whether they're construct-only, readable,
  writable

#### Scenario: Agent discovers available signals
- **WHEN** an agent needs to know what signals a `Gtk.Button` emits
- **THEN** the MCP returns `clicked`, `activate`, `toggled` (if
  `Gtk.ToggleButton`) with their parameter signatures, distinguishing
  inherited from class-native signals

#### Scenario: Agent validates API existence before suggesting code
- **WHEN** an agent is about to suggest `widget.set_type_hint(...)` and
  the spec mentions `Gdk.WindowTypeHint`
- **THEN** the MCP confirms that `set_type_hint` does not exist in GTK4's
  `Gtk.Window` (removed; `Gdk.Toplevel` replaces it with a different API)
  so the agent can correct its suggestion before proposing broken code

### Requirement: Python GI (GObject Introspection) doc generator MCP
The system SHALL provide an MCP server that generates Python-specific
documentation for `gi.repository` modules, mapping C/GObject type
information to idiomatic PyGObject usage patterns.

#### Scenario: Agent gets Python-callable API for a GI module
- **WHEN** an agent queries `gi.repository.Gtk` for a specific class
- **THEN** the MCP returns Python constructor signatures, keyword
  arguments (mapped from GObject properties), method names (with
  underscore-to-dash conversion), and any Python-specific overrides
  documented by PyGObject's `.override` files

#### Scenario: Agent discovers GObject property Python naming
- **WHEN** an agent queries the `margin-start` GObject property
- **THEN** the MCP returns that it's accessible in Python as both
  `widget.props.margin_start` (attribute) and
  `widget.set_margin_start(...)` (setter), with the type (int or None)
  and default value

### Requirement: GDK/GTK widget tree inspector over D-Bus
The system SHALL provide a D-Bus-accessible inspector (GTK4's built-in
Inspector exposed via `GTK_DEBUG=interactive` over D-Bus, or an MCP
wrapper around it) that lets an AI agent query the live widget tree of a
running Sugar process.

#### Scenario: Agent inspects live widget hierarchy
- **WHEN** jarabe is running in windowed mode inside nested Wayfire
- **THEN** the agent can request the widget tree (window → containers →
  leaf widgets) with each widget's type, GObject name (if set), CSS
  classes, and size allocation, without needing a human to open the GTK
  Inspector UI

#### Scenario: Agent finds a specific widget by role or property
- **WHEN** an agent needs to locate the button that triggers activity
  launching
- **THEN** the inspector MCP can search the widget tree by type name or
  property value (e.g., "label == 'Start new'") and return the widget
  path from the root `Gtk.ApplicationWindow` down to the match

### Requirement: CSS inspector for GTK themes
The system SHALL provide an MCP server that exposes the GTK CSS
stylesheet applied to a running Sugar widget, including resolved
property values (accounting for CSS cascade, specificity, and
inheritance), so an agent can debug visual styling issues.

#### Scenario: Agent queries resolved CSS on a widget
- **WHEN** a widget renders with unexpected sizing or color
- **THEN** the CSS inspector MCP returns the resolved values for
  `min-width`, `min-height`, `margin`, `padding`, `background-color`,
  `font-size`, etc. from the active GTK theme, with source rule origin
  (theme CSS, user CSS, inline style, default)

#### Scenario: Agent discovers CSS classes available for a widget type
- **WHEN** an agent wants to apply Sugar-themed styling to a custom
  widget
- **THEN** the CSS inspector MCP lists all CSS node names and style
  classes exposed by that widget type in GTK4's CSS node tree (e.g.,
  `GtkButton` exposes `button`, with `.suggested-action`,
  `.destructive-action`, `.flat`, etc.)

### Requirement: Runtime widget state snapshotter
The system SHALL provide an MCP server that can capture a serialized
snapshot of a running Sugar widget or window: its geometry, visibility
state, child layout, CSS state, and property values, in a diffable format
useful for regression testing.

#### Scenario: Agent snapshots before/after a code change
- **WHEN** an agent modifies jarabe widget layout code
- **THEN** it can capture a widget-state snapshot before and after the
  change, diff them, and confirm only the intended properties changed
  (e.g., window size changed, but no child widgets disappeared)

#### Scenario: Snapshot is JSON-serializable and diffable
- **WHEN** a snapshot is taken
- **THEN** the output is valid JSON with deterministic key ordering, so a
  standard `diff` tool can show exactly what changed between two runs

## Design Decisions

**D1 — MCP servers are Python processes, not in-process imports.**
Rationale: GTK4's main-loop ownership and PyGObject's singleton GObject
type system mean that a process can only talk to one GI repository at a
time without potential state corruption. MCP servers run as subprocesses,
each with its own GTK context, communicating over stdio (the MCP protocol
transport). The widget-inspector and CSS-inspector MCPs run against the
running jarabe process via D-Bus, not by importing jarabe's modules.

**D2 — GTK Inspector over D-Bus is preferred to custom C extensions.**
Rationale: GTK4 already ships `libgtk-4.so` with a D-Bus inspector
interface (`GTK_DEBUG=interactive`). Wrapping that in an MCP avoids
maintaining a custom C extension that would need to track GTK4's internal
struct layouts across versions. If the D-Bus interface proves
insufficient, the fallback is a PyGObject-based inspector that imports
from the target process's own `gi.repository.Gtk` (same version,
matching ABI).

**D3 — No Sugar theme redesign in this spec.**
Rationale: The `nested-wayfire-dev-session` and `jarabe-gtk4-integration`
specs already note that no Sugar GTK4 theme exists. The CSS inspector
described here is for reading/discovering the current (empty or Adwaita)
theme applied to widgets, not for creating a new theme. Theme creation is
a separate spec.

## Not Yet Implemented

This spec is aspirational. No MCP servers exist in the workspace as of
2026-07-08. Dependencies to investigate include: the GTK4 D-Bus inspector
protocol (is it stable enough to wrap?), PyGObject's introspection
repository query APIs (`gi.Repository`), and whether `Gtk.Widget`'s
`get_state_flags()` / `get_style_context()` provide enough CSS-resolved
value access for the CSS inspector without needing libadwaita or custom C
code.
