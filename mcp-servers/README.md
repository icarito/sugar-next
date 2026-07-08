# MCP Servers for GTK4 / Sugar Stack

This directory contains MCP (Model Context Protocol) servers that provide AI
agent visibility into the GObject/GTK4/Sugar development stack. Each server
communicates via stdio JSON-RPC 2.0 and can be used with Kilo, Claude Code, or
any MCP-compatible client.

## Servers

### 1. GI Repository Browser (`gi-inspector.py`)

Introspects the GObject Introspection type system by reading `.gir` XML files
and optionally querying live GI modules at runtime.

**Tools:**
| Tool | Description |
|------|-------------|
| `list_namespaces` | List all available GI namespaces (GIR and typelib) with versions |
| `query_namespace` | Parse a namespace GIR: classes, interfaces, enums, functions |
| `query_class` | Full detail on a class: hierarchy, properties, signals, methods |
| `query_live_gi` | Runtime introspection via `gi.repository` (requires importable typelib) |
| `search_type` | Search for a type name across all GI namespaces |

**Requirements:** Python 3.8+, system GIR files in `/usr/share/gir-1.0/`

**Usage:**
```bash
python3 mcp-servers/gi-inspector.py
```

### 2. GTK Inspector MCP (`gtk-inspector-mcp.py`)

Connects to a running GTK4 application's inspector D-Bus interface. Reads
widget trees, CSS node data, object properties, and accessibility trees at
runtime.

**Tools:**
| Tool | Description |
|------|-------------|
| `list_apps` | List running GTK4 apps with inspector enabled |
| `get_object_tree` | Get the full widget object tree |
| `get_properties` | Get all GObject properties for a widget by ID |
| `get_css_data` | Get CSS node path and style data for a widget |
| `get_size` | Get widget size and allocation |
| `highlight_widget` | Flash/highlight a widget in the running app |
| `get_accessible_tree` | Get the AT-SPI accessibility tree |
| `introspect_dbus` | Introspect the full inspector D-Bus interface |

**Requirements:** `dbus-python`, running GTK4 app with `GTK_DEBUG=interactive`

**Usage:**
```bash
# Start your GTK4 app with the inspector enabled:
GTK_DEBUG=interactive python3 path/to/sugar

# Then connect the MCP server:
python3 mcp-servers/gtk-inspector-mcp.py
```

### 3. Python Doc MCP (`python-doc-mcp.py`)

Generates and serves pydoc/docstring documentation from the `sugar4` and
`jarabe` packages by parsing Python source files with AST.

**Tools:**
| Tool | Description |
|------|-------------|
| `list_modules` | List all modules in sugar4/jarabe |
| `get_module_info` | Docstrings, classes, functions, imports for a module |
| `search_symbols` | Search for classes/functions by name |
| `list_symbols` | List all symbols (classes and functions) across packages |

**Requirements:** Python 3.8+, `sugar4` and `jarabe` source directories

**Environment:**
- `SUGAR4_PATH` — path to `sugar4` package (default: `repos/sugar-toolkit-gtk4/src/sugar4`)
- `JARABE_PATH` — path to `jarabe` package (default: `repos/sugar/src/jarabe`)

**Usage:**
```bash
SUGAR4_PATH=repos/sugar-toolkit-gtk4/src/sugar4 \
JARABE_PATH=repos/sugar/src/jarabe \
python3 mcp-servers/python-doc-mcp.py
```

### 4. Wayland Protocol MCP (`wayland-protocol-mcp.py`)

Reads Wayland protocol XML files from the system protocol directories and
exposes interface definitions, requests, events, and enums.

**Tools:**
| Tool | Description |
|------|-------------|
| `list_protocols` | List all available Wayland protocol XML files |
| `parse_protocol` | Parse a protocol XML and return all interfaces and messages |
| `search_interfaces` | Search for Wayland interfaces by name across all protocols |
| `get_interface` | Full detail on a specific interface (requests, events, enums, args) |
| `summarize_all` | Summary of all protocols with interface names and counts |

**Requirements:** Python 3.8+, system Wayland protocol XML files

**Usage:**
```bash
python3 mcp-servers/wayland-protocol-mcp.py
```

## Protocol

All servers use MCP-compatible stdio JSON-RPC 2.0:

```
-> {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {...}}
<- {"jsonrpc": "2.0", "id": 1, "result": {...}}

-> {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
<- {"jsonrpc": "2.0", "id": 2, "result": {"tools": [...]}}

-> {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "...", "arguments": {...}}}
<- {"jsonrpc": "2.0", "id": 3, "result": {"content": [{"type": "text", "text": "..."}]}}
```

Each message is a single JSON object on one line, followed by a newline.
This is the standard MCP stdio transport.

## Configuration Files

- **`.kilo/kilo.jsonc`** — Kilo IDE MCP config (uses `"mcp"` top-level key)
- **`.claude/settings.json`** — Claude Code MCP config (uses `"mcpServers"` top-level key)

Both files reference the same Python server scripts in this directory.

## Quick Test

Start a server and send JSON-RPC messages to stdin:

```bash
# Test GI Inspector
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' | python3 mcp-servers/gi-inspector.py
echo '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}' | python3 mcp-servers/gi-inspector.py

# Test Python Doc MCP
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' | SUGAR4_PATH=repos/sugar-toolkit-gtk4/src/sugar4 JARABE_PATH=repos/sugar/src/jarabe python3 mcp-servers/python-doc-mcp.py
echo '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}' | SUGAR4_PATH=repos/sugar-toolkit-gtk4/src/sugar4 JARABE_PATH=repos/sugar/src/jarabe python3 mcp-servers/python-doc-mcp.py

# Test Wayland Protocols
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' | python3 mcp-servers/wayland-protocol-mcp.py
echo '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}' | python3 mcp-servers/wayland-protocol-mcp.py
```
