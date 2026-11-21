#!/usr/bin/env python3
"""Select atomic cards for Step 4 cross-domain variant review."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import random
from pathlib import Path
from typing import Any

from config import get_vault_path, parse_markdown_note


def parse_date(value: Any) -> dt.date | None:
    if not value:
        return None
    try:
        return dt.date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


def load_candidates(vault_path: Path, today: dt.date) -> list[dict[str, Any]]:
    cards_dir = vault_path / "20-Cards"
    if not cards_dir.is_dir():
        return []

    items: list[dict[str, Any]] = []
    for md_file in sorted(cards_dir.rglob("*.md")):
        meta, body = parse_markdown_note(md_file)
        domains = meta.get("domain") or []
        if isinstance(domains, str):
            domains = [domains]
        next_rev = parse_date(meta.get("next_review"))
        overdue_days = (today - next_rev).days if next_rev else 0
        review_count = int(meta.get("review_count") or 0)
        items.append(
            {
                "title": md_file.stem,
                "path": str(md_file.relative_to(vault_path)),
                "domain": domains,
                "status": meta.get("status") or "seedling",
                "review_count": review_count,
                "next_review": str(next_rev) if next_rev else None,
                "overdue_days": overdue_days,
                "body": body.strip(),
            }
        )
    return items


def pick_cards(
    candidates: list[dict[str, Any]], count: int, seed: int | None = None
) -> list[dict[str, Any]]:
    if not candidates or count <= 0:
        return []
    rng = random.Random(seed)
    pool = list(candidates)
    rng.shuffle(pool)
    # Prioritize due/overdue cards first, then fewer reviews.
    pool.sort(key=lambda c: (-1 if c["overdue_days"] >= 0 else 0, -c["overdue_days"], c["review_count"]))

    picked: list[dict[str, Any]] = []
    used_domains: set[str] = set()

    # First pass: maximize cross-domain diversity.
    for card in pool:
        if len(picked) >= count:
            break
        card_domains = set(card["domain"])
        if not used_domains or not card_domains or not (card_domains & used_domains):
            picked.append(card)
            used_domains.update(card_domains)

    # Second pass: fill remaining slots if needed.
    picked_paths = {c["path"] for c in picked}
    for card in pool:
        if len(picked) >= count:
            break
        if card["path"] not in picked_paths:
            picked.append(card)
            picked_paths.add(card["path"])

    return picked


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Pick due & cross-domain atomic cards for variant review."
    )
    parser.add_argument("-n", "--count", type=int, default=3, help="Number of cards to pick.")
    parser.add_argument("--vault", help="Override VAULT_PATH.")
    parser.add_argument("--seed", type=int, help="Optional random seed for reproducibility.")
    parser.add_argument(
        "--format",
        choices=("markdown", "json"),
        default="markdown",
        help="Output format (default: markdown).",
    )
    args = parser.parse_args()

    vault = get_vault_path(args.vault)
    today = dt.date.today()
    candidates = load_candidates(vault, today)
    picked = pick_cards(candidates, args.count, args.seed)

    if args.format == "json":
        print(json.dumps(picked, ensure_ascii=False, indent=2))
        return 0

    if not picked:
        print(f"(No atomic cards available for review in {vault / '20-Cards'})")
        return 0

    print(f"# Variant Review Batch ({today.isoformat()} | {len(picked)} cards)\n")
    for idx, card in enumerate(picked, 1):
        domains = ", ".join(card["domain"]) if card["domain"] else "uncategorized"
        print(f"## Card {idx}: {card['title']}")
        print(
            f"- Path: `{card['path']}` | Domain: `{domains}` | Reviews: `{card['review_count']}` | Next review: `{card['next_review']}`\n"
        )
        print(card["body"])
        print("\n---\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
