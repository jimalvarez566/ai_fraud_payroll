"""Seed default policy rules into the database.

Run once from the backend/ directory:
    python seed_policies.py

Safe to re-run — existing rules (matched by name) are skipped, not duplicated.
"""
import asyncio
import sys

from sqlalchemy import select

from app.database import async_session
from app.models.policy_rule import PolicyRule

DEFAULT_RULES = [
    {
        "rule_name": "Meal amount limit",
        "rule_type": "amount_limit",
        "severity": "medium",
        "parameters": {"category": "meals", "limit": 75.00},
    },
    {
        "rule_name": "Supplies amount limit",
        "rule_type": "amount_limit",
        "severity": "medium",
        "parameters": {"category": "supplies", "limit": 200.00},
    },
    {
        "rule_name": "No future dates",
        "rule_type": "future_date",
        "severity": "high",
        "parameters": {},
    },
    {
        "rule_name": "Approved expense categories",
        "rule_type": "vendor_category",
        "severity": "medium",
        "parameters": {
            "allowed_categories": {
                "meals": [
                    "restaurant", "cafe", "coffee", "starbucks", "dunkin",
                    "mcdonald", "burger", "pizza", "food", "grill", "kitchen",
                    "diner", "bistro", "bakery", "sushi", "taco", "sandwich",
                    "donut", "bagel", "smoothie", "juice", "bar & grill",
                ],
                "travel": [
                    "hotel", "inn", "suites", "marriott", "hilton", "hyatt",
                    "sheraton", "westin", "airbnb", "delta", "united",
                    "american airlines", "southwest", "jetblue", "spirit",
                    "frontier", "alaska airlines", "uber", "lyft", "taxi",
                    "hertz", "enterprise", "avis", "budget", "national",
                    "amtrak", "greyhound", "parking", "toll",
                ],
                "supplies": [
                    "staples", "office depot", "office max", "amazon",
                    "best buy", "costco", "walmart", "target", "home depot",
                    "fedex", "ups", "usps", "post office", "print", "ink",
                    "paper", "notebook", "pen", "binder",
                ],
            }
        },
    },
    {
        "rule_name": "Round number detection",
        "rule_type": "round_number",
        "severity": "low",
        "parameters": {"min_amount": 10.00},
    },
    {
        "rule_name": "Short window duplicate",
        "rule_type": "short_window_duplicate",
        "severity": "high",
        "parameters": {"window_hours": 48, "amount_tolerance_pct": 10},
    },
]


async def seed() -> None:
    inserted = 0
    skipped = 0

    async with async_session() as db:
        for rule_def in DEFAULT_RULES:
            result = await db.execute(
                select(PolicyRule).where(PolicyRule.rule_name == rule_def["rule_name"])
            )
            existing = result.scalar_one_or_none()

            if existing:
                print(f"  SKIP   '{rule_def['rule_name']}' (already exists, id={existing.id})")
                skipped += 1
            else:
                rule = PolicyRule(
                    rule_name=rule_def["rule_name"],
                    rule_type=rule_def["rule_type"],
                    severity=rule_def["severity"],
                    parameters=rule_def["parameters"],
                    is_active=True,
                )
                db.add(rule)
                await db.flush()
                print(f"  INSERT '{rule_def['rule_name']}' (id={rule.id})")
                inserted += 1

        await db.commit()

    print(f"\nDone — {inserted} inserted, {skipped} skipped.")


if __name__ == "__main__":
    print("Seeding policy rules...\n")
    try:
        asyncio.run(seed())
    except Exception as exc:
        print(f"\nError: {exc}", file=sys.stderr)
        sys.exit(1)
