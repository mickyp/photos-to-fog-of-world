#!/usr/bin/env python3
"""Generate CHANGELOG.md entries from git commit history."""

from __future__ import annotations

import argparse
import subprocess
from datetime import date
from pathlib import Path

from app_version import APP_VERSION, project_root


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate or update CHANGELOG.md for the current project version."
    )
    parser.add_argument(
        "--version",
        default=APP_VERSION,
        help="Version to write into CHANGELOG.md. Defaults to the VERSION file.",
    )
    parser.add_argument(
        "--date",
        dest="release_date",
        default=str(date.today()),
        help="Release date to write into CHANGELOG.md, in YYYY-MM-DD format.",
    )
    return parser.parse_args()


def run_git_command(args: list[str]) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=project_root(),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=True,
    )
    return result.stdout.strip()


def latest_version_tag() -> str | None:
    output = run_git_command(["tag", "--list", "v*", "--sort=-version:refname"])
    tags = [line.strip() for line in output.splitlines() if line.strip()]
    current_tag = f"v{APP_VERSION}"
    for tag in tags:
        if tag != current_tag:
            return tag
    return None


def collect_commit_subjects() -> list[str]:
    previous_tag = latest_version_tag()
    git_args = ["log", "--pretty=%s"]
    if previous_tag:
        git_args.append(f"{previous_tag}..HEAD")

    output = run_git_command(git_args)
    subjects: list[str] = []
    for line in output.splitlines():
        subject = line.strip()
        if not subject or subject.startswith("Merge "):
            continue
        if subject not in subjects:
            subjects.append(subject)
    return subjects


def changelog_header() -> str:
    return (
        "# Changelog\n\n"
        "本檔案記錄每個版本的重要變更。\n\n"
        "## [Unreleased]\n\n"
        "- 尚未整理新的未釋出變更。\n"
    )


def build_release_section(version: str, release_date: str, subjects: list[str]) -> str:
    if not subjects:
        subjects = ["維護與整理釋出內容。"]

    bullet_lines = "\n".join(f"- {subject}" for subject in subjects)
    return f"## [{version}] - {release_date}\n\n### Changes\n\n{bullet_lines}\n"


def upsert_release_section(changelog_text: str, section_text: str, version: str) -> str:
    marker = f"## [{version}]"
    if marker in changelog_text:
        start = changelog_text.index(marker)
        next_start = changelog_text.find("\n## [", start + len(marker))
        if next_start == -1:
            return changelog_text[:start].rstrip() + "\n\n" + section_text.strip() + "\n"
        return (
            changelog_text[:start].rstrip()
            + "\n\n"
            + section_text.strip()
            + "\n\n"
            + changelog_text[next_start + 1 :].lstrip()
        )

    unreleased_marker = "## [Unreleased]"
    if unreleased_marker not in changelog_text:
        changelog_text = changelog_header()

    insertion_point = changelog_text.index(unreleased_marker) + len(unreleased_marker)
    next_section = changelog_text.find("\n## [", insertion_point)
    if next_section == -1:
        return (
            changelog_text.rstrip()
            + "\n\n"
            + section_text.strip()
            + "\n"
        )

    unreleased_block = changelog_text[:next_section].rstrip()
    remainder = changelog_text[next_section:].lstrip()
    return unreleased_block + "\n\n" + section_text.strip() + "\n\n" + remainder


def main() -> int:
    args = parse_args()
    changelog_path = project_root() / "CHANGELOG.md"
    existing = (
        changelog_path.read_text(encoding="utf-8")
        if changelog_path.exists()
        else changelog_header()
    )
    section = build_release_section(args.version, args.release_date, collect_commit_subjects())
    updated = upsert_release_section(existing, section, args.version)
    changelog_path.write_text(updated.rstrip() + "\n", encoding="utf-8")
    print(f"Updated CHANGELOG.md for version {args.version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
