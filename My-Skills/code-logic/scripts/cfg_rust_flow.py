from typing import Optional
from ir_graph import NodeType, EdgeType, Node


class RustFlowMixin:
    """
    Handles complex control flow (if, match, loops).
    Part of the RustCFGBuilder mixin composition.
    """

    def _dispatch_flow(self, node, current_node: Node) -> Optional[Node]:
        t = node.type
        if t == "if_expression":
            return self._handle_if(node, current_node)
        if t == "match_expression":
            return self._handle_match(node, current_node)
        if t == "loop_expression":
            return self._handle_loop(node, current_node)
        if t == "while_expression":
            return self._handle_while(node, current_node)
        if t == "for_expression":
            return self._handle_for(node, current_node)
        if t == "break_expression":
            return self._handle_break(node, current_node)
        if t == "continue_expression":
            return self._handle_continue(node, current_node)
        return current_node

    def _handle_if(self, node, current_node: Node) -> Optional[Node]:
        cond_text = self._get_text(node.child_by_field_name("condition"))
        fork = self.graph.add_node(
            NodeType.FORK, label=f"if {cond_text}", ast_node=node
        )
        self.graph.add_edge(current_node, fork, EdgeType.SEQ)

        # True Branch
        true_start_node = self.graph.add_node(
            NodeType.BLOCK, label="Then", ast_node=node
        )  # Dummy connector?
        # Optimization: We pass the fork directly to process_block, but we want the edge to be labeled.
        # Since process_block is generic, we handle the edge manually here.

        # Branch 1: True
        consequence = node.child_by_field_name("consequence")
        # We process the block, starting from 'fork'.
        # But wait, IRGraph.add_edge allows us to specify type.
        # So we process the block *separately*? No, we need the block chain.

        # New strategy: Create a temporary node or just correct the edge logic?
        # Let's trust the logic: if we call _process_block(consequence, fork), it adds SEQ edge.
        # We want COND_TRUE.
        # To avoid patching, we manually invoke dispatch on children but use specific edge type for the first one.
        # Actually, simpler: Fork -> (True Edge) -> BlockStart.

        true_end = self._process_branch_block(
            consequence, fork, EdgeType.COND_TRUE, "True"
        )

        # Branch 2: False
        alternative = node.child_by_field_name("alternative")
        false_end = fork
        if alternative:
            # handle else if vs else block
            target = alternative
            # Skip the 'else' keyword node if present (tree-sitter structure usually puts block/if as field 'alternative')
            false_end = self._process_branch_block(
                target, fork, EdgeType.COND_FALSE, "False"
            )
        else:
            # Implicit else -> connect fork to join later with COND_FALSE
            pass

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

    def _process_branch_block(
        self, node, start_node, edge_type, edge_label
    ) -> Optional[Node]:
        """Helper to process a branch starting with a specific edge type."""
        # For the very first statement/block, we add the edge manually.
        # But _process_block iterates children.
        # We can create a dummy "Entry" for the block? No, adds noise.
        # We manually peek the first child?

        # Let's iterate manually for the first child to establish the edge.
        if node.type == "block":
            # It's a block { ... }
            # We use a custom version of process_block that accepts an edge type for the first link
            return self._process_block_custom_edge(
                node, start_node, edge_type, edge_label
            )
        else:
            # It's a single statement (e.g. else if ...)
            # We want: start_node --[edge_type]--> first_stmt
            # _dispatch_statement normally adds SEQ.
            # We can't easily override without patching or changing dispatch signature.
            # Patching IS the cleanest way if we don't want to pass edge_type everywhere.
            # But we promised no patching.

            # Solution: Create a 'Routing Node' (Virtual) if needed, or just accept patching for this specific case?
            # Or: add_edge(start, target, type) is called INSIDE dispatch.
            # Let's pass `edge_type` to a modified dispatch? No, too complex.

            # Compromise: We add the edge explicitly to a "Virtual Entry" for the branch?
            # No. Let's do the manual first-child dispatch here.

            # 1. Create the node for the statement
            # This requires knowing what node dispatch would create.
            # This is getting recursive.

            # Revert to patching for this specific logic?
            # No, we refactored IRGraph to `add_edge`.
            # We can just add the edge ourselves IF we know the target node ID.

            # Let's use a "Ghost" node logic:
            # Fork -> (Cond Edge) -> [Virtual: True Branch] -> (Seq) -> Logic
            # This is mathematically clean.
            v_node = self.graph.add_node(NodeType.VIRTUAL, label=edge_label)
            self.graph.add_edge(start_node, v_node, edge_type, edge_label)

            if node.type == "block":
                return self._process_block(node, v_node)
            else:
                return self._dispatch_statement(node, v_node)

    def _handle_match(self, node, current_node: Node) -> Optional[Node]:
        val_text = self._get_text(node.child_by_field_name("value"))
        fork = self.graph.add_node(
            NodeType.FORK, label=f"match {val_text}", ast_node=node
        )
        self.graph.add_edge(current_node, fork, EdgeType.SEQ)

        join = self.graph.add_node(NodeType.JOIN, label="end match")
        has_paths = False

        body = node.child_by_field_name("body")
        for child in body.children:
            if child.type == "match_arm":
                pat_text = self._get_text(child.child_by_field_name("pattern"))
                value = child.child_by_field_name("value")

                # Fork -> (Cond Edge) -> Virtual Arm Entry -> Logic
                arm_entry = self.graph.add_node(
                    NodeType.VIRTUAL, label=f"Case {pat_text}"
                )
                self.graph.add_edge(fork, arm_entry, EdgeType.COND_TRUE, pat_text)

                if value.type == "block":
                    arm_end = self._process_block(value, arm_entry)
                else:
                    arm_end = self._dispatch_statement(value, arm_entry)

                if arm_end:
                    self.graph.add_edge(arm_end, join, EdgeType.SEQ)
                    has_paths = True

        return join if has_paths else None

    def _handle_loop(self, node, current_node: Node) -> Optional[Node]:
        loop_entry = self.graph.add_node(NodeType.JOIN, label="loop", ast_node=node)
        self.graph.add_edge(current_node, loop_entry, EdgeType.SEQ)
        loop_exit = self.graph.add_node(NodeType.JOIN, label="end loop")

        self.loop_stack.append((loop_entry, loop_exit))
        body_end = self._process_block(node.child_by_field_name("body"), loop_entry)
        if body_end:
            self.graph.add_edge(body_end, loop_entry, EdgeType.JUMP, "repeat")
        self.loop_stack.pop()

        return loop_exit

    def _handle_while(self, node, current_node: Node) -> Optional[Node]:
        cond_text = self._get_text(node.child_by_field_name("condition"))
        check = self.graph.add_node(
            NodeType.FORK, label=f"while {cond_text}", ast_node=node
        )
        self.graph.add_edge(current_node, check, EdgeType.SEQ)

        loop_exit = self.graph.add_node(NodeType.JOIN, label="end while")
        self.graph.add_edge(check, loop_exit, EdgeType.COND_FALSE, "False")

        self.loop_stack.append((check, loop_exit))

        # Virtual Entry for body to carry the True edge
        body_start = self.graph.add_node(NodeType.VIRTUAL, label="Body")
        self.graph.add_edge(check, body_start, EdgeType.COND_TRUE, "True")

        body_end = self._process_block(node.child_by_field_name("body"), body_start)
        if body_end:
            self.graph.add_edge(body_end, check, EdgeType.JUMP, "repeat")

        self.loop_stack.pop()
        return loop_exit

    def _handle_for(self, node, current_node: Node) -> Optional[Node]:
        pat_text = self._get_text(node.child_by_field_name("pattern"))
        val_text = self._get_text(node.child_by_field_name("value"))
        check = self.graph.add_node(
            NodeType.FORK, label=f"for {pat_text} in {val_text}", ast_node=node
        )
        self.graph.add_edge(current_node, check, EdgeType.SEQ)

        loop_exit = self.graph.add_node(NodeType.JOIN, label="end for")
        self.graph.add_edge(check, loop_exit, EdgeType.COND_FALSE, "Done")

        self.loop_stack.append((check, loop_exit))

        body_start = self.graph.add_node(NodeType.VIRTUAL, label="Body")
        self.graph.add_edge(check, body_start, EdgeType.COND_TRUE, "Next")

        body_end = self._process_block(node.child_by_field_name("body"), body_start)
        if body_end:
            self.graph.add_edge(body_end, check, EdgeType.JUMP, "repeat")

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
