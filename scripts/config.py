"""Shared configuration and lightweight Markdown frontmatter helpers (stdlib only)."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

ENGINE_ROOT = Path(__file__).resolve().parent.parent


def load_dotenv(env_path: Path | None = None) -> dict[str, str]:
    path = env_path or (ENGINE_ROOT / ".env")
    values: dict[str, str] = {}
    if not path.is_file():
        return values
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, val = line.split("=", 1)
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        if key:
            values[key] = val
    return values


def get_vault_path(cli_override: str | None = None) -> Path:
    if cli_override:
        return Path(cli_override).expanduser().resolve()
    env_val = os.environ.get("VAULT_PATH") or load_dotenv().get("VAULT_PATH")
    if env_val:
        return Path(env_val).expanduser().resolve()
    return (ENGINE_ROOT.parent / "my-knowledge-vault").resolve()


def _parse_scalar(raw: str) -> Any:
    val = raw.strip()
    if not val or val in {"null", "~"}:
        return None
    if (val.startswith('"') and val.endswith('"')) or (
        val.startswith("'") and val.endswith("'")
    ):
        return val[1:-1]
    if val.startswith("[") and val.endswith("]"):
        inner = val[1:-1].strip()
        if not inner:
            return []
        return [_parse_scalar(part) for part in inner.split(",") if part.strip()]
    if re.fullmatch(r"-?\d+", val):
        return int(val)
    return val


def parse_markdown_note(path: Path) -> tuple[dict[str, Any], str]:
    """Parse simple YAML frontmatter and return (metadata, body)."""
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return {}, text

    end_idx = text.find("\n---\n", 4)
    if end_idx == -1:
        if text.endswith("\n---"):
            end_idx = len(text) - 4
        else:
            return {}, text

    fm_block = text[4:end_idx]
    body = text[end_idx + 5 :].lstrip("\n")

    meta: dict[str, Any] = {}
    current_list_key: str | None = None

    for raw_line in fm_block.splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("- ") and current_list_key:
            meta.setdefault(current_list_key, []).append(_parse_scalar(stripped[2:]))
            continue
        current_list_key = None
        if ":" not in raw_line:
            continue
        key, val = raw_line.split(":", 1)
        key = key.strip()
        val_stripped = val.strip()
        if not val_stripped:
            meta[key] = []
            current_list_key = key
        else:
            meta[key] = _parse_scalar(val_stripped)

    return meta, body


def extract_wikilinks(text: str) -> list[str]:
    """Extract unique [[Target]] or [[Target|Alias]] targets preserving order."""
    seen: set[str] = set()
    links: list[str] = []
    for match in re.finditer(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]", text):
        target = match.group(1).strip()
        if target and target not in seen:
            seen.add(target)
            links.append(target)
    return links
