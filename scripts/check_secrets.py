#!/usr/bin/env python3
"""Prüft das Repo auf versehentlich committete Secrets (CI & lokal)."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

SKIP_DIRS = {".venv", ".git", "__pycache__", "data", "node_modules", ".github"}
SKIP_FILES = {"check_secrets.py", "secrets.py"}
SCAN_EXTENSIONS = {".py", ".md", ".txt", ".yml", ".yaml", ".json", ".toml"}

PATTERNS = [
    re.compile(r"sk-proj-[a-zA-Z0-9_-]{20,}"),
    re.compile(r"sk-[a-zA-Z0-9]{20,}"),
]

PLACEHOLDER_OK = {"your_openai_api_key_here", "sk-your-key-here", "sk-..."}


def _is_gitignored(path: Path) -> bool:
    try:
        subprocess.run(
            ["git", "check-ignore", "-q", str(path)],
            cwd=ROOT,
            check=True,
            capture_output=True,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def _is_tracked(path: Path) -> bool:
    try:
        subprocess.run(
            ["git", "ls-files", "--error-unmatch", str(path.relative_to(ROOT))],
            cwd=ROOT,
            check=True,
            capture_output=True,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def scan() -> list[str]:
    findings: list[str] = []

    env_file = ROOT / ".env"
    if env_file.exists() and _is_tracked(env_file):
        findings.append(".env ist von Git getrackt – sofort entfernen (git rm --cached .env)")

    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.name in SKIP_FILES or path.name == ".env":
            continue
        if path.suffix and path.suffix not in SCAN_EXTENSIONS and path.name != ".env.example":
            continue

        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        for line_no, line in enumerate(content.splitlines(), 1):
            stripped = line.strip()
            if any(p in stripped for p in PLACEHOLDER_OK):
                continue
            for pattern in PATTERNS:
                if pattern.search(line):
                    findings.append(
                        f"{path.relative_to(ROOT)}:{line_no}: mögliches Secret"
                    )
    return findings


def main() -> int:
    issues = scan()
    if issues:
        print("Secret-Scan FEHLGESCHLAGEN:")
        for issue in issues:
            print(f"  - {issue}")
        return 1
    print("Secret-Scan OK – keine Secrets im Repo gefunden.")
    if (ROOT / ".env").exists() and not _is_gitignored(ROOT / ".env"):
        print("  Hinweis: .env existiert – stelle sicher, dass sie in .gitignore steht.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
