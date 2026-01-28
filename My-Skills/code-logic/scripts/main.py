import argparse
import sys
import os
from ast_engine import ASTEngine
from cfg_rust_core import RustCFGBuilder
from cfg_python_core import PythonCFGBuilder
from renderer_dot import DotRenderer
from renderer_dsl import DSLRenderer


from config_loader import ConfigLoader


def main():
    # Load Config (Singleton)
    config = ConfigLoader("logic_config.yaml")
    parser = argparse.ArgumentParser(
        description="Code Logic Analyzer: Unassailable Logic Visualization"
    )
    parser.add_argument("file", help="Path to source file")
    parser.add_argument(
        "--format", choices=["svg", "dsl", "both"], default="both", help="Output format"
    )
    parser.add_argument(
        "--focus", help="Focus on specific function (by name)", default=None
    )
    parser.add_argument(
        "--svg-dir", help="Directory to save the generated SVG file", default=None
    )
    parser.add_argument(
        "--config", help="Path to logic_config.yaml", default="logic_config.yaml"
    )  # New arg


from symbol_table import SymbolTable
from ir_graph import UniversalLogicGraph, EdgeType, Node, NodeType


def main():
    # Load Config (Singleton)
    config = ConfigLoader("logic_config.yaml")
    parser = argparse.ArgumentParser(
        description="Code Logic Analyzer: Unassailable Logic Visualization"
    )
    parser.add_argument("file", help="Path to source file or directory")
    parser.add_argument(
        "--format", choices=["svg", "dsl", "both"], default="both", help="Output format"
    )
    parser.add_argument(
        "--focus", help="Focus on specific function (by name)", default=None
    )
    parser.add_argument(
        "--svg-dir", help="Directory to save the generated SVG file", default=None
    )
    parser.add_argument(
        "--config", help="Path to logic_config.yaml", default="logic_config.yaml"
    )
    parser.add_argument(
        "--unified", action="store_true", help="Generate a unified project graph"
    )

    args = parser.parse_args()

    # Reload config if custom path provided
    if args.config != "logic_config.yaml":
        config = ConfigLoader(args.config)

    # Determine input mode: File vs Directory
    input_path = os.path.abspath(args.file)
    if not os.path.exists(input_path):
        print(f"Error: Path not found: {input_path}")
        sys.exit(1)

    targets = []
    if os.path.isdir(input_path):
        # Recursive scan
        for root, _, files in os.walk(input_path):
            for file in files:
                if file.endswith((".rs", ".py")):
                    targets.append(os.path.join(root, file))
        print(f"[*] Project Mode: Found {len(targets)} source files in {input_path}")
    else:
        # Single file
        targets.append(input_path)

    # V1.3: Unified Atlas Mode
    if args.unified and len(targets) > 1:
        run_unified_atlas(targets, args, config, input_path)
    else:
        # Classic Mode (Per file)
        for file_path in targets:
            process_file(
                file_path,
                args,
                config,
                input_path if os.path.isdir(input_path) else None,
            )


def run_unified_atlas(targets, args, config, project_root):
    print("[*] Starting Phase A: Symbol Indexing...")
    symbol_table = SymbolTable()
    graphs = {}  # Map file_path -> ULG

    # Phase A & B Interleaved: Parse and Build Graphs
    for file_path in targets:
        try:
            builder, tree = get_builder_for_file(file_path, config)
            if not builder:
                continue

            # 1. Find all functions in file
            root = tree.root_node
            lang = "rs" if file_path.endswith(".rs") else "py"
            funcs = find_functions(root, lang)

            file_graph = UniversalLogicGraph(os.path.basename(file_path))

            # 2. Build each function and merge into file_graph
            for fn_node in funcs:
                with open(file_path, "rb") as f:
                    code = f.read()

                b_class = RustCFGBuilder if lang == "rs" else PythonCFGBuilder
                sub_builder = b_class(code)
                sub_builder.set_config_loader(config)

                fn_graph = sub_builder.build_from_function(fn_node)

                if not fn_graph.entry_node:
                    continue

                entry_node = fn_graph.get_node(fn_graph.entry_node)
                fn_name_raw = entry_node.label.split(" ")[1]
                fn_name = fn_name_raw.split("(")[0]

                file_graph.merge_graph(fn_graph, fn_name)

                final_entry_id = f"{fn_name}_{entry_node.id}"
                symbol_table.register(fn_name, file_path, final_entry_id)

            graphs[file_path] = file_graph

        except Exception as e:
            print(f"[!] Failed to index {file_path}: {e}")

    print("[*] Starting Phase B: Graph Fusion...")
    unified_graph = UniversalLogicGraph("ProjectAtlas")

    for file_path, file_graph in graphs.items():
        # Prefix with relative path to avoid "main.rs" vs "other/main.rs" collision
        rel_path = (
            os.path.relpath(file_path, project_root)
            .replace(os.sep, "_")
            .replace(".", "_")
        )
        unified_graph.merge_graph(file_graph, rel_path)

        # Update Symbol Table mapping to reflect the double prefix?
        # Wait, merge_graph prefixes IDs.
        # file_graph IDs were "func_id".
        # unified_graph IDs will be "rel_path_func_id".
        # We need to re-index or just calculate it?
        # Let's re-index? No, we can just update the symbol table logic.
        # Ideally, we should have built the symbol table *after* fusion?
        # Or, we update the symbol table entries now.
        pass

    print("[*] Starting Phase C: Cross-Linking...")
    # Iterate all CALL nodes in unified_graph
    link_count = 0
    for node in unified_graph.nodes():
        if node.type == NodeType.CALL:
            # Extract name "foo()" -> "foo"
            call_name = node.label.replace("()", "")

            # Lookup
            target_info = symbol_table.resolve(call_name)
            if target_info:
                # We need the final ID of the target in the unified graph.
                # target_info stored "func_id" (from file graph phase).
                # We need "file_prefix_func_id".

                # Reconstruct target ID
                # This requires us to know which file the target came from.
                # SymbolInfo has file_path.
                target_rel = (
                    os.path.relpath(target_info.file_path, project_root)
                    .replace(os.sep, "_")
                    .replace(".", "_")
                )
                final_target_id = f"{target_rel}_{target_info.node_id}"

                # Add LINK edge
                # Check if target node exists (it should)
                try:
                    target_node = unified_graph.get_node(final_target_id)
                    unified_graph.add_edge(node, target_node, EdgeType.LINK, "calls")
                    link_count += 1
                except:
                    pass  # Node missing?

    print(
        f"[*] Atlas Generated: {len(unified_graph.graph.nodes)} nodes, {link_count} cross-links."
    )

    # Render
    output_dir = args.svg_dir if args.svg_dir else "atlas_output"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    base_name = "project_atlas"

    if args.format in ["svg", "both"]:
        dot_out = DotRenderer(unified_graph).render()
        dot_path = os.path.join(output_dir, f"{base_name}.dot")
        svg_path = os.path.join(output_dir, f"{base_name}.svg")

        with open(dot_path, "w", encoding="utf-8") as f:
            f.write(dot_out)

        try:
            import subprocess

            # Use fdp or sfdp for large disconnected graphs? Or dot is fine with clusters?
            # dot is best for hierarchical.
            subprocess.run(["dot", "-Tsvg", dot_path, "-o", svg_path], check=True)
            print(f"[+] Atlas SVG saved to: {svg_path}")
        except Exception as e:
            print(f"[!] Graphviz failed: {e}")


def get_builder_for_file(file_path, config):
    try:
        engine = ASTEngine()
        tree, code_bytes = engine.parse_file(file_path)
        ext = file_path.split(".")[-1].lower()
        if ext == "rs":
            return RustCFGBuilder(code_bytes), tree
        if ext == "py":
            return PythonCFGBuilder(code_bytes), tree
        return None, None
    except:
        return None, None


def find_functions(node, lang_type):
    funcs = []
    if lang_type == "rs" and node.type == "function_item":
        funcs.append(node)
    elif lang_type == "py" and node.type == "function_definition":
        funcs.append(node)

    if hasattr(node, "children"):
        for child in node.children:
            funcs.extend(find_functions(child, lang_type))
    return funcs


def process_file(file_path, args, config, project_root):
    print(f"[*] Analyzing {file_path}...")

    # 1. Parse AST
    try:
        engine = ASTEngine()
        tree, code_bytes = engine.parse_file(file_path)
    except Exception as e:
        print(f"[!] AST Parsing Failed: {e}")
        print(
            "    Ensure tree-sitter, tree-sitter-rust, and tree-sitter-python are installed."
        )
        sys.exit(1)

    # 2. Build CFG
    # Find the target function or use the first one for now
    # TODO: Handle multiple functions / file-level module analysis
    target_node = None
    root = tree.root_node

    functions = []

    # Dispatch based on extension for CFG Builder
    ext = file_path.split(".")[-1].lower()

    # Search for functions (recursively for methods)
    def find_functions(node, lang_type):
        funcs = []
        # Check current node
        if lang_type == "rs" and node.type == "function_item":
            funcs.append(node)
        elif lang_type == "py" and node.type == "function_definition":
            funcs.append(node)

        # Recurse
        if hasattr(node, "children"):
            for child in node.children:
                funcs.extend(find_functions(child, lang_type))
        return funcs

    builder = None
    if ext == "rs":
        builder = RustCFGBuilder(code_bytes)
        functions = find_functions(root, "rs")
    elif ext == "py":
        builder = PythonCFGBuilder(code_bytes)
        functions = find_functions(root, "py")
    else:
        print(f"[!] Unsupported extension for CFG building: {ext}")
        sys.exit(1)

    # Inject config loader into builder if supported
    if hasattr(builder, "set_config_loader"):
        builder.set_config_loader(config)

    if not functions:
        print("[!] No functions found in file.")
        sys.exit(0)

    # Select function
    if args.focus:
        for fn in functions:
            name_node = fn.child_by_field_name("name")
            name = code_bytes[name_node.start_byte : name_node.end_byte].decode("utf-8")
            if name == args.focus:
                target_node = fn
                break
        if not target_node:
            print(f"[!] Function '{args.focus}' not found.")
            sys.exit(1)
    else:
        # Default to first function for Prototype v1
        print(f"[*] No focus specified, analyzing first function found.")
        target_node = functions[0]

    ulg = builder.build_from_function(target_node)

    # 3. Render Outputs
    base_name = os.path.splitext(file_path)[0]
    filename = os.path.basename(base_name)
    output_dir = f"{base_name}_logic"

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    if args.format in ["dsl", "both"]:
        dsl_out = DSLRenderer(ulg).render()
        dsl_path = os.path.join(output_dir, f"{filename}.logic.lisp")
        with open(dsl_path, "w", encoding="utf-8") as f:
            f.write(dsl_out)
        print(f"[+] Generated Logic DSL: {dsl_path}")

    if args.format in ["svg", "both"]:
        dot_out = DotRenderer(ulg).render()
        dot_path = os.path.join(output_dir, f"{filename}.logic.dot")

        # Determine SVG path
        if args.svg_dir:
            # If project root is set, mirror structure
            if project_root:
                rel_path = os.path.relpath(os.path.dirname(file_path), project_root)
                target_svg_dir = os.path.join(args.svg_dir, rel_path)
            else:
                target_svg_dir = args.svg_dir

            if not os.path.exists(target_svg_dir):
                os.makedirs(target_svg_dir)
            svg_path = os.path.join(target_svg_dir, f"{filename}.logic.svg")
        else:
            svg_path = os.path.join(output_dir, f"{filename}.logic.svg")

        with open(dot_path, "w", encoding="utf-8") as f:
            f.write(dot_out)

        # Try running dot
        try:
            import subprocess

            subprocess.run(["dot", "-Tsvg", dot_path, "-o", svg_path], check=True)
            print(f"[+] Generated Visualization: {svg_path}")
            # Optional: remove dot file
            # os.remove(dot_path)
        except FileNotFoundError:
            print(
                f"[!] Graphviz 'dot' command not found. Saved .dot file only: {dot_path}"
            )
        except Exception as e:
            print(f"[!] Graphviz generation failed: {e}")


if __name__ == "__main__":
    main()
