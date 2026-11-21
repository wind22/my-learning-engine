#!/usr/bin/env python3
"""Build a compact index of atomic cards (20-Cards/) and mental models (30-Models/) for LLM retrieval."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from config import extract_wikilinks, get_vault_path, parse_markdown_note


def extract_section(body: str, heading: str) -> str:
    pattern = rf"^##\s+{re.escape(heading)}.*$"
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
    return " ".join(collected)[:200]


def extract_callout_summary(body: str) -> str:
    lines = body.splitlines()
    for idx, line in enumerate(lines):
        if line.strip().startswith("> [!") and idx + 1 < len(lines):
            nxt = lines[idx + 1].strip().lstrip(">").strip()
            if nxt:
                return nxt[:180]
    return ""


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
        models = meta.get("models") or []
        if isinstance(models, str):
            models = [models]
        records.append(
            {
                "kind": "card",
                "title": md_file.stem,
                "path": str(md_file.relative_to(vault_path)),
                "domain": domains,
                "status": meta.get("status") or "seedling",
                "trigger": meta.get("trigger") or "",
                "models": models,
                "review_count": meta.get("review_count") or 0,
                "next_review": meta.get("next_review"),
                "core": extract_section(body, "核心方法论"),
                "links": extract_wikilinks(body),
            }
        )
    return records


def scan_models(vault_path: Path) -> list[dict[str, Any]]:
    models_dir = vault_path / "30-Models"
    if not models_dir.is_dir():
        return []

    records: list[dict[str, Any]] = []
    for md_file in sorted(models_dir.rglob("*.md")):
        meta, body = parse_markdown_note(md_file)
        domains = meta.get("domain") or []
        if isinstance(domains, str):
            domains = [domains]
        records.append(
            {
                "kind": "model",
                "title": md_file.stem,
                "path": str(md_file.relative_to(vault_path)),
                "domain": domains,
                "status": meta.get("status") or "draft",
                "usage_count": meta.get("usage_count") or 0,
                "last_used": meta.get("last_used"),
                "essence": extract_callout_summary(body),
                "triggers": extract_section(body, "触发信号"),
                "checklist": extract_section(body, "决策自检清单"),
                "boundaries": extract_section(body, "盲区与失效边界"),
                "links": extract_wikilinks(body),
            }
        )
    return records


def main() -> int:
    parser = argparse.ArgumentParser(
        description="List compact metadata for atomic cards (20-Cards/) and mental models (30-Models/)."
    )
    parser.add_argument("--vault", help="Override VAULT_PATH.")
    parser.add_argument(
        "--scope",
        choices=("all", "cards", "models"),
        default="all",
        help="What to index (default: all).",
    )
    parser.add_argument(
        "--format",
        choices=("markdown", "json"),
        default="markdown",
        help="Output format (default: markdown).",
    )
    args = parser.parse_args()

    vault = get_vault_path(args.vault)
    models = scan_models(vault) if args.scope in ("all", "models") else []
    cards = scan_cards(vault) if args.scope in ("all", "cards") else []

    if args.format == "json":
        payload = {"models": models, "cards": cards}
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    if args.scope in ("all", "models"):
        if not models:
            print(f"(No mental models found in {vault / '30-Models'})")
        else:
            print(f"# Mental Models Index ({len(models)} models)\n")
            for m in models:
                domains = ", ".join(m["domain"]) if m["domain"] else "general"
                print(
                    f"- **[[{m['title']}]]** (`{domains}` | `{m['status']}` | used `{m['usage_count']}`x)"
                )
                if m["essence"]:
                    print(f"  - 本质: {m['essence']}")
                if m["triggers"]:
                    print(f"  - 触发信号: {m['triggers']}")
                if m["boundaries"]:
                    print(f"  - 失效边界: {m['boundaries']}")
        if args.scope == "all":
            print()

    if args.scope in ("all", "cards"):
        if not cards:
            print(f"(No atomic cards found in {vault / '20-Cards'})")
        else:
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
