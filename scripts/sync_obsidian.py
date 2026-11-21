#!/usr/bin/env python3
"""Push/Pull Obsidian UI customization between my-learning-engine/obsidian/ and any Vault."""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

from config import ENGINE_ROOT, get_vault_path

OBSIDIAN_SRC = ENGINE_ROOT / "obsidian"

# Explicit allowlist of non-sensitive Obsidian config files safe to version & reuse across vaults.
# Never includes workspace.json, workspace-mobile.json, or any plugin data.json.
SAFE_CONFIG_FILES = (
    "app.json",
    "appearance.json",
    "hotkeys.json",
    "templates.json",
    "core-plugins.json",
    "community-plugins.json",
    "graph.json",
)

PLUGIN_RUNTIME_FILES = (
    "manifest.json",
    "main.js",
    "styles.css",
)


def copy_file(src: Path, dst: Path, dry_run: bool) -> str:
    if dst.exists() and dst.read_bytes() == src.read_bytes():
        return "unchanged"
    if not dry_run:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
    return "updated"


def push_to_vault(vault_path: Path, dry_run: bool) -> int:
    obs_dst = vault_path / ".obsidian"
    changed = 0
    prefix = "[DRY-RUN] " if dry_run else ""

    # 1. Config JSONs
    config_src = OBSIDIAN_SRC / "config"
    if config_src.is_dir():
        for name in SAFE_CONFIG_FILES:
            src_file = config_src / name
            if src_file.is_file():
                dst_file = obs_dst / name
                status = copy_file(src_file, dst_file, dry_run)
                if status == "updated":
                    changed += 1
                    print(f"{prefix}push config:  {src_file.name} -> {dst_file}")

    # 2. CSS snippets
    snippets_src = OBSIDIAN_SRC / "snippets"
    if snippets_src.is_dir():
        for css_file in sorted(snippets_src.glob("*.css")):
            dst_file = obs_dst / "snippets" / css_file.name
            status = copy_file(css_file, dst_file, dry_run)
            if status == "updated":
                changed += 1
                print(f"{prefix}push snippet: {css_file.name} -> {dst_file}")

    # 3. Themes
    themes_src = OBSIDIAN_SRC / "themes"
    if themes_src.is_dir():
        for item in sorted(themes_src.rglob("*")):
            if not item.is_file() or item.name in {".gitkeep", ".DS_Store"}:
                continue
            rel = item.relative_to(themes_src)
            dst_file = obs_dst / "themes" / rel
            status = copy_file(item, dst_file, dry_run)
            if status == "updated":
                changed += 1
                print(f"{prefix}push theme:   {rel} -> {dst_file}")

    # 4. Built custom plugins (runtime artifacts only, never touches data.json)
    plugins_src = OBSIDIAN_SRC / "plugins"
    if plugins_src.is_dir():
        for plugin_dir in sorted(p for p in plugins_src.iterdir() if p.is_dir()):
            if not (plugin_dir / "manifest.json").is_file() or not (plugin_dir / "main.js").is_file():
                continue
            for filename in PLUGIN_RUNTIME_FILES:
                src_file = plugin_dir / filename
                if not src_file.is_file():
                    continue
                dst_file = obs_dst / "plugins" / plugin_dir.name / filename
                status = copy_file(src_file, dst_file, dry_run)
                if status == "updated":
                    changed += 1
                    print(f"{prefix}push plugin:  {plugin_dir.name}/{filename} -> {dst_file}")

    print(f"{prefix}Done. {changed} file(s) pushed to {obs_dst}.")
    return 0


def pull_from_vault(vault_path: Path, dry_run: bool) -> int:
    obs_src = vault_path / ".obsidian"
    if not obs_src.is_dir():
        print(f"Error: {obs_src} does not exist.", file=sys.stderr)
        return 1

    changed = 0
    prefix = "[DRY-RUN] " if dry_run else ""

    # 1. Safe allowlisted config JSONs
    for name in SAFE_CONFIG_FILES:
        src_file = obs_src / name
        if src_file.is_file():
            dst_file = OBSIDIAN_SRC / "config" / name
            status = copy_file(src_file, dst_file, dry_run)
            if status == "updated":
                changed += 1
                print(f"{prefix}pull config:  {src_file} -> {dst_file}")

    # 2. CSS snippets
    snippets_src = obs_src / "snippets"
    if snippets_src.is_dir():
        for css_file in sorted(snippets_src.glob("*.css")):
            dst_file = OBSIDIAN_SRC / "snippets" / css_file.name
            status = copy_file(css_file, dst_file, dry_run)
            if status == "updated":
                changed += 1
                print(f"{prefix}pull snippet: {css_file} -> {dst_file}")

    # 3. Themes
    themes_src = obs_src / "themes"
    if themes_src.is_dir():
        for item in sorted(themes_src.rglob("*")):
            if not item.is_file() or item.name in {".gitkeep", ".DS_Store"}:
                continue
            rel = item.relative_to(themes_src)
            dst_file = OBSIDIAN_SRC / "themes" / rel
            status = copy_file(item, dst_file, dry_run)
            if status == "updated":
                changed += 1
                print(f"{prefix}pull theme:   {item} -> {dst_file}")

    print(f"{prefix}Done. {changed} file(s) pulled into {OBSIDIAN_SRC}.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Sync Obsidian UI config/snippets/themes/plugins between engine and any vault."
    )
    parser.add_argument(
        "action",
        choices=("push", "pull"),
        help="push: deploy engine/obsidian -> vault/.obsidian; pull: import safe UI config vault -> engine.",
    )
    parser.add_argument("--vault", help="Target vault path (defaults to VAULT_PATH in .env).")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without writing.")
    args = parser.parse_args()

    vault_path = get_vault_path(args.vault)
    if not vault_path.is_dir():
        print(f"Error: vault directory not found: {vault_path}", file=sys.stderr)
        return 1

    if args.action == "push":
        return push_to_vault(vault_path, args.dry_run)
    return pull_from_vault(vault_path, args.dry_run)


if __name__ == "__main__":
    raise SystemExit(main())
