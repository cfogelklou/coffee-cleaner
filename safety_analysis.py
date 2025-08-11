import os
import fnmatch
import json
import flet as ft
from config import PREDEFINED_RULES, debug_log
from config_manager import config_manager

"""Safety Analysis for Mac Cleaner & Analyzer.
Provides safety level assessment for files and directories using predefined rules and AI analysis.
"""

# Optional AI imports
try:
    import google.generativeai as genai

    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    debug_log("Google Generative AI not available. Install with: pip install google-generativeai")

try:
    import openai

    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    debug_log("OpenAI not available. Install with: pip install openai")


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
    cached_result = config_manager.get_cached_analysis(normalized_path)
    if cached_result:
        debug_log(f"Using cached analysis for {path}")
        return cached_result

    # Check against predefined rules
    for pattern, info in PREDEFINED_RULES.items():
        pattern_normalized = normalize_path(pattern)
        if fnmatch.fnmatch(normalized_path, pattern_normalized):
            debug_log(f"Matched predefined rule for {path}: {info['safety']}")
            return info

    # If no rule matches, return grey (unknown) to trigger AI analysis later
    debug_log(f"No predefined rule found for {path}, marking as unknown")
    return {"safety": "grey", "reason": "Safety level unknown. Click AI icon for analysis."}


def ai_analyze_path(path, force_provider=None):
    """
    Use AI to analyze unknown paths for safety assessment.
    Returns a dict with 'safety' (green/orange/red) and 'reason'.

    Args:
        path: The file/directory path to analyze
        force_provider: Force use of specific AI provider ("gemini" or "openai")
    """
    normalized_path = normalize_path(path)

    # Check if already cached (unless we're forcing a provider for testing)
    if not force_provider:
        cached_result = config_manager.get_cached_analysis(normalized_path)
        if cached_result:
            debug_log(f"Using cached AI analysis for {path}")
            return cached_result

    # Determine which provider to use
    provider = force_provider or config_manager.get_preferred_ai_provider()

    # Check if AI analysis is enabled and we have API keys
    if not force_provider and not config_manager.is_ai_analysis_enabled():
        debug_log("AI analysis is disabled in settings")
        return _fallback_heuristic_analysis(normalized_path)

    # Get the appropriate API key
    if provider == "gemini":
        api_key = config_manager.get_gemini_api_key()
    elif provider == "openai":
        api_key = config_manager.get_openai_api_key()
    else:
        api_key = None

    if not api_key or not api_key.strip():
        debug_log(f"No valid {provider} API key configured")
        if not force_provider:
            return _fallback_heuristic_analysis(normalized_path)
        else:
            return {"safety": "grey", "reason": f"Error: No valid {provider} API key"}
        return _fallback_heuristic_analysis(normalized_path)

    # Try AI analysis
    try:
        provider = config_manager.get_preferred_ai_provider()
        if provider == "gemini" and GEMINI_AVAILABLE:
            result = _analyze_with_gemini(normalized_path)
        elif provider == "openai" and OPENAI_AVAILABLE:
            result = _analyze_with_openai(normalized_path)
        else:
            debug_log(f"AI provider {provider} not available, using fallback")
            result = _fallback_heuristic_analysis(normalized_path)

        # Cache the result
        config_manager.cache_analysis(normalized_path, result)
        return result

    except Exception as e:
        debug_log(f"AI analysis failed for {path}: {e}")
        return _fallback_heuristic_analysis(normalized_path)


def _fallback_heuristic_analysis(path):
    """
    Fallback heuristic analysis when AI is not available.
    Uses simple rules based on file names and extensions.
    """
    debug_log(f"Using heuristic analysis for {path}")

    basename = os.path.basename(path).lower()

    # Safe patterns (green)
    safe_patterns = ["cache", "temp", "tmp", "log", ".ds_store", "thumbs.db", ".localized", "desktop.ini", "icon\r"]
    if any(pattern in basename for pattern in safe_patterns):
        return {
            "safety": "green",
            "reason": (
                "Heuristic Analysis: Appears to be temporary/cache files. Likely safe to delete. "
                "Add an API Key in Settings for AI analysis"
            ),
        }

    # Safe file extensions
    safe_extensions = [".tmp", ".cache", ".log", ".bak", ".old", ".orig"]
    if any(basename.endswith(ext) for ext in safe_extensions):
        return {
            "safety": "green",
            "reason": (
                "Heuristic Analysis: Temporary file extension. Likely safe to delete. "
                "Add an API Key in Settings for AI analysis"
            ),
        }

    # Caution patterns (orange)
    caution_patterns = ["config", "pref", "setting", "preference", "profile"]
    if any(pattern in basename for pattern in caution_patterns):
        return {
            "safety": "orange",
            "reason": (
                "Heuristic Analysis: Configuration or preference files. Deleting may affect "
                "application behavior. Add an API Key in Settings for AI analysis"
            ),
        }

    # System/dangerous patterns (red)
    danger_patterns = ["system", "kernel", "driver", "boot", "recovery", "firmware"]
    if any(pattern in basename for pattern in danger_patterns):
        return {
            "safety": "red",
            "reason": (
                "Heuristic Analysis: System-related files. Not recommended for deletion. "
                "Add an API Key in Settings for AI analysis"
            ),
        }

    # Default to caution
    return {
        "safety": "orange",
        "reason": (
            "Heuristic Analysis: Unknown file type. Exercise caution when deleting. "
            "Add an API Key in Settings for AI analysis"
        ),
    }


def _analyze_with_gemini(path):
    """Analyze path using Google Gemini API."""
    debug_log(f"Analyzing {path} with Gemini AI")

    if not GEMINI_AVAILABLE:
        raise Exception("Gemini API not available")
    api_key = config_manager.get_gemini_api_key()
    if not api_key:
        raise Exception("No Gemini API key configured")

    # Configure Gemini
    genai.configure(api_key=api_key)

    # Use the model from configuration
    from config import AI_CONFIG

    model_name = AI_CONFIG.get("model", "gemini-1.5-flash")
    model = genai.GenerativeModel(model_name)

    # Create analysis prompt
    prompt = f"""
    Analyze this macOS file/directory path for deletion safety: {path}

    Context: This is a macOS file cleaner application. Users want to know if it's safe to
    delete this item.

    Please respond with ONLY a JSON object in this exact format:
    {{
        "safety": "green|orange|red",
        "reason": "Brief explanation of why it's safe/unsafe to delete"
    }}

    Safety levels:
    - green: Safe to delete (cache, temp files, user files that can be easily replaced)
    - orange: Caution needed (user data, preferences, may affect apps but not critical)
    - red: Do not delete (system files, critical applications, essential data)

    Consider the file path, common macOS directory structures, and typical user needs.
    """

    response = model.generate_content(prompt)

    # Parse the response
    try:
        response_text = response.text.strip()
        debug_log(f"Raw Gemini response: {response_text}")

        # Handle markdown code blocks
        if response_text.startswith("```json"):
            # Extract JSON from markdown code block
            start = response_text.find("```json") + 7
            end = response_text.rfind("```")
            if end > start:
                response_text = response_text[start:end].strip()
        elif response_text.startswith("```"):
            # Handle generic code blocks
            start = response_text.find("```") + 3
            end = response_text.rfind("```")
            if end > start:
                response_text = response_text[start:end].strip()

        result = json.loads(response_text)
        debug_log(f"Parsed Gemini AI analysis for {path}: {result}")

        # Validate the response format
        if not isinstance(result, dict) or "safety" not in result or "reason" not in result:
            raise ValueError("Invalid response format")

        # Add AI prefix to reason
        result["reason"] = f"AI Analysis: {result['reason']}"
        return result

    except (json.JSONDecodeError, ValueError) as e:
        debug_log(f"Failed to parse Gemini response: {response.text}")
        debug_log(f"Parse error: {str(e)}")
        raise Exception("Invalid AI response format")


def _analyze_with_openai(path):
    """Analyze path using OpenAI API."""
    debug_log(f"Analyzing {path} with OpenAI")

    if not OPENAI_AVAILABLE:
        raise Exception("OpenAI API not available")
    api_key = config_manager.get_openai_api_key()
    if not api_key:
        raise Exception("No OpenAI API key configured")

    # Configure OpenAI
    openai.api_key = api_key

    # Create analysis prompt
    prompt = f"""
    Analyze this macOS file/directory path for deletion safety: {path}

    Context: This is a macOS file cleaner application. Users want to know if it's safe to
    delete this item.

    Please respond with ONLY a JSON object in this exact format:
    {{
        "safety": "green|orange|red",
        "reason": "Brief explanation of why it's safe/unsafe to delete"
    }}

    Safety levels:
    - green: Safe to delete (cache, temp files, user files that can be easily replaced)
    - orange: Caution needed (user data, preferences, may affect apps but not critical)
    - red: Do not delete (system files, critical applications, essential data)

    Consider the file path, common macOS directory structures, and typical user needs.
    """

    response = openai.ChatCompletion.create(
        model="gpt-4.1",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=200,
    )

    # Parse the response
    try:
        response_text = response.choices[0].message.content.strip()
        debug_log(f"Raw OpenAI response: {response_text}")

        # Handle markdown code blocks
        if response_text.startswith("```json"):
            # Extract JSON from markdown code block
            start = response_text.find("```json") + 7
            end = response_text.rfind("```")
            if end > start:
                response_text = response_text[start:end].strip()
        elif response_text.startswith("```"):
            # Handle generic code blocks
            start = response_text.find("```") + 3
            end = response_text.rfind("```")
            if end > start:
                response_text = response_text[start:end].strip()

        result = json.loads(response_text)
        debug_log(f"Parsed OpenAI analysis for {path}: {result}")

        # Validate the response format
        if not isinstance(result, dict) or "safety" not in result or "reason" not in result:
            raise ValueError("Invalid response format")

        # Add AI prefix to reason
        result["reason"] = f"AI Analysis: {result['reason']}"
        return result

    except (json.JSONDecodeError, ValueError) as e:
        debug_log(f"Failed to parse OpenAI response: {response.choices[0].message.content}")
        debug_log(f"Parse error: {str(e)}")
        raise Exception("Invalid AI response format")


def get_safety_color(safety_level):
    """Return the appropriate color for the safety level."""
    colors = {
        "green": ft.Colors.GREEN,
        "orange": ft.Colors.ORANGE,
        "red": ft.Colors.RED,
        "grey": ft.Colors.GREY_400,
    }
    return colors.get(safety_level, ft.Colors.GREY_400)
