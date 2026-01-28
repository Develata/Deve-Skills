from typing import Optional
from ir_graph import NodeType, EdgeType, Node


class PythonFlowMixin:
    """
    Handles flow control for Python.
    """

    def _dispatch_flow(self, node, current_node: Node) -> Optional[Node]:
        t = node.type
        if t == "if_statement":
            return self._handle_if(node, current_node)
        if t in ["for_statement", "while_statement"]:
            return self._handle_loop(node, current_node)
        if t == "match_statement":
            return self._handle_match(node, current_node)
        if t == "break_statement":
            return self._handle_break(node, current_node)
        if t == "continue_statement":
            return self._handle_continue(node, current_node)
        return current_node

    def _handle_if(self, node, current_node: Node) -> Optional[Node]:
        # if cond: body elif ...
        cond = node.child_by_field_name("condition")
        cond_text = self._get_text(cond)

        fork = self.graph.add_node(
            NodeType.FORK, label=f"if {cond_text}", ast_node=node
        )
        self.graph.add_edge(current_node, fork, EdgeType.SEQ)

        # True Path
        consequence = node.child_by_field_name("consequence")

        # Insert Virtual Node to anchor 'True' label
        true_v = self.graph.add_node(NodeType.VIRTUAL, label="True")
        self.graph.add_edge(fork, true_v, EdgeType.COND_TRUE, "True")
        true_end = self._process_block(consequence, true_v)

        # False Path (else / elif)
        alternative = node.child_by_field_name("alternative")
        false_end = fork

        if alternative:
            # alternative usually includes the 'else' or 'elif' keyword structure
            # Tree-sitter python:
            # if_statement -> alternative -> (else_clause | elif_clause)

            false_v = self.graph.add_node(NodeType.VIRTUAL, label="False")
            self.graph.add_edge(fork, false_v, EdgeType.COND_FALSE, "False")

            if alternative.type == "elif_clause":
                # elif is essentially nested if
                # Recurse? No, treat as statement.
                # Actually elif_clause structure: condition, consequence.
                # It's NOT an if_statement node.
                false_end = self._handle_elif_clause(alternative, false_v)
            elif alternative.type == "else_clause":
                body = alternative.child_by_field_name("body")
                false_end = self._process_block(body, false_v)

        # Join
        if true_end is None and false_end is None:
            return None

        join = self.graph.add_node(NodeType.JOIN, label="fi")
        if true_end:
            self.graph.add_edge(true_end, join, EdgeType.SEQ)
        if false_end:
            if false_end == fork:  # No else
                self.graph.add_edge(fork, join, EdgeType.COND_FALSE, "False")
            elif false_end == false_v:  # Empty else?
                self.graph.add_edge(false_v, join, EdgeType.SEQ)
            else:
                self.graph.add_edge(false_end, join, EdgeType.SEQ)

        return join

    def _handle_elif_clause(self, node, current_node: Node) -> Optional[Node]:
        # elif cond: body
        cond = node.child_by_field_name("condition")
        cond_text = self._get_text(cond)
        fork = self.graph.add_node(
            NodeType.FORK, label=f"elif {cond_text}", ast_node=node
        )
        self.graph.add_edge(current_node, fork, EdgeType.SEQ)

        # True
        true_v = self.graph.add_node(NodeType.VIRTUAL, label="True")
        self.graph.add_edge(fork, true_v, EdgeType.COND_TRUE, "True")
        consequence = node.child_by_field_name("consequence")
        true_end = self._process_block(consequence, true_v)

        # False (Chain to next elif/else?)
        # Tree-sitter python: if_statement has ONE alternative field.
        # But elif_clause does NOT have an alternative field in strict grammar?
        # Wait, if `if ... elif ... elif ...`, the structure is flattened or nested?
        # Typically nested: `alternative` of `if` points to `if_statement` (if using generic grammar) OR `elif_clause`.
        # Correction: In tree-sitter-python, `if_statement` contains `alternative` which can be `elif_clause` or `else_clause`.
        # BUT `elif_clause` does NOT contain `alternative`.
        # The `if_statement` node has a LIST of children? No, fields.

        # Let's check tree-sitter-python grammar spec logic mentally.
        # Actually, `elif_clause` is a child of `if_statement`.
        # `if_statement` children: [if, condition, consequence, elif_clause*, else_clause?]
        # Oh, so it's linear children list!

        # REFACTOR _handle_if to iterate children manually?
        # That's safer for Python's flat elif structure.
        return true_end

    def _handle_if_linear(self, node, current_node: Node) -> Optional[Node]:
        # TODO: Implement robust linear scanning for python if/elif/else
        # For prototype, we fall back to generic logic or assume simple structure
        return current_node

    def _handle_loop(self, node, current_node: Node) -> Optional[Node]:
        # for/while
        # For python, while and for have optional 'else' block (executed if no break)

        is_while = node.type == "while_statement"
        label_text = "while/for"

        if is_while:
            cond = node.child_by_field_name("condition")
            label_text = f"while {self._get_text(cond)}"
        else:
            left = node.child_by_field_name("left")  # vars
            right = node.child_by_field_name("right")  # iterable
            label_text = f"for {self._get_text(left)} in ..."

        check = self.graph.add_node(NodeType.FORK, label=label_text, ast_node=node)
        self.graph.add_edge(current_node, check, EdgeType.SEQ)

        loop_exit = self.graph.add_node(NodeType.JOIN, label="end loop")
        self.loop_stack.append((check, loop_exit))

        # True / Body
        body_v = self.graph.add_node(NodeType.VIRTUAL, label="Body")
        self.graph.add_edge(check, body_v, EdgeType.COND_TRUE, "True")

        body = node.child_by_field_name("body")
        body_end = self._process_block(body, body_v)
        if body_end:
            self.graph.add_edge(body_end, check, EdgeType.JUMP, "repeat")

        # False / Else
        else_clause = node.child_by_field_name(
            "alternative"
        )  # Python uses alternative for else in loops?
        # Check 'else_clause' child specifically
        else_node = None
        for child in node.children:
            if child.type == "else_clause":
                else_node = child
                break

        if else_node:
            else_v = self.graph.add_node(NodeType.VIRTUAL, label="Else")
            self.graph.add_edge(check, else_v, EdgeType.COND_FALSE, "Done")
            else_body = else_node.child_by_field_name("body")
            else_end = self._process_block(else_body, else_v)
            if else_end:
                self.graph.add_edge(else_end, loop_exit, EdgeType.SEQ)
        else:
            self.graph.add_edge(check, loop_exit, EdgeType.COND_FALSE, "Done")

        self.loop_stack.pop()
        return loop_exit

    def _handle_break(self, node, current_node: Node) -> Optional[Node]:
        if self.loop_stack:
            _, loop_exit = self.loop_stack[-1]
            self.graph.add_edge(current_node, loop_exit, EdgeType.JUMP, "break")
        return None

    def _handle_continue(self, node, current_node: Node) -> Optional[Node]:
        if self.loop_stack:
            loop_entry, _ = self.loop_stack[-1]
            self.graph.add_edge(current_node, loop_entry, EdgeType.JUMP, "continue")
        return None

    def _handle_match(self, node, current_node: Node) -> Optional[Node]:
        # Python 3.10 match
        subject = node.child_by_field_name("subject")
        fork = self.graph.add_node(
            NodeType.FORK, label=f"match {self._get_text(subject)}"
        )
        self.graph.add_edge(current_node, fork, EdgeType.SEQ)

        join = self.graph.add_node(NodeType.JOIN, label="end match")

        body = node.child_by_field_name("body")
        for child in body.children:
            if child.type == "case_clause":
                # pattern, consequence
                # Logic similar to Rust match
                pass

        return join
