"""Export database tables to JSONL files.

Each table is exported to its own .jsonl file, with one JSON object per line
using SQLModel's model_dump_json() method.

Usage:
    python scripts/export_data.py [--output-dir OUTPUT_DIR] [--db DB_PATH]
"""

import argparse
import asyncio
import os
import sys
from pathlib import Path

# Add src/ to the Python path so we can import project modules.
script_dir = os.path.dirname(os.path.realpath(__file__))
src_path = os.path.realpath(os.path.join(script_dir, "../src"))
sys.path.insert(0, src_path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export database tables to JSONL files.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(os.path.join(script_dir, "../export")),
        help="Directory to write the JSONL files to (default: ../export relative to this script).",
    )
    default_db = Path(os.path.join(script_dir, "../budgetassistant.db")).resolve()
    parser.add_argument(
        "--db",
        type=Path,
        default=default_db,
        help=f"Path to the SQLite database file (default: {default_db}).",
    )
    return parser.parse_args()


# Parse args before importing project modules so we can override DATABASE_URL
# before the engine is created at import time.
args = parse_args()

db_path = str(args.db.resolve())
if not args.db.exists():
    print(f"ERROR: Database file not found: {db_path}")
    sys.exit(1)
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{db_path}"
print(f"Using database: {db_path}")

from sqlmodel import SQLModel, select  # noqa: E402

from db.database import AsyncSessionLocal, engine  # noqa: E402
from models.budget import BudgetTreeNode  # noqa: E402
from models.category import Category  # noqa: E402
from models.transaction import Transaction  # noqa: E402

# Tables to export: (model_class, output_filename)
TABLES_TO_EXPORT: list[tuple[type[SQLModel], str]] = [
    (Transaction, "transaction.jsonl"),
    (Category, "category.jsonl"),
    (BudgetTreeNode, "budgettreenode.jsonl"),
]


async def export_table(
    session_factory: type[AsyncSessionLocal],
    model: type[SQLModel],
    output_path: Path,
) -> int:
    """Export all rows of a table to a JSONL file.

    Returns the number of rows exported.
    """
    count = 0
    async with session_factory() as session:
        result = await session.execute(select(model))
        rows = result.scalars().all()

        with open(output_path, "w", encoding="utf-8") as f:
            for row in rows:
                f.write(row.model_dump_json() + "\n")
                count += 1

    return count


async def main(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    for model, filename in TABLES_TO_EXPORT:
        output_path = output_dir / filename
        count = await export_table(AsyncSessionLocal, model, output_path)
        print(f"Exported {count:>6} rows  ->  {output_path}")

    # Clean up the async engine
    await engine.dispose()
    print("Done.")


if __name__ == "__main__":
    asyncio.run(main(args.output_dir))
