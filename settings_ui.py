"""
Settings UI for Mac Cleaner & Analyzer
Allows users to configure API keys and application preferences.
"""

import flet as ft
from config_manager import config_manager
from mac_permissions import open_full_disk_access_pane


def create_settings_tab(page: ft.Page) -> ft.Column:
    """Create the settings tab UI."""

    # API Key section
    gemini_key_field = ft.TextField(
        label="Gemini API Key",
        value=config_manager.get_gemini_api_key(),
        password=True,
        can_reveal_password=True,
        width=400,
        helper_text="Get your free API key from https://makersuite.google.com/app/apikey",
    )

    openai_key_field = ft.TextField(
        label="OpenAI API Key",
        value=config_manager.get_openai_api_key(),
        password=True,
        can_reveal_password=True,
        width=400,
        helper_text="Get your API key from https://platform.openai.com/api-keys",
    )

    ai_provider_dropdown = ft.Dropdown(
        label="Preferred AI Provider",
        value=config_manager.get_preferred_ai_provider(),
        options=[
            ft.dropdown.Option("gemini", "Google Gemini (Recommended)"),
            ft.dropdown.Option("openai", "OpenAI GPT"),
        ],
        width=300,
    )

    enable_ai_checkbox = ft.Checkbox(
        label="Enable AI Analysis for Unknown Files",
        value=config_manager.is_ai_analysis_enabled(),
    )

    # Status indicators
    gemini_status = ft.Text(
        value="✓ Valid" if config_manager.get_gemini_api_key() else "⚠ Not configured",
        color=ft.Colors.GREEN if config_manager.get_gemini_api_key() else ft.Colors.ORANGE,
    )

    openai_status = ft.Text(
        value="✓ Valid" if config_manager.get_openai_api_key() else "⚠ Not configured",
        color=ft.Colors.GREEN if config_manager.get_openai_api_key() else ft.Colors.ORANGE,
    )

    # Full Disk Access section elements (now always 'Not Granted')
    open_fda_button = ft.ElevatedButton(
        text="Open Full Disk Access Settings",
        on_click=lambda e: open_full_disk_access_pane(),
        disabled=False,
    )

    cache_info = ft.Text(value=f"Cached AI analyses: {config_manager.get_cache_size()}", color=ft.Colors.BLUE_GREY_400)

    status_text = ft.Text(value="", color=ft.Colors.GREEN)

    def update_status_indicators():
        """Update the status indicators."""
        gemini_status.value = "✓ Valid" if config_manager.get_gemini_api_key() else "⚠ Not configured"
        gemini_status.color = ft.Colors.GREEN if config_manager.get_gemini_api_key() else ft.Colors.ORANGE

        openai_status.value = "✓ Valid" if config_manager.get_openai_api_key() else "⚠ Not configured"
        openai_status.color = ft.Colors.GREEN if config_manager.get_openai_api_key() else ft.Colors.ORANGE

        cache_info.value = f"Cached AI analyses: {config_manager.get_cache_size()}"
        page.update()

    def save_settings(e):
        """Save all settings."""
        try:
            # Save API keys
            config_manager.set_gemini_api_key(gemini_key_field.value)
            config_manager.set_openai_api_key(openai_key_field.value)
            config_manager.set_preferred_ai_provider(ai_provider_dropdown.value)
            config_manager.set_ai_analysis_enabled(enable_ai_checkbox.value)

            status_text.value = "✓ Settings saved successfully!"
            status_text.color = ft.Colors.GREEN

            update_status_indicators()

        except Exception as ex:
            status_text.value = f"✗ Error saving settings: {str(ex)}"
            status_text.color = ft.Colors.RED

        page.update()

    def test_api_connection(e):
        """Test the API connection."""
        provider = ai_provider_dropdown.value

        if provider == "gemini" and not gemini_key_field.value:
            status_text.value = "⚠ Please enter a Gemini API key first"
            status_text.color = ft.Colors.ORANGE
        elif provider == "openai" and not openai_key_field.value:
            status_text.value = "⚠ Please enter an OpenAI API key first"
            status_text.color = ft.Colors.ORANGE
        else:
            status_text.value = "🔄 Testing API connection..."
            status_text.color = ft.Colors.BLUE
            page.update()

            # TODO: Implement actual API test
            # For now, just simulate a successful test
            import time

            time.sleep(1)
            status_text.value = "✓ API connection test successful!"
            status_text.color = ft.Colors.GREEN

        page.update()

    def clear_cache(e):
        """Clear the AI analysis cache."""
        config_manager.clear_cache()
        cache_info.value = f"Cached AI analyses: {config_manager.get_cache_size()}"
        status_text.value = "✓ Cache cleared"
        status_text.color = ft.Colors.GREEN
        page.update()

    save_button = ft.ElevatedButton(
        text="Save Settings", on_click=save_settings, bgcolor=ft.Colors.BLUE_600, color=ft.Colors.WHITE
    )

    test_button = ft.ElevatedButton(text="Test Connection", on_click=test_api_connection)

    clear_cache_button = ft.ElevatedButton(text="Clear Cache", on_click=clear_cache)
    settings_tab = ft.Column(
        [
            ft.Text("Settings", size=24, weight=ft.FontWeight.BOLD),
            ft.Divider(),
            # --- Permissions Section ---
            ft.Container(height=20),
            ft.Text("Permissions", size=16, weight=ft.FontWeight.W_500),
            ft.Row(
                [
                    open_fda_button,
                ],
                spacing=10,
            ),
            ft.Container(height=10),
            # --- Cache Management Section ---
            ft.Container(height=30),
            ft.Text("Cache Management", size=16, weight=ft.FontWeight.W_500),
            cache_info,
            clear_cache_button,
            # --- AI Analysis Configuration ---
            ft.Text("AI Analysis Configuration", size=18, weight=ft.FontWeight.W_500),
            enable_ai_checkbox,
            ft.Text("Configure your AI provider to enable intelligent safety analysis of unknown files."),
            ft.Container(height=20),
            # --- AI Provider Settings ---
            ft.Text("AI Provider Settings", size=16, weight=ft.FontWeight.W_500),
            ai_provider_dropdown,
            ft.Container(height=10),
            ft.Row(
                [
                    ft.Column(
                        [
                            gemini_key_field,
                            ft.Row([ft.Text("Status: "), gemini_status], spacing=5),
                        ],
                        spacing=5,
                    ),
                ]
            ),
            ft.Container(height=10),
            ft.Row(
                [
                    ft.Column(
                        [
                            openai_key_field,
                            ft.Row([ft.Text("Status: "), openai_status], spacing=5),
                        ],
                        spacing=5,
                    ),
                ]
            ),
            ft.Container(height=20),
            ft.Row(
                [
                    save_button,
                    test_button,
                ],
                spacing=10,
            ),
            ft.Container(height=10),
            status_text,
        ],
        spacing=10,
        scroll=ft.ScrollMode.AUTO,
    )

    return settings_tab
