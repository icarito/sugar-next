#!/usr/bin/env python3
"""
Wayland Protocol MCP Server

Reads and exposes Wayland protocol XML files for debugging and reference.
Parses protocol definitions and makes them queryable via MCP JSON-RPC 2.0.

It can:
- List all available Wayland protocol XML files
- Parse a protocol and return interfaces, requests, events, and enums
- Search for interfaces across all protocols
- Show wire format detail (arguments, types)

Protocol: stdio JSON-RPC 2.0 (MCP-compatible)
"""

import json
import sys
import os
import xml.etree.ElementTree as ET
from typing import Any


WAYLAND_PROTOCOL_DIRS = [
    "/usr/share/wayland-protocols",
    "/usr/share/wayland",
    "/usr/local/share/wayland-protocols",
]


def find_protocol_xml_files() -> list[dict]:
    files = []
    for d in WAYLAND_PROTOCOL_DIRS:
        if not os.path.isdir(d):
            continue
        for dirpath, dirnames, filenames in os.walk(d):
            for f in sorted(filenames):
                if f.endswith(".xml"):
                    full_path = os.path.join(dirpath, f)
                    category = "core" if "wayland" in dirpath and "wayland-protocols" not in dirpath else ""
                    if not category:
                        rel = os.path.relpath(dirpath, d)
                        parts = rel.split(os.sep)
                        if len(parts) >= 2:
                            category = parts[0]
                        elif len(parts) == 1:
                            category = parts[0]
                    files.append({
                        "name": f,
                        "path": full_path,
                        "category": category,
                        "stability": parts[-1] if len(parts) >= 1 else "unknown",
                    })
    return files


def parse_protocol(filepath: str) -> dict[str, Any]:
    if not os.path.isfile(filepath):
        return {"error": f"File not found: {filepath}"}

    try:
        tree = ET.parse(filepath)
        root = tree.getroot()
    except ET.ParseError as e:
        return {"error": f"XML parse error: {e}"}

    result: dict[str, Any] = {
        "file": filepath,
        "name": root.get("name", ""),
        "copyright": "",
        "interfaces": [],
    }

    copyright_el = root.find("copyright")
    if copyright_el is not None and copyright_el.text:
        result["copyright"] = copyright_el.text.strip()[:200]

    for interface in root.findall("interface"):
        iface = {
            "name": interface.get("name", ""),
            "version": int(interface.get("version", 0)),
            "description": "",
            "requests": [],
            "events": [],
            "enums": [],
        }
        desc_el = interface.find("description")
        if desc_el is not None and desc_el.text:
            iface["description"] = desc_el.text.strip()[:300]

        for child in interface:
            tag = child.tag
            if tag == "description":
                pass
            elif tag == "request":
                iface["requests"].append(_parse_message(child, "request"))
            elif tag == "event":
                iface["events"].append(_parse_message(child, "event"))
            elif tag == "enum":
                iface["enums"].append(_parse_enum(child))

        result["interfaces"].append(iface)

    return result


def _parse_message(elem: ET.Element, msg_type: str) -> dict[str, Any]:
    result: dict[str, Any] = {
        "name": elem.get("name", ""),
        "type": msg_type,
        "since": elem.get("since", "1"),
        "description": "",
        "args": [],
    }
    for child in elem:
        if child.tag == "description" and child.text:
            result["description"] = child.text.strip()[:200]
        elif child.tag == "arg":
            arg_entry = {
                "name": child.get("name", ""),
                "type": child.get("type", ""),
                "summary": child.get("summary", ""),
                "interface": child.get("interface", ""),
                "allow_null": child.get("allow-null", "false") == "true",
            }
            enum = child.get("enum")
            if enum:
                arg_entry["enum"] = enum
            result["args"].append(arg_entry)
    return result


def _parse_enum(elem: ET.Element) -> dict[str, Any]:
    result: dict[str, Any] = {
        "name": elem.get("name", ""),
        "since": elem.get("since", "1"),
        "bitfield": elem.get("bitfield", "false") == "true",
        "description": "",
        "entries": [],
    }
    for child in elem:
        if child.tag == "description" and child.text:
            result["description"] = child.text.strip()[:200]
        elif child.tag == "entry":
            result["entries"].append({
                "name": child.get("name", ""),
                "value": child.get("value", ""),
                "since": child.get("since", "1"),
                "summary": child.get("summary", ""),
            })
    return result


def search_interfaces(query: str) -> dict[str, Any]:
    matches = []
    xml_files = find_protocol_xml_files()
    for f in xml_files:
        try:
            proto = parse_protocol(f["path"])
        except Exception:
            continue
        if "error" in proto:
            continue
        for iface in proto["interfaces"]:
            query_lower = query.lower()
            name_lower = iface["name"].lower()
            if query_lower in name_lower:
                matches.append({
                    "protocol": proto["name"],
                    "protocol_file": f["name"],
                    "category": f["category"],
                    "interface": iface["name"],
                    "version": iface["version"],
                    "requests_count": len(iface["requests"]),
                    "events_count": len(iface["events"]),
                })
    return {"query": query, "count": len(matches), "results": matches}


def get_interface_detail(protocol_file: str, interface_name: str) -> dict[str, Any]:
    xml_files = find_protocol_xml_files()
    filepath = None
    for f in xml_files:
        if f["name"] == protocol_file or f["path"].endswith(protocol_file):
            filepath = f["path"]
            break

    if not filepath:
        for f in xml_files:
            if os.path.basename(f["path"]) == protocol_file:
                filepath = f["path"]
                break

    if not filepath:
        return {"error": f"Protocol file not found: {protocol_file}"}

    proto = parse_protocol(filepath)
    if "error" in proto:
        return proto

    for iface in proto["interfaces"]:
        if iface["name"] == interface_name:
            return {
                "protocol": proto["name"],
                "file": proto["file"],
                "interface": iface,
            }

    return {"error": f"Interface '{interface_name}' not found in protocol '{proto['name']}'"}


def summarize_protocols() -> dict[str, Any]:
    xml_files = find_protocol_xml_files()
    summary = []
    for f in xml_files:
        try:
            proto = parse_protocol(f["path"])
        except Exception:
            continue
        if "error" in proto:
            continue
        summary.append({
            "file": f["name"],
            "category": f["category"],
            "protocol_name": proto["name"],
            "interface_count": len(proto["interfaces"]),
            "interfaces": [i["name"] for i in proto["interfaces"]],
        })
    return {"total_files": len(xml_files), "protocols": summary}


# --- JSON-RPC Server ---

def handle_request(request: dict) -> dict | None:
    method = request.get("method", "")
    req_id = request.get("id")
    params = request.get("params", {}) or {}

    try:
        if method == "initialize":
            return {"jsonrpc": "2.0", "id": req_id, "result": {
                "protocolVersion": "2024-11-05",
                "serverInfo": {"name": "wayland-protocol-mcp", "version": "1.0.0"},
                "capabilities": {"tools": {}},
            }}
        elif method == "notifications/initialized":
            return None
        elif method == "tools/list":
            return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": [
                {
                    "name": "list_protocols",
                    "description": "List all available Wayland protocol XML files with categories and interface counts",
                    "inputSchema": {"type": "object", "properties": {}, "required": []},
                },
                {
                    "name": "parse_protocol",
                    "description": "Parse a specific Wayland protocol XML file and return all interfaces, requests, events, and enums",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "filepath": {"type": "string", "description": "Absolute path or filename of the protocol XML file"},
                        },
                        "required": ["filepath"],
                    },
                },
                {
                    "name": "search_interfaces",
                    "description": "Search for Wayland interfaces by name across all protocol files",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Interface name or partial name to search for"},
                        },
                        "required": ["query"],
                    },
                },
                {
                    "name": "get_interface",
                    "description": "Get detailed information about a specific interface (all requests, events, args, enums)",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "protocol_file": {"type": "string", "description": "XML protocol filename (e.g. xdg-shell.xml, wayland.xml)"},
                            "interface_name": {"type": "string", "description": "Interface name (e.g. wl_surface, xdg_wm_base)"},
                        },
                        "required": ["protocol_file", "interface_name"],
                    },
                },
                {
                    "name": "summarize_all",
                    "description": "Summarize all Wayland protocols: file, category, interface names, and counts",
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
    if name == "list_protocols":
        xml_files = find_protocol_xml_files()
        return {"files": xml_files, "count": len(xml_files)}
    elif name == "parse_protocol":
        filepath = args["filepath"]
        if not os.path.isabs(filepath):
            for f in find_protocol_xml_files():
                if f["name"] == filepath or os.path.basename(f["path"]) == filepath:
                    filepath = f["path"]
                    break
        return parse_protocol(filepath)
    elif name == "search_interfaces":
        return search_interfaces(args["query"])
    elif name == "get_interface":
        return get_interface_detail(args["protocol_file"], args["interface_name"])
    elif name == "summarize_all":
        return summarize_protocols()
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
