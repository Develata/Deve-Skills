from typing import Optional, Any
from ir_graph import NodeType, EdgeType, Node


class PythonStmtMixin:
    """
    Handles simple statements, try/except, and with blocks.
    """

    def _dispatch_statement(self, node, current_node: Node) -> Optional[Node]:
        t = node.type

        # Simple statements
        if t == "expression_statement":
            # Handle assignments, calls within expression stmt
            return self._dispatch_statement(node.children[0], current_node)
        elif t == "assignment":
            return self._handle_simple_stmt(node, current_node, label_prefix="")
        elif t == "return_statement":
            return self._handle_return(node, current_node)
        elif t == "raise_statement":
            return self._handle_raise(node, current_node)
        elif t == "assert_statement":
            return self._handle_simple_stmt(node, current_node, label_prefix="assert ")
        elif t == "call":
            return self._handle_call(node, current_node)

        # Complex statements
        elif t == "try_statement":
            return self._handle_try(node, current_node)
        elif t == "with_statement":
            return self._handle_with(node, current_node)
        elif t == "function_definition":
            # Nested function def is just a statement that defines a name
            return self._handle_simple_stmt(node, current_node, label_prefix="def ")
        elif t == "class_definition":
            return self._handle_simple_stmt(node, current_node, label_prefix="class ")

        # Flow dispatch
        elif t in [
            "if_statement",
            "for_statement",
            "while_statement",
            "match_statement",
        ]:
            return self._dispatch_flow(node, current_node)
        elif t in ["break_statement", "continue_statement"]:
            return self._dispatch_flow(node, current_node)

        # Default fallback
        else:
            return self._handle_simple_stmt(node, current_node)

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

    def _handle_call(self, node, current_node: Node) -> Optional[Node]:
        func_node = node.child_by_field_name("function")
        func_name = self._get_text(func_node)

        call_node = self.graph.add_node(
            NodeType.CALL, label=f"{func_name}()", ast_node=node
        )
        self.graph.add_edge(current_node, call_node, EdgeType.SEQ)
        return call_node

    def _handle_return(self, node, current_node: Node) -> Optional[Node]:
        ret_node = self.graph.add_node(NodeType.EXIT, label="return", ast_node=node)
        self.graph.add_edge(current_node, ret_node, EdgeType.SEQ)
        if self.fn_exit:
            self.graph.add_edge(ret_node, self.fn_exit, EdgeType.SEQ)
        return None

    def _handle_raise(self, node, current_node: Node) -> Optional[Node]:
        raise_node = self.graph.add_node(NodeType.EXIT, label="raise", ast_node=node)
        self.graph.add_edge(current_node, raise_node, EdgeType.SEQ)
        if self.fn_exit:
            self.graph.add_edge(raise_node, self.fn_exit, EdgeType.ERR)
        return None

    def _handle_try(self, node, current_node: Node) -> Optional[Node]:
        # try -> body
        #     -> except 1
        #     -> except 2

        # Virtual Scope Node acting as the 'Fork' for exceptions
        try_scope = self.graph.add_node(
            NodeType.VIRTUAL, label="try scope", ast_node=node
        )
        self.graph.add_edge(current_node, try_scope, EdgeType.SEQ)

        # The 'Happy Path' enters the block
        body = node.child_by_field_name("body")
        body_end = self._process_block(body, try_scope)

        # Finally block (if any)
        finally_node = None
        finally_clause = node.child_by_field_name("finalizer")
        if finally_clause:
            # finally is a convergence point.
            # It's executed after body_end OR after except blocks.
            finally_body = finally_clause.child_by_field_name("body")
            # We treat finally start as a JOIN point logically, but also a BLOCK start.
            finally_start = self.graph.add_node(NodeType.JOIN, label="finally")
            finally_node = finally_start

        # Process Except blocks
        exception_handlers = []
        for child in node.children:
            if child.type == "except_clause":
                # Link from Try Scope to Handler (ERR edge)
                handler_start = self.graph.add_node(
                    NodeType.BLOCK, label="except", ast_node=child
                )
                self.graph.add_edge(try_scope, handler_start, EdgeType.ERR, label="Ex")

                handler_body = child.child_by_field_name("body")
                if handler_body:  # Check for body existence
                    handler_end = self._process_block(handler_body, handler_start)
                    if handler_end:
                        exception_handlers.append(handler_end)
                else:
                    # Except block without body? Unlikely in valid python but possible in partial parse.
                    exception_handlers.append(handler_start)

        # Convergence
        join_target = (
            finally_node
            if finally_node
            else self.graph.add_node(NodeType.JOIN, label="end try")
        )

        # Connect Happy Path
        if body_end:
            self.graph.add_edge(body_end, join_target, EdgeType.SEQ)

        # Connect Handlers
        for handler_end in exception_handlers:
            self.graph.add_edge(handler_end, join_target, EdgeType.SEQ)

        # Process Finally Body if exists
        if finally_node:
            finalizer = node.child_by_field_name("finalizer")
            fin_body = finalizer.child_by_field_name("body")
            return self._process_block(fin_body, finally_node)

        return join_target

    def _handle_with(self, node, current_node: Node) -> Optional[Node]:
        # with A() as x:
        #   body
        # implicit: __exit__ called at end

        # 1. Context Entry
        items = node.child_by_field_name("items")  # could be multiple
        # For prototype, simplify to single label
        ctx_label = "with ..."

        enter_node = self.graph.add_node(NodeType.CALL, label=ctx_label, ast_node=node)
        self.graph.add_edge(current_node, enter_node, EdgeType.SEQ)

        # 2. Body
        body = node.child_by_field_name("body")
        body_end = self._process_block(body, enter_node)

        if body_end is None:
            return (
                None  # Returned inside with? __exit__ still called but flow diverged.
            )

        # 3. Context Exit (Virtual)
        exit_node = self.graph.add_node(NodeType.VIRTUAL, label="__exit__")
        self.graph.add_edge(body_end, exit_node, EdgeType.SEQ)

        return exit_node
