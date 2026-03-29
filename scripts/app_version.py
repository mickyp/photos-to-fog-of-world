#!/usr/bin/env python3
"""Helpers for reading the project version."""

from __future__ import annotations

import sys
from pathlib import Path


def project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def version_file_candidates() -> list[Path]:
    candidates = [project_root() / "VERSION"]

    if getattr(sys, "frozen", False):
        candidates.append(Path(sys.executable).resolve().parent / "VERSION")
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            candidates.append(Path(meipass) / "VERSION")

    return candidates


def read_version() -> str:
    for version_file in version_file_candidates():
        try:
            version = version_file.read_text(encoding="utf-8").strip()
        except FileNotFoundError:
            continue
        if version:
            return version
    return "0.0.0"


APP_VERSION = read_version()
