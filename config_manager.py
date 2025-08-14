"""
Configuration Manager for CoffeeCleaner
Handles API keys, user preferences, and application settings.
"""

import os
import json
from typing import Optional, Dict, Any

# Configuration file path
CONFIG_FILE = "user_config.json"
CACHE_FILE = "ai_analysis_cache.json"


class ConfigManager:
    """Manages application configuration and API keys."""

    def __init__(self):
        self.config_path = os.path.join(os.getcwd(), CONFIG_FILE)
        self.cache_path = os.path.join(os.getcwd(), CACHE_FILE)
        self._config = self._load_config()
        self._cache = self._load_cache()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file."""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                print("Warning: Could not load config file, using defaults")

        # Default configuration
        return {
            "gemini_api_key": "",
            "openai_api_key": "",
            "preferred_ai_provider": "gemini",  # "gemini" or "openai"
            "enable_ai_analysis": True,
            "cache_ai_results": True,
            "debug_mode": True,
        }

    def _save_config(self):
        """Save configuration to file."""
        try:
            with open(self.config_path, "w") as f:
                json.dump(self._config, f, indent=2)
        except IOError as e:
            print(f"Warning: Could not save config file: {e}")

    def _load_cache(self) -> Dict[str, Any]:
        """Load AI analysis cache from file."""
        if os.path.exists(self.cache_path):
            try:
                with open(self.cache_path, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return {}

    def _save_cache(self):
        """Save AI analysis cache to file."""
        try:
            with open(self.cache_path, "w") as f:
                json.dump(self._cache, f, indent=2)
        except IOError as e:
            print(f"Warning: Could not save cache file: {e}")

    # API Key Management
    def get_gemini_api_key(self) -> str:
        """Get Gemini API key."""
        return self._config.get("gemini_api_key", "")

    def set_gemini_api_key(self, key: str):
        """Set Gemini API key."""
        self._config["gemini_api_key"] = key.strip()
        self._save_config()

    def get_openai_api_key(self) -> str:
        """Get OpenAI API key."""
        return self._config.get("openai_api_key", "")

    def set_openai_api_key(self, key: str):
        """Set OpenAI API key."""
        self._config["openai_api_key"] = key.strip()
        self._save_config()

    def get_preferred_ai_provider(self) -> str:
        """Get preferred AI provider."""
        return self._config.get("preferred_ai_provider", "gemini")

    def set_preferred_ai_provider(self, provider: str):
        """Set preferred AI provider."""
        if provider in ["gemini", "openai"]:
            self._config["preferred_ai_provider"] = provider
            self._save_config()

    def has_valid_api_key(self) -> bool:
        """Check if we have a valid API key for the preferred provider."""
        provider = self.get_preferred_ai_provider()
        if provider == "gemini":
            return len(self.get_gemini_api_key()) > 0
        elif provider == "openai":
            return len(self.get_openai_api_key()) > 0
        return False

    # General Settings
    def is_ai_analysis_enabled(self) -> bool:
        """Check if AI analysis is enabled."""
        return self._config.get("enable_ai_analysis", True)

    def set_ai_analysis_enabled(self, enabled: bool):
        """Enable or disable AI analysis."""
        self._config["enable_ai_analysis"] = enabled
        self._save_config()

    def is_debug_mode(self) -> bool:
        """Check if debug mode is enabled."""
        return self._config.get("debug_mode", True)

    # Cache Management
    def get_cached_analysis(self, path: str) -> Optional[Dict[str, Any]]:
        """Get cached AI analysis for a path."""
        if not self._config.get("cache_ai_results", True):
            return None
        return self._cache.get(path)

    def cache_analysis(self, path: str, result: Dict[str, Any]):
        """Cache AI analysis result for a path."""
        if self._config.get("cache_ai_results", True):
            self._cache[path] = result
            self._save_cache()

    def clear_cache(self):
        """Clear all cached AI analysis results."""
        self._cache = {}
        self._save_cache()

    def get_cache_size(self) -> int:
        """Get number of cached analysis results."""
        return len(self._cache)


# Global configuration manager instance
config_manager = ConfigManager()
