"""NetworkX graph store for entity relationship queries.

Graph persisted as JSON at _meta/wb-graph.json relative to vault root.
"""

from __future__ import annotations

import json
import os
from abc import ABC, abstractmethod
from collections import deque
from typing import Any, Optional

import networkx as nx

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from wb_core.validation import RELATIONSHIP_INVERSES


class GraphAdapter(ABC):
    """Abstract base for graph stores."""

    @abstractmethod
    def add_entity(self, id: str, attrs: dict) -> None: ...

    @abstractmethod
    def add_relationship(self, src: str, tgt: str, attrs: dict) -> None: ...

    @abstractmethod
    def remove_entity(self, id: str) -> None: ...

    @abstractmethod
    def neighbors(self, id: str, edge_types: Optional[list[str]] = None, depth: int = 1) -> list: ...

    @abstractmethod
    def shortest_path(self, src: str, tgt: str) -> list: ...

    @abstractmethod
    def subgraph(self, entity_ids: list[str]) -> dict: ...

    @abstractmethod
    def serialize(self, path: str) -> None: ...

    @abstractmethod
    def deserialize(self, path: str) -> None: ...


class NetworkXGraphStore(GraphAdapter):
    """NetworkX MultiDiGraph-backed graph store."""

    def __init__(self, vault_root: str):
        self.vault_root = vault_root
        self.graph_path = os.path.join(vault_root, "_meta", "wb-graph.json")
        self.graph: nx.MultiDiGraph = nx.MultiDiGraph()

        if os.path.exists(self.graph_path):
            self.deserialize(self.graph_path)

    def add_entity(self, id: str, attrs: dict) -> None:
        """Add or update a node with the given attributes."""
        self.graph.add_node(id, **attrs)

    def add_relationship(self, src: str, tgt: str, attrs: dict) -> None:
        """Add a directed edge from src to tgt, plus the inverse edge."""
        # Ensure both nodes exist
        if not self.graph.has_node(src):
            self.graph.add_node(src)
        if not self.graph.has_node(tgt):
            self.graph.add_node(tgt)

        self.graph.add_edge(src, tgt, **attrs)

        # Add inverse edge
        rel_type = attrs.get("type", "")
        inverse_type = RELATIONSHIP_INVERSES.get(rel_type, rel_type)
        inverse_attrs = {**attrs, "type": inverse_type}
        self.graph.add_edge(tgt, src, **inverse_attrs)

    def remove_entity(self, id: str) -> None:
        """Remove a node and all incident edges."""
        if self.graph.has_node(id):
            self.graph.remove_node(id)

    def neighbors(
        self,
        id: str,
        edge_types: Optional[list[str]] = None,
        depth: int = 1,
    ) -> list:
        """BFS to find neighbors up to given depth, optionally filtered by edge type.

        Returns list of dicts: {"id": str, "depth": int, "edge_type": str}.
        """
        if not self.graph.has_node(id):
            return []

        visited: set[str] = {id}
        results: list[dict] = []
        queue: deque[tuple[str, int]] = deque([(id, 0)])

        while queue:
            current, current_depth = queue.popleft()
            if current_depth >= depth:
                continue

            # Check both successors and predecessors for full neighborhood
            for neighbor in set(self.graph.successors(current)) | set(self.graph.predecessors(current)):
                if neighbor in visited:
                    continue

                # Check edge types if filter is specified
                edges_out = self.graph.get_edge_data(current, neighbor) or {}
                edges_in = self.graph.get_edge_data(neighbor, current) or {}

                all_edges = list(edges_out.values()) + list(edges_in.values())
                edge_type_strs = [e.get("type", "") for e in all_edges]

                if edge_types:
                    matching = [t for t in edge_type_strs if t in edge_types]
                    if not matching:
                        continue
                    edge_type_str = matching[0]
                else:
                    edge_type_str = edge_type_strs[0] if edge_type_strs else ""

                visited.add(neighbor)
                results.append({
                    "id": neighbor,
                    "depth": current_depth + 1,
                    "edge_type": edge_type_str,
                })
                queue.append((neighbor, current_depth + 1))

        return results

    def shortest_path(self, src: str, tgt: str) -> list:
        """Find shortest path between two nodes (ignoring edge direction)."""
        try:
            undirected = self.graph.to_undirected()
            return nx.shortest_path(undirected, src, tgt)
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return []

    def subgraph(self, entity_ids: list[str]) -> dict:
        """Extract a subgraph as a serializable dict."""
        existing_ids = [eid for eid in entity_ids if self.graph.has_node(eid)]
        sg = self.graph.subgraph(existing_ids)
        data = nx.node_link_data(sg)
        return data

    def serialize(self, path: str = None) -> None:
        """Write graph to JSON file."""
        target = path or self.graph_path
        os.makedirs(os.path.dirname(target), exist_ok=True)
        data = nx.node_link_data(self.graph)
        with open(target, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)

    def deserialize(self, path: str = None) -> None:
        """Load graph from JSON file."""
        target = path or self.graph_path
        if not os.path.exists(target):
            return
        with open(target, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.graph = nx.node_link_graph(data, directed=True, multigraph=True)

    def node_count(self) -> int:
        return self.graph.number_of_nodes()

    def edge_count(self) -> int:
        return self.graph.number_of_edges()

    def has_entity(self, id: str) -> bool:
        return self.graph.has_node(id)

    def get_all_ids(self) -> list[str]:
        return list(self.graph.nodes())
