import argparse
import sys
import os
from ast_engine import ASTEngine
from cfg_rust_core import RustCFGBuilder
from renderer_dot import DotRenderer
from renderer_dsl import DSLRenderer


def main():
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

    args = parser.parse_args()

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
        print("    Ensure tree-sitter and tree-sitter-rust are installed.")
        sys.exit(1)

    # 2. Build CFG
    # Find the target function or use the first one for now
    # TODO: Handle multiple functions / file-level module analysis
    target_node = None
    root = tree.root_node

    functions = []
    # Simple search for function_item
    for child in root.children:
        if child.type == "function_item":
            functions.append(child)

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

    builder = RustCFGBuilder(code_bytes)
    ulg = builder.build_from_function(target_node)

    # 3. Render Outputs
    base_name = os.path.splitext(file_path)[0]

    if args.format in ["dsl", "both"]:
        dsl_out = DSLRenderer(ulg).render()
        dsl_path = f"{base_name}.logic.lisp"
        with open(dsl_path, "w", encoding="utf-8") as f:
            f.write(dsl_out)
        print(f"[+] Generated Logic DSL: {dsl_path}")

    if args.format in ["svg", "both"]:
        dot_out = DotRenderer(ulg).render()
        dot_path = f"{base_name}.logic.dot"
        svg_path = f"{base_name}.logic.svg"

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
