from ir_graph import UniversalLogicGraph, NodeType, EdgeType


class DotRenderer:
    def __init__(self, graph: UniversalLogicGraph):
        self.graph = graph

    def render(self) -> str:
        lines = []
        lines.append("digraph LogicFlow {")
        lines.append("  rankdir=TB;")
        lines.append("  splines=ortho;")
        lines.append(
            '  node [fontname="Courier New", shape=box, style=filled, fillcolor=white];'
        )
        lines.append('  edge [fontname="Arial", fontsize=10];')

        # Nodes
        for node in self.graph.nodes():
            attr = self._get_node_attr(node)
            lines.append(f"  {node.id} [{attr}];")

        # Edges
        for u, v, type, label in self.graph.edges():
            attr = self._get_edge_attr(type, label)
            lines.append(f"  {u.id} -> {v.id} [{attr}];")

        lines.append("}")
        return "\n".join(lines)

    def _get_node_attr(self, node) -> str:
        label = node.label.replace('"', '\\"')

        # Base attributes
        attrs = [f'label="{label}"']

        if node.type == NodeType.BLOCK:
            attrs.append("shape=box")
        elif node.type == NodeType.FORK:
            attrs.append('shape=diamond, fillcolor="#FFF3CD"')  # Light yellow
        elif node.type == NodeType.JOIN:
            attrs.append("shape=point, width=0.1")
        elif node.type == NodeType.CALL:
            attrs.append('shape=ellipse, fillcolor="#E2E3E5"')  # Light gray
        elif node.type == NodeType.EXIT:
            attrs.append(
                'shape=doublecircle, fillcolor="#F8D7DA", color="#DC3545"'
            )  # Reddish
        elif node.type == NodeType.VIRTUAL:
            attrs.append('style="dashed,filled"')

        return ", ".join(attrs)

    def _get_edge_attr(self, type: EdgeType, label: str) -> str:
        attrs = []
        if label:
            attrs.append(f'label="{label}"')

        if type == EdgeType.SEQ:
            attrs.append('color="black"')
        elif type == EdgeType.COND_TRUE:
            attrs.append('color="#198754", fontcolor="#198754"')  # Green
        elif type == EdgeType.COND_FALSE:
            attrs.append('color="#FD7E14", fontcolor="#FD7E14"')  # Orange
        elif type == EdgeType.ERR:
            attrs.append('color="#DC3545", style="dashed"')  # Red
        elif type == EdgeType.JUMP:
            attrs.append('color="#6C757D", constraint=false')  # Gray

        return ", ".join(attrs)
