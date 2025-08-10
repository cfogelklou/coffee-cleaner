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

# Candidate protected paths. Some may not exist on all systems/user profiles.
# We'll test whichever exist.
_PROTECTED_PATH_CANDIDATES: List[str] = [
    os.path.expanduser("~/Library/Messages/chat.db"),            # iMessage DB
    os.path.expanduser("~/Library/Safari/History.db"),           # Safari history
    "/Library/Application Support/com.apple.TCC/TCC.db",        # TCC database (system-wide, very protected)
    os.path.expanduser("~/Library/Calendar/Calendar.sqlitedb"),  # Calendar data
]

@dataclass
class FullDiskAccessStatus:
    has_fda: bool
    checked_paths: List[Tuple[str, str]]  # (path, result)
    is_root: bool


def _can_access(path: str) -> Tuple[bool, str]:
    """Attempt a lightweight access check on a path.

    We use os.stat because it doesn't read file contents, only metadata, which is
    enough to trigger a permission error if FDA is missing.
    """
    try:
        os.stat(path)
        return True, "ok"
    except FileNotFoundError:
        return False, "missing"
    except PermissionError as e:
        return False, f"permission_error:{e.errno}"
    except OSError as e:  # Catch 'Operation not permitted' (EPERM) etc.
        return False, f"os_error:{e.errno}"


def has_full_disk_access() -> FullDiskAccessStatus:
    """Heuristically determine if the current process likely has Full Disk Access.

    Strategy: For existing protected files, attempt os.stat(). If ANY protected
    file that exists is accessible, we treat that as evidence FDA is granted.

    Limitations: Could produce false negatives if user lacks those apps/data.
    We bias towards False if unsure.
    """
    if platform.system() != "Darwin":
        return FullDiskAccessStatus(False, [], os.geteuid() == 0 if hasattr(os, "geteuid") else False)

    results: List[Tuple[str, str]] = []
    accessible_any = False
    for p in _PROTECTED_PATH_CANDIDATES:
        can, info = _can_access(p)
        results.append((p, info))
        # We only treat it as affirmative if the path exists (not 'missing') and accessible
        if info == "ok":
            accessible_any = True
    return FullDiskAccessStatus(accessible_any, results, os.geteuid() == 0 if hasattr(os, "geteuid") else False)


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
    "FullDiskAccessStatus",
    "has_full_disk_access",
    "open_full_disk_access_pane",
]
