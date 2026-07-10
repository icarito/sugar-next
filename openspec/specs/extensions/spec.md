## Purpose

Define the Sugar Next extension system's non-Python language backends and
the launch-cancel hook return contract. The full extension contract
(hooks, lifecycle, error isolation, enable/disable) and the in-process
Python backend are documented separately in the
`sugar-next-views-and-backends` change's `extension-contract.md`; this
spec covers the requirements introduced by that change.

## Requirements

### Requirement: Non-Python language backends

The shell SHALL be able to load extensions written in languages other than
Python by running them as subprocesses that speak a line-delimited JSON
protocol over stdin/stdout, so the extension language is decoupled from the
shell. Python remains the in-process primary backend.

#### Scenario: gjs extension receives a hook event
- **WHEN** a JavaScript extension is installed and the shell fires a hook
  (e.g. `on_app_launch`)
- **THEN** the shell spawns the gjs backend and delivers the event as one
  JSON object per line on the extension's stdin, and reads its
  acknowledgement (`{"ok": true}`) or error (`{"error": "..."}`) from stdout

#### Scenario: A broken subprocess extension is isolated
- **WHEN** a subprocess extension crashes or emits an `{"error": ...}`
  response
- **THEN** the shell logs it and continues with the next extension; no
  other extension and no shell function is affected

### Requirement: Launch-cancel return contract

A hook fired before an application launch (`on_app_launch`) SHALL be able to
cancel that launch by returning `{"cancel": true}`. Extensions that return
nothing keep the launch proceeding, preserving backward compatibility.

#### Scenario: Extension cancels a launch
- **WHEN** an `on_app_launch` hook returns `{"cancel": true}`
- **THEN** the shell does not launch the application

#### Scenario: Silent extension does not affect launches
- **WHEN** an `on_app_launch` hook returns nothing
- **THEN** the application launches normally
