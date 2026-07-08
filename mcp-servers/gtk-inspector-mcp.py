#!/usr/bin/env python3
"""
GTK Inspector MCP Server

Connects to a running GTK4 application's inspector D-Bus interface and exposes
the widget tree, CSS nodes, properties, and runtime state via MCP JSON-RPC 2.0.

Requirements:
- A GTK4 application running with the inspector enabled:
    GTK_DEBUG=interactive your-app
  Or via environment:
    GTK_DEBUG=interactive ./sugar

- D-Bus session bus access

When the inspector is active, GTK4 exposes:
  org.gtk.Inspector at object path /org/gtk/Inspector

Protocol: stdio JSON-RPC 2.0 (MCP-compatible)
"""

import json
import sys
import subprocess
from typing import Any


try:
    import dbus
    HAS_DBUS = True
    DBusException = dbus.DBusException
except ImportError:
    HAS_DBUS = False
    DBusException = Exception

INSPECTOR_BUS = "org.gtk.Inspector"
INSPECTOR_PATH = "/org/gtk/Inspector"


def _get_inspector_iface():
    if not HAS_DBUS:
        raise RuntimeError("dbus-python not available. Install with: pip install dbus-python")

    bus = dbus.SessionBus()
    obj = bus.get_object(INSPECTOR_BUS, INSPECTOR_PATH)
    return dbus.Interface(obj, INSPECTOR_BUS)


def list_inspector_running_apps() -> list[dict]:
    """List GTK apps with inspector via D-Bus introspection or process scan."""
    apps = []
    try:
        result = subprocess.run(
            ["pgrep", "-a", "-f", "GTK_DEBUG=interactive|python.*sugar|python.*Sugar"],
            capture_output=True, text=True, timeout=5
        )
        if result.stdout.strip():
            for line in result.stdout.strip().split("\n"):
                parts = line.strip().split(" ", 1)
                pid = parts[0]
                cmd = parts[1] if len(parts) > 1 else ""
                apps.append({"pid": int(pid), "command": cmd})
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    # Also check for GTK4 applications via D-Bus name listing
    try:
        output = subprocess.run(
            ["gdbus", "call", "--session", "--dest", "org.freedesktop.DBus",
             "--object-path", "/org/freedesktop/DBus",
             "--method", "org.freedesktop.DBus.ListNames"],
            capture_output=True, text=True, timeout=5
        )
        if output.stdout:
            names_raw = output.stdout.strip()
            if "org.gtk.Inspector" in names_raw:
                apps.append({"inspector": "active", "note": "org.gtk.Inspector found on session bus"})
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    if not apps:
        apps.append({
            "note": "No inspector apps found. Start with: GTK_DEBUG=interactive your-gtk4-app",
            "tips": [
                "Set GTK_DEBUG=interactive before launching Sugar",
                'Use gdbus to verify: gdbus introspect --session --dest org.gtk.Inspector --object-path /org/gtk/Inspector',
            ]
        })
    return apps


def get_inspector_object_tree() -> Any:
    """Get the widget object tree from the GTK inspector."""
    try:
        iface = _get_inspector_iface()
        result = iface.GetObjectTree()
        # result is typically an array of arrays: [[id, name, parent_id], ...]
        objects = []
        for obj in result:
            objects.append({
                "id": int(obj[0]),
                "name": str(obj[1]),
                "parent_id": int(obj[2]) if len(obj) > 2 else None,
            })
        return {"total": len(objects), "objects": objects}
    except DBusException as e:
        return {"error": f"D-Bus error: {e}"}
    except Exception as e:
        return {"error": str(e)}


def get_object_properties(object_id: int) -> Any:
    """Get properties of a specific widget object by its inspector ID."""
    try:
        iface = _get_inspector_iface()
        result = iface.GetProperties(object_id)
        properties = []
        if result:
            for prop in result:
                properties.append({
                    "name": str(prop[0]),
                    "value": str(prop[1]),
                })
        return {"object_id": object_id, "properties": properties}
    except DBusException as e:
        return {"error": f"D-Bus error: {e}"}
    except Exception as e:
        return {"error": str(e)}


def get_object_css_data(object_id: int) -> Any:
    """Get CSS node and style data for a widget."""
    try:
        iface = _get_inspector_iface()
        try:
            css_path = iface.GetCssPath(object_id)
        except (AttributeError, DBusException):
            css_path = "N/A"
        return {"object_id": object_id, "css_path": str(css_path)}
    except DBusException as e:
        return {"error": f"D-Bus error: {e}"}
    except Exception as e:
        return {"error": str(e)}


def get_object_size(object_id: int) -> Any:
    """Get size/allocation info for a widget."""
    try:
        iface = _get_inspector_iface()
        try:
            size = iface.GetSize(object_id)
        except DBusException:
            size = "N/A"
        return {"object_id": object_id, "size": str(size)}
    except Exception as e:
        return {"error": str(e)}


def highlight_object(object_id: int) -> dict:
    """Highlight a widget in the running application."""
    try:
        iface = _get_inspector_iface()
        iface.HighlightWidget(object_id)
        return {"object_id": object_id, "highlighted": True}
    except Exception as e:
        return {"error": str(e)}


def list_accessible_tree() -> Any:
    """Get the accessibility tree from the inspector."""
    try:
        iface = _get_inspector_iface()
        result = iface.GetAccessibilityTree()
        return {"accessible_tree": str(result)}
    except DBusException as e:
        return {"error": f"D-Bus error: {e}"}
    except Exception as e:
        return {"error": str(e)}


def introspect_inspector_dbus() -> str:
    """Introspect the inspector D-Bus interface and return XML."""
    try:
        result = subprocess.run(
            ["gdbus", "introspect", "--session", "--dest",
             INSPECTOR_BUS, "--object-path", INSPECTOR_PATH],
            capture_output=True, text=True, timeout=10
        )
        return result.stdout if result.stdout else result.stderr
    except FileNotFoundError:
        return "gdbus not available"
    except Exception as e:
        return str(e)


# --- JSON-RPC Server ---

def handle_request(request: dict) -> dict | None:
    method = request.get("method", "")
    req_id = request.get("id")
    params = request.get("params", {}) or {}

    try:
        if method == "initialize":
            return {"jsonrpc": "2.0", "id": req_id, "result": {
                "protocolVersion": "2024-11-05",
                "serverInfo": {"name": "gtk-inspector-mcp", "version": "1.0.0"},
                "capabilities": {"tools": {}},
            }}
        elif method == "notifications/initialized":
            return None
        elif method == "tools/list":
            return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": [
                {
                    "name": "list_apps",
                    "description": "List running GTK4 applications that have the inspector enabled",
                    "inputSchema": {"type": "object", "properties": {}, "required": []},
                },
                {
                    "name": "get_object_tree",
                    "description": "Get the full widget object tree from the running GTK4 application inspector",
                    "inputSchema": {"type": "object", "properties": {}, "required": []},
                },
                {
                    "name": "get_properties",
                    "description": "Get all GObject properties for a widget by its inspector object ID",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "object_id": {"type": "integer", "description": "Widget object ID from the object tree"},
                        },
                        "required": ["object_id"],
                    },
                },
                {
                    "name": "get_css_data",
                    "description": "Get CSS node path and style data for a widget",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "object_id": {"type": "integer", "description": "Widget object ID from the object tree"},
                        },
                        "required": ["object_id"],
                    },
                },
                {
                    "name": "get_size",
                    "description": "Get size and allocation information for a widget",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "object_id": {"type": "integer", "description": "Widget object ID from the object tree"},
                        },
                        "required": ["object_id"],
                    },
                },
                {
                    "name": "highlight_widget",
                    "description": "Highlight/flash a widget in the running GTK4 application",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "object_id": {"type": "integer", "description": "Widget object ID to highlight"},
                        },
                        "required": ["object_id"],
                    },
                },
                {
                    "name": "get_accessible_tree",
                    "description": "Get the accessibility (AT-SPI) tree from the running application",
                    "inputSchema": {"type": "object", "properties": {}, "required": []},
                },
                {
                    "name": "introspect_dbus",
                    "description": "Introspect the full D-Bus inspector interface and return the XML description",
                    "inputSchema": {"type": "object", "properties": {}, "required": []},
                },
            ]}}
        elif method == "tools/call":
            tool_name = params.get("name", "")
            arguments = params.get("arguments", {}) or {}
            result = _call_tool(tool_name, arguments)
            return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]}}
        elif method == "ping":
            return {"jsonrpc": "2.0", "id": req_id, "result": {}}
        else:
            return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": f"Method not found: {method}"}}
    except Exception as e:
        return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32603, "message": str(e)}}


def _call_tool(name: str, args: dict) -> Any:
    if name == "list_apps":
        return {"apps": list_inspector_running_apps()}
    elif name == "get_object_tree":
        return get_inspector_object_tree()
    elif name == "get_properties":
        return get_object_properties(args["object_id"])
    elif name == "get_css_data":
        return get_object_css_data(args["object_id"])
    elif name == "get_size":
        return get_object_size(args["object_id"])
    elif name == "highlight_widget":
        return highlight_object(args["object_id"])
    elif name == "get_accessible_tree":
        return list_accessible_tree()
    elif name == "introspect_dbus":
        return {"xml": introspect_inspector_dbus()}
    return {"error": f"Unknown tool: {name}"}


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
            response = handle_request(request)
            if response is not None:
                sys.stdout.write(json.dumps(response) + "\n")
                sys.stdout.flush()
        except json.JSONDecodeError:
            error_response = {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "Parse error"}}
            sys.stdout.write(json.dumps(error_response) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
