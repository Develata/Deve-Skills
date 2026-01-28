from typing import Optional, Any
from ir_graph import NodeType, EdgeType, Node


class RustStmtMixin:
    """
    Handles simple statements and expressions logic.
    Part of the RustCFGBuilder mixin composition.
    """

    def _dispatch_statement(self, node, current_node: Node) -> Optional[Node]:
        # 1. Check for '?' operator side effects first
        current_node = self._scan_for_try_operator(node, current_node)
        if current_node is None:
            return None

        t = node.type

        # Simple statements dispatch
        if t == "let_declaration":
            return self._handle_simple_stmt(node, current_node, label_prefix="let ")
        elif t == "return_expression":
            return self._handle_return(node, current_node)
        elif t == "expression_statement":
            return self._dispatch_statement(node.children[0], current_node)
        elif t == "macro_invocation":
            return self._handle_macro(node, current_node)

        # Complex flow dispatch (delegated to RustFlowMixin)
        elif t in [
            "if_expression",
            "match_expression",
            "loop_expression",
            "while_expression",
            "for_expression",
            "break_expression",
            "continue_expression",
        ]:
            return self._dispatch_flow(node, current_node)

        # Default fallback
        else:
            return self._handle_simple_stmt(node, current_node)

    def _scan_for_try_operator(self, root_node, current_node: Node) -> Optional[Node]:
        """
        DFS scan for `try_expression` (?).
        Fix: Stops at closure/async boundaries to prevent scope leakage.
        """
        # Stop recursion at scope boundaries
        if root_node.type in ["closure_expression", "async_block"]:
            return current_node

        if root_node.type == "try_expression":
            # Found '?': Insert Virtual Node & Error Path
            check_node = self.graph.add_node(
                NodeType.VIRTUAL, label="Check '?'", ast_node=root_node
            )
            self.graph.add_edge(current_node, check_node, EdgeType.SEQ)
            self.graph.add_edge(check_node, self.fn_exit, EdgeType.ERR, label="Err")
            return check_node

        # Recursive Step
        temp_current = current_node
        if hasattr(root_node, "children"):
            for child in root_node.children:
                result = self._scan_for_try_operator(child, temp_current)
                # If advanced, update pointer
                if result is not None and result != temp_current:
                    temp_current = result
                # If flow terminated (e.g. nested ? failed?), handle it?
                # For now assuming linear scan logic updates temp_current

        return temp_current

    def _handle_simple_stmt(
        self, node, current_node: Node, label_prefix=""
    ) -> Optional[Node]:
        text = self._get_text(node)
        summary = text.split("\n")[0].strip()
        if len(summary) > 40:
            summary = summary[:37] + "..."
        if label_prefix and not summary.startswith(label_prefix):
            summary = label_prefix + summary

        stmt_node = self.graph.add_node(NodeType.BLOCK, label=summary, ast_node=node)
        self.graph.add_edge(current_node, stmt_node, EdgeType.SEQ)
        return stmt_node

    def _handle_return(self, node, current_node: Node) -> Optional[Node]:
        ret_node = self.graph.add_node(NodeType.EXIT, label="return", ast_node=node)
        self.graph.add_edge(current_node, ret_node, EdgeType.SEQ)
        self.graph.add_edge(ret_node, self.fn_exit, EdgeType.SEQ)
        return None

    def _handle_macro(self, node, current_node: Node) -> Optional[Node]:
        macro_name = self._get_text(node.child_by_field_name("name"))
        if macro_name == "panic":
            p_node = self.graph.add_node(NodeType.EXIT, label="panic!", ast_node=node)
            self.graph.add_edge(current_node, p_node, EdgeType.SEQ)
            return None
        return self._handle_simple_stmt(node, current_node)
