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

    args = parser.parse_args()

    # Reload config if custom path provided
    if args.config != "logic_config.yaml":
        config = ConfigLoader(args.config)

    file_path = os.path.abspath(args.file)
    if not os.path.exists(file_path):
        print(f"Error: File not found: {file_path}")
        sys.exit(1)

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
            if not os.path.exists(args.svg_dir):
                os.makedirs(args.svg_dir)
            svg_path = os.path.join(args.svg_dir, f"{filename}.logic.svg")
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
