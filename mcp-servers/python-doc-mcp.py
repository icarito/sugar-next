#!/usr/bin/env python3
"""
Python Doc MCP Server

Generates and serves pydoc/docstring documentation from the `sugar4` and
`jarabe` packages via MCP JSON-RPC 2.0 over stdio.

It can:
- List all modules in sugar4 and jarabe
- Retrieve docstrings for modules, classes, functions
- Show source file locations and line numbers
- Search for symbols by name across packages

Environment variables:
  SUGAR4_PATH  - path to sugar4 package (default: repos/sugar-toolkit-gtk4/src/sugar4)
  JARABE_PATH  - path to jarabe package  (default: repos/sugar/src/jarabe)

Protocol: stdio JSON-RPC 2.0 (MCP-compatible)
"""

import json
import sys
import os
import ast
import importlib
import importlib.util
from pathlib import Path
from typing import Any


def _get_project_root() -> str:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.dirname(script_dir)


def _resolve_package_path(pkg_name: str, env_var: str, default_rel: str) -> str | None:
    env_path = os.environ.get(env_var)
    if env_path:
        path = os.path.join(_get_project_root(), env_path)
        if os.path.isdir(path):
            return path
        if os.path.isdir(env_path):
            return env_path

    path = os.path.join(_get_project_root(), default_rel)
    if os.path.isdir(path):
        return path
    return None


SUGAR4_PATH = _resolve_package_path("sugar4", "SUGAR4_PATH", "repos/sugar-toolkit-gtk4/src/sugar4")
JARABE_PATH = _resolve_package_path("jarabe", "JARABE_PATH", "repos/sugar/src/jarabe")

PACKAGES = {
    "sugar4": {"path": SUGAR4_PATH, "parent_path": os.path.dirname(SUGAR4_PATH) if SUGAR4_PATH else None},
    "jarabe": {"path": JARABE_PATH, "parent_path": os.path.dirname(JARABE_PATH) if JARABE_PATH else None},
}


def _walk_python_modules(root: str) -> list[str]:
    modules = []
    if not root or not os.path.isdir(root):
        return modules
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if not d.startswith(".") and d != "__pycache__"]
        rel = os.path.relpath(dirpath, root)
        for f in filenames:
            if f.endswith(".py"):
                mod_path = os.path.splitext(os.path.join(rel, f))[0].replace(os.sep, ".")
                if mod_path == "__init__":
                    mod_path = ""
                if mod_path:
                    modules.append(mod_path)
    return sorted(modules)


def _parse_python_file(filepath: str) -> dict[str, Any]:
    if not os.path.isfile(filepath):
        return {"error": f"File not found: {filepath}"}

    with open(filepath, "r", encoding="utf-8") as f:
        source = f.read()

    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        return {"error": f"Syntax error: {e}"}

    result: dict[str, Any] = {
        "module_doc": ast.get_docstring(tree) or "",
        "classes": [],
        "functions": [],
        "imports": [],
    }

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            methods = []
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    args = []
                    for a in item.args.args:
                        arg_str = a.arg
                        if a.annotation:
                            arg_str += f": {ast.unparse(a.annotation)}"
                        args.append(arg_str)
                    methods.append({
                        "name": item.name,
                        "doc": ast.get_docstring(item) or "",
                        "decorators": [ast.unparse(d) for d in item.decorator_list],
                        "args": args,
                        "lineno": item.lineno,
                    })
            result["classes"].append({
                "name": node.name,
                "doc": ast.get_docstring(node) or "",
                "bases": [ast.unparse(b) for b in node.bases],
                "decorators": [ast.unparse(d) for d in node.decorator_list],
                "methods": methods,
                "lineno": node.lineno,
            })
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if _is_top_level(node, tree):
                args = []
                for a in node.args.args:
                    arg_str = a.arg
                    if a.annotation:
                        arg_str += f": {ast.unparse(a.annotation)}"
                    args.append(arg_str)
                result["functions"].append({
                    "name": node.name,
                    "doc": ast.get_docstring(node) or "",
                    "decorators": [ast.unparse(d) for d in node.decorator_list],
                    "args": args,
                    "lineno": node.lineno,
                })
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            if _is_top_level(node, tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        result["imports"].append({"module": alias.name, "alias": alias.asname})
                elif node.module:
                    result["imports"].append({"module": node.module, "names": [n.name for n in node.names]})

    return result


def _is_top_level(node: ast.AST, tree: ast.Module) -> bool:
    for child in ast.iter_child_nodes(tree):
        if child is node:
            return True
        if isinstance(child, ast.ClassDef):
            for inner in child.body:
                if inner is node:
                    return False
    return True


def list_modules(package: str | None = None) -> dict[str, Any]:
    result: dict[str, Any] = {}
    packages_to_query = {package: PACKAGES[package]} if package and package in PACKAGES else PACKAGES

    for pkg_name, pkg_info in packages_to_query.items():
        if not pkg_info["path"]:
            result[pkg_name] = {"error": f"Package not found: {pkg_name}"}
            continue
        modules = _walk_python_modules(pkg_info["path"])
        result[pkg_name] = {"path": pkg_info["path"], "count": len(modules), "modules": modules}
    return result


def get_module_info(package: str, module_name: str) -> dict[str, Any]:
    if package not in PACKAGES:
        return {"error": f"Unknown package: {package}"}

    pkg_info = PACKAGES[package]
    if not pkg_info["path"]:
        return {"error": f"Package path not configured: {package}"}

    parts = module_name.split(".")
    rel_path = os.path.join(*parts) + ".py"
    filepath = os.path.join(pkg_info["path"], rel_path)

    if not os.path.isfile(filepath):
        init_path = os.path.join(pkg_info["path"], *parts, "__init__.py")
        if os.path.isfile(init_path):
            filepath = init_path
        else:
            return {"error": f"Module not found: {module_name} in {package} (tried {filepath})"}

    info = _parse_python_file(filepath)
    info["file"] = filepath
    info["package"] = package
    info["module"] = module_name
    return info


def search_symbols(query: str) -> dict[str, Any]:
    results = []
    for pkg_name, pkg_info in PACKAGES.items():
        if not pkg_info["path"]:
            continue
        modules = _walk_python_modules(pkg_info["path"])
        for mod in modules:
            parts = mod.split(".")
            filepath = os.path.join(pkg_info["path"], *parts) + ".py"
            if not os.path.isfile(filepath):
                filepath = os.path.join(pkg_info["path"], *parts, "__init__.py")
            if not os.path.isfile(filepath):
                continue
            info = _parse_python_file(filepath)
            if "error" in info:
                continue
            for cls in info["classes"]:
                if query.lower() in cls["name"].lower():
                    results.append({
                        "package": pkg_name,
                        "module": mod,
                        "name": cls["name"],
                        "kind": "class",
                        "lineno": cls["lineno"],
                        "file": filepath,
                        "doc_preview": cls["doc"][:200] if cls["doc"] else "",
                    })
            for func in info["functions"]:
                if query.lower() in func["name"].lower():
                    results.append({
                        "package": pkg_name,
                        "module": mod,
                        "name": func["name"],
                        "kind": "function",
                        "lineno": func["lineno"],
                        "file": filepath,
                        "doc_preview": func["doc"][:200] if func["doc"] else "",
                    })
            if len(results) >= 50:
                break
        if len(results) >= 50:
            break
    return {"query": query, "count": len(results), "results": results}


def list_all_symbols(package: str | None = None) -> dict[str, Any]:
    result: dict[str, Any] = {}
    packages_to_query = {package: PACKAGES[package]} if package and package in PACKAGES else PACKAGES

    for pkg_name, pkg_info in packages_to_query.items():
        if not pkg_info["path"]:
            result[pkg_name] = {"error": "Package not found"}
            continue
        modules = _walk_python_modules(pkg_info["path"])
        symbols = []
        for mod in modules:
            parts = mod.split(".")
            filepath = os.path.join(pkg_info["path"], *parts) + ".py"
            if not os.path.isfile(filepath):
                filepath = os.path.join(pkg_info["path"], *parts, "__init__.py")
            if not os.path.isfile(filepath):
                continue
            info = _parse_python_file(filepath)
            if "error" in info:
                continue
            for cls in info["classes"]:
                symbols.append({"module": mod, "name": cls["name"], "kind": "class", "lineno": cls["lineno"]})
            for func in info["functions"]:
                symbols.append({"module": mod, "name": func["name"], "kind": "function", "lineno": func["lineno"]})
        result[pkg_name] = {"count": len(symbols), "symbols": symbols}
    return result


# --- JSON-RPC Server ---

def handle_request(request: dict) -> dict | None:
    method = request.get("method", "")
    req_id = request.get("id")
    params = request.get("params", {}) or {}

    try:
        if method == "initialize":
            return {"jsonrpc": "2.0", "id": req_id, "result": {
                "protocolVersion": "2024-11-05",
                "serverInfo": {"name": "python-doc-mcp", "version": "1.0.0"},
                "capabilities": {"tools": {}},
            }}
        elif method == "notifications/initialized":
            return None
        elif method == "tools/list":
            return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": [
                {
                    "name": "list_modules",
                    "description": "List all Python modules in sugar4 and jarabe packages",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "package": {"type": "string", "description": "Optional: filter by package name (sugar4 or jarabe)"},
                        },
                    },
                },
                {
                    "name": "get_module_info",
                    "description": "Get docstrings, classes, functions, and imports for a specific module",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "package": {"type": "string", "description": "Package name: sugar4 or jarabe"},
                            "module_name": {"type": "string", "description": "Module path relative to package (e.g. 'activity.activity' for sugar4.activity.activity)"},
                        },
                        "required": ["package", "module_name"],
                    },
                },
                {
                    "name": "search_symbols",
                    "description": "Search for classes and functions by name across sugar4 and jarabe",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Symbol name or partial name to search for"},
                        },
                        "required": ["query"],
                    },
                },
                {
                    "name": "list_symbols",
                    "description": "List all classes and functions in the sugar4/jarabe packages",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "package": {"type": "string", "description": "Optional: filter by package name"},
                        },
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
    if name == "list_modules":
        return list_modules(args.get("package"))
    elif name == "get_module_info":
        return get_module_info(args["package"], args["module_name"])
    elif name == "search_symbols":
        return search_symbols(args["query"])
    elif name == "list_symbols":
        return list_all_symbols(args.get("package"))
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
