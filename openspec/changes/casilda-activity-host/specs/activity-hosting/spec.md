# activity-hosting — Delta Spec

## ADDED Requirements

### Requirement: Launched apps embed inside the shell
The shell SHALL host each app it launches as an embedded Wayland client of a
shell-owned Casilda compositor, rendering inside the Sugar Next window. The
launch MUST exec the desktop entry's `Exec=` command line (field codes
stripped) via the compositor's spawn, and MUST NOT use D-Bus activation, so
that the window cannot escape to the host compositor.

#### Scenario: Launching from the Home View embeds the app
- **WHEN** the learner activates an app from the App Grid or the Desktop pie
  menu
- **THEN** the app's window renders inside the Sugar Next window as the
  frontmost activity, and no new toplevel appears on the host desktop

#### Scenario: DBusActivatable app still embeds
- **WHEN** the learner launches an app whose desktop entry declares
  `DBusActivatable=true`
- **THEN** the app is spawned from its `Exec=` line and renders embedded,
  identically to a non-DBusActivatable app

#### Scenario: Identical behavior regardless of host
- **WHEN** the same app is launched with Sugar Next running as a window
  inside another desktop and with Sugar Next running as the only client of a
  bare compositor
- **THEN** the embedded launch behaves identically in both environments

### Requirement: One compositor page per activity
The shell SHALL host each launched activity in its own compositor instance,
presented as one switchable page. Additional toplevels opened by the same
activity (dialogs, secondary windows) SHALL render within that activity's
page.

#### Scenario: Two activities do not share a surface
- **WHEN** two apps are launched in sequence
- **THEN** each renders in its own page; switching pages shows one activity
  at a time, full-size

#### Scenario: A dialog stays with its activity
- **WHEN** an embedded activity opens a secondary window or dialog
- **THEN** it renders inside that activity's page, not as a separate Frame
  entry

### Requirement: Activity lifecycle tracked from compositor events
The shell SHALL derive an activity's running state from its compositor's
toplevel events: running while at least one toplevel is mapped, closed when
the last toplevel closes. On close the shell MUST fire the `on_app_close`
extension hook, remove the activity's Frame entry, and dispose its page. The
shell MUST NOT track activity lifetime via launch PIDs or via host-compositor
window-listing protocols.

#### Scenario: Closing the last window ends the activity
- **WHEN** the learner closes an embedded activity's last window from within
  the app
- **THEN** its Frame entry disappears, `on_app_close` fires with the
  activity's app id, and the page is disposed

#### Scenario: Launch veto hook still applies
- **WHEN** an extension's `on_app_launch` hook returns a cancel result
- **THEN** no process is spawned and no page is created

### Requirement: Named ambient socket for external clients
The shell SHALL listen on a named Wayland socket in `XDG_RUNTIME_DIR` using a
collision-scanned name (`sugar-next-<n>`), attached to an ambient compositor
page. A toplevel from an externally-started client connecting to this socket
SHALL appear in the shell like a launched activity.

#### Scenario: Terminal redirect joins the shell
- **WHEN** a user runs `WAYLAND_DISPLAY=sugar-next-0 <some-wayland-app>` from
  a terminal while the shell is running
- **THEN** the app renders inside Sugar Next and gains a Frame entry while
  its window is open

#### Scenario: Socket name does not collide
- **WHEN** the shell starts and `sugar-next-0` is already taken in
  `XDG_RUNTIME_DIR`
- **THEN** the shell binds the next free `sugar-next-<n>` name instead of
  failing

### Requirement: "Open outside" escape hatch in cooperative mode
When a host desktop session is present, the shell SHALL offer a secondary
per-app launch action that opens the app on the host desktop via
`Gio.AppInfo.launch()` instead of embedding. Escape-hatch windows are not
tracked by the shell and receive no Frame entry; this limitation SHALL be
stated in user-facing documentation. The action SHALL NOT be offered when no
host desktop exists.

#### Scenario: Opening outside hands off to the host
- **WHEN** the learner chooses "Open outside" on an app while Sugar Next runs
  inside another desktop
- **THEN** the app opens as a normal host-desktop window and no Frame entry
  is created

#### Scenario: No escape hatch standalone
- **WHEN** Sugar Next is the session's only shell
- **THEN** the "Open outside" action is not offered
