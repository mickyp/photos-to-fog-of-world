#!/usr/bin/env python3
"""Helpers for reading the project version."""

from __future__ import annotations

from pathlib import Path


def project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def read_version() -> str:
    version_file = project_root() / "VERSION"
    try:
        version = version_file.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        return "0.0.0"
    return version or "0.0.0"


APP_VERSION = read_version()
