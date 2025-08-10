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
MACOS_INSTALLERS = "macos_installers"
XCODE_DERIVED_DATA = "xcode_derived_data"
IOS_SIMULATORS = "ios_simulators"
CRASH_REPORTS = "crash_reports"
MAIL_ATTACHMENTS = "mail_attachments"
TEMP_FILES = "temp_files"
DISK_IMAGES = "disk_images"
APP_SUPPORT_CACHES = "app_support_caches"

CATEGORY_LABELS = {
    USER_CACHE: "User Cache",
    SYSTEM_LOGS: "System Logs",
    TRASH: "Trash",
    IOS_BACKUPS: "iOS / Device Backups",
    MACOS_INSTALLERS: "macOS Installers",
    XCODE_DERIVED_DATA: "Xcode Derived Data",
    IOS_SIMULATORS: "iOS Simulators",
    CRASH_REPORTS: "Crash Reports",
    MAIL_ATTACHMENTS: "Mail Attachments",
    TEMP_FILES: "Temporary Files",
    DISK_IMAGES: "Disk Images (.dmg)",
    APP_SUPPORT_CACHES: "App Support Caches",
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

def gather_macos_installers() -> List[QuickCleanItem]:
    items: List[QuickCleanItem] = []
    app_dir = "/Applications"
    try:
        for entry in os.scandir(app_dir):
            if entry.name.startswith("Install macOS") and entry.name.endswith(".app"):
                path = entry.path
                try:
                    size = directory_size(path) if entry.is_dir(follow_symlinks=False) else os.path.getsize(path)
                except OSError:
                    size = 0
                if size > 0:
                    items.append(QuickCleanItem(path, size, MACOS_INSTALLERS))
    except OSError:
        pass
    return items

def gather_xcode_derived_data() -> List[QuickCleanItem]:
    derived_data_root = os.path.join(HOME, "Library", "Developer", "Xcode", "DerivedData")
    items: List[QuickCleanItem] = []
    if not os.path.isdir(derived_data_root):
        return items
    try:
        for entry in os.scandir(derived_data_root):
            path = entry.path
            try:
                size = directory_size(path) if entry.is_dir(follow_symlinks=False) else os.path.getsize(path)
            except OSError:
                size = 0
            if size > 0:
                items.append(QuickCleanItem(path, size, XCODE_DERIVED_DATA))
    except OSError:
        pass
    return items

def gather_ios_simulators() -> List[QuickCleanItem]:
    simulator_root = os.path.join(HOME, "Library", "Developer", "CoreSimulator", "Devices")
    items: List[QuickCleanItem] = []
    if not os.path.isdir(simulator_root):
        return items
    try:
        for entry in os.scandir(simulator_root):
            path = entry.path
            if entry.is_dir(follow_symlinks=False):
                size = directory_size(path)
                if size > 0:
                    items.append(QuickCleanItem(path, size, IOS_SIMULATORS))
    except OSError:
        pass
    return items

def gather_crash_reports() -> List[QuickCleanItem]:
    items: List[QuickCleanItem] = []
    crash_paths = [
        os.path.join(HOME, "Library", "Logs", "DiagnosticReports"),
        "/Library/Logs/DiagnosticReports"
    ]
    for base in crash_paths:
        if not os.path.isdir(base):
            continue
        try:
            for entry in os.scandir(base):
                path = entry.path
                if entry.is_file(follow_symlinks=False) and (
                    path.endswith(".crash") or path.endswith(".diag") or path.endswith(".panic")
                ):
                    try:
                        size = os.path.getsize(path)
                    except OSError:
                        size = 0
                    if size > 0:
                        items.append(QuickCleanItem(path, size, CRASH_REPORTS))
        except OSError:
            continue
    return items

def gather_mail_attachments() -> List[QuickCleanItem]:
    items: List[QuickCleanItem] = []
    # Check for both old and new Mail attachment locations
    mail_paths = [
        os.path.join(HOME, "Library", "Mail", "V*", "MailData", "Attachments"),
        os.path.join(HOME, "Library", "Mail", "MailData", "Attachments")
    ]
    
    for mail_path_pattern in mail_paths:
        import glob
        for mail_path in glob.glob(mail_path_pattern):
            if not os.path.isdir(mail_path):
                continue
            try:
                for root, dirs, files in os.walk(mail_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        try:
                            size = os.path.getsize(file_path)
                            if size > 0:
                                items.append(QuickCleanItem(file_path, size, MAIL_ATTACHMENTS))
                        except OSError:
                            pass
            except OSError:
                continue
    return items

def gather_temp_files() -> List[QuickCleanItem]:
    items: List[QuickCleanItem] = []
    temp_paths = ["/private/var/tmp", "/private/var/folders"]
    
    for base in temp_paths:
        if not os.path.isdir(base):
            continue
        try:
            if base == "/private/var/folders":
                # For /private/var/folders, go one level deeper to find temp files
                for entry in os.scandir(base):
                    if entry.is_dir(follow_symlinks=False):
                        temp_subdir = entry.path
                        try:
                            for subentry in os.scandir(temp_subdir):
                                if subentry.is_dir(follow_symlinks=False):
                                    path = subentry.path
                                    size = directory_size(path)
                                    if size > 1024 * 1024:  # Only include if > 1MB
                                        items.append(QuickCleanItem(path, size, TEMP_FILES))
                        except OSError:
                            continue
            else:
                for entry in os.scandir(base):
                    path = entry.path
                    try:
                        size = directory_size(path) if entry.is_dir(follow_symlinks=False) else os.path.getsize(path)
                        if size > 1024 * 1024:  # Only include if > 1MB
                            items.append(QuickCleanItem(path, size, TEMP_FILES))
                    except OSError:
                        pass
        except OSError:
            continue
    return items

def gather_disk_images() -> List[QuickCleanItem]:
    items: List[QuickCleanItem] = []
    search_paths = [
        os.path.join(HOME, "Downloads"),
        os.path.join(HOME, "Documents"),
        os.path.join(HOME, "Desktop")
    ]
    
    for base in search_paths:
        if not os.path.isdir(base):
            continue
        try:
            for entry in os.scandir(base):
                if entry.is_file(follow_symlinks=False) and entry.name.endswith(".dmg"):
                    path = entry.path
                    try:
                        size = os.path.getsize(path)
                        if size > 0:
                            items.append(QuickCleanItem(path, size, DISK_IMAGES))
                    except OSError:
                        pass
        except OSError:
            continue
    return items

def gather_app_support_caches() -> List[QuickCleanItem]:
    app_support_root = os.path.join(HOME, "Library", "Application Support")
    items: List[QuickCleanItem] = []
    if not os.path.isdir(app_support_root):
        return items
    
    # Common cache subdirectories in Application Support
    cache_patterns = ["*Cache*", "*cache*", "*Caches*", "*caches*"]
    
    try:
        for entry in os.scandir(app_support_root):
            if entry.is_dir(follow_symlinks=False):
                app_dir = entry.path
                try:
                    for subentry in os.scandir(app_dir):
                        if subentry.is_dir(follow_symlinks=False):
                            for pattern in cache_patterns:
                                if fnmatch.fnmatch(subentry.name, pattern):
                                    path = subentry.path
                                    size = directory_size(path)
                                    if size > 0:
                                        items.append(QuickCleanItem(path, size, APP_SUPPORT_CACHES))
                                    break
                except OSError:
                    continue
    except OSError:
        pass
    return items

GATHERERS = {
    USER_CACHE: gather_user_cache,
    SYSTEM_LOGS: gather_system_logs,
    TRASH: gather_trash,
    IOS_BACKUPS: gather_ios_backups,
    MACOS_INSTALLERS: gather_macos_installers,
    XCODE_DERIVED_DATA: gather_xcode_derived_data,
    IOS_SIMULATORS: gather_ios_simulators,
    CRASH_REPORTS: gather_crash_reports,
    MAIL_ATTACHMENTS: gather_mail_attachments,
    TEMP_FILES: gather_temp_files,
    DISK_IMAGES: gather_disk_images,
    APP_SUPPORT_CACHES: gather_app_support_caches,
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
    "MACOS_INSTALLERS",
    "XCODE_DERIVED_DATA",
    "IOS_SIMULATORS",
    "CRASH_REPORTS",
    "MAIL_ATTACHMENTS",
    "TEMP_FILES",
    "DISK_IMAGES",
    "APP_SUPPORT_CACHES",
    "CATEGORY_LABELS",
    "QuickCleanItem",
    "QuickCleanResult",
    "analyze_quick_clean",
    "analyze_quick_clean_iter",
    "perform_quick_clean",
    "format_size",
]

def analyze_quick_clean_iter(selected_categories: List[str]):
    """Yield (category, items, total_size_for_category) sequentially for streaming UI updates."""
    for cat in selected_categories:
        if cat not in GATHERERS:
            continue
        try:
            items = GATHERERS[cat]()
        except Exception as e:  # noqa: BLE001
            debug_log(f"Error gathering category {cat}: {e}")
            items = []
        yield cat, items, sum(i.size for i in items)
