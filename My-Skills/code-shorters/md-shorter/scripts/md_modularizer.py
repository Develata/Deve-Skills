#!/usr/bin/env python3
"""Markdown refactor: split by H2 headings or chunk size."""

import argparse
from pathlib import Path


def split_by_heading(lines):
    sections = []
    current = []
    for line in lines:
        if line.startswith("## ") and current:
            sections.append(current)
            current = []
        current.append(line)
    if current:
        sections.append(current)
    return sections


def chunk_lines(lines, max_lines=120):
    return [lines[i : i + max_lines] for i in range(0, len(lines), max_lines)]


def write_chunks(src: Path, output_dir: Path, chunks):
    output_dir.mkdir(parents=True, exist_ok=True)
    for idx, chunk in enumerate(chunks, 1):
        part_path = output_dir / f"{src.stem}_part{idx}.md"
        part_path.write_text("\n".join(chunk) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Markdown modularizer")
    parser.add_argument("file_path", help="Markdown file")
    parser.add_argument("--max-lines", type=int, default=120)
    parser.add_argument("--output-dir", default="refactored")
    args = parser.parse_args()

    src = Path(args.file_path)
    if not src.exists():
        print("File not found.")
        raise SystemExit(1)

    lines = src.read_text(encoding="utf-8", errors="ignore").splitlines()
    if len(lines) <= args.max_lines:
        print("File is already within limit.")
        return

    sections = split_by_heading(lines)
    if len(sections) == 1:
        sections = chunk_lines(lines, args.max_lines)

    output_dir = src.parent / args.output_dir
    write_chunks(src, output_dir, sections)
    print(f"Generated {len(sections)} parts in {output_dir}")


if __name__ == "__main__":
    main()
