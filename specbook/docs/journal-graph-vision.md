# Journal & Knowledge-Graph — Design North Star

Direction, not a committed change. This captures the constructionist thinking
behind a future Journal for Sugar Next so it is not lost between sessions. When
this becomes real work it will be one or more OpenSpec changes; nothing here is
a spec yet. The launcher surface (Home View) is tracked separately in the
`unified-home-view` change — this document is about the *object* model, not the
*app* model.

## Why a Journal, and why a graph

Sugar classic had two worlds: the Home/launcher ("what can I do?" — activities
as verbs) and the Journal ("what have I done?" — objects/sessions as nouns).
The Journal was radically constructionist in intent: **there are no files,
there is activity.** You did not open "a .odt", you resumed "that time you
wrote the story." The object carried its own history — versions, who you
collaborated with, snapshots of the process. That is Papert: knowledge as
something you build and reflect on, not documents inert in folders.

But the classic Journal had an internal betrayal: **it was a flat, chronological
list.** Constructionism is not chronological — it is *relational*. Ideas are
built by connecting to other ideas. A volcano project connects a drawing, a
text, a photo, a Scratch game, a conversation. That is a **graph**, not a
timeline. The flat Journal flattened exactly the structure that made the
learning meaningful.

So "graph of nodes" means: *let the learner see and build the connections
between their objects of knowledge, not just scroll a list of when they touched
them.*

## Decisions taken in exploration

These were reasoned through with Sebastian. They are commitments of *direction*,
to be honored (or deliberately revisited) when the work starts.

### The object model is hybrid: bytes in files, relations in the graph

The **bytes** live in real files (`drawing.png` is a real PNG — any tool opens,
sends, backs it up). The **relations and history** live in the graph (what
connects to what, with whom, when). Neither layer is secondary: a file without
the graph loses meaning; the graph without the file loses content.

This is the constructionist distinction made concrete. A LEGO brick is bytes;
the knowledge is in *how you connected it to the others*. The file is the
brick, the graph is the construction. Separating them is fidelity to Papert,
not merely a technical compromise.

### The graph is always backend; the interface is faceted

The learner **never sees a node-and-edge web.** A force-directed graph is
faithful to the data structure and alien to an 8-year-old's mind, which thinks
in places, things, and time. The graph feeds the relations underneath; the
surface speaks the child's language: views faceted by time, by theme, by
person, by activity — with clusters that *emerge* when things belong together.

Note the symmetry with the Home View: filtering apps by favorites/active/all is
the same mental pattern as faceting objects by time/theme/person/activity — a
body of things, axes to slice by, a layout. The Journal is not a new interface;
it is the Home View's surface switched to the object lens.

### Layers are switchable: Apps ↔ Journal ↔ Files

The same surface projects three lenses: the app launcher, the Journal (objects,
graph-backed, for the learner), and a files view (for interop). The same object
is two projections — the graph is the truth for *learning*, the filesystem is
the truth for *interoperating*, and neither is "the real one." This honors HIG
#9 ("opt-in, never opt-out"): the Journal is a layer the learner opts into, not
a mode forced on them.

### Sugar observes the filesystem; it does not own it (Level 2)

Sugar watches the filesystem (`GFileMonitor`/inotify) and keeps the graph
current when things move/rename/delete *outside* Sugar. Sugar does not modify
the file manager and is not coupled to Nautilus's extension API — so it works
with Dolphin, the terminal, git, whatever. This honors HIG #8 ("the environment
is malleable"): the system accompanies the learner, it does not cage them. The
rejected alternatives were Level 1 (import/export bridges only — accumulates
broken references) and Level 3 (a plugin *inside* Nautilus — ties the learner to
Nautilus specifically).

### Start from folders; the indexer comes later

- **For now**: the graph *is* the folder hierarchy the user already builds. A
  folder (`~/volcan/` with drawing + text + photo inside) is already a
  collection node — a deliberate edge the user constructed by hand. No database,
  no tags, no indexer. Portable, zero-fragile, observable with `GFileMonitor`.
  This starts the graph 100% *deliberate* (user-authored relations), which is
  the constructionist-correct starting point: begin with what the learner
  built, not what a machine inferred.
- **Eventually**: an indexer (Zeitgeist / tinysparql, already present on the
  system) adds *automatic* edges — "used in the same session", "opened one after
  another", "same collaborator present", "same activity produced them". These
  feed the navigation facets (time/person/activity). Automatic edges are
  *received* knowledge (help the learner *re-find*); deliberate edges are
  *constructed* knowledge (the learner authors *meaning*). Memory vs. authorship.

### Tags are deferred (Nautilus does not really have them)

Modern Nautilus offers no arbitrary user tags — only "starred" + emblems, stored
in a private binary GVfs metadata store (not portable, lost on copy). Portable
tags (`xattr user.xdg.tags`, a freedesktop standard) exist but Nautilus neither
reads nor writes them. Rather than promise something the desktop does not
deliver today, the "for now" leans **only on folders**; tags (and automatic
edges) wait for the indexer era.

## How this rests on what already exists

- **The hook system is already the graph substrate.** `on_app_launch`,
  `on_app_close`, `on_peer_join`, `on_peer_leave` (in
  `sugar_next/api/hooks.py`) already capture the activity and *collaboration*
  dimensions. HIG #7 says it outright: "the same hook system powers logging,
  counting, a SQLite journal, and eventually collaborative sharing" — and "the
  Journal itself is an extension." The Journal-as-extension listening to hooks
  and reading folders *is* the Journal lens; the mechanism exists, the extension
  is what remains to be written.
- **The gap** is an *object/file* event, not just an *activity* event: something
  (a new hook like `on_object_saved(uri)`, or the Level-2 `GFileMonitor`) that
  tells the graph when files are born, change, or move. That is the link between
  the existing hook system and the hybrid graph.

## Constraints inherited from the HIG

- **Reflection is facilitated, not forced** (HIG #5). The graph is *consulted*,
  never a notification or a feed. No "look what you did today!" — it waits in
  silence until the learner decides to look back. The reflection belongs to the
  learner, not to the system pushing it.
- **Tasks are multi-application** (HIG #6). "What was I working on?" is a
  question about the *state of the system over time*, not which app was focused
  — which is exactly what an indexer like Zeitgeist answers.

## Open threads (not yet decided)

- What a "node" looks like to the learner in each facet, and how navigation
  moves between facets.
- Whether the Journal lens fully replaces or coexists with the app Home View on
  the same surface.
- How deliberate collections (learner-named projects) are created and named
  without breaking flow.
- The exact shape of the object/file event that keeps the graph in sync.
