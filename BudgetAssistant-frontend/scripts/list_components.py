"""
List all Angular components in the BudgetAssistant-frontend project.

This script scans for all .component.ts files and outputs them in various formats.
Can be used to generate the componentlist.tsv file needed by generate_plans.py.
"""

import os
from pathlib import Path
import argparse
import json


def find_angular_components(src_dir: Path) -> list[dict]:
    """
    Find all Angular components in the given source directory.

    Args:
        src_dir: Path to the Angular src directory

    Returns:
        List of dicts with 'file' and 'directory' keys
    """
    components = []

    for root, dirs, files in os.walk(src_dir):
        # Skip node_modules if present
        if "node_modules" in root:
            continue

        for file in files:
            if file.endswith(".component.ts"):
                full_path = Path(root)
                components.append(
                    {
                        "file": file,
                        "directory": str(full_path),
                        "relative_path": str(full_path.relative_to(src_dir)),
                        "component_name": file.replace(".component.ts", ""),
                    }
                )

    # Sort by component name
    components.sort(key=lambda x: x["file"])
    return components


def output_table(components: list[dict]):
    """Print components as a formatted table."""
    print(f"\n{'Component File':<55} {'Directory'}")
    print("-" * 120)
    for comp in components:
        print(f"{comp['file']:<55} {comp['relative_path']}")


def output_tsv(components: list[dict], output_file: Path):
    """Write components to a TSV file."""
    with open(output_file, "w", encoding="utf-8") as f:
        for comp in components:
            f.write(f"{comp['file']}\t{comp['directory']}\n")
    print(f"\nTSV file saved to: {output_file}")


def output_json(components: list[dict], output_file: Path | None = None):
    """Output components as JSON."""
    json_str = json.dumps(components, indent=2)
    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(json_str)
        print(f"\nJSON file saved to: {output_file}")
    else:
        print(json_str)


def main():
    parser = argparse.ArgumentParser(
        description="List all Angular components in the project"
    )
    parser.add_argument(
        "--format",
        choices=["table", "tsv", "json"],
        default="table",
        help="Output format (default: table)",
    )
    parser.add_argument(
        "--output", "-o", type=Path, help="Output file path (for tsv/json formats)"
    )
    parser.add_argument(
        "--src-dir",
        type=Path,
        help="Angular src directory to scan (default: auto-detect)",
    )

    args = parser.parse_args()

    # Determine the src directory
    if args.src_dir:
        src_dir = args.src_dir
    else:
        # Auto-detect: assume script is in BudgetAssistant-frontend/scripts
        script_dir = Path(__file__).parent
        src_dir = script_dir.parent / "src"

        if not src_dir.exists():
            # Try from BudgetAssistant-backend-fastapi/scripts
            src_dir = script_dir.parent.parent / "BudgetAssistant-frontend" / "src"

    if not src_dir.exists():
        print(f"Error: Source directory not found: {src_dir}")
        print("Please specify --src-dir explicitly")
        return 1

    print(f"Scanning for Angular components in: {src_dir}")

    components = find_angular_components(src_dir)
    print(f"Found {len(components)} components")

    if args.format == "table":
        output_table(components)
    elif args.format == "tsv":
        output_file = args.output or (src_dir.parent / "componentlist.tsv")
        output_tsv(components, output_file)
    elif args.format == "json":
        output_json(components, args.output)

    return 0


if __name__ == "__main__":
    exit(main())
