#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path


EXCLUDED_DIRS = {".git", ".runtime", "__pycache__", "models", "downloads", "temp", "outputs", "work"}
EXCLUDED_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".mp4", ".mov", ".mkv", ".m4a", ".aac", ".wav", ".mp3", ".zip", ".pyc"}

PATTERNS = [
    re.compile(r"AKID[A-Za-z0-9]{10,}"),
    re.compile(r"sk-[A-Za-z0-9_-]{16,}"),
    re.compile(r"(?i)bearer\s+[A-Za-z0-9._-]{20,}"),
    re.compile(r"(?i)(secret[_-]?(id|key)|api[_-]?key|token)\s*[:=]\s*['\"][^'\"]{12,}['\"]"),
]

ALLOWLIST = {
    "TENCENTCLOUD_APPID",
    "TENCENTCLOUD_SECRET_ID",
    "TENCENTCLOUD_SECRET_KEY",
}


def should_scan(path: Path) -> bool:
    if any(part in EXCLUDED_DIRS for part in path.parts):
        return False
    return path.suffix.lower() not in EXCLUDED_SUFFIXES


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    findings: list[str] = []
    for path in root.rglob("*"):
        if not path.is_file() or not should_scan(path.relative_to(root)):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for index, line in enumerate(text.splitlines(), start=1):
            if any(name in line for name in ALLOWLIST):
                continue
            for pattern in PATTERNS:
                if pattern.search(line):
                    findings.append(f"{path.relative_to(root)}:{index}: possible secret")
                    break
    if findings:
        print("\n".join(findings), file=sys.stderr)
        return 2
    print("secret scan ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
