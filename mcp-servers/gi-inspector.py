#!/usr/bin/env python3
"""
GI Repository Browser MCP Server

Provides an MCP-compatible stdio JSON-RPC 2.0 server that introspects the
GObject Introspection type system. It can:

- List all available GObject/GTK namespaces and their versions
- Query class hierarchies, properties, signals, and methods for any GI namespace
- Return method signatures with parameter names and types
- Search for types across namespaces

Protocol: stdio JSON-RPC 2.0 (MCP-compatible)
"""

import json
import sys
import os
import xml.etree.ElementTree as ET
from typing import Any


GIR_DIRS = [
    "/usr/share/gir-1.0",
    "/usr/local/share/gir-1.0",
]

TYPELIB_DIRS = [
    "/usr/lib/girepository-1.0",
    "/usr/lib64/girepository-1.0",
    "/usr/lib/x86_64-linux-gnu/girepository-1.0",
]


def find_gir_files() -> dict[str, list[str]]:
    namespaces: dict[str, list[str]] = {}
    for d in GIR_DIRS:
        if not os.path.isdir(d):
            continue
        for f in sorted(os.listdir(d)):
            if not f.endswith(".gir"):
                continue
            base = f[:-4]
            parts = base.rsplit("-", 1)
            if len(parts) == 2:
                ns, ver = parts
            else:
                ns, ver = base, "1.0"
            if ns not in namespaces:
                namespaces[ns] = []
            if ver not in namespaces[ns]:
                namespaces[ns].append(ver)
    return namespaces


def find_typelib_files() -> dict[str, list[str]]:
    namespaces: dict[str, list[str]] = {}
    for d in TYPELIB_DIRS:
        if not os.path.isdir(d):
            continue
        for f in sorted(os.listdir(d)):
            if not f.endswith(".typelib"):
                continue
            base = f[:-8]
            parts = base.rsplit("-", 1)
            if len(parts) == 2:
                ns, ver = parts
            else:
                ns, ver = base, "1.0"
            if ns not in namespaces:
                namespaces[ns] = []
            if ver not in namespaces[ns]:
                namespaces[ns].append(ver)
    return namespaces


def find_gir_path(namespace: str, version: str | None = None) -> str | None:
    for d in GIR_DIRS:
        if not os.path.isdir(d):
            continue
        candidates = []
        for f in os.listdir(d):
            if not f.endswith(".gir"):
                continue
            base = f[:-4]
            parts = base.rsplit("-", 1)
            ns, ver = (parts[0], parts[1]) if len(parts) == 2 else (base, "1.0")
            if ns == namespace:
                if version and ver == version:
                    return os.path.join(d, f)
                candidates.append((ver, os.path.join(d, f)))
        if candidates:
            candidates.sort(key=lambda x: x[0], reverse=True)
            return candidates[0][1]
    return None


def parse_gir_info(gir_path: str) -> dict[str, Any]:
    try:
        tree = ET.parse(gir_path)
    except ET.ParseError:
        return {"error": f"XML parse error in {gir_path}"}
    root = tree.getroot()
    ns_uri = "{http://www.gtk.org/introspection/core/1.0}"
    c_uri = "{http://www.gtk.org/introspection/c/1.0}"
    glib_uri = "{http://www.gtk.org/introspection/glib/1.0}"

    def apply_ns(tag: str) -> str:
        return f"{ns_uri}{tag}"

    repo = root if root.tag == apply_ns("repository") else root.find(apply_ns("repository"))
    if repo is None:
        repo = root

    ns_elem = repo.find(apply_ns("namespace")) if repo is not None else None
    if ns_elem is None:
        return {"classes": [], "interfaces": [], "enums": [], "functions": [], "records": [], "aliases": []}

    result: dict[str, Any] = {
        "namespace": ns_elem.get("name", ""),
        "version": ns_elem.get("version", ""),
        "classes": [],
        "interfaces": [],
        "enums": [],
        "functions": [],
        "records": [],
        "aliases": [],
    }

    for cls in ns_elem.findall(apply_ns("class")):
        entry = _parse_gi_class_like(cls, apply_ns, glib_uri)
        result["classes"].append(entry)

    for iface in ns_elem.findall(apply_ns("interface")):
        entry = _parse_gi_class_like(iface, apply_ns, glib_uri)
        result["interfaces"].append(entry)

    for enum in ns_elem.findall(apply_ns("enumeration")):
        entry = {
            "name": enum.get("name", ""),
            "c_type": enum.get(f"{c_uri}type", "")
            if "}" not in c_uri
            else enum.get("{%s}type" % c_uri.strip("{}"), ""),
        }
        result["enums"].append(entry)

    for func in ns_elem.findall(apply_ns("function")):
        entry = _parse_callable(func, apply_ns, c_uri)
        result["functions"].append(entry)

    return result


def _parse_gi_class_like(
    elem: ET.Element, apply_ns: callable, glib_uri: str
) -> dict[str, Any]:
    c_uri_inner = "{http://www.gtk.org/introspection/c/1.0}"
    entry: dict[str, Any] = {
        "name": elem.get("name", ""),
        "parent": elem.get("parent", ""),
        "abstract": elem.get("abstract", "0") == "1",
        "type_name": elem.get(f"{glib_uri}type-name", ""),
        "get_type": elem.get(f"{glib_uri}get-type", ""),
        "constructors": [],
        "methods": [],
        "properties": [],
        "signals": [],
        "fields": [],
    }

    for child in elem:
        tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
        if tag == "constructor":
            entry["constructors"].append(_parse_callable(child, apply_ns, c_uri_inner))
        elif tag == "method":
            entry["methods"].append(_parse_callable(child, apply_ns, c_uri_inner))
        elif tag == "property":
            entry["properties"].append({
                "name": child.get("name", ""),
                "readable": child.get("readable", "1") == "1",
                "writable": child.get("writable", "0") == "1",
                "transfer_ownership": child.get("transfer-ownership", "none"),
            })
        elif tag == "signal":
            entry["signals"].append({
                "name": child.get("name", ""),
                "when": child.get("when", "clean"),
                "parameters": [
                    _param_info(p, apply_ns) for p in child.findall(apply_ns("parameter"))
                ],
                "return": _return_value(child, apply_ns),
            })
        elif tag == "field":
            entry["fields"].append({
                "name": child.get("name", ""),
                "readable": child.get("readable", "1") == "1",
                "writable": child.get("writable", "1") == "1",
                "bits": child.get("bits"),
            })
    return entry


def _parse_callable(
    elem: ET.Element, apply_ns: callable, c_uri: str
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "name": elem.get("name", ""),
        "c_identifier": elem.get(f"{c_uri}identifier", "") if "}" not in c_uri else "",
        "parameters": [],
    }
    for param in elem.findall(apply_ns("parameter")):
        owner = param.get("instance-parameter")
        if owner is not None and owner == "1" and elem.tag.split('}')[-1] == "method":
            continue
        result["parameters"].append(_param_info(param, apply_ns))
    ret = _return_value(elem, apply_ns)
    if ret:
        result["return"] = ret
    return result


def _param_info(elem: ET.Element, apply_ns: callable) -> dict[str, Any]:
    type_elem = elem.find(apply_ns("type"))
    type_str = type_elem.get("name", "") if type_elem is not None else ""
    if type_str == "" and type_elem is not None:
        ctype = type_elem.get(f"{{http://www.gtk.org/introspection/c/1.0}}type", "")
        type_str = ctype or "unknown"
    return {
        "name": elem.get("name", ""),
        "type": type_str,
        "direction": elem.get("direction", "in"),
        "nullable": elem.get("nullable", "0") == "1" if elem.get("nullable") else False,
        "transfer_ownership": elem.get("transfer-ownership", "none"),
        "caller_allocates": elem.get("caller-allocates", "0") == "1",
    }


def _return_value(
    elem: ET.Element, apply_ns: callable
) -> dict[str, Any] | None:
    ret_elem = elem.find(apply_ns("return-value"))
    if ret_elem is None:
        return None
    type_elem = ret_elem.find(apply_ns("type"))
    type_str = type_elem.get("name", "") if type_elem is not None else "void"
    if type_str == "" and type_elem is not None:
        type_str = type_elem.get(
            "{http://www.gtk.org/introspection/c/1.0}type", "unknown"
        )
    return {
        "type": type_str,
        "nullable": ret_elem.get("nullable", "0") == "1" if ret_elem.get("nullable") else False,
        "transfer_ownership": ret_elem.get("transfer-ownership", "none"),
    }


def query_class_hierarchy(namespace: str, class_name: str | None = None) -> Any:
    gir_path = find_gir_path(namespace)
    if not gir_path:
        return {"error": f"Namespace '{namespace}' not found in GIR directories"}
    info = parse_gir_info(gir_path)
    if class_name:
        result = {"namespace": info["namespace"], "class": None}
        for cls in info["classes"]:
            if cls["name"] == class_name:
                result["class"] = cls
                result["hierarchy"] = _build_hierarchy(cls, info)
                return result
        for iface in info["interfaces"]:
            if iface["name"] == class_name:
                result["class"] = iface
                return result
        return {"error": f"Class '{class_name}' not found in namespace '{namespace}'"}
    return info


def _build_hierarchy(
    cls: dict[str, Any], info: dict[str, Any]
) -> list[dict[str, Any]]:
    chain = [{"name": cls["name"], "properties": len(cls["properties"]), "signals": len(cls["signals"])}]
    current = cls.get("parent", "")
    while current:
        parent_info = None
        for c in info["classes"]:
            if c["name"] == current:
                parent_info = c
                break
        if parent_info:
            chain.append({
                "name": current,
                "properties": len(parent_info["properties"]),
                "signals": len(parent_info["signals"]),
            })
            current = parent_info.get("parent", "")
        else:
            chain.append({"name": current, "properties": 0, "signals": 0})
            current = ""
    return chain


# --- Live GI Runtime Introspection (optional) ---

def query_live_gi(namespace: str) -> dict[str, Any]:
    try:
        import gi
        gi.require_version(namespace, None)
        mod = __import__(f"gi.repository.{namespace}", fromlist=[namespace])
        repo = gi.Repository.get_default()
        versions = repo.get_loaded_namespaces()

        result: dict[str, Any] = {"namespace": namespace, "types": []}
        for name in dir(mod):
            if name.startswith("_"):
                continue
            obj = getattr(mod, name)
            type_info = {
                "name": name,
                "type": type(obj).__name__,
            }
            if hasattr(obj, "__gtype__"):
                gtype = obj.__gtype__
                type_info["gtype_name"] = gtype.name
                type_info["gtype_id"] = str(gtype)
            if callable(obj) and not isinstance(obj, type):
                import inspect
                try:
                    sig = inspect.signature(obj)
                    type_info["signature"] = str(sig)
                except (ValueError, TypeError):
                    pass
            result["types"].append(type_info)
        return result
    except Exception as e:
        return {"error": str(e)}


# --- JSON-RPC Server ---

def handle_request(request: dict) -> dict | None:
    method = request.get("method", "")
    req_id = request.get("id")
    params = request.get("params", {}) or {}

    try:
        if method == "initialize":
            return {"jsonrpc": "2.0", "id": req_id, "result": {
                "protocolVersion": "2024-11-05",
                "serverInfo": {"name": "gi-inspector", "version": "1.0.0"},
                "capabilities": {"tools": {}},
            }}
        elif method == "notifications/initialized":
            return None
        elif method == "tools/list":
            return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": [
                {
                    "name": "list_namespaces",
                    "description": "List all available GObject Introspection namespaces (GIR and typelib) with versions",
                    "inputSchema": {"type": "object", "properties": {}, "required": []},
                },
                {
                    "name": "query_namespace",
                    "description": "Query a GI namespace: list all classes, interfaces, enums, functions with their details",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "namespace": {"type": "string", "description": "GI namespace name (e.g. Gtk, Gdk, GObject)"},
                            "version": {"type": "string", "description": "Optional: namespace version (e.g. 4.0). Defaults to latest."},
                        },
                        "required": ["namespace"],
                    },
                },
                {
                    "name": "query_class",
                    "description": "Query a specific class: hierarchy chain, properties, signals, methods with signatures",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "namespace": {"type": "string", "description": "GI namespace name"},
                            "class_name": {"type": "string", "description": "GObject class name (e.g. Window, Button, Application)"},
                        },
                        "required": ["namespace", "class_name"],
                    },
                },
                {
                    "name": "query_live_gi",
                    "description": "Introspect a live loaded GI namespace at runtime (requires the typelib to be importable)",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "namespace": {"type": "string", "description": "GI namespace to import and introspect"},
                        },
                        "required": ["namespace"],
                    },
                },
                {
                    "name": "search_type",
                    "description": "Search for a type name across all available GIR namespaces",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Type name or partial name to search for"},
                        },
                        "required": ["query"],
                    },
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
    if name == "list_namespaces":
        gir = find_gir_files()
        typelib = find_typelib_files()
        return {"gir_namespaces": gir, "typelib_namespaces": typelib}
    elif name == "query_namespace":
        ns = args["namespace"]
        ver = args.get("version")
        gir_path = find_gir_path(ns, ver)
        if not gir_path:
            return {"error": f"Namespace '{ns}' not found"}
        return parse_gir_info(gir_path)
    elif name == "query_class":
        ns = args["namespace"]
        cn = args["class_name"]
        return query_class_hierarchy(ns, cn)
    elif name == "query_live_gi":
        ns = args["namespace"]
        return query_live_gi(ns)
    elif name == "search_type":
        query = args["query"].lower()
        matches = []
        for ns, versions in find_gir_files().items():
            gir_path = find_gir_path(ns)
            if not gir_path:
                continue
            info = parse_gir_info(gir_path)
            if "error" in info:
                continue
            search_in = (
                [(c["name"], "class") for c in info.get("classes", [])]
                + [(i["name"], "interface") for i in info.get("interfaces", [])]
                + [(e["name"], "enum") for e in info.get("enums", [])]
                + [(r["name"], "record") for r in info.get("records", [])]
            )
            for name, kind in search_in:
                if query in name.lower():
                    matches.append({"namespace": ns, "version": versions[0] if versions else "unknown", "name": name, "kind": kind})
            if len(matches) >= 50:
                break
        return {"matches": matches[:50]}
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
