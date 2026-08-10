#!/usr/bin/env python3
"""Validate relative links and images in repository Markdown files."""

from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import unquote


PROJECT_ROOT = Path(__file__).resolve().parents[1]
LINK_PATTERN = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
SKIP_PREFIXES = ("http://", "https://", "mailto:", "#", "data:")


def markdown_files(root: Path = PROJECT_ROOT) -> list[Path]:
    """Return repository Markdown files while excluding generated caches."""

    return sorted(
        path
        for path in root.rglob("*.md")
        if ".git" not in path.parts and ".pytest_cache" not in path.parts
    )


def broken_links(root: Path = PROJECT_ROOT) -> list[str]:
    """Return human-readable descriptions of missing local Markdown targets."""

    failures: list[str] = []
    for markdown_path in markdown_files(root):
        text = markdown_path.read_text(encoding="utf-8")
        for match in LINK_PATTERN.finditer(text):
            raw_target = match.group(1).strip().strip("<>")
            target = raw_target.split(maxsplit=1)[0]
            if not target or target.startswith(SKIP_PREFIXES):
                continue
            target = unquote(target.split("#", 1)[0])
            resolved = (markdown_path.parent / target).resolve()
            if not resolved.exists():
                relative_source = markdown_path.relative_to(root).as_posix()
                failures.append(f"{relative_source}: missing target {raw_target}")
    return failures


def main() -> int:
    failures = broken_links()
    if failures:
        print("Broken repository links:")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print(f"Repository link check passed ({len(markdown_files())} Markdown files).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
