"""
Set budget amounts on BudgetTreeNodes based on categorized transaction spending.

Reads categorized_transactions.jsonl to compute actual spending per category,
then assigns budget amounts to each BudgetTreeNode. Some categories are
deliberately set below actual spending (over budget) and some above (within budget)
so the frontend budget-check component has a realistic mix.

Usage:
    python scripts/set_budget_amounts.py
    python scripts/set_budget_amounts.py --save-to-db
    python scripts/set_budget_amounts.py --save-to-db --db path/to/budgetassistant.db
"""

import argparse
import asyncio
import json
import os
import sys
from collections import defaultdict
from pathlib import Path

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
EXPORT_DIR = Path(os.path.join(SCRIPT_DIR, "../export"))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Set budget amounts on BudgetTreeNodes based on categorized spending.")
    default_db = Path(os.path.join(SCRIPT_DIR, "../budgetassistant.db")).resolve()
    parser.add_argument(
        "--save-to-db",
        action="store_true",
        default=False,
        help="Also update amounts on BudgetTreeNodes in the SQLite database.",
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=default_db,
        help=f"Path to the SQLite database file (default: {default_db}).",
    )
    return parser.parse_args()


def compute_spending(path: Path) -> dict[int, float]:
    """Compute total absolute spending per expense category_id."""
    spending: dict[int, float] = defaultdict(float)
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            tx = json.loads(line)
            if tx["amount"] < 0 and tx.get("category_id") is not None:
                spending[tx["category_id"]] += abs(tx["amount"])
    return dict(spending)


def load_budget_nodes(path: Path) -> list[dict]:
    nodes = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            nodes.append(json.loads(line))
    return nodes


def load_categories(path: Path) -> dict[int, dict]:
    categories = {}
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            cat = json.loads(line)
            categories[cat["id"]] = cat
    return categories


# ── Budget design ──────────────────────────────────────────────────────────
#
# Actual spending from categorized_transactions.jsonl (amounts are absolute):
#
#   cat  2 (auto & vervoer):                     22.50  (Uber taxi)
#   cat  4 (auto & vervoer#benzine):            135.20
#   cat  6 (auto & vervoer#parkeren):            68.50
#   cat  7 (auto & vervoer#trein):              209.00
#   cat 18 (energie#gas & elektriciteit):       120.00
#   cat 22 (giften#cadeau's):                    77.50
#   cat 27 (huishouden#boodschappen#supermarkt):116.75
#   cat 41 (kledij & verzorging#kapper):         32.00
#   cat 42 (kledij & verzorging#kleren):        210.99
#   cat 43 (kledij & verzorging#schoenen):      169.95
#   cat 48 (medisch#apotheek):                   46.95
#   cat 59 (telecom#internet & tv):              47.96
#   cat 69 (vrije tijd#hobby):                  217.28
#   cat 70 (vrije tijd#reizen):                 175.00
#   cat 71 (vrije tijd#restaurant):             119.70
#   cat 72 (vrije tijd#uitgaan):                310.00
#   cat 73 (webshops):                          259.20
#
# Strategy – leaf-node budgets only (parent nodes stay 0; the frontend sums
# children). We deliberately set some BELOW actual spending so those show as
# "over budget", and some ABOVE so they show as "within budget".
#
#   OVER BUDGET  (budget < actual):
#     - cat 69 hobby:       spent 217 → budget 150   (over by ~67)
#     - cat 72 uitgaan:     spent 310 → budget 200   (over by ~110)
#     - cat 42 kleren:      spent 211 → budget 100   (over by ~111)
#     - cat  7 trein:       spent 209 → budget 150   (over by ~59)
#     - cat 73 webshops:    spent 259 → budget 150   (over by ~109)
#     - cat 70 reizen:      spent 175 → budget 100   (over by ~75)
#     - cat 22 cadeau's:    spent  78 → budget  50   (over by ~28)
#
#   WITHIN BUDGET  (budget >= actual):
#     - cat  4 benzine:     spent 135 → budget 150
#     - cat  6 parkeren:    spent  69 → budget 100
#     - cat 18 gas & elek:  spent 120 → budget 150
#     - cat 27 supermarkt:  spent 117 → budget 200
#     - cat 41 kapper:      spent  32 → budget  50
#     - cat 43 schoenen:    spent 170 → budget 200
#     - cat 48 apotheek:    spent  47 → budget  75
#     - cat 59 internet&tv: spent  48 → budget  60
#     - cat 71 restaurant:  spent 120 → budget 150
#     - cat  2 auto&vervoer:spent  23 → budget  50    (general/taxi rides)
#
#   Categories with no spending in the data but realistic monthly budgets:
#     - cat  8 bankkosten:           5
#     - cat 19 water:               30
#     - cat 29 lunch werk:          80
#     - cat 46 woonlening:        800
#     - cat 52 mutualiteit:        25
#     - cat 60 telefonie:          30
#     - cat 64 brand&familiale:    40
#     - cat 80 poetsdienst:       100

BUDGET_AMOUNTS: dict[int, int] = {
    # ── auto & vervoer ──
    2: 50,  # general (taxi etc.) – WITHIN
    4: 150,  # benzine – WITHIN
    6: 100,  # parkeren – WITHIN
    7: 150,  # trein – OVER
    # ── bankkosten ──
    8: 5,
    # ── energie ──
    18: 150,  # gas & elektriciteit – WITHIN
    19: 30,  # water
    # ── giften ──
    22: 50,  # cadeau's – OVER
    # ── huishouden ──
    27: 200,  # supermarkt – WITHIN
    29: 80,  # lunch werk
    # ── kledij & verzorging ──
    41: 50,  # kapper – WITHIN
    42: 100,  # kleren – OVER
    43: 200,  # schoenen – WITHIN
    # ── leningen ──
    46: 800,  # woonlening
    # ── medisch ──
    48: 75,  # apotheek – WITHIN
    52: 25,  # mutualiteit
    # ── telecom ──
    59: 60,  # internet & tv – WITHIN
    60: 30,  # telefonie
    # ── verzekeringen ──
    64: 40,  # brand- en familiale verzekering
    # ── vrije tijd ──
    69: 150,  # hobby – OVER
    70: 100,  # reizen – OVER
    71: 150,  # restaurant – WITHIN
    72: 200,  # uitgaan – OVER
    # ── webshops ──
    73: 150,  # webshops – OVER
    # ── wonen ──
    80: 100,  # poetsdienst
}


def main():
    args = parse_args()
    spending = compute_spending(EXPORT_DIR / "categorized_transactions.jsonl")
    categories = load_categories(EXPORT_DIR / "category.jsonl")
    nodes = load_budget_nodes(EXPORT_DIR / "budgettreenode.jsonl")

    # Apply amounts
    updated_nodes: list[dict] = []
    for node in nodes:
        cat_id = node["category_id"]
        node["amount"] = BUDGET_AMOUNTS.get(cat_id, 0)
        updated_nodes.append(node)

    # Write updated JSONL
    output_path = EXPORT_DIR / "budgettreenode.jsonl"
    with open(output_path, "w", encoding="utf-8") as f:
        for node in updated_nodes:
            f.write(json.dumps(node, ensure_ascii=False) + "\n")

    print(f"Updated {len(updated_nodes)} budget tree nodes -> {output_path}")

    # Print comparison table
    print(f"\n{'Category':<45} {'Spent':>8} {'Budget':>8} {'Status':>12}")
    print("-" * 77)
    for cat_id in sorted(set(list(spending.keys()) + list(BUDGET_AMOUNTS.keys()))):
        cat_name = categories.get(cat_id, {}).get("qualified_name", f"cat-{cat_id}")
        spent = spending.get(cat_id, 0)
        budget = BUDGET_AMOUNTS.get(cat_id, 0)
        if budget == 0 and spent == 0:
            continue
        status = "OVER" if spent > budget else "within"
        print(f"  {cat_name:<43} {spent:>8.2f} {budget:>8d} {status:>12}")

    if args.save_to_db:
        asyncio.run(save_to_database(args.db, updated_nodes))


async def save_to_database(db_path: Path, nodes: list[dict]) -> None:
    """Update amount on each BudgetTreeNode in the database."""
    db_path = db_path.resolve()
    if not db_path.exists():
        print(f"ERROR: Database file not found: {db_path}")
        sys.exit(1)

    os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{db_path}"
    print(f"\nUsing database: {db_path}")

    src_path = os.path.realpath(os.path.join(SCRIPT_DIR, "../src"))
    sys.path.insert(0, src_path)

    from sqlmodel import select  # noqa: E402

    from db.database import AsyncSessionLocal, engine  # noqa: E402
    from models.budget import BudgetTreeNode  # noqa: E402

    updated = 0
    async with AsyncSessionLocal() as session:
        for node_data in nodes:
            result = await session.execute(select(BudgetTreeNode).where(BudgetTreeNode.id == node_data["id"]))
            db_node = result.scalar_one_or_none()
            if db_node is None:
                print(f"  WARNING: BudgetTreeNode id={node_data['id']} not found in DB, skipping")
                continue
            db_node.amount = node_data["amount"]
            session.add(db_node)
            updated += 1

        await session.commit()

    await engine.dispose()
    print(f"Updated {updated}/{len(nodes)} budget tree nodes in the database.")


if __name__ == "__main__":
    main()
