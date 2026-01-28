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


@dataclass
class Node:
    id: str
    type: NodeType
    label: str = ""
    ast_node: Any = None  # Reference to original Tree-sitter node (opaque)
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
    A wrapper around NetworkX DiGraph to enforce strict logic semantics.
    """

    def __init__(self, name: str):
        self.name = name
        self.graph = nx.DiGraph()
        self.entry_node: Optional[str] = None
        self._counter = 0

    def _gen_id(self, prefix: str) -> str:
        self._counter += 1
        return f"{prefix}_{self._counter}"

    def add_node(self, type: NodeType, label: str = "", ast_node=None) -> Node:
        # Auto-generate ID based on type
        nid = self._gen_id(type.name.lower())
        node = Node(id=nid, type=type, label=label, ast_node=ast_node)
        self.graph.add_node(nid, data=node)
        return node

    def add_edge(self, source: Node, target: Node, type: EdgeType, label: str = ""):
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
