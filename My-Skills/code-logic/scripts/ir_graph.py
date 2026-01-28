from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional, List, Any, Dict
import networkx as nx

# --- Definitions ---


class NodeType(Enum):
    BLOCK = auto()  # Sequence of statements
    FORK = auto()  # Branching point (if, match)
    JOIN = auto()  # Merge point
    CALL = auto()  # Function call
    VIRTUAL = auto()  # Implicit logic (e.g., '?' operator)
    EXIT = auto()  # Return or Panic


class EdgeType(Enum):
    SEQ = auto()  # Sequential flow
    COND_TRUE = auto()  # Condition matches / True branch
    COND_FALSE = auto()  # Condition fails / False branch
    ERR = auto()  # Error propagation / Panic
    JUMP = auto()  # Loop back
    LINK = auto()  # Cross-file reference (New in v1.3)


@dataclass
class Node:
    id: str
    type: NodeType
    label: str = ""
    ast_node: Any = None
    description: str = ""  # Added for Chinese comments
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __hash__(self):
        return hash(self.id)


@dataclass
class Edge:
    source: str
    target: str
    type: EdgeType
    label: str = ""


# --- Graph Structure ---


class UniversalLogicGraph:
    """
    Wrapper around NetworkX DiGraph.
    Refactored to support atomic edge creation.
    """

    def __init__(self, name: str):
        self.name = name
        self.graph = nx.DiGraph()
        self.entry_node: Optional[str] = None
        self._counter = 0

    def _gen_id(self, prefix: str) -> str:
        self._counter += 1
        return f"{prefix}_{self._counter}"

    def add_node(
        self, type: NodeType, label: str = "", ast_node=None, description: str = ""
    ) -> Node:
        nid = self._gen_id(type.name.lower())
        node = Node(
            id=nid, type=type, label=label, ast_node=ast_node, description=description
        )
        self.graph.add_node(nid, data=node)
        return node

    def add_edge(self, source: Node, target: Node, type: EdgeType, label: str = ""):
        """
        Atomic edge creation. No more post-hoc patching.
        """
        self.graph.add_edge(source.id, target.id, type=type, label=label)

    def get_node(self, nid: str) -> Node:
        return self.graph.nodes[nid]["data"]

    def set_entry(self, node: Node):
        self.entry_node = node.id

    def nodes(self):
        for nid in self.graph.nodes:
            yield self.get_node(nid)

    def edges(self):
        for u, v, data in self.graph.edges(data=True):
            yield (self.get_node(u), self.get_node(v), data["type"], data["label"])

    def merge_graph(self, other_graph, prefix: str):
        """
        Merge another graph into this one, prefixing IDs to avoid collisions.
        """
        id_map = {}

        # 1. Copy Nodes
        for node in other_graph.nodes():
            original_id = node.id
            new_id = f"{prefix}_{original_id}"
            id_map[original_id] = new_id

            # Create new node data copy
            new_node = Node(
                id=new_id,
                type=node.type,
                label=node.label,
                ast_node=node.ast_node,
                description=node.description,
                metadata=node.metadata.copy(),  # Shallow copy dict
            )
            # Tag with cluster info for Graphviz
            new_node.metadata["cluster"] = prefix

            self.graph.add_node(new_id, data=new_node)

        # 2. Copy Edges
        for u, v, type, label in other_graph.edges():
            new_u_id = id_map[u.id]
            new_v_id = id_map[v.id]
            self.graph.add_edge(new_u_id, new_v_id, type=type, label=label)
