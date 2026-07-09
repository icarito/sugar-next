# Sugar Next — Design

*for **A Learning Shell for Everyday Computing***

## Architecture

```
sugar-next/
├── shell/                  # GTK4 shell (replaces jarabe)
│   ├── main.py             # Entry point
│   ├── app-grid.py         # App grid view
│   ├── frame.py            # Universal frame (future)
│   └── extensions/         # Extension loader
├── bundles/                # Bundle types
│   ├── activity-bundle.py  # Sugar activity wrapper
│   └── desktop-bundle.py   # .desktop file wrapper
├── api/                    # Extension API
│   └── hooks.py            # on_app_launch, etc.
├── data/                   # Default config, icons
└── pyproject.toml          # pip-installable package
```

## Stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| Shell | GTK4 + Python (PyGObject) | Community already has GTK4 experience from toolkit-gtk4 |
| Extension API | Python, no GObject needed | Low floor for creators |
| App scanner | XDG Desktop Menu spec | Zero-config, works with any Linux distro |
| Packaging | pip + OCI | Self-contained, any distro; no Nix dependency |
| Compositor | Wayland (host compositor) | No embedded compositor needed — Sugar Next runs as a normal Wayland client |
| Collaboration | XMPP (link-local + federated) | Zero-config LAN discovery + standard server federation; no account required for local use |

## App Grid (Fase 1)

- Simple `Gtk.FlowBox` with category sections
- Icons from `.desktop` files (via `Gio.DesktopAppInfo`)
- Click → `Gio.AppInfo.launch()`
- Search bar at the top
- Future: favorite/star system, activity overlay

## Extension API (Fase 2)

```python
# ~/.local/share/sugar-next/extensions/my-ext.py

def on_app_launch(app_id: str, app_info: Gio.AppInfo) -> None:
    """Called before an app launches."""
    print(f"Launched {app_id}")

def on_shell_start() -> None:
    """Called when the shell starts."""
    pass
```

Minimal, synchronous hooks. No GObject, no decorators, no registration step.

## Frame (Fase 3+)

- Shows all windows (not just Sugar activities)
- Accessed via hot-corner or keybinding
- Per-window palette: "Pin to favorites", "Add to Journal", etc.
- Icons mode first, thumbnails later

**v0 scope note** (decided during implementation): as a normal Wayland
client, the shell cannot enumerate other clients' windows — that needs the
`wlr-foreign-toplevel-management` protocol, which GTK does not expose and
which would add a pywayland dependency and compositor coupling. Frame v0
therefore shows **pinned favorites + apps launched this session** (hot
corner + F6, per-item palette). True universal window listing is future
work, likely its own OpenSpec change — the candidate path is the wlroots
`wlr-foreign-toplevel-management` protocol (via pywayland), which covers
Wayfire/Sway/labwc and other wlroots compositors.

## Design system

- **Light/dark**: respects `prefers-color-scheme`, with user override.
- **High contrast**: shell provides a contrast slider independent of theme.
- **Active app tint**: the shell chrome subtly shifts to echo the focused
  application's icon palette — the learner always knows where their
  attention is without looking away from the content.
- **Tokens**: CSS custom properties (`--sn-bg`, `--sn-accent`, etc.),
  documented in `sugar-next/HIG.md`.

## Activity model (reimagined)

An "Activity" in Sugar Next is not a bundle type. It is a **temporal
context**: a named, sharable workspace that can span multiple apps.
Example: a learner researching birds has a browser tab, a terminal, and a
drawing app open. They name this context "Birds". Sugar Next tracks which
apps belong to it, can share the whole context with a peer, and records it
in the Journal as a single episode.

This is future work — the extension API must first prove itself. But the
principle is set: activities are not apps, they are agglomerations of apps
in time.

## Collaboration (Fase 5)

Collaboration is a property of the environment, not a feature of an
activity. The shell provides a presence bus that any extension or app can
use:

```
Presence bus (XMPP)
├── link-local: zero-config LAN discovery (Avahi/DNS-SD), no account
├── federated: standard XMPP server for cross-network presence
└── Share substrate exposed via extension API:
    ├── cursor/share
    ├── clipboard exchange
    └── app-level data channels (extensions opt in)
```

The presence bus runs as a shell service — it must be active for any peer
discovery. The share substrate is an API that apps call through extensions,
never coupling them to XMPP directly.

## Journal (Fase 4, opt-in)

- Not part of the shell by default
- Extension that subscribes to `on_app_launch` and `on_app_close`
- Explicit publish: user chooses what goes into the Journal
- Backend: SQLite flat file, no D-Bus service

**v0 API** (decided during implementation): the Journal ships as a regular
extension file (`examples/extensions/journal.py`) — installing it *is* the
opt-in. It subscribes to `on_app_launch` and records events into
`~/.local/share/sugar-next/journal.sqlite`, one table:

```sql
CREATE TABLE entries (
    id INTEGER PRIMARY KEY,
    timestamp TEXT NOT NULL,   -- ISO 8601
    app_id TEXT NOT NULL,
    title TEXT NOT NULL,
    kind TEXT NOT NULL         -- 'launch' for now; 'close', 'publish' later
);
```

`on_app_close` and explicit publish need shell support that doesn't exist
yet (process tracking, UI) — deferred with the rest of window management.
A promising richer event source is **Zeitgeist** (the freedesktop activity
log): instead of the shell tracking everything itself, the Journal
extension could subscribe to Zeitgeist events (documents opened, apps
closed) and keep SQLite only as its publish store. To evaluate in the
follow-up change alongside wlroots toplevel tracking.
