# Sugar Next HIG — Human Interface Guidelines

*A Learning Shell for Everyday Computing*

## Principles

### 1. Collaboration is central

Computing is social, not solitary. The shell makes peers discoverable and
communication effortless — link-local (zero-config, no server, no account)
for the classroom and the home; federated (XMPP) for schools with
infrastructure. Collaboration is not a "feature" of an activity; it is a
property of the environment. Every app can be shared because the shell
provides the substrate.

### 2. Color is meaningful

Color communicates state, not decoration. The shell respects the system
light/dark preference and adds high-contrast control. The active
application's palette may influence the shell's chrome — the frame, the
grid background — so the learner always knows where their attention is.
Profile colors (XO-style) are a future possibility for multi-user
sessions.

### 3. Flow is protected

The shell never interrupts. No prompts, no dialogs, no "did you know"
popups. Reflection is *facilitated*, not forced — the Journal exists to be
consulted, not to notify. The learner decides when to look back.

### 4. Tasks are multi-application

Modern work flows across apps. The Frame shows everything running, not
just "the current activity". The Journal crosses app boundaries: "what was
I working on?" is a question about *state of the system*, not about which
app was in focus.

### 5. Low floor, wide walls, high ceiling

- **Low floor:** an extension is a `.py` file in a folder. No build system,
  no registration, no GObject.
- **Wide walls:** the same hook system powers logging, counting, a SQLite
  journal, and eventually collaborative sharing.
- **High ceiling:** the extension API exposes enough to build real
  tooling. The Journal itself is an extension. There is no privileged
  internal API.

### 6. The environment is malleable

Every part of the shell that can be an extension, should be. Learners who
want to look inside find plain Python files, not compiled binaries. The
shell's behavior is discoverable and changeable by its users.

### 7. Opt-in, never opt-out

Every layer beyond the App Grid is a choice: Journal, collaboration,
favorites sync, activity model. Installing an extension *is* the act of
opting in. The base shell is complete on its own.

## Color system

| Token | Usage |
|-------|-------|
| `--sn-bg` | Shell background (adapts to light/dark) |
| `--sn-bg-alt` | Frame bar, search bar background |
| `--sn-accent` | Active highlight, selection |
| `--sn-text` | Primary text |
| `--sn-text-secondary` | Labels, metadata |
| `--sn-surface` | Card backgrounds (grid cells) |

The shell reads the system `prefers-color-scheme` and sets these tokens
accordingly. Users may override via `~/.config/sugar-next/colors.css`.

## Collaboration model

```
┌─────────────────────────────────────┐
│          Sugar Next Shell           │
│  ┌──────────────────────────────┐   │
│  │  Presence bus (XMPP)         │   │
│  │  ├── link-local (LAN,        │   │
│  │  │   zero-config, no account)│   │
│  │  └── federated (server,      │   │
│  │      cross-network)           │   │
│  └──────────────────────────────┘   │
│  ┌──────────────────────────────┐   │
│  │  Share substrate             │   │
│  │  ├── cursor/share            │   │
│  │  ├── clipboard              │   │
│  │  └── app-level channels     │   │
│  └──────────────────────────────┘   │
└─────────────────────────────────────┘
```

The presence bus is a shell service, not an extension — it needs to be
running for any app to discover peers. The share substrate (cursor, clipboard,
app data channels) is exposed through the extension API so that apps can
opt in to collaboration without coupling to a specific protocol.

## Activity model (reimagined)

An "Activity" in Sugar Next is not a bundle type. It is a *temporal
context*: a named, sharable workspace that can span multiple apps.

Example: a learner is researching birds. They have a browser tab open, a
terminal with a Python script, and a drawing app. They name this context
"Birds". Sugar Next tracks which apps belong to it, can share the whole
context with a peer, and records it in the Journal as a single episode.

This is future work — the extension API must first prove itself before we
design the context layer. But the principle is set: activities are not
apps, they are *agglomerations of apps in time*.
