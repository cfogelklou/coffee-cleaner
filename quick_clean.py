"""quick_clean.py
Logic for Quick Clean feature: analyze common junk locations and provide
aggregate sizes plus deletion helpers.

We purposely keep the scan shallow to stay fast:
- User Cache: immediate children of ~/Library/Caches
- System Logs: *.log files in /private/var/log and ~/Library/Logs
- Trash: direct children of ~/.Trash
- iOS Backups: immediate children of ~/Library/Application Support/MobileSync/Backup

Deletion strategy: remove the returned paths (files or directories) directly.
Applications will recreate needed cache directories automatically.
"""
from __future__ import annotations

import os
import fnmatch
import shutil
from dataclasses import dataclass
from typing import List, Dict, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

from config import debug_log
from deletion import perform_deletion

HOME = os.path.expanduser("~")

# Category identifiers
USER_CACHE = "user_cache"
SYSTEM_LOGS = "system_logs"
TRASH = "trash"
IOS_BACKUPS = "ios_backups"

CATEGORY_LABELS = {
    USER_CACHE: "User Cache",
    SYSTEM_LOGS: "System Logs",
    TRASH: "Trash",
    IOS_BACKUPS: "iOS / Device Backups",
}

@dataclass
class QuickCleanItem:
    path: str
    size: int
    category: str

@dataclass
class QuickCleanResult:
    items: List[QuickCleanItem]
    total_size: int

# ---------------- Size Helpers ---------------- #

def format_size(size_bytes: int) -> str:
    if size_bytes <= 0:
        return "0 B"
    units = ["B", "KB", "MB", "GB", "TB"]
    idx = 0
    s = float(size_bytes)
    while s >= 1024 and idx < len(units) - 1:
        s /= 1024
        idx += 1
    return f"{s:.2f} {units[idx]}"


def directory_size(path: str) -> int:
    total = 0
    for root, dirs, files in os.walk(path, onerror=lambda e: None):  # noqa: B023
        for f in files:
            fp = os.path.join(root, f)
            if os.path.islink(fp):
                continue
            try:
                total += os.path.getsize(fp)
            except OSError:
                pass
    return total

# ---------------- Gathering Functions ---------------- #

def gather_user_cache() -> List[QuickCleanItem]:
    cache_root = os.path.join(HOME, "Library", "Caches")
    items: List[QuickCleanItem] = []
    if not os.path.isdir(cache_root):
        return items
    try:
        for entry in os.scandir(cache_root):
            path = entry.path
            try:
                size = directory_size(path) if entry.is_dir(follow_symlinks=False) else os.path.getsize(path)
            except OSError:
                size = 0
            if size > 0:
                items.append(QuickCleanItem(path, size, USER_CACHE))
    except OSError:
        pass
    return items

def gather_system_logs() -> List[QuickCleanItem]:
    items: List[QuickCleanItem] = []
    log_paths = ["/private/var/log", os.path.join(HOME, "Library", "Logs")]
    patterns = ["*.log", "*.0", "system.log.*"]
    for base in log_paths:
        if not os.path.isdir(base):
            continue
        try:
            for entry in os.scandir(base):
                path = entry.path
                if entry.is_dir(follow_symlinks=False):
                    continue  # skip directories; stay shallow
                name = os.path.basename(path)
                if any(fnmatch.fnmatch(name, pat) for pat in patterns):
                    try:
                        size = os.path.getsize(path)
                    except OSError:
                        size = 0
                    if size > 0:
                        items.append(QuickCleanItem(path, size, SYSTEM_LOGS))
        except OSError:
            continue
    return items

def gather_trash() -> List[QuickCleanItem]:
    trash_root = os.path.join(HOME, ".Trash")
    items: List[QuickCleanItem] = []
    if not os.path.isdir(trash_root):
        return items
    try:
        for entry in os.scandir(trash_root):
            path = entry.path
            if entry.is_dir(follow_symlinks=False):
                size = directory_size(path)
            else:
                try:
                    size = os.path.getsize(path)
                except OSError:
                    size = 0
            if size > 0:
                items.append(QuickCleanItem(path, size, TRASH))
    except OSError:
        pass
    return items

def gather_ios_backups() -> List[QuickCleanItem]:
    backup_root = os.path.join(HOME, "Library", "Application Support", "MobileSync", "Backup")
    items: List[QuickCleanItem] = []
    if not os.path.isdir(backup_root):
        return items
    try:
        for entry in os.scandir(backup_root):
            path = entry.path
            if entry.is_dir(follow_symlinks=False):
                size = directory_size(path)
                if size > 0:
                    items.append(QuickCleanItem(path, size, IOS_BACKUPS))
    except OSError:
        pass
    return items

GATHERERS = {
    USER_CACHE: gather_user_cache,
    SYSTEM_LOGS: gather_system_logs,
    TRASH: gather_trash,
    IOS_BACKUPS: gather_ios_backups,
}

# ---------------- Public API ---------------- #

def analyze_quick_clean(selected_categories: List[str]) -> QuickCleanResult:
    debug_log(f"Analyzing quick clean categories: {selected_categories}")
    items: List[QuickCleanItem] = []
    with ThreadPoolExecutor(max_workers=min(4, len(selected_categories) or 1)) as tp:
        futures = {tp.submit(GATHERERS[c]): c for c in selected_categories if c in GATHERERS}
        for fut in as_completed(futures):
            try:
                gathered = fut.result()
                items.extend(gathered)
            except Exception as e:  # noqa: BLE001
                debug_log(f"Error gathering category {futures[fut]}: {e}")
    total_size = sum(i.size for i in items)
    # Sort largest first
    items.sort(key=lambda i: i.size, reverse=True)
    debug_log(f"Quick clean analysis complete: {len(items)} items, total size {format_size(total_size)}")
    return QuickCleanResult(items=items, total_size=total_size)

def perform_quick_clean(result: QuickCleanResult, categories: List[str]) -> Tuple[int, int]:
    # Filter items by categories in case user changed selection
    paths = [i.path for i in result.items if i.category in categories]
    debug_log(f"Performing quick clean deletion on {len(paths)} paths")
    return perform_deletion(paths)

__all__ = [
    "USER_CACHE",
    "SYSTEM_LOGS",
    "TRASH",
    "IOS_BACKUPS",
    "CATEGORY_LABELS",
    "QuickCleanItem",
    "QuickCleanResult",
    "analyze_quick_clean",
    "perform_quick_clean",
    "format_size",
]
