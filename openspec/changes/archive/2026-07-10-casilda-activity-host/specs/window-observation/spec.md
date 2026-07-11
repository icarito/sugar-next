# window-observation — Delta Spec

## ADDED Requirements

### Requirement: One event contract for all window state
The shell SHALL track open/close/focus state for windows through exactly
one internal contract (`app_state`: `add_open`, `remove_open`,
`set_focused`), regardless of which adapter supplies the events. The
Frame's running list and the `on_app_close` hook SHALL consume this
contract without branching on which adapter produced an event.

#### Scenario: Frame rendering does not know the active adapter
- **WHEN** a window opens, whether via the GNOME Shell extension adapter
  or the wlr-foreign-toplevel adapter
- **THEN** the Frame's running-list code path is identical; no
  adapter-specific logic runs outside the two adapter modules

### Requirement: Hosted mode uses the GNOME Shell extension adapter
When the shell detects it is running inside a GNOME session, it SHALL
source window events from the `sugar-next-windows` GNOME Shell extension
over D-Bus: window open/close/focus events, and a method to request a
window be focused. The shell SHALL fail loudly (not silently degrade) if
the extension is not installed or fails to respond, per the workspace
standard that environment friction is a bug.

#### Scenario: External window is tracked
- **WHEN** an app is opened from outside Sugar Next (e.g. a terminal) while
  the shell runs hosted inside GNOME
- **THEN** the extension reports the window and it appears in the shell's
  tracked-open state, same as a shell-launched app

### Requirement: External windows get a real Frame entry when resolvable
The shell SHALL, when a window-observation adapter reports a window it
did not launch, attempt to resolve a desktop-entry bundle for it
(matching the window's app id against installed `.desktop` files) and, if
one is found, show it in the Frame's running list exactly as it would a
shell-launched app — same icon, name, and focus/close behavior. Windows
with no resolvable desktop entry SHALL still update icon/open state via
the shared `app_state` contract but SHALL NOT get a Frame entry (nothing
to render a name or icon from).

#### Scenario: Externally-launched app appears in the Frame
- **WHEN** a learner opens a terminal (via the standalone session's
  terminal binding, or a host app in hosted mode) and launches an
  installed app from it
- **THEN** that app appears in the Frame's running list with its real
  icon and name, and clicking it focuses its window — indistinguishable
  from an app the learner launched through the Home View or Apps grid

#### Scenario: Window with no installed desktop entry has no Frame entry
- **WHEN** a window-observation adapter reports a window whose app id
  matches no installed `.desktop` file
- **THEN** the window's open/focus state is still tracked (e.g. for icon
  state elsewhere), but no Frame entry is created for it

#### Scenario: DBusActivatable app close is tracked
- **WHEN** the learner launches a `DBusActivatable=true` app and later
  closes it
- **THEN** the extension's close event fires `on_app_close`, even though
  the pid-watch in `desktop_bundle.py` could not observe this app (pid=0)

#### Scenario: Extension missing fails loudly
- **WHEN** the shell starts inside a GNOME session and the
  `sugar-next-windows` extension is not installed or not enabled
- **THEN** the shell reports a clear, actionable error rather than silently
  running with no window tracking

### Requirement: Standalone mode uses the wlr-foreign-toplevel adapter
The shell SHALL, in standalone mode (no host desktop session present),
source window events from `zwlr_foreign_toplevel_management_unstable_v1`
via the existing `toplevel_tracker.py` client, unmodified from its
pre-existing implementation. This adapter is compositor-generic within the
wlroots family; **Wayfire** is the reference/verified target compositor
for this change.

#### Scenario: Standalone tracks windows natively
- **WHEN** the shell runs as a standalone session's client on Wayfire
- **THEN** window open/close/focus events arrive via the foreign-toplevel
  protocol with no polling and no host-specific IPC

### Requirement: Launch mechanism is unchanged
`Gio.AppInfo.launch()` SHALL remain the sole app-launch mechanism in both
startup modes. The shell SHALL NOT parse or exec desktop-entry `Exec=`
lines directly, and SHALL NOT embed launched apps inside a shell-owned
compositor surface.

#### Scenario: Launching opens a normal window
- **WHEN** the learner activates an app from the App Grid or Desktop pie
  menu
- **THEN** the app opens as an independent window, placed and (in
  standalone mode) tiled by the active compositor — not embedded inside
  the Sugar Next window
