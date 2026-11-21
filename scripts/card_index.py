#!/usr/bin/env python3
"""Build a compact index of atomic cards in 20-Cards/ for LLM cross-domain linking."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from config import extract_wikilinks, get_vault_path, parse_markdown_note


def extract_section(body: str, heading: str) -> str:
    pattern = rf"^##\s+{re.escape(heading)}\s*$"
    lines = body.splitlines()
    capture = False
    collected: list[str] = []
    for line in lines:
        if re.match(pattern, line.strip()):
            capture = True
            continue
        if capture and line.startswith("## "):
            break
        if capture:
            cleaned = line.strip()
            if cleaned and not cleaned.startswith("<!--"):
                collected.append(cleaned)
    return " ".join(collected)[:180]


def scan_cards(vault_path: Path) -> list[dict[str, Any]]:
    cards_dir = vault_path / "20-Cards"
    if not cards_dir.is_dir():
        return []

    records: list[dict[str, Any]] = []
    for md_file in sorted(cards_dir.rglob("*.md")):
        meta, body = parse_markdown_note(md_file)
        domains = meta.get("domain") or []
        if isinstance(domains, str):
            domains = [domains]
        records.append(
            {
                "title": md_file.stem,
                "path": str(md_file.relative_to(vault_path)),
                "domain": domains,
                "status": meta.get("status") or "seedling",
                "trigger": meta.get("trigger") or "",
                "review_count": meta.get("review_count") or 0,
                "next_review": meta.get("next_review"),
                "core": extract_section(body, "核心方法论"),
                "links": extract_wikilinks(body),
            }
        )
    return records


def main() -> int:
    parser = argparse.ArgumentParser(
        description="List compact metadata for all atomic cards in 20-Cards/."
    )
    parser.add_argument("--vault", help="Override VAULT_PATH.")
    parser.add_argument(
        "--format",
        choices=("markdown", "json"),
        default="markdown",
        help="Output format (default: markdown).",
    )
    args = parser.parse_args()

    vault = get_vault_path(args.vault)
    cards = scan_cards(vault)

    if args.format == "json":
        print(json.dumps(cards, ensure_ascii=False, indent=2))
        return 0

    if not cards:
        print(f"(No atomic cards found in {vault / '20-Cards'})")
        return 0

    print(f"# Atomic Cards Index ({len(cards)} cards)\n")
    for c in cards:
        domains = ", ".join(c["domain"]) if c["domain"] else "uncategorized"
        links = ", ".join(f"[[{l}]]" for l in c["links"]) if c["links"] else "none"
        print(f"- **[[{c['title']}]]** (`{domains}` | `{c['status']}`)")
        if c["trigger"]:
            print(f"  - 触发点: {c['trigger']}")
        if c["core"]:
            print(f"  - 方法论: {c['core']}")
        print(f"  - 已有链接: {links}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
