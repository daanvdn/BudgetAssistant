# generate_openapi.py
import argparse
import os
import sys
from pathlib import Path

# get parent of script dir
script_dir = os.path.dirname(os.path.realpath(__file__))
src_pth = os.path.realpath(os.path.join(script_dir, "../src"))
print(f"Adding {src_pth} to sys.path")
sys.path.insert(0, src_pth)

from main import app  # noqa: E402, I001
import json  # noqa: E402


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate OpenAPI schema")
    parser.add_argument(
        "--output", type=str, help="Output file for OpenAPI schema (e.g., openapi.json)", default="./openapi.json"
    )
    args = parser.parse_args()
    output_file = args.output
    # make sure the file is a .json file
    if not output_file.endswith(".json"):
        raise ValueError("Output file must be a .json file!")
    # make sure parent dir exists
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    print("Generating OpenAPI schema...")
    schema = app.openapi()
    print(f"Saving OpenAPI schema to {output_file}...")
    with open(output_file, "w") as f:
        json.dump(schema, f, indent=2)
        print("Done!")
