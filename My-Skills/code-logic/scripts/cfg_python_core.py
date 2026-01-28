from typing import Optional
from ir_graph import UniversalLogicGraph, NodeType, EdgeType, Node
from cfg_python_stmt import PythonStmtMixin
from cfg_python_flow import PythonFlowMixin


class PythonCFGBuilder(PythonStmtMixin, PythonFlowMixin):
    """
    Python CFG Builder.
    """

    def __init__(self, code_bytes: bytes):
        self.code = code_bytes
        self.graph = UniversalLogicGraph("python_cfg")
        self.loop_stack = []
        self.fn_exit = None
        self.config_loader = None

    def set_config_loader(self, loader):
        self.config_loader = loader

    def build_from_function(self, fn_node):
        fn_name = self._get_text(fn_node.child_by_field_name("name"))

        desc = ""
        if self.config_loader:
            desc = self.config_loader.get_description(fn_name)

        entry = self.graph.add_node(
            NodeType.BLOCK, label=f"def {fn_name}", ast_node=fn_node, description=desc
        )
        self.graph.set_entry(entry)

        self.fn_exit = self.graph.add_node(NodeType.EXIT, label="return/exit")

        body = fn_node.child_by_field_name("body")
        final_node = self._process_block(body, entry)

        if final_node and final_node.type != NodeType.EXIT:
            self.graph.add_edge(
                final_node, self.fn_exit, EdgeType.SEQ
            )  # implicit return None

        return self.graph

    def _process_block(self, block_node, parent_node: Node) -> Optional[Node]:
        current = parent_node
        for child in block_node.children:
            if child.type in [":", "block_comment", "comment"]:
                continue  # Python specific tokens
            if current is None:
                continue
            current = self._dispatch_statement(child, current)
        return current

    def _get_text(self, node) -> str:
        if not node:
            return ""
        return self.code[node.start_byte : node.end_byte].decode("utf-8")
