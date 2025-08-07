"""
Safety analysis and AI functionality for the Mac Cleaner & Analyzer.
"""

import os
import time
import fnmatch
import flet as ft
from config import PREDEFINED_RULES, ai_analysis_cache, debug_log


def normalize_path(path):
    """Normalize a path by expanding ~ and resolving .. components."""
    return os.path.normpath(os.path.expanduser(path))


def get_safety_info(path):
    """
    Determine safety level and reason for a given path using predefined rules.
    Returns a dict with 'safety' (green/orange/red/grey) and 'reason'.
    """
    normalized_path = normalize_path(path)

    # Check cache first
    if normalized_path in ai_analysis_cache:
        return ai_analysis_cache[normalized_path]

    # Check against predefined rules
    for pattern, info in PREDEFINED_RULES.items():
        pattern_normalized = normalize_path(pattern)
        if fnmatch.fnmatch(normalized_path, pattern_normalized):
            return info

    # If no rule matches, return grey (unknown)
    return {
        "safety": "grey",
        "reason": "Safety level unknown. Click AI icon for analysis.",
    }


def ai_analyze_path(path):
    """
    Use Gemini API to analyze unknown paths.
    For now, this is a placeholder that simulates AI analysis.
    TODO: Integrate actual Gemini API when API key is available.
    """
    normalized_path = normalize_path(path)

    # Check if already cached
    if normalized_path in ai_analysis_cache:
        return ai_analysis_cache[normalized_path]

    # Simulate AI analysis (placeholder)
    # In real implementation, this would call Gemini API
    time.sleep(0.5)  # Simulate API call delay

    # Simple heuristic-based analysis for simulation
    basename = os.path.basename(normalized_path).lower()

    if any(word in basename for word in ["cache", "temp", "tmp", "log"]):
        result = {
            "safety": "green",
            "reason": "AI Analysis: Appears to be temporary/cache files. Likely safe to delete.",
        }
    elif any(word in basename for word in ["config", "pref", "setting"]):
        result = {
            "safety": "orange",
            "reason": "AI Analysis: Configuration or preference files. Deleting may affect application behavior.",
        }
    elif any(word in basename for word in ["system", "kernel", "driver"]):
        result = {
            "safety": "red",
            "reason": "AI Analysis: System-related files. Not recommended for deletion.",
        }
    else:
        result = {
            "safety": "orange",
            "reason": "AI Analysis: Unknown file type. Exercise caution when deleting.",
        }

    # Cache the result
    ai_analysis_cache[normalized_path] = result
    return result


def get_safety_color(safety_level):
    """Return the appropriate color for the safety level."""
    colors = {
        "green": ft.Colors.GREEN,
        "orange": ft.Colors.ORANGE,
        "red": ft.Colors.RED,
        "grey": ft.Colors.GREY_400,
    }
    return colors.get(safety_level, ft.Colors.GREY_400)
