from ir_graph import UniversalLogicGraph


class DSLRenderer:
    def __init__(self, graph: UniversalLogicGraph):
        self.graph = graph

    def render(self) -> str:
        lines = []
        lines.append(f'(flow-graph :name "{self.graph.name}"')

        # Nodes section
        lines.append("  (nodes")
        for node in self.graph.nodes():
            lines.append(self._render_node(node))
        lines.append("  )")

        # Edges section
        lines.append("  (edges")
        for u, v, type, label in self.graph.edges():
            lines.append(self._render_edge(u, v, type, label))
        lines.append("  )")

        lines.append(")")
        return "\n".join(lines)

    def _render_node(self, node) -> str:
        # Sanitize label
        label = node.label.replace('"', '\\"').replace("\n", " ")
        type_str = node.type.name.lower()
        return f'    ({type_str:<6} :id {node.id:<10} :label "{label}")'

    def _render_edge(self, u, v, type, label) -> str:
        type_str = type.name.lower()
        lbl_part = f' :label "{label}"' if label else ""
        return f"    ({type_str:<8} {u.id} -> {v.id}{lbl_part})"
