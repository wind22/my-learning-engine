#!/usr/bin/env python3
"""Push/Pull Obsidian UI customization & install curated community plugins for any Vault."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import urllib.error
import urllib.request
from pathlib import Path

from config import ENGINE_ROOT, get_vault_path

OBSIDIAN_SRC = ENGINE_ROOT / "obsidian"
REGISTRY_URL = (
    "https://raw.githubusercontent.com/obsidianmd/obsidian-releases/master/community-plugins.json"
)

# Explicit allowlist of non-sensitive Obsidian config files safe to version & reuse across vaults.
# Never includes workspace.json, workspace-mobile.json, or secret-bearing plugin data.json.
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


def apply_plugin_defaults(vault_path: Path, dry_run: bool, force: bool = False) -> int:
    defaults_root = OBSIDIAN_SRC / "config" / "plugin-defaults"
    if not defaults_root.is_dir():
        return 0
    changed = 0
    prefix = "[DRY-RUN] " if dry_run else ""
    for plugin_dir in sorted(p for p in defaults_root.iterdir() if p.is_dir()):
        src_data = plugin_dir / "data.json"
        if not src_data.is_file():
            continue
        dst_data = vault_path / ".obsidian" / "plugins" / plugin_dir.name / "data.json"
        if dst_data.exists() and not force:
            continue
        status = copy_file(src_data, dst_data, dry_run)
        if status == "updated":
            changed += 1
            print(f"{prefix}plugin default: {plugin_dir.name}/data.json -> {dst_data}")
    return changed


def install_community_plugins(
    vault_path: Path, dry_run: bool, force_defaults: bool = False
) -> int:
    list_file = OBSIDIAN_SRC / "config" / "community-plugins.json"
    if not list_file.is_file():
        print(f"Error: {list_file} not found.", file=sys.stderr)
        return 1

    plugin_ids: list[str] = json.loads(list_file.read_text(encoding="utf-8"))
    if not plugin_ids:
        print("No community plugins listed.")
        return 0

    print(f"Fetching official Obsidian plugin registry ({len(plugin_ids)} plugins)...")
    req = urllib.request.Request(REGISTRY_URL, headers={"User-Agent": "my-learning-engine/1.0"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        registry = {item["id"]: item for item in json.loads(resp.read().decode("utf-8"))}

    prefix = "[DRY-RUN] " if dry_run else ""
    installed = 0

    for pid in plugin_ids:
        entry = registry.get(pid)
        if not entry:
            print(f"Warning: plugin '{pid}' not found in official registry, skipping.", file=sys.stderr)
            continue
        repo = entry["repo"]
        target_dir = vault_path / ".obsidian" / "plugins" / pid
        print(f"{prefix}install plugin: {pid} ({repo})")
        if dry_run:
            installed += 1
            continue

        target_dir.mkdir(parents=True, exist_ok=True)
        for filename in PLUGIN_RUNTIME_FILES:
            dl_url = f"https://github.com/{repo}/releases/latest/download/{filename}"
            dl_req = urllib.request.Request(dl_url, headers={"User-Agent": "my-learning-engine/1.0"})
            try:
                with urllib.request.urlopen(dl_req, timeout=30) as resp:
                    (target_dir / filename).write_bytes(resp.read())
            except urllib.error.HTTPError as err:
                if filename == "styles.css" and err.code == 404:
                    continue
                print(f"  Error downloading {dl_url}: HTTP {err.code}", file=sys.stderr)
                return 1
        installed += 1

    defaults_changed = apply_plugin_defaults(vault_path, dry_run, force=force_defaults)
    print(
        f"{prefix}Done. {installed} plugin(s) installed, {defaults_changed} default config(s) applied."
    )
    return 0


def push_to_vault(vault_path: Path, dry_run: bool, force_defaults: bool = False) -> int:
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

    # 5. Non-secret plugin defaults (only written if missing, unless --force-defaults)
    changed += apply_plugin_defaults(vault_path, dry_run, force=force_defaults)

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
        choices=("push", "pull", "install-plugins"),
        help="push: deploy engine/obsidian -> vault; pull: import safe UI config vault -> engine; install-plugins: download curated community plugins into vault.",
    )
    parser.add_argument("--vault", help="Target vault path (defaults to VAULT_PATH in .env).")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without writing.")
    parser.add_argument(
        "--force-defaults",
        action="store_true",
        help="Overwrite existing non-secret plugin data.json from obsidian/config/plugin-defaults/.",
    )
    args = parser.parse_args()

    vault_path = get_vault_path(args.vault)
    if not vault_path.is_dir():
        print(f"Error: vault directory not found: {vault_path}", file=sys.stderr)
        return 1

    if args.action == "push":
        return push_to_vault(vault_path, args.dry_run, force_defaults=args.force_defaults)
    if args.action == "install-plugins":
        return install_community_plugins(
            vault_path, args.dry_run, force_defaults=args.force_defaults
        )
    return pull_from_vault(vault_path, args.dry_run)


if __name__ == "__main__":
    raise SystemExit(main())
