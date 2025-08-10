"""mac_permissions.py
Utility helpers to detect Full Disk Access (FDA) and elevated privileges on macOS
and to open the System Settings pane where the user can grant FDA.

Notes:
- There is no official public Python API to query Full Disk Access directly.
- We heuristically attempt to read metadata from several known protected files.
  If at least one protected file is readable, we assume FDA is granted.
- Root (sudo) does NOT automatically imply FDA, and FDA does not grant root.
- We provide a helper that opens the proper System Settings / Preferences pane
  via URL schemes. (macOS 13+ uses System Settings, earlier used System Preferences.)

This module is lightweight and safe; if run on non-macOS it returns conservative defaults.
"""
from __future__ import annotations

import os
import platform
import subprocess
from dataclasses import dataclass
from typing import List, Tuple



def open_full_disk_access_pane() -> bool:
    """Open the System Settings / Preferences pane for Full Disk Access.

    Returns True if we successfully launched System Settings, False otherwise.
    """
    if platform.system() != "Darwin":
        return False

    # Modern (Ventura / Sonoma / later) URL
    urls = [
        "x-apple.systempreferences:com.apple.preference.security?Privacy_AllFiles",  # macOS 13+
        "x-apple.systempreferences:com.apple.preference.security?Privacy_FullDiskAccess",  # older fallback
    ]
    for url in urls:
        try:
            subprocess.run(["open", url], check=True)
            return True
        except Exception:
            continue
    return False

__all__ = [
    "open_full_disk_access_pane",
]
