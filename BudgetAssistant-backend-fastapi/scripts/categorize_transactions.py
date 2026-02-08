"""
Categorize transactions based on category hierarchy and transaction details.
Reads transaction.jsonl and category.jsonl, assigns the best-fit category to each transaction,
and writes the result to categorized_transactions.jsonl.

Usage:
    python scripts/categorize_transactions.py
    python scripts/categorize_transactions.py --save-to-db
    python scripts/categorize_transactions.py --save-to-db --db path/to/budgetassistant.db
"""

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
EXPORT_DIR = Path(os.path.join(SCRIPT_DIR, "../export"))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Categorize transactions and optionally save to the database.")
    default_db = Path(os.path.join(SCRIPT_DIR, "../budgetassistant.db")).resolve()
    parser.add_argument(
        "--save-to-db",
        action="store_true",
        default=False,
        help="Also update category_id on transactions in the SQLite database.",
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=default_db,
        help=f"Path to the SQLite database file (default: {default_db}).",
    )
    return parser.parse_args()


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


def load_transactions(path: Path) -> list[dict]:
    transactions = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            transactions.append(json.loads(line))
    return transactions


# Manual categorization mapping: transaction_number -> (category_id, rationale)
# Built by analyzing each transaction's description, communication, counterparty and amount sign.
#
# Category reference (EXPENSES):
#   2=auto & vervoer, 3=autoverzekering, 4=benzine, 5=onderhoud & herstelling,
#   6=parkeren, 7=trein, 8=bankkosten, 9=belastingen, 10=KI, 11=boekhouder,
#   12=gemeentebelasting, 13=personenbelasting, 14=provinciebelasting, 15=verkeersbelasting,
#   16=cash geldopname, 17=energie, 18=gas & elektriciteit, 19=water,
#   20=gemeenschappelijke kosten, 21=giften, 22=cadeau's,
#   23=huishouden, 24=boodschappen, 25=bakker, 26=slager, 27=supermarkt, 28=colruyt,
#   29=lunch werk, 30=kinderen, 31=kinderopvang, 32=kinderen kleding, 33=school,
#   34=boeken/materiaal, 35=middagmaal, 36=schoolreis, 37=speelgoed, 38=uitrusting,
#   39=kledij & verzorging, 40=accessoires, 41=kapper, 42=kleren, 43=schoenen,
#   44=kredietkaart, 45=leningen, 46=woonlening,
#   47=medisch, 48=apotheek, 49=dierenarts, 50=dokter, 51=kinesist, 52=mutualiteit,
#   53=tandarts, 54=ziekenhuis, 55=sparen, 56=algemeen, 57=pensioensparen,
#   58=telecom, 59=internet & tv, 60=telefonie, 61=vakbond,
#   62=verzekeringen, 63=autoverzekering, 64=brand- en familiale verzekering,
#   65=hospitalisatieverzekering, 66=schuldsaldo,
#   67=vrije tijd, 68=café, 69=hobby, 70=reizen, 71=restaurant, 72=uitgaan,
#   73=webshops, 74=wonen, 75=chauffage, 76=electro, 77=keuken, 78=loodgieter,
#   79=meubelen & accessoires, 80=poetsdienst, 81=renovaties, 82=tuin
#
# Category reference (REVENUE):
#   84=loon, 85=schenking, 86=spaargeld, 87=terugbetaling allerhande,
#   88=terugbetaling mutualiteit, 89=terugbetaling verzekeringen, 90=uitkering

CATEGORIZATION: dict[str, tuple[int, str]] = {
    # === EXPENSES (negative amounts) ===
    # Tx 1: Netflix streaming subscription
    "1": (59, "telecom#internet & tv"),
    # Tx 2: Bol.com online purchase (headphones)
    "2": (73, "webshops"),
    # Tx 3: Albert Heijn supermarket groceries
    "3": (27, "huishouden#boodschappen#supermarkt"),
    # Tx 4: Monthly energy bill
    "4": (18, "energie#gas & elektriciteit"),
    # Tx 5: Parking fee city center
    "5": (6, "auto & vervoer#parkeren"),
    # Tx 6: Dinner at Bistro Belle
    "6": (71, "vrije tijd#restaurant"),
    # Tx 7: Jack & Jones clothing purchase
    "7": (42, "kledij & verzorging#kleren"),
    # Tx 8: Pathé cinema tickets
    "8": (72, "vrije tijd#uitgaan"),
    # Tx 9: FitNow gym membership
    "9": (69, "vrije tijd#hobby"),
    # Tx 10: Udemy Python course (online purchase)
    "10": (73, "webshops"),
    # === REVENUE (positive amounts) ===
    # Tx 11: April salary from Acme BV
    "11": (84, "loon"),
    # Tx 12: Insurance damage claim refund from AXA
    "12": (89, "terugbetaling verzekeringen"),
    # Tx 13: Government childcare benefit
    "13": (90, "uitkering"),
    # Tx 14: Student finance (DUO)
    "14": (90, "uitkering"),
    # Tx 15: Freelance work payment
    "15": (84, "loon"),
    # Tx 16: Social welfare benefit
    "16": (90, "uitkering"),
    # Tx 17: Tikkie reimbursement dinner
    "17": (87, "terugbetaling allerhande"),
    # Tx 18: Sold second-hand office chair via Marktplaats
    "18": (87, "terugbetaling allerhande"),
    # Tx 19: Housing allowance (huurtoeslag)
    "19": (90, "uitkering"),
    # Tx 20: Inheritance from grandfather
    "20": (85, "schenking"),
    # === EXPENSES continued ===
    # Tx 21: Spotify music streaming subscription
    "21": (59, "telecom#internet & tv"),
    # Tx 22: Hotel stay weekend trip Berlin
    "22": (70, "vrije tijd#reizen"),
    # Tx 23: Thalys train ticket Amsterdam-Paris return
    "23": (7, "auto & vervoer#trein"),
    # Tx 24: Amazon book order
    "24": (73, "webshops"),
    # Tx 25: Shell fuel for car
    "25": (4, "auto & vervoer#benzine"),
    # Tx 26: Pharmacy - medication purchase
    "26": (48, "medisch#apotheek"),
    # Tx 27: Haircut at salon
    "27": (41, "kledij & verzorging#kapper"),
    # Tx 28: Mudam museum visit (Luxembourg day trip)
    "28": (72, "vrije tijd#uitgaan"),
    # Tx 29: Flowers birthday gift for mother
    "29": (22, "giften#cadeau's"),
    # Tx 30: Steam video game purchase
    "30": (69, "vrije tijd#hobby"),
    # Tx 31: Concert tickets Olympia Paris
    "31": (72, "vrije tijd#uitgaan"),
    # Tx 32: Torfs shoes purchase
    "32": (43, "kledij & verzorging#schoenen"),
    # Tx 33: Spotify monthly payment (duplicate subscription)
    "33": (59, "telecom#internet & tv"),
    # Tx 34: Thalys train to Paris
    "34": (7, "auto & vervoer#trein"),
    # Tx 35: Concert tickets Ziggo Dome
    "35": (72, "vrije tijd#uitgaan"),
    # Tx 36: Uber taxi ride to Schiphol airport
    "36": (2, "auto & vervoer"),
    # Tx 37: Adidas webshop sports articles
    "37": (73, "webshops"),
    # Tx 38: Pharmacy Etos - medication
    "38": (48, "medisch#apotheek"),
    # Tx 39: Netflix monthly payment
    "39": (59, "telecom#internet & tv"),
    # Tx 40: Flowers for birthday
    "40": (22, "giften#cadeau's"),
    # Tx 41: Louvre museum tickets (travel to Paris)
    "41": (70, "vrije tijd#reizen"),
    # Tx 42: Parking fine Amsterdam
    "42": (6, "auto & vervoer#parkeren"),
    # === REVENUE continued ===
    # Tx 43: Q1 bonus from employer
    "43": (84, "loon"),
    # Tx 44: Insurance payout
    "44": (89, "terugbetaling verzekeringen"),
    # Tx 45: Income tax refund
    "45": (87, "terugbetaling allerhande"),
    # Tx 46: Airbnb rental income
    "46": (84, "loon"),
    # Tx 47: Sold second-hand bicycle via Marktplaats
    "47": (87, "terugbetaling allerhande"),
    # Tx 48: Hotel booking cancellation refund
    "48": (87, "terugbetaling allerhande"),
    # Tx 49: Sold second-hand bicycle via Marktplaats
    "49": (87, "terugbetaling allerhande"),
    # === EXPENSES final batch ===
    # Tx 50: Jacket purchase clothing store
    "50": (42, "kledij & verzorging#kleren"),
    # Tx 51: Dinner with friends at restaurant
    "51": (71, "vrije tijd#restaurant"),
    # Tx 52: Novel purchase at bookshop
    "52": (69, "vrije tijd#hobby"),
    # Tx 53: Weekly groceries Albert Heijn
    "53": (27, "huishouden#boodschappen#supermarkt"),
    # Tx 54: Birthday gift purchase
    "54": (22, "giften#cadeau's"),
    # Tx 55: Pathé cinema evening
    "55": (72, "vrije tijd#uitgaan"),
    # Tx 56: Online photography course
    "56": (69, "vrije tijd#hobby"),
    # Tx 57: New running shoes
    "57": (43, "kledij & verzorging#schoenen"),
    # Tx 58: Car fuel
    "58": (4, "auto & vervoer#benzine"),
    # Tx 59: Steam video game
    "59": (69, "vrije tijd#hobby"),
    # === REVENUE final batch ===
    # Tx 60: Monthly salary April
    "60": (84, "loon"),
    # Tx 61: AXA insurance damage compensation
    "61": (89, "terugbetaling verzekeringen"),
    # Tx 62: Sold old laptop via Marktplaats
    "62": (87, "terugbetaling allerhande"),
    # Tx 63: Airbnb rental income
    "63": (84, "loon"),
    # Tx 64: Income tax refund
    "64": (87, "terugbetaling allerhande"),
    # Tx 65: Freelance work payment
    "65": (84, "loon"),
    # Tx 66: Student finance May (DUO)
    "66": (90, "uitkering"),
    # Tx 67: Tikkie lunch reimbursement
    "67": (87, "terugbetaling allerhande"),
    # Tx 68: Housing allowance (huurtoeslag)
    "68": (90, "uitkering"),
    # Tx 69: Inheritance from grandfather
    "69": (85, "schenking"),
}


def main():
    args = parse_args()
    _categories = load_categories(EXPORT_DIR / "category.jsonl")
    transactions = load_transactions(EXPORT_DIR / "transaction.jsonl")

    output_path = EXPORT_DIR / "categorized_transactions.jsonl"
    categorized_count = 0
    categorized_txs: list[tuple[str, int]] = []  # (transaction_id, category_id)

    with open(output_path, "w", encoding="utf-8") as out:
        for tx in transactions:
            tx_num = tx["transaction_number"]
            if tx_num in CATEGORIZATION:
                cat_id, qualified_name = CATEGORIZATION[tx_num]
                tx["category_id"] = cat_id
                tx["category_qualified_name"] = qualified_name
                categorized_txs.append((tx["transaction_id"], cat_id))
                categorized_count += 1
            else:
                print(f"WARNING: No categorization for transaction {tx_num}: {tx['transaction']}")
                tx["category_qualified_name"] = None

            out.write(json.dumps(tx, ensure_ascii=False) + "\n")

    print(f"Categorized {categorized_count}/{len(transactions)} transactions")
    print(f"Output written to: {output_path}")

    # Print summary by category
    cat_summary: dict[str, int] = {}
    for tx_num, (cat_id, qname) in CATEGORIZATION.items():
        cat_summary[qname] = cat_summary.get(qname, 0) + 1
    print("\nCategory distribution:")
    for qname, count in sorted(cat_summary.items(), key=lambda x: -x[1]):
        print(f"  {qname}: {count}")

    if args.save_to_db:
        asyncio.run(save_to_database(args.db, categorized_txs))


async def save_to_database(db_path: Path, categorized_txs: list[tuple[str, int]]) -> None:
    """Update category_id for each categorized transaction in the database."""
    db_path = db_path.resolve()
    if not db_path.exists():
        print(f"ERROR: Database file not found: {db_path}")
        sys.exit(1)

    os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{db_path}"
    print(f"\nUsing database: {db_path}")

    # Import project modules after setting DATABASE_URL
    src_path = os.path.realpath(os.path.join(SCRIPT_DIR, "../src"))
    sys.path.insert(0, src_path)

    from sqlmodel import select  # noqa: E402

    from db.database import AsyncSessionLocal, engine  # noqa: E402
    from models.transaction import Transaction  # noqa: E402

    updated = 0
    async with AsyncSessionLocal() as session:
        for transaction_id, category_id in categorized_txs:
            result = await session.execute(select(Transaction).where(Transaction.transaction_id == transaction_id))
            tx = result.scalar_one_or_none()
            if tx is None:
                print(f"  WARNING: transaction {transaction_id} not found in DB, skipping")
                continue
            tx.category_id = category_id
            session.add(tx)
            updated += 1

        await session.commit()

    await engine.dispose()
    print(f"Updated {updated}/{len(categorized_txs)} transactions in the database.")


if __name__ == "__main__":
    main()
