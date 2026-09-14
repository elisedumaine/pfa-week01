#!/usr/bin/env python3
"""Print a simple file and image-sequence report for an animation project folder."""

from __future__ import annotations

import argparse
import re
from collections import Counter, defaultdict
from pathlib import Path

# This finds a frame number at the end of a filename, before its extension.
FRAME_NUMBER = re.compile(r"^(.*?)(\d+)$")


def find_sequence_gaps(files: list[Path]) -> list[str]:
    """Return descriptions of missing frame numbers in similarly named files."""
    sequences: dict[tuple[str, str, int], list[int]] = defaultdict(list)

    for file_path in files:
        match = FRAME_NUMBER.match(file_path.stem)
        if match is None:
            continue

        prefix, number_text = match.groups()
        key = (prefix, file_path.suffix.lower(), len(number_text))
        sequences[key].append(int(number_text))

    gaps = []
    for (prefix, extension, padding), numbers in sorted(sequences.items()):
        unique_numbers = sorted(set(numbers))
        if len(unique_numbers) < 2:
            continue

        missing = [
            number
            for number in range(unique_numbers[0], unique_numbers[-1] + 1)
            if number not in unique_numbers
        ]
        if missing:
            missing_text = ", ".join(f"{number:0{padding}d}" for number in missing)
            gaps.append(f"{prefix}*{extension}: missing frame(s) {missing_text}")

    return gaps


def build_report(folder: Path) -> str:
    """Scan one folder and return a readable report string."""
    files = sorted(path for path in folder.iterdir() if path.is_file())
    extensions = Counter(path.suffix.lower() or "[no extension]" for path in files)
    total_size = sum(path.stat().st_size for path in files)

    lines = [
        "Animation Project File Report",
        f"Folder: {folder.resolve()}",
        f"Files scanned: {len(files)}",
        f"Total size: {total_size:,} bytes",
        "",
        "Files:",
    ]

    if files:
        lines.extend(f"  {path.name} ({path.stat().st_size:,} bytes)" for path in files)
    else:
        lines.append("  No files found.")

    lines.extend(["", "File types:"])
    if extensions:
        lines.extend(
            f"  {extension}: {count} file(s)"
            for extension, count in sorted(extensions.items())
        )
    else:
        lines.append("  No file types found.")

    gaps = find_sequence_gaps(files)
    lines.extend(["", "Possible image-sequence gaps:"])
    if gaps:
        lines.extend(f"  {gap}" for gap in gaps)
    else:
        lines.append("  No numbered filename gaps found.")

    return "\n".join(lines)


def main() -> None:
    """Read command-line options, print the report, and optionally save it."""
    parser = argparse.ArgumentParser(
        description="Create a file report for one animation project folder."
    )
    parser.add_argument(
        "folder",
        nargs="?",
        default=".",
        help="folder to scan (default: the current folder)",
    )
    parser.add_argument(
        "--output",
        help="optional text file in which to save the report",
    )
    args = parser.parse_args()

    folder = Path(args.folder)
    if not folder.is_dir():
        parser.error(f"'{folder}' is not a folder")

    report = build_report(folder)
    print(report)

    if args.output:
        output_path = Path(args.output)
        output_path.write_text(report + "\n", encoding="utf-8")
        print(f"\nReport saved to: {output_path}")


if __name__ == "__main__":
    main()
