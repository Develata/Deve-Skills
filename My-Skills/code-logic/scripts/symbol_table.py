from typing import Dict, Optional, List, Tuple
from dataclasses import dataclass


@dataclass
class SymbolInfo:
    name: str
    file_path: str
    node_id: str  # The ID in the ULG
    description: str = ""


class SymbolTable:
    def __init__(self):
        # Map simple function name to list of potential definitions
        # Key: "function_name", Value: [SymbolInfo, ...]
        self.index: Dict[str, List[SymbolInfo]] = {}

    def register(self, name: str, file_path: str, node_id: str, description: str = ""):
        if name not in self.index:
            self.index[name] = []

        self.index[name].append(SymbolInfo(name, file_path, node_id, description))

    def resolve(self, name: str) -> Optional[SymbolInfo]:
        """
        Resolve a function name to a single definition.
        Heuristic:
        1. If only one match, return it.
        2. If multiple, return None (ambiguous) or first?
        For V1.3, we return first if unique, else None to avoid false links.
        Wait, heuristics can be smarter later.
        """
        candidates = self.index.get(name)
        if not candidates:
            return None

        if len(candidates) == 1:
            return candidates[0]

        # Ambiguity resolution logic could go here (e.g. check import paths)
        # For now, return None to be strict/unassailable.
        # Or return the first one if we accept looseness?
        # Perfect logic requires strictness. Ambiguity = No explicit link.
        return None

    def get_candidates(self, name: str) -> List[SymbolInfo]:
        return self.index.get(name, [])
