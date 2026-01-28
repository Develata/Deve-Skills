import os
from tree_sitter import Language, Parser
import tree_sitter_rust


class ASTEngine:
    def __init__(self):
        self.parsers = {}
        self._init_rust()

    def _init_rust(self):
        try:
            # New API for tree-sitter >= 0.22
            rust_lang = Language(tree_sitter_rust.language())
            parser = Parser(rust_lang)
            self.parsers["rs"] = parser
        except Exception as e:
            print(f"Error initializing Rust parser: {e}")
            # Fallback or strict failure?
            # Given our "perfect" axiom, we should probably fail if we can't parse.
            raise e

    def parse_file(self, file_path: str):
        ext = file_path.split(".")[-1]
        if ext not in self.parsers:
            raise ValueError(f"Unsupported file extension: {ext}")

        with open(file_path, "rb") as f:
            code = f.read()

        tree = self.parsers[ext].parse(code)

        # Check for syntax errors
        if self._has_error(tree.root_node):
            print(
                f"Warning: Syntax errors detected in {file_path}. Analysis might be partial."
            )

        return tree, code

    def _has_error(self, node) -> bool:
        """Recursively check for ERROR nodes."""
        if node.type == "ERROR":
            return True
        for child in node.children:
            if self._has_error(child):
                return True
        return False


# Quick test if run directly
if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        engine = ASTEngine()
        tree, _ = engine.parse_file(sys.argv[1])
        print(tree.root_node.sexp())
