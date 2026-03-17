#!/usr/bin/env python3
"""Bootstrap script for World Builder data stores.

Run from the vault root directory:
    python path/to/_lib/setup.py

This will:
1. Check Python version (3.10+ required)
2. Create a venv at _meta/.wb-venv/
3. Install requirements
4. Initialize empty SQLite DB, NetworkX graph, and ChromaDB collection
"""

from __future__ import annotations

import json
import os
import subprocess
import sys


def check_python_version():
    """Ensure Python 3.10+."""
    if sys.version_info < (3, 10):
        print(f"Error: Python 3.10+ required. You have {sys.version}", file=sys.stderr)
        sys.exit(1)
    print(f"[ok] Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")


def create_venv(vault_root: str) -> str:
    """Create venv at _meta/.wb-venv/ if it doesn't exist. Returns venv path."""
    venv_path = os.path.join(vault_root, "_meta", ".wb-venv")

    if os.path.exists(venv_path):
        print(f"[ok] Virtual environment already exists at {venv_path}")
    else:
        print(f"[..] Creating virtual environment at {venv_path}")
        subprocess.run(
            [sys.executable, "-m", "venv", venv_path],
            check=True,
        )
        print(f"[ok] Virtual environment created")

    return venv_path


def get_venv_python(venv_path: str) -> str:
    """Get the python executable path inside the venv."""
    if sys.platform == "win32":
        return os.path.join(venv_path, "Scripts", "python.exe")
    return os.path.join(venv_path, "bin", "python")


def get_venv_pip(venv_path: str) -> str:
    """Get the pip executable path inside the venv."""
    if sys.platform == "win32":
        return os.path.join(venv_path, "Scripts", "pip.exe")
    return os.path.join(venv_path, "bin", "pip")


def install_requirements(venv_path: str, lib_dir: str):
    """Install requirements.txt via pip in the venv."""
    pip = get_venv_pip(venv_path)
    req_file = os.path.join(lib_dir, "requirements.txt")

    if not os.path.exists(req_file):
        print(f"Warning: requirements.txt not found at {req_file}", file=sys.stderr)
        return

    print("[..] Installing requirements...")
    subprocess.run(
        [pip, "install", "-r", req_file],
        check=True,
    )
    print("[ok] Requirements installed")


def init_sqlite(vault_root: str, lib_dir: str, venv_path: str):
    """Initialize empty SQLite database."""
    print("[..] Initializing SQLite database...")
    python = get_venv_python(venv_path)
    script = (
        "import sys; "
        f"sys.path.insert(0, {lib_dir!r}); "
        "from wb_stores.sqlite_store import SqliteStore; "
        f"store = SqliteStore({vault_root!r}); "
        "store.close(); "
        "print('[ok] SQLite database initialized')"
    )
    subprocess.run([python, "-c", script], check=True)


def init_graph(vault_root: str):
    """Initialize empty NetworkX graph JSON."""
    graph_path = os.path.join(vault_root, "_meta", "wb-graph.json")
    if os.path.exists(graph_path):
        print(f"[ok] Graph file already exists at {graph_path}")
        return

    print("[..] Initializing empty graph...")
    os.makedirs(os.path.dirname(graph_path), exist_ok=True)
    empty_graph = {
        "directed": True,
        "multigraph": True,
        "graph": {},
        "nodes": [],
        "links": [],
    }
    with open(graph_path, "w", encoding="utf-8") as f:
        json.dump(empty_graph, f, indent=2)
    print("[ok] Empty graph created")


def init_chromadb(vault_root: str, lib_dir: str, venv_path: str):
    """Initialize empty ChromaDB collection."""
    print("[..] Initializing ChromaDB collection...")
    python = get_venv_python(venv_path)
    script = (
        "import sys; "
        f"sys.path.insert(0, {lib_dir!r}); "
        "from wb_stores.vector_store import VectorStore; "
        f"store = VectorStore({vault_root!r}); "
        f"print(f'[ok] ChromaDB initialized ({{store.count()}} entities)')"
    )
    subprocess.run([python, "-c", script], check=True)


def main():
    # Determine paths
    lib_dir = os.path.dirname(os.path.abspath(__file__))
    vault_root = os.getcwd()

    print("=" * 60)
    print("World Builder — Setup")
    print("=" * 60)
    print(f"Vault root: {vault_root}")
    print(f"Lib dir:    {lib_dir}")
    print()

    # 1. Check Python version
    check_python_version()

    # 2. Create venv
    meta_dir = os.path.join(vault_root, "_meta")
    os.makedirs(meta_dir, exist_ok=True)
    venv_path = create_venv(vault_root)

    # 3. Install requirements
    install_requirements(venv_path, lib_dir)

    # 4. Initialize SQLite
    init_sqlite(vault_root, lib_dir, venv_path)

    # 5. Initialize NetworkX graph
    init_graph(vault_root)

    # 6. Initialize ChromaDB
    init_chromadb(vault_root, lib_dir, venv_path)

    print()
    print("=" * 60)
    print("Setup complete!")
    print("=" * 60)
    print()
    print("Usage:")
    venv_python = get_venv_python(venv_path)
    wb_script = os.path.join(lib_dir, "wb.py")
    print(f"  {venv_python} {wb_script} sync --full")
    print(f"  {venv_python} {wb_script} query --type person")
    print(f"  {venv_python} {wb_script} sync --status")
    print()
    print("Or activate the venv first:")
    if sys.platform == "win32":
        print(f"  {os.path.join(venv_path, 'Scripts', 'activate')}")
    else:
        print(f"  source {os.path.join(venv_path, 'bin', 'activate')}")
    print(f"  python {wb_script} sync --full")


if __name__ == "__main__":
    main()
