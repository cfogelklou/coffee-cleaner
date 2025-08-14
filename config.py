"""
Configuration and constants for the CoffeeCleaner application.
"""

# Debug flag - set to True to enable detailed logging
DEBUG_MODE = True


def debug_log(message):
    """Print debug messages if DEBUG_MODE is enabled."""
    if DEBUG_MODE:
        print(f"[DEBUG] {message}")


# Pre-defined safety rules as specified in GEMINI.md - Comprehensive macOS Database
PREDEFINED_RULES = {
    # === SAFE TO DELETE (GREEN) === #
    # Cache directories - generally safe to delete
    "~/Library/Caches/*": {
        "safety": "green",
        "reason": "Application cache files. Generally safe to delete.",
    },
    "~/Library/Caches/com.apple.Safari/*": {
        "safety": "green",
        "reason": "Safari browser cache. Safe to delete, will be regenerated.",
    },
    "~/Library/Caches/com.google.Chrome/*": {
        "safety": "green",
        "reason": "Chrome browser cache. Safe to delete, will be regenerated.",
    },
    "~/Library/Caches/com.mozilla.firefox/*": {
        "safety": "green",
        "reason": "Firefox browser cache. Safe to delete, will be regenerated.",
    },
    "/System/Library/Caches/*": {
        "safety": "green",
        "reason": "System cache files. Safe to delete, macOS will regenerate as needed.",
    },
    "/private/var/folders/*/C/*": {
        "safety": "green",
        "reason": "Temporary cache files. Safe to delete.",
    },
    # Temporary files
    "/tmp/*": {
        "safety": "green",
        "reason": "Temporary files. Safe to delete.",
    },
    "~/Library/Application Support/*/Temp/*": {
        "safety": "green",
        "reason": "Application temporary files. Safe to delete.",
    },
    # Downloads and user-controlled areas
    "~/Downloads/*": {
        "safety": "green",
        "reason": "User-downloaded files. User should verify before deleting.",
    },
    "~/Desktop/*": {
        "safety": "green",
        "reason": "User desktop files. User should verify before deleting.",
    },
    "~/.Trash/*": {
        "safety": "green",
        "reason": "Items in trash. Safe to delete permanently.",
    },
    # Log files (older ones typically safe)
    "/private/var/log/*": {
        "safety": "green",
        "reason": "System log files. Generally safe to delete but useful for troubleshooting.",
    },
    "~/Library/Logs/*": {
        "safety": "green",
        "reason": "User application logs. Generally safe to delete.",
    },
    # Browser data that can be safely removed
    "~/Library/Safari/Downloads.plist": {
        "safety": "green",
        "reason": "Safari downloads list. Safe to delete.",
    },
    "~/Library/Safari/History.db*": {
        "safety": "green",
        "reason": "Safari browsing history. Safe to delete if you don't need history.",
    },
    # === CAUTION REQUIRED (ORANGE) === #
    # iOS backups
    "~/Library/Application Support/MobileSync/Backup/*": {
        "safety": "orange",
        "reason": "iOS device backups. Safe to delete if you have recent cloud backups, but deletion is permanent.",
    },
    # User data directories
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
    # Library directories with user settings
    "~/Library/*": {
        "safety": "orange",
        "reason": "Contains important user settings and data. Be very careful.",
    },
    "~/Library/Preferences/*": {
        "safety": "orange",
        "reason": "Application preferences. Deleting may reset app settings.",
    },
    "~/Library/Application Support/*": {
        "safety": "orange",
        "reason": "Application support files and user data. May contain important information.",
    },
    "~/Library/Keychains/*": {
        "safety": "orange",
        "reason": "Keychain files containing passwords and certificates. Be very careful.",
    },
    "~/Library/Mail/*": {
        "safety": "orange",
        "reason": "Mail data and settings. Deleting will remove email data.",
    },
    "~/Library/Calendars/*": {
        "safety": "orange",
        "reason": "Calendar data. Deleting will remove calendar events.",
    },
    "~/Library/Contacts/*": {
        "safety": "orange",
        "reason": "Contact data. Deleting will remove address book entries.",
    },
    # System directories that may have important data
    "/usr/local/*": {
        "safety": "orange",
        "reason": "User-installed software and libraries. May be safe to delete specific items.",
    },
    "/opt/*": {
        "safety": "orange",
        "reason": "Third-party software installations. Check before deleting.",
    },
    "/var/db/*": {
        "safety": "orange",
        "reason": "System databases. Some files may be safe to delete, others are critical.",
    },
    "/var/log/*": {
        "safety": "orange",
        "reason": "System log files. Generally safe but useful for troubleshooting.",
    },
    "/var/tmp/*": {
        "safety": "orange",
        "reason": "Temporary files that persist across reboots. Usually safe but check contents.",
    },
    # === UNSAFE TO DELETE (RED) === #
    # Core system directories
    "/System/*": {
        "safety": "red",
        "reason": "Critical macOS system files. Do not delete.",
    },
    "/Library/*": {
        "safety": "red",
        "reason": "System library files. Critical for macOS operation.",
    },
    "/bin/*": {
        "safety": "red",
        "reason": "Essential system binaries. Do not delete.",
    },
    "/sbin/*": {
        "safety": "red",
        "reason": "System administration binaries. Do not delete.",
    },
    "/usr/bin/*": {
        "safety": "red",
        "reason": "User system binaries. Do not delete.",
    },
    "/usr/sbin/*": {
        "safety": "red",
        "reason": "User system administration binaries. Do not delete.",
    },
    "/usr/lib/*": {
        "safety": "red",
        "reason": "System libraries. Do not delete.",
    },
    "/usr/libexec/*": {
        "safety": "red",
        "reason": "System executables. Do not delete.",
    },
    "/usr/share/*": {
        "safety": "red",
        "reason": "System shared files. Do not delete.",
    },
    # Boot and core directories
    "/boot/*": {
        "safety": "red",
        "reason": "Boot files. Do not delete.",
    },
    "/etc/*": {
        "safety": "red",
        "reason": "System configuration files. Do not delete.",
    },
    "/dev/*": {
        "safety": "red",
        "reason": "Device files. Do not delete.",
    },
    "/proc/*": {
        "safety": "red",
        "reason": "Process information. Do not delete.",
    },
    # Application directories (generally shouldn't delete entire folders)
    "/Applications/*": {
        "safety": "red",
        "reason": "Installed applications. Do not delete this folder directly.",
    },
    "/Applications/Utilities/*": {
        "safety": "red",
        "reason": "System utility applications. Do not delete.",
    },
    # Core system support
    "/var/root/*": {
        "safety": "red",
        "reason": "Root user directory. Do not delete.",
    },
    "/var/vm/*": {
        "safety": "red",
        "reason": "Virtual memory files. Do not delete.",
    },
    "/var/run/*": {
        "safety": "red",
        "reason": "Runtime system files. Do not delete.",
    },
    "/var/spool/*": {
        "safety": "red",
        "reason": "System spool files. Do not delete.",
    },
    # User home directory structure (folders themselves)
    "~/Library/Keychains/login.keychain*": {
        "safety": "red",
        "reason": "Main user keychain. Contains all saved passwords. Do not delete.",
    },
    "~/Library/Preferences/com.apple.loginwindow.plist": {
        "safety": "red",
        "reason": "Login window preferences. Critical for user login.",
    },
    # === COMMON FILE EXTENSIONS === #
    # Safe file types (generally user-created content)
    "*.tmp": {
        "safety": "green",
        "reason": "Temporary file. Generally safe to delete.",
    },
    "*.cache": {
        "safety": "green",
        "reason": "Cache file. Safe to delete, will be regenerated if needed.",
    },
    "*.log": {
        "safety": "green",
        "reason": "Log file. Generally safe to delete but useful for troubleshooting.",
    },
    "*/.DS_Store": {
        "safety": "green",
        "reason": "macOS folder view settings. Safe to delete, will be regenerated.",
    },
    "*/Thumbs.db": {
        "safety": "green",
        "reason": "Windows thumbnail cache. Safe to delete on macOS.",
    },
    # Document files (user should decide)
    "*.doc": {"safety": "orange", "reason": "Document file. User should verify before deleting."},
    "*.docx": {"safety": "orange", "reason": "Document file. User should verify before deleting."},
    "*.pdf": {"safety": "orange", "reason": "PDF document. User should verify before deleting."},
    "*.txt": {"safety": "orange", "reason": "Text file. User should verify before deleting."},
    "*.rtf": {"safety": "orange", "reason": "Rich text file. User should verify before deleting."},
    # Media files
    "*.jpg": {"safety": "orange", "reason": "Image file. User should verify before deleting."},
    "*.jpeg": {"safety": "orange", "reason": "Image file. User should verify before deleting."},
    "*.png": {"safety": "orange", "reason": "Image file. User should verify before deleting."},
    "*.gif": {"safety": "orange", "reason": "Image file. User should verify before deleting."},
    "*.mp4": {"safety": "orange", "reason": "Video file. User should verify before deleting."},
    "*.mov": {"safety": "orange", "reason": "Video file. User should verify before deleting."},
    "*.mp3": {"safety": "orange", "reason": "Audio file. User should verify before deleting."},
    "*.wav": {"safety": "orange", "reason": "Audio file. User should verify before deleting."},
    # System and executable files
    "*.dylib": {
        "safety": "red",
        "reason": "Dynamic library. Critical for application operation. Do not delete.",
    },
    "*.framework/*": {
        "safety": "red",
        "reason": "macOS framework. Critical for system/application operation. Do not delete.",
    },
    "*.kext/*": {
        "safety": "red",
        "reason": "Kernel extension. Critical system component. Do not delete.",
    },
    "*.app/*": {
        "safety": "red",
        "reason": "Application bundle. Deleting will remove the entire application.",
    },
    "*/Contents/MacOS/*": {
        "safety": "red",
        "reason": "Application executable. Critical for application operation.",
    },
}

# Cache for AI analysis results to avoid repeated API calls
ai_analysis_cache = {}

# AI Configuration
AI_CONFIG = {
    "enabled": True,  # Set to False to disable AI analysis
    "provider": "gemini",  # "gemini" or "openai"
    "api_key": None,  # Will be loaded from environment or user input
    "model": "gemini-1.5-flash",  # Default Gemini model
    "timeout": 10,  # API request timeout in seconds
    "max_retries": 3,  # Number of retry attempts
    "fallback_to_heuristic": True,  # Use heuristic analysis if AI fails
}

# Environment variable names for API keys
API_KEY_ENV_VARS = {
    "gemini": "GEMINI_API_KEY",
    "openai": "OPENAI_API_KEY",
}
