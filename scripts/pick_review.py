#!/usr/bin/env python3
"""Pick due decisions (40-Decisions/), mental models (30-Models/), or atomic cards (20-Cards/) for review."""

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


def load_decisions(vault_path: Path, today: dt.date, due_only: bool) -> list[dict[str, Any]]:
    dec_dir = vault_path / "40-Decisions"
    if not dec_dir.is_dir():
        return []
    items: list[dict[str, Any]] = []
    for md_file in sorted(dec_dir.rglob("*.md")):
        meta, body = parse_markdown_note(md_file)
        status = str(meta.get("status") or "pending-review")
        if status == "verified":
            continue
        rev_date = parse_date(meta.get("review_date"))
        overdue_days = (today - rev_date).days if rev_date else 0
        if due_only and rev_date and overdue_days < 0:
            continue
        models_used = meta.get("models_used") or []
        if isinstance(models_used, str):
            models_used = [models_used]
        items.append(
            {
                "kind": "decision",
                "title": md_file.stem,
                "path": str(md_file.relative_to(vault_path)),
                "status": status,
                "models_used": models_used,
                "confidence": meta.get("confidence"),
                "review_date": str(rev_date) if rev_date else None,
                "overdue_days": overdue_days,
                "body": body.strip(),
            }
        )
    items.sort(key=lambda d: (-d["overdue_days"], d["title"]))
    return items


def load_cards_or_models(
    vault_path: Path, folder: str, kind: str, today: dt.date
) -> list[dict[str, Any]]:
    target_dir = vault_path / folder
    if not target_dir.is_dir():
        return []

    items: list[dict[str, Any]] = []
    for md_file in sorted(target_dir.rglob("*.md")):
        meta, body = parse_markdown_note(md_file)
        domains = meta.get("domain") or []
        if isinstance(domains, str):
            domains = [domains]
        next_rev = parse_date(meta.get("next_review"))
        overdue_days = (today - next_rev).days if next_rev else 0
        count_val = int(meta.get("usage_count" if kind == "model" else "review_count") or 0)
        items.append(
            {
                "kind": kind,
                "title": md_file.stem,
                "path": str(md_file.relative_to(vault_path)),
                "domain": domains,
                "status": meta.get("status") or ("draft" if kind == "model" else "seedling"),
                "count": count_val,
                "next_review": str(next_rev) if next_rev else None,
                "overdue_days": overdue_days,
                "body": body.strip(),
            }
        )
    return items


def pick_diverse(
    candidates: list[dict[str, Any]], count: int, seed: int | None = None
) -> list[dict[str, Any]]:
    if not candidates or count <= 0:
        return []
    rng = random.Random(seed)
    pool = list(candidates)
    rng.shuffle(pool)
    pool.sort(key=lambda c: (-1 if c["overdue_days"] >= 0 else 0, -c["overdue_days"], c["count"]))

    picked: list[dict[str, Any]] = []
    used_domains: set[str] = set()

    for item in pool:
        if len(picked) >= count:
            break
        item_domains = set(item["domain"])
        if not used_domains or not item_domains or not (item_domains & used_domains):
            picked.append(item)
            used_domains.update(item_domains)

    picked_paths = {c["path"] for c in picked}
    for item in pool:
        if len(picked) >= count:
            break
        if item["path"] not in picked_paths:
            picked.append(item)
            picked_paths.add(item["path"])

    return picked


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Pick due decisions, mental models, or atomic cards for review & post-mortem."
    )
    parser.add_argument(
        "--mode",
        choices=("decisions", "models", "cards"),
        default="cards",
        help="What to pick: decisions (post-mortem), models (variant drill), or cards (default).",
    )
    parser.add_argument("-n", "--count", type=int, default=3, help="Max items to return.")
    parser.add_argument(
        "--all-pending",
        action="store_true",
        help="In decisions mode, include pending decisions whose review_date is in the future.",
    )
    parser.add_argument("--vault", help="Override VAULT_PATH.")
    parser.add_argument("--seed", type=int, help="Optional random seed.")
    parser.add_argument(
        "--format",
        choices=("markdown", "json"),
        default="markdown",
        help="Output format (default: markdown).",
    )
    args = parser.parse_args()

    vault = get_vault_path(args.vault)
    today = dt.date.today()

    if args.mode == "decisions":
        picked = load_decisions(vault, today, due_only=not args.all_pending)[: args.count]
    elif args.mode == "models":
        candidates = load_cards_or_models(vault, "30-Models", "model", today)
        picked = pick_diverse(candidates, args.count, args.seed)
    else:
        candidates = load_cards_or_models(vault, "20-Cards", "card", today)
        picked = pick_diverse(candidates, args.count, args.seed)

    if args.format == "json":
        print(json.dumps(picked, ensure_ascii=False, indent=2))
        return 0

    if not picked:
        print(f"(No {args.mode} ready for review in {vault})")
        return 0

    print(f"# Review Batch [{args.mode}] ({today.isoformat()} | {len(picked)} item(s))\n")
    for idx, item in enumerate(picked, 1):
        print(f"## {idx}. {item['title']}")
        if item["kind"] == "decision":
            models = ", ".join(item["models_used"]) if item["models_used"] else "none"
            print(
                f"- Path: `{item['path']}` | Models: `{models}` | Confidence: `{item['confidence']}%` | Review date: `{item['review_date']}`\n"
            )
        else:
            domains = ", ".join(item["domain"]) if item["domain"] else "uncategorized"
            print(
                f"- Path: `{item['path']}` | Domain: `{domains}` | Count: `{item['count']}` | Next review: `{item['next_review']}`\n"
            )
        print(item["body"])
        print("\n---\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
