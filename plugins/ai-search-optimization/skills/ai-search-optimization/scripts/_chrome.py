#!/usr/bin/env python3
"""Shared Chromium-family browser detection for the AISO plugin scripts.

Used by generate_report.py (to print HTML → PDF) and by fetch_and_audit.py
(to fetch the post-JS rendered DOM via --dump-dom when --render is passed).

Python stdlib only.
"""

from __future__ import annotations

import os
import shutil


def find_chromium_binary() -> str | None:
    """Return the path to an installed Chromium-family browser, or None.

    Searches platform-specific install locations first, then falls back to
    PATH lookups for common binary names. Order prefers Chrome, then Brave,
    then Chromium, then Edge — matches typical user familiarity.
    """
    candidates: list[str] = [
        # macOS app bundles
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Google Chrome Canary.app/Contents/MacOS/Google Chrome Canary",
        "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
        "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
        # Linux conventional paths
        "/usr/bin/google-chrome",
        "/usr/bin/google-chrome-stable",
        "/usr/bin/chromium",
        "/usr/bin/chromium-browser",
        "/usr/bin/brave-browser",
        "/snap/bin/chromium",
        # Windows
        os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"),
    ]
    for c in candidates:
        if c and os.path.exists(c):
            return c
    for name in (
        "google-chrome",
        "google-chrome-stable",
        "chromium",
        "chromium-browser",
        "brave-browser",
        "msedge",
        "chrome",
    ):
        found = shutil.which(name)
        if found:
            return found
    return None
