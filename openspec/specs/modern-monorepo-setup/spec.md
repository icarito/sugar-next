## Purpose

Define a modern, reproducible monorepo workspace for Sugar GTK4
development that integrates `sugar-toolkit-gtk4`, jarabe (`sugar/gtk4-port`),
and potentially other Sugar repositories under a single root with shared
dev tooling — replacing the current ad-hoc setup where each repo has
inconsistent Python environments, build systems, and documentation
standards.

## Requirements

### Requirement: Nix flake provides a reproducible dev environment
The system SHALL provide a `flake.nix` at the workspace root that
declares all system dependencies (wlroots, GTK4, Meson, Ninja,
gobject-introspection, PyGObject, Wayland/Wayfire, D-Bus dev libs) and
produces a reproducible development shell with the correct `GI_TYPELIB_PATH`,
`LD_LIBRARY_PATH`, `PYTHONPATH`, and `PATH` set.

#### Scenario: Developer enters the dev shell in one command
- **WHEN** a developer runs `nix develop` (or `direnv allow` with the
  included `.envrc`) at the workspace root
- **THEN** they get a shell where `python3 -c "import gi; gi.require_version('Gtk', '4.0'); from gi.repository import Gtk"` succeeds,
  `meson setup _build repos/casilda` works, `make test` in
  `repos/sugar-toolkit-gtk4` passes, and `wayfire` runs nested

#### Scenario: Flake pins exact dependency versions
- **WHEN** the flake is evaluated on any machine with Nix installed
- **THEN** it produces the same versions of wlroots (0.20.x), GTK4
  (4.22.x), Meson, and Python packages that were validated in this
  workspace, regardless of what the host distro provides

#### Scenario: Flake coexists with non-Nix workflows
- **WHEN** a developer prefers not to use Nix
- **THEN** the flake's `flake.nix`, `flake.lock`, and `.envrc` are
  optional — the documented distro-package procedure (from
  `specbook/docs/gtk-porting-standards.md`) remains valid and is not
  gated on Nix

### Requirement: VS Code workspace configuration
The system SHALL provide a `.vscode/` directory at the workspace root
with Python debugger configuration (`launch.json`), shared editor
settings (`settings.json` matching the project's Python conventions), and
recommended extensions (`extensions.json`).

#### Scenario: Debug jarabe with one click
- **WHEN** a developer selects "Debug: jarabe (windowed)" from the VS Code
  Run and Debug dropdown
- **THEN** `debugpy` attaches to a launched jarabe process inside nested
  Wayfire, breakpoints in both `sugar-toolkit-gtk4` and `jarabe` source
  files are hit, and `justMyCode: false` is configured so stepping into
  `sugar4`/`gi` modules works

#### Scenario: Shared Python settings across repos
- **WHEN** a developer opens any Python file in `repos/sugar-toolkit-gtk4/`
  or `repos/sugar/`
- **THEN** VS Code uses the same formatter (ruff), type checker (mypy), and
  Python interpreter (workspace venv or Nix shell's Python) without
  per-repo configuration drift

#### Scenario: Recommended extensions are surfaced
- **WHEN** a developer opens this workspace in VS Code for the first time
- **THEN** VS Code prompts to install the recommended extensions (Python,
  Pylance, Nix IDE if the flake is present, and any Sugar-specific
  extensions if they exist)

### Requirement: Python tooling is standardized across repos
The system SHALL standardize Python tooling across `sugar-toolkit-gtk4`
and `sugar` (jarabe) to use the same linter (ruff), type checker (mypy
with identical strictness settings), test runner (pytest), and debugger
(debugpy).

#### Scenario: Linting is consistent
- **WHEN** a developer runs `make lint` in either repo
- **THEN** the same ruff configuration applies (line length, rule set,
  exclusions), producing consistent results regardless of which repo the
  file lives in

#### Scenario: Type checking catches cross-repo breaks
- **WHEN** a change in `sugar-toolkit-gtk4` removes or renames a public
  API that jarabe imports
- **THEN** `make typecheck` in `repos/sugar/` (if configured to include
  `sugar4` types) catches the break before the dev runs jarabe
  interactively

#### Scenario: Tests run the same way everywhere
- **WHEN** a developer runs `make test` in either repo
- **THEN** it invokes `pytest` with the same invocation pattern, coverage
  threshold (if any), and report format

### Requirement: Task automation provides consistent entry points
The system SHALL provide a root-level `Makefile` (or equivalent task
runner) that dispatches to per-repo targets, so a developer can work
without remembering which repo a given command lives in.

#### Scenario: Build everything from root
- **WHEN** a developer runs `make build` at the workspace root
- **THEN** it builds `sugar-toolkit-gtk4` (`pip install -e .`), Casilda
  (if present), and any other repo with a build step — or reports which
  repos are not cloned/present

#### Scenario: Run full test suite from root
- **WHEN** a developer runs `make test` at the workspace root
- **THEN** it runs `make test` in each repo that has a `Makefile` test
  target, aggregates results, and reports per-repo pass/fail and total
  failures

#### Scenario: Launch jarabe in windowed mode from root
- **WHEN** a developer runs `make run-jarabe-windowed` at the workspace
  root
- **THEN** it sets the documented environment variables
  (`JARABE_WINDOWED=1`, `PYTHONPATH`, `GI_TYPELIB_PATH`,
  `LD_LIBRARY_PATH`), starts Wayfire nested (if not already running),
  and runs jarabe — regardless of the developer's current working
  directory

### Requirement: Multi-repo coordination supports cross-repo changes
The system SHALL support a workflow where a change to
`sugar-toolkit-gtk4` (e.g., a new `sugar4` module) can be developed and
tested alongside jarabe changes that consume it, without requiring the
toolkit change to be published to PyPI first.

#### Scenario: Editable install of toolkit visible to jarabe
- **WHEN** jarabe imports from `sugar4.something_new`
- **THEN** the `PYTHONPATH` configured by the workspace environment
  (Nix shell, Makefile, VS Code launch config) includes
  `repos/sugar-toolkit-gtk4/src/` so the editable install is always used
  — jarabe sees the live source, not a stale pip-installed copy

#### Scenario: Toolkit test run does not break jarabe
- **WHEN** `make test` runs in `sugar-toolkit-gtk4`
- **THEN** it does not import jarabe or mutate global state that would
  affect jarabe's behavior — the two repos are coupled at the
  `PYTHONPATH` level but their test suites are independent

#### Scenario: Cross-repo change is documented for future archeologists
- **WHEN** a change spans both `sugar-toolkit-gtk4` and `sugar`
- **THEN** the change's OpenSpec proposal, design, and tasks explicitly
  list both repos, which files are touched in each, and why the change
  must be atomic (could not be split into two independent changes)

## Design Decisions

**D1 — Nix flake is opt-in, not mandatory.**
Rationale: Many Sugar contributors will never install Nix. The flake
exists for reproducibility and CI, but the documented distro-package
procedure from `specbook/docs/gtk-porting-standards.md` remains the
primary developer onramp. The flake must not gate any essential workflow.

**D2 — Root Makefile delegates to per-repo Makefiles.**
Rationale: Each repo (`sugar-toolkit-gtk4`, `sugar/gtk4-port`) already
has or should have its own Makefile targets. The root Makefile should
not duplicate those recipes — it should `$(MAKE) -C repos/<name> <target>`.
This avoids drift between root-level and repo-level commands.

**D3 — Standard tooling configs live in the workspace root (not per-repo)
where practical.**
Rationale: `ruff.toml`, `mypy.ini` (or `pyproject.toml` tool sections),
and `.vscode/` settings apply to all repos. Each repo's own config
(present or future) should extend/override the root, not conflict with
it. For repos that already have their own config (like
`sugar-toolkit-gtk4`'s `pyproject.toml`), the root config is the
baseline and the repo config is the refinement.

**D4 — No monorepo merging of git histories.**
Rationale: `sugar-toolkit-gtk4`, `sugar`, and Casilda live under `repos/`
as independent git clones. They are not merged into a single repository
or submoduled. This spec's "monorepo" is at the OpenSpec/workspace level,
not the git level — it's about coordinated dev tooling, not a unified VCS
history.

## Not Yet Implemented

This spec is aspirational. As of 2026-07-08, no `flake.nix`, no root
`Makefile`, no `.vscode/` directory, and no standardized tooling configs
exist in the workspace. `sugar-toolkit-gtk4` has its own `flake.nix`
(per-repo, not workspace-level) and `sugar` (jarabe/gtk4-port) has no
build system or tooling configuration at all. The ad-hoc setup documented
in `specbook/docs/gtk-porting-standards.md` (manual env var exports,
hardcoded `PYTHONPATH`) is the current state.
