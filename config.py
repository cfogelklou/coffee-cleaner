"""
Configuration and constants for the Mac Cleaner & Analyzer application.
"""

# Debug flag - set to True to enable detailed logging
DEBUG_MODE = True

def debug_log(message):
    """Print debug messages if DEBUG_MODE is enabled."""
    if DEBUG_MODE:
        print(f"[DEBUG] {message}")

# Pre-defined safety rules as specified in GEMINI.md
PREDEFINED_RULES = {
    "~/Library/Caches/*": {
        "safety": "green",
        "reason": "Application cache files. Generally safe to delete.",
    },
    "~/Downloads/*": {
        "safety": "green",
        "reason": "User-downloaded files. User should verify before deleting.",
    },
    "~/Library/Application Support/MobileSync/Backup/*": {
        "safety": "orange",
        "reason": "iOS device backups. Safe to delete if you have recent cloud backups, but deletion is permanent.",
    },
    "/System/*": {
        "safety": "red",
        "reason": "Critical macOS system files. Do not delete.",
    },
    "/Applications/*": {
        "safety": "red",
        "reason": "Installed applications. Do not delete this folder directly.",
    },
    "~/Library/*": {
        "safety": "orange",
        "reason": "Contains important user settings and data. Be very careful.",
    },
    "~/.Trash/*": {
        "safety": "green",
        "reason": "Items in trash. Safe to delete permanently.",
    },
    "/private/var/log/*": {
        "safety": "orange",
        "reason": "System log files. Generally safe to delete but useful for troubleshooting.",
    },
    "~/Desktop/*": {
        "safety": "green",
        "reason": "User desktop files. User should verify before deleting.",
    },
    "~/Documents/*": {
        "safety": "orange",
        "reason": "User documents. Important files - be careful when deleting.",
    },
    "~/Pictures/*": {
        "safety": "orange",
        "reason": "User photos and images. Important files - be careful when deleting.",
    },
    "~/Movies/*": {
        "safety": "orange",
        "reason": "User videos. Important files - be careful when deleting.",
    },
    "~/Music/*": {
        "safety": "orange",
        "reason": "User music files. Important files - be careful when deleting.",
    },
    "/usr/*": {
        "safety": "red",
        "reason": "System utilities and programs. Do not delete.",
    },
    "/bin/*": {"safety": "red", "reason": "Essential system binaries. Do not delete."},
    "/sbin/*": {
        "safety": "red",
        "reason": "System administration binaries. Do not delete.",
    },
    "/var/*": {
        "safety": "orange",
        "reason": "Variable data files. Some may be safe to delete, others are critical.",
    },
    "~/Library/Preferences/*": {
        "safety": "orange",
        "reason": "Application preferences. Deleting may reset app settings.",
    },
}

# Cache for AI analysis results to avoid repeated API calls
ai_analysis_cache = {}
