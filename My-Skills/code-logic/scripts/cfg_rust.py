from typing import Optional
from ir_graph import UniversalLogicGraph, NodeType, EdgeType, Node


class RustCFGBuilder:
    def __init__(self, code_bytes: bytes):
        self.code = code_bytes
        self.graph = UniversalLogicGraph("rust_cfg")
        self.loop_stack = []  # Stack of (continue_target, break_target) nodes

    def build_from_function(self, fn_node):
        """
        Builds CFG for a single function_item node.
        """
        fn_name = self._get_text(fn_node.child_by_field_name("name"))
        entry = self.graph.add_node(
            NodeType.BLOCK, label=f"fn {fn_name}", ast_node=fn_node
        )
        self.graph.set_entry(entry)

        # Create a unified Exit node for the function
        self.fn_exit = self.graph.add_node(NodeType.EXIT, label="Function Exit")

        body = fn_node.child_by_field_name("body")
        if body:
            final_node = self._process_block(body, entry)
            # If the final node isn't already an exit (i.e. flow didn't terminate), connect to function exit
            if final_node and final_node.type != NodeType.EXIT:
                self.graph.add_edge(final_node, self.fn_exit, EdgeType.SEQ)

        return self.graph

    def _process_block(self, block_node, parent_node: Node) -> Optional[Node]:
        """
        Process a block of statements ({ ... }).
        Returns the last node in the flow, or None if flow terminates (e.g., return).
        """
        current = parent_node

        # Iterate over children
        for child in block_node.children:
            if child.type in ["{", "}", "line_comment", "block_comment"]:
                continue

            # Check if flow is already terminated (unreachable code)
            if current is None:
                # We could log a warning about unreachable code here
                continue

            # Dispatch
            current = self._dispatch_statement(child, current)

        return current

    def _dispatch_statement(self, node, current_node: Node) -> Optional[Node]:
        """
        Handles a single statement/expression node.
        Returns the node after this statement executes.
        """
        # 1. First, check for hidden control flow inside expressions (like '?')
        # We need to process pre-computation logic that might branch early.
        current_node = self._scan_for_try_operator(node, current_node)
        if current_node is None:
            return None  # Flow terminated by ? error path

        t = node.type

        if t == "let_declaration":
            return self._handle_simple_stmt(node, current_node, label_prefix="let ")
        elif t == "return_expression":
            return self._handle_return(node, current_node)
        elif t == "expression_statement":
            # Unwrap and handle inner expression
            return self._dispatch_statement(node.children[0], current_node)
        elif t == "if_expression":
            return self._handle_if(node, current_node)
        elif t == "match_expression":
            return self._handle_match(node, current_node)
        elif t == "loop_expression":
            return self._handle_loop(node, current_node)
        elif t == "while_expression":
            return self._handle_while(node, current_node)
        elif t == "for_expression":
            return self._handle_for(node, current_node)
        elif t == "break_expression":
            return self._handle_break(node, current_node)
        elif t == "continue_expression":
            return self._handle_continue(node, current_node)
        elif t == "macro_invocation":
            return self._handle_macro(node, current_node)
        else:
            # Generic expression/statement (function calls, assignments)
            return self._handle_simple_stmt(node, current_node)

    def _scan_for_try_operator(self, root_node, current_node: Node) -> Optional[Node]:
        """
        DFS scan for `try_expression` (the '?' operator).
        If found, insert a Virtual split node.
        """
        if root_node.type == "try_expression":
            # logic: operand -> ? -> (next / return err)

            # Add the Check Point
            check_node = self.graph.add_node(
                NodeType.VIRTUAL, label="Check '?'", ast_node=root_node
            )
            self.graph.add_edge(current_node, check_node, EdgeType.SEQ)

            # Add Error Path (Exit)
            self.graph.add_edge(check_node, self.fn_exit, EdgeType.ERR, label="Err")

            # Continue Path
            return check_node

        # Recursive step
        temp_current = current_node
        if hasattr(root_node, "children"):
            for child in root_node.children:
                result = self._scan_for_try_operator(child, temp_current)
                # If we detected a '?', update temp_current to the new virtual node
                if result is not None and result != temp_current:
                    temp_current = result
                # Note: scan_for_try_operator semantics in original thought were mixed.
                # Correct logic: We modify the graph and return the "latest" node to attach subsequent logic to.
                # If recursion returns something different, it means we advanced.

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
        return None  # Flow terminates here

    def _handle_macro(self, node, current_node: Node) -> Optional[Node]:
        macro_name = self._get_text(node.child_by_field_name("name"))
        if macro_name == "panic":
            p_node = self.graph.add_node(NodeType.EXIT, label="panic!", ast_node=node)
            self.graph.add_edge(current_node, p_node, EdgeType.SEQ)
            return None
        else:
            return self._handle_simple_stmt(node, current_node)

    def _handle_if(self, node, current_node: Node) -> Optional[Node]:
        cond_node = node.child_by_field_name("condition")
        cond_text = self._get_text(cond_node)

        fork = self.graph.add_node(
            NodeType.FORK, label=f"if {cond_text}", ast_node=node
        )
        self.graph.add_edge(current_node, fork, EdgeType.SEQ)

        consequence = node.child_by_field_name("consequence")
        true_end = self._process_block(consequence, fork)
        self._update_last_edge_type(fork, EdgeType.COND_TRUE, "True")

        alternative = node.child_by_field_name("alternative")
        false_end = fork

        if alternative:
            if alternative.type == "block":
                false_end = self._process_block(alternative, fork)
            else:
                false_end = self._dispatch_statement(alternative, fork)

            self._update_last_edge_type(fork, EdgeType.COND_FALSE, "False")

        if true_end is None and false_end is None:
            return None

        join = self.graph.add_node(NodeType.JOIN, label="fi")

        if true_end:
            self.graph.add_edge(true_end, join, EdgeType.SEQ)

        if false_end:
            if false_end == fork:
                self.graph.add_edge(fork, join, EdgeType.COND_FALSE, "False")
            else:
                self.graph.add_edge(false_end, join, EdgeType.SEQ)

        return join

    def _handle_match(self, node, current_node: Node) -> Optional[Node]:
        value_node = node.child_by_field_name("value")
        value_text = self._get_text(value_node)

        fork = self.graph.add_node(
            NodeType.FORK, label=f"match {value_text}", ast_node=node
        )
        self.graph.add_edge(current_node, fork, EdgeType.SEQ)

        body = node.child_by_field_name("body")

        join = self.graph.add_node(NodeType.JOIN, label="end match")
        has_paths = False

        for child in body.children:
            if child.type == "match_arm":
                pattern = child.child_by_field_name("pattern")
                pat_text = self._get_text(pattern)
                value = child.child_by_field_name("value")

                arm_end = None
                if value.type == "block":
                    arm_end = self._process_block(value, fork)
                else:
                    arm_end = self._dispatch_statement(value, fork)

                self._update_last_edge_type(fork, EdgeType.COND_TRUE, pat_text)

                if arm_end:
                    self.graph.add_edge(arm_end, join, EdgeType.SEQ)
                    has_paths = True

        if not has_paths:
            return None

        return join

    def _handle_loop(self, node, current_node: Node) -> Optional[Node]:
        loop_entry = self.graph.add_node(NodeType.JOIN, label="loop", ast_node=node)
        self.graph.add_edge(current_node, loop_entry, EdgeType.SEQ)

        loop_exit = self.graph.add_node(NodeType.JOIN, label="end loop")
        self.loop_stack.append((loop_entry, loop_exit))

        body = node.child_by_field_name("body")
        body_end = self._process_block(body, loop_entry)

        if body_end:
            self.graph.add_edge(body_end, loop_entry, EdgeType.JUMP, "repeat")

        self.loop_stack.pop()
        return loop_exit

    def _handle_while(self, node, current_node: Node) -> Optional[Node]:
        cond = node.child_by_field_name("condition")
        cond_text = self._get_text(cond)

        check = self.graph.add_node(
            NodeType.FORK, label=f"while {cond_text}", ast_node=node
        )
        self.graph.add_edge(current_node, check, EdgeType.SEQ)

        loop_exit = self.graph.add_node(NodeType.JOIN, label="end while")
        self.graph.add_edge(check, loop_exit, EdgeType.COND_FALSE, "False")

        self.loop_stack.append((check, loop_exit))

        body = node.child_by_field_name("body")
        body_end = self._process_block(body, check)
        self._update_last_edge_type(check, EdgeType.COND_TRUE, "True")

        if body_end:
            self.graph.add_edge(body_end, check, EdgeType.JUMP, "repeat")

        self.loop_stack.pop()
        return loop_exit

    def _handle_for(self, node, current_node: Node) -> Optional[Node]:
        pat = node.child_by_field_name("pattern")
        val = node.child_by_field_name("value")
        label = f"for {self._get_text(pat)} in {self._get_text(val)}"

        check = self.graph.add_node(NodeType.FORK, label=label, ast_node=node)
        self.graph.add_edge(current_node, check, EdgeType.SEQ)

        loop_exit = self.graph.add_node(NodeType.JOIN, label="end for")
        self.graph.add_edge(check, loop_exit, EdgeType.COND_FALSE, "Done")

        self.loop_stack.append((check, loop_exit))

        body = node.child_by_field_name("body")
        body_end = self._process_block(body, check)
        self._update_last_edge_type(check, EdgeType.COND_TRUE, "Next")

        if body_end:
            self.graph.add_edge(body_end, check, EdgeType.JUMP, "repeat")

        self.loop_stack.pop()
        return loop_exit

    def _handle_break(self, node, current_node: Node) -> Optional[Node]:
        if not self.loop_stack:
            return current_node
        _, loop_exit = self.loop_stack[-1]
        self.graph.add_edge(current_node, loop_exit, EdgeType.JUMP, "break")
        return None

    def _handle_continue(self, node, current_node: Node) -> Optional[Node]:
        if not self.loop_stack:
            return current_node
        loop_entry, _ = self.loop_stack[-1]
        self.graph.add_edge(current_node, loop_entry, EdgeType.JUMP, "continue")
        return None

    def _update_last_edge_type(
        self, source_node: Node, new_type: EdgeType, new_label: str
    ):
        out_edges = list(self.graph.graph.out_edges(source_node.id, data=True))
        if out_edges:
            u, v, data = out_edges[-1]
            data["type"] = new_type
            data["label"] = new_label

    def _get_text(self, node) -> str:
        if not node:
            return ""
        return self.code[node.start_byte : node.end_byte].decode("utf-8")
