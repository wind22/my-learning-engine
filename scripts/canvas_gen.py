#!/usr/bin/env python3
"""Generate an Obsidian JSON Canvas 1.0 (.canvas) file from a topic skeleton JSON."""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path
from typing import Any

from config import get_vault_path

NODE_COLORS = ["1", "2", "3", "4", "5", "6"]


def sanitize_filename(name: str) -> str:
    cleaned = re.sub(r'[\\/:*?"<>|]+', "-", name).strip()
    return cleaned or "untitled-map"


def build_canvas(skeleton: dict[str, Any]) -> dict[str, Any]:
    title = str(skeleton.get("title", "Untitled Topic")).strip()
    essence = str(skeleton.get("essence", "")).strip()
    elements = skeleton.get("elements") or []
    links = skeleton.get("links") or []

    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []

    core_w, core_h = 380, 190
    nodes.append(
        {
            "id": "core",
            "type": "text",
            "x": -core_w // 2,
            "y": -core_h // 2,
            "width": core_w,
            "height": core_h,
            "color": "6",
            "text": f"# {title}\n\n{essence}",
        }
    )

    elem_w, elem_h = 280, 150
    radius_x, radius_y = 460, 310
    count = max(len(elements), 1)
    id_set = {"core"}

    for idx, elem in enumerate(elements):
        eid = str(elem.get("id") or f"e{idx + 1}")
        id_set.add(eid)
        angle = (2 * math.pi * idx / count) - (math.pi / 2)
        cx = int(round(radius_x * math.cos(angle)))
        cy = int(round(radius_y * math.sin(angle)))

        el_title = str(elem.get("title", f"要素 {idx + 1}")).strip()
        el_summary = str(elem.get("summary", "")).strip()
        text = f"### {el_title}\n\n{el_summary}".strip()

        nodes.append(
            {
                "id": eid,
                "type": "text",
                "x": cx - elem_w // 2,
                "y": cy - elem_h // 2,
                "width": elem_w,
                "height": elem_h,
                "color": NODE_COLORS[idx % (len(NODE_COLORS) - 1)],
                "text": text,
            }
        )

        edge: dict[str, Any] = {
            "id": f"edge-core-{eid}",
            "fromNode": "core",
            "toNode": eid,
        }
        rel = str(elem.get("relation_to_core", "")).strip()
        if rel:
            edge["label"] = rel
        edges.append(edge)

    for idx, link in enumerate(links):
        src = str(link.get("from", "")).strip()
        dst = str(link.get("to", "")).strip()
        if src not in id_set or dst not in id_set:
            continue
        edge = {
            "id": f"edge-link-{idx + 1}",
            "fromNode": src,
            "toNode": dst,
        }
        label = str(link.get("label", "")).strip()
        if label:
            edge["label"] = label
        edges.append(edge)

    return {"nodes": nodes, "edges": edges}


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate an Obsidian JSON Canvas (.canvas) from a skeleton JSON."
    )
    parser.add_argument(
        "--input",
        "-i",
        help="Path to skeleton JSON file (reads stdin if omitted).",
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Explicit output .canvas file path.",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Write directly to <VAULT_PATH>/10-Maps/<title>.canvas.",
    )
    parser.add_argument("--vault", help="Override VAULT_PATH.")
    args = parser.parse_args()

    raw = (
        Path(args.input).read_text(encoding="utf-8")
        if args.input
        else sys.stdin.read()
    )
    if not raw.strip():
        print("Error: empty JSON input.", file=sys.stderr)
        return 1

    skeleton = json.loads(raw)
    canvas = build_canvas(skeleton)
    rendered = json.dumps(canvas, ensure_ascii=False, indent=2) + "\n"

    if args.output:
        out_path = Path(args.output).expanduser().resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(rendered, encoding="utf-8")
        print(f"Wrote canvas: {out_path}")
    elif args.write:
        vault = get_vault_path(args.vault)
        filename = sanitize_filename(str(skeleton.get("title", "untitled-map")))
        out_path = vault / "10-Maps" / f"{filename}.canvas"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(rendered, encoding="utf-8")
        print(f"Wrote canvas: {out_path}")
    else:
        sys.stdout.write(rendered)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
