#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path


NAME_RE = re.compile(r"^[a-z0-9-]{1,63}$")


def fail(message: str) -> int:
    print(f"validate_skill: {message}", file=sys.stderr)
    return 2


def parse_frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---\n"):
        raise ValueError("SKILL.md must start with YAML frontmatter")
    end = text.find("\n---\n", 4)
    if end < 0:
        raise ValueError("SKILL.md frontmatter is not closed")
    data: dict[str, str] = {}
    for line in text[4:end].splitlines():
        if not line.strip():
            continue
        if ":" not in line:
            raise ValueError(f"invalid frontmatter line: {line}")
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip().strip('"')
    return data


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    skill = root / "SKILL.md"
    if not skill.is_file():
        return fail("missing SKILL.md")
    try:
        meta = parse_frontmatter(skill.read_text(encoding="utf-8"))
    except Exception as exc:
        return fail(str(exc))
    if set(meta) != {"name", "description"}:
        return fail("frontmatter must contain only name and description")
    if not NAME_RE.fullmatch(meta["name"]):
        return fail("invalid skill name")
    if len(meta["description"]) < 40:
        return fail("description is too short to trigger reliably")
    required = [
        root / "agents" / "openai.yaml",
        root / "references" / "rights-labels.md",
    ]
    missing = [str(path.relative_to(root)) for path in required if not path.is_file()]
    if missing:
        return fail("missing required files: " + ", ".join(missing))
    print("skill validation ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
