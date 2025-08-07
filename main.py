"""
Mac Cleaner & Analyzer - Main Application
A multi-functional macOS utility for cleaning junk files and analyzing disk usage.
"""

import flet as ft
import time
import random
import os
import math
import threading
import shutil
from concurrent.futures import ThreadPoolExecutor

# Import our custom modules
from config import debug_log
from safety_analysis import get_safety_info, get_safety_color, ai_analyze_path
from deletion import create_deletion_manager
from config_manager import config_manager
from config_manager import config_manager


def main(page: ft.Page):
    page.title = "Mac Cleaner & Analyzer"
    page.window_width = 600
    page.window_height = 700
    page.window_resizable = True

    page.appbar = ft.AppBar(
        title=ft.Text("Mac Cleaner & Analyzer"),
        center_title=True,
    )

    # --- Common Utility Functions --- #
    def format_size(size_bytes):
        if size_bytes == 0:
            return "0B"
        size_name = ("B", "KB", "MB", "GB", "TB")
        i = int(math.floor(math.log(size_bytes, 1024)))
        p = math.pow(1024, i)
        s = round(size_bytes / p, 2)
        return f"{s} {size_name[i]}"

    # --- Quick Clean Tab --- #
    user_cache_checkbox = ft.Checkbox(label="User Cache", value=True)
    system_logs_checkbox = ft.Checkbox(label="System Logs", value=True)
    trash_checkbox = ft.Checkbox(label="Trash", value=True)
    ios_backups_checkbox = ft.Checkbox(label="iOS Backups", value=False)

    analyze_button = ft.ElevatedButton(text="Analyze")
    clean_button = ft.ElevatedButton(text="Clean", disabled=True)
    analysis_results_text = ft.Text("Analysis results will be shown here.")
    quick_clean_file_list = ft.ListView(height=200, spacing=5, auto_scroll=True)

    def analyze_files(e):
        analysis_results_text.value = "Analyzing..."
        quick_clean_file_list.controls.clear()
        page.update()
        time.sleep(1)  # Simulate analysis time

        total_size = 0
        files_to_delete = []

        if user_cache_checkbox.value:
            size = random.randint(100, 1000)
            total_size += size
            files_to_delete.append(f"~/Library/Caches/some_app/cache.db ({size} MB)")
        if system_logs_checkbox.value:
            size = random.randint(50, 500)
            total_size += size
            files_to_delete.append(f"/private/var/log/system.log ({size} MB)")
        if trash_checkbox.value:
            size = random.randint(0, 2000)
            total_size += size
            if size > 0:
                files_to_delete.append(f"~/.Trash/some_file ({size} MB)")
        if ios_backups_checkbox.value:
            size = random.randint(0, 10000)
            total_size += size
            if size > 0:
                files_to_delete.append(
                    f"~/Library/Application Support/MobileSync/Backup/some_backup ({size} MB)"
                )

        analysis_results_text.value = f"Found {total_size} MB of junk files."
        for file_path in files_to_delete:
            quick_clean_file_list.controls.append(ft.Text(file_path))

        clean_button.disabled = False
        page.update()

    def clean_files(e):
        analysis_results_text.value = "Cleaning..."
        quick_clean_file_list.controls.clear()
        page.update()
        time.sleep(1)

        analysis_results_text.value = "Cleaning complete!"
        clean_button.disabled = True
        page.update()

    analyze_button.on_click = analyze_files
    clean_button.on_click = clean_files

    quick_clean_tab = ft.Column(
        controls=[
            user_cache_checkbox,
            system_logs_checkbox,
            trash_checkbox,
            ios_backups_checkbox,
            ft.Row(
                controls=[analyze_button, clean_button],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            analysis_results_text,
            ft.Container(
                content=quick_clean_file_list,
                border=ft.border.all(1, "#1F000000"),
                border_radius=5,
                padding=10,
                height=250,
            ),
        ],
        spacing=10,
        alignment=ft.MainAxisAlignment.START,
    )

    # --- Disk Analyzer Tab --- #
    scan_status_text = ft.Text("")
    scan_progress_bar = ft.ProgressBar(width=400, value=0)
    scan_results_list = ft.ListView(expand=True, spacing=5, auto_scroll=True)
    breadcrumb_row = ft.Row([], spacing=5)

    scan_thread_state = {"cancelled": False, "current_path": os.path.expanduser("~")}

    def get_size_threaded(path_info):
        path = path_info["path"]
        if scan_thread_state["cancelled"]:
            return None

        total_size = 0
        try:
            if path_info["is_dir"]:
                for dirpath, _, filenames in os.walk(path):
                    if scan_thread_state["cancelled"]:
                        return None
                    for f in filenames:
                        fp = os.path.join(dirpath, f)
                        if not os.path.islink(fp):
                            try:
                                total_size += os.path.getsize(fp)
                            except OSError:
                                pass
            else:
                total_size = os.path.getsize(path)
        except OSError:
            return {
                "path": path,
                "size": 0,
                "is_dir": path_info["is_dir"],
            }  # Return 0 if not accessible
        return {"path": path, "size": total_size, "is_dir": path_info["is_dir"]}

    def scan_directory_thread(selected_path):
        scan_thread_state["cancelled"] = False
        scan_thread_state["current_path"] = selected_path

        try:
            entries = [
                {"path": entry.path, "is_dir": entry.is_dir(follow_symlinks=False)}
                for entry in os.scandir(selected_path)
            ]
        except OSError as e:
            scan_status_text.value = f"Error: {e.strerror}"
            page.update()
            reset_scan_ui()
            return

        results = []
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(get_size_threaded, entry) for entry in entries]
            for i, future in enumerate(futures):
                if scan_thread_state["cancelled"]:
                    executor.shutdown(wait=False, cancel_futures=True)
                    break

                result = future.result()
                if result:
                    results.append(result)

                progress = (i + 1) / len(entries)
                scan_progress_bar.value = progress
                page.update()

        if not scan_thread_state["cancelled"]:
            results.sort(key=lambda x: x["size"], reverse=True)
            display_scan_results(results, selected_path)

        reset_scan_ui()

    def check_delete_button_state():
        """Check if delete button should be enabled based on selections."""
        debug_log("=== CHECKING DELETE BUTTON STATE ===")
        
        has_selection = False
        has_unsafe = False

        for i, control in enumerate(scan_results_list.controls):
            if hasattr(control, "trailing") and hasattr(control.trailing, "controls"):
                trailing_controls = control.trailing.controls
                if len(trailing_controls) > 0 and isinstance(trailing_controls[0], ft.Checkbox):
                    checkbox = trailing_controls[0]
                    if checkbox.value and hasattr(control, "data"):
                        has_selection = True
                        path = control.data
                        safety_info = get_safety_info(path)
                        debug_log(f"  Control {i}: selected, path={path}, safety={safety_info['safety']}")
                        if safety_info["safety"] == "red":
                            has_unsafe = True
                            break

        button_should_be_enabled = has_selection and not has_unsafe
        debug_log(f"Button state: has_selection={has_selection}, has_unsafe={has_unsafe}, enabled={button_should_be_enabled}")
        
        delete_button.disabled = not button_should_be_enabled
        page.update()
        
        debug_log(f"Delete button disabled state is now: {delete_button.disabled}")

    # Forward declaration of scan_and_display function
    def scan_and_display(path):
        scan_button.disabled = True
        cancel_button.disabled = False
        directory_dropdown.disabled = True
        scan_status_text.value = f"Scanning {path}..."
        scan_results_list.controls.clear()
        page.update()
        
        threading.Thread(
            target=scan_directory_thread, args=(path,), daemon=True
        ).start()

    # Create deletion manager with proper closure
    delete_selected_handler, delete_selected_items = create_deletion_manager(
        page, scan_results_list, scan_thread_state, scan_and_display
    )

    # Confirmation UI elements (hidden by default)
    confirmation_row = ft.Row(
        controls=[
            ft.Text("", expand=True),  # Confirmation message
            ft.ElevatedButton(
                text="Yes, Delete",
                bgcolor=ft.Colors.RED_600,
                color=ft.Colors.WHITE,
                on_click=None,  # Will be set dynamically
            ),
            ft.ElevatedButton(
                text="Cancel",
                on_click=None,  # Will be set dynamically
            ),
        ],
        visible=False,  # Hidden by default
        alignment=ft.MainAxisAlignment.CENTER,
        spacing=10,
    )

    def show_confirmation_ui(selected_items):
        """Show inline confirmation UI instead of modal dialog."""
        debug_log(f"Showing confirmation UI for {len(selected_items)} items")
        
        # Update confirmation message
        if len(selected_items) == 1:
            message = f"Delete '{os.path.basename(selected_items[0]['path'])}'?"
        else:
            message = f"Delete {len(selected_items)} selected items?"
        
        confirmation_row.controls[0].value = message
        
        # Set up Yes button
        def confirm_deletion(e):
            debug_log("User confirmed deletion")
            confirmation_row.visible = False
            delete_button.visible = True
            page.update()
            
            # Perform the actual deletion
            perform_deletion(selected_items)
        
        # Set up Cancel button  
        def cancel_deletion(e):
            debug_log("User cancelled deletion")
            confirmation_row.visible = False
            delete_button.visible = True
            page.update()
        
        confirmation_row.controls[1].on_click = confirm_deletion
        confirmation_row.controls[2].on_click = cancel_deletion
        
        # Show confirmation UI and hide delete button
        confirmation_row.visible = True
        delete_button.visible = False
        page.update()

    def perform_deletion(selected_items):
        """Actually delete the selected files and show results."""
        debug_log(f"Performing deletion of {len(selected_items)} items")
        
        deletion_results = []
        for item in selected_items:
            try:
                path = item['path']
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)
                deletion_results.append(f"✓ Deleted: {os.path.basename(path)}")
                debug_log(f"Successfully deleted: {path}")
            except Exception as ex:
                error_msg = f"✗ Failed to delete {os.path.basename(item['path'])}: {str(ex)}"
                deletion_results.append(error_msg)
                debug_log(f"Failed to delete {item['path']}: {ex}")
        
        # Show results in scan status
        scan_status_text.value = f"Deletion complete. {'\n'.join(deletion_results[:3])}"
        if len(deletion_results) > 3:
            scan_status_text.value += f"\n... and {len(deletion_results) - 3} more results"
        
        # Refresh the current directory
        scan_and_display(scan_thread_state["current_path"])

    def simple_delete_selected_handler(e):
        """Handle delete button click with inline confirmation."""
        debug_log("Delete button clicked")
        
        selected_items = []
        unsafe_items = []
        
        # Collect selected items and check safety
        for control in scan_results_list.controls:
            if hasattr(control, 'trailing') and hasattr(control.trailing, 'controls'):
                trailing_controls = control.trailing.controls
                if len(trailing_controls) > 0 and isinstance(trailing_controls[0], ft.Checkbox):
                    checkbox = trailing_controls[0]
                    if checkbox.value and hasattr(control, 'data'):
                        path = control.data
                        safety_info = get_safety_info(path)
                        selected_items.append({"path": path, "safety": safety_info['safety']})
                        
                        if safety_info['safety'] == 'red':
                            unsafe_items.append(path)
        
        if not selected_items:
            scan_status_text.value = "No items selected for deletion."
            page.update()
            return
        
        if unsafe_items:
            unsafe_names = [os.path.basename(p) for p in unsafe_items]
            scan_status_text.value = f"Cannot delete unsafe items (red): {', '.join(unsafe_names)}"
            page.update()
            return
        
        # Show inline confirmation
        show_confirmation_ui(selected_items)

    def display_scan_results(results, current_path):
        scan_results_list.controls.clear()
        update_breadcrumbs(current_path)

        # Add ".." entry to go up
        if current_path != "/":
            parent_dir = os.path.dirname(current_path)
            scan_results_list.controls.append(
                ft.ListTile(
                    title=ft.Text(".."),
                    leading=ft.Icon(ft.Icons.ARROW_UPWARD),
                    on_click=lambda _, p=parent_dir: scan_and_display(p),
                )
            )

        for item in results:
            is_dir = item["is_dir"]
            icon = ft.Icons.FOLDER if is_dir else ft.Icons.INSERT_DRIVE_FILE

            # Get safety information for this path
            safety_info = get_safety_info(item["path"])
            safety_color = get_safety_color(safety_info["safety"])

            def create_ai_analyze_handler(path):
                def handler(e):
                    # Show loading state
                    e.control.icon = ft.Icons.HOURGLASS_EMPTY
                    e.control.tooltip = "Analyzing..."
                    page.update()

                    # Perform AI analysis in a separate thread
                    def analyze():
                        result = ai_analyze_path(path)

                        # Update the UI on the main thread
                        def update_ui():
                            # Find and update the safety dot and AI icon
                            for control in scan_results_list.controls:
                                if hasattr(control, "data") and control.data == path:
                                    # Update safety dot color
                                    if len(control.leading.controls) > 0:
                                        control.leading.controls[0].bgcolor = (
                                            get_safety_color(result["safety"])
                                        )
                                    # Update AI icon
                                    if len(control.trailing.controls) > 1:
                                        ai_icon = control.trailing.controls[1]
                                        ai_icon.icon = ft.Icons.PSYCHOLOGY
                                        ai_icon.tooltip = result["reason"]
                                    page.update()

                        # Call update_ui directly - Flet handles thread safety
                        update_ui()

                    threading.Thread(target=analyze, daemon=True).start()

                return handler

            # Create safety dot
            safety_dot = ft.Container(
                width=12,
                height=12,
                bgcolor=safety_color,
                border_radius=6,
                tooltip=safety_info["reason"],
            )

            # Create AI analysis icon (only show for grey/unknown items)
            ai_icon = None
            if safety_info["safety"] == "grey":
                ai_icon = ft.IconButton(
                    icon=ft.Icons.PSYCHOLOGY_OUTLINED,
                    tooltip="Click for AI analysis",
                    icon_size=16,
                    on_click=create_ai_analyze_handler(item["path"]),
                )
            else:
                # Placeholder to maintain alignment
                ai_icon = ft.Container(width=32, height=32)

            # Create checkbox for selection
            def create_checkbox_handler():
                def handler(e):
                    debug_log(f"Checkbox clicked for path: {item['path'] if 'path' in item else 'unknown'}")
                    debug_log(f"Checkbox new value: {e.control.value if hasattr(e, 'control') else 'unknown'}")
                    check_delete_button_state()

                return handler

            checkbox = ft.Checkbox(value=False, on_change=create_checkbox_handler())
            debug_log(f"Created checkbox for {item['path']}")

            leading_row = ft.Row(controls=[safety_dot, ft.Icon(icon)], tight=True, spacing=8)

            trailing_row = ft.Row(controls=[checkbox, ai_icon], tight=True, spacing=4)

            # Create proper click handler with closure
            def create_directory_click_handler(path, is_directory):
                if is_directory:
                    return lambda _: scan_and_display(path)
                else:
                    return None

            list_tile = ft.ListTile(
                title=ft.Text(os.path.basename(item["path"])),
                subtitle=ft.Text(format_size(item["size"])),
                leading=leading_row,
                trailing=trailing_row,
                on_click=create_directory_click_handler(item["path"], is_dir),
                data=item["path"],  # Store path for reference
            )

            scan_results_list.controls.append(list_tile)

        scan_status_text.value = (
            f"Scan of {current_path} complete. Found {len(results)} items."
        )
        page.update()

    def update_breadcrumbs(path):
        breadcrumb_row.controls.clear()
        parts = path.split(os.sep)
        if path == "/":
            parts = [""]

        for i, part in enumerate(parts):
            if i == 0 and part == "":
                current_path_str = "/"
                display_part = "/"
            else:
                current_path_str = os.path.join(*parts[: i + 1])
                display_part = part

            breadcrumb_row.controls.append(
                ft.Container(
                    content=ft.Text(display_part),
                    on_click=lambda e, p=current_path_str: scan_and_display(p),
                    padding=ft.padding.symmetric(horizontal=5, vertical=2),
                    border_radius=5,
                    ink=True,
                )
            )
            if i < len(parts) - 1:
                breadcrumb_row.controls.append(ft.Text("/"))
        page.update()

    def reset_scan_ui():
        scan_button.disabled = False
        cancel_button.disabled = True
        directory_dropdown.disabled = False
        if scan_thread_state["cancelled"]:
            scan_status_text.value = "Scan cancelled."
        scan_progress_bar.value = 0
        page.update()

    def scan_directory_handler(e):
        scan_and_display(directory_dropdown.value)

    def cancel_scan_handler(e):
        scan_thread_state["cancelled"] = True
        scan_status_text.value = "Cancelling..."
        page.update()

    directory_dropdown = ft.Dropdown(
        value=os.path.expanduser("~"),
        options=[
            ft.dropdown.Option("/"),
            ft.dropdown.Option(os.path.expanduser("~")),
            ft.dropdown.Option(os.path.expanduser("~/Downloads")),
            ft.dropdown.Option(os.path.expanduser("~/Documents")),
        ],
        width=350,
    )

    scan_button = ft.ElevatedButton(text="Scan", on_click=scan_directory_handler)
    cancel_button = ft.ElevatedButton(text="Cancel", on_click=cancel_scan_handler, disabled=True)
    
    debug_log("Creating delete button with simple handler")
    delete_button = ft.ElevatedButton(
        text="Delete Selected",
        on_click=simple_delete_selected_handler,
        disabled=True,
        bgcolor=ft.Colors.RED_400,
        color=ft.Colors.WHITE,
    )
    debug_log(f"Delete button created: {delete_button}")
    debug_log(f"Delete button on_click handler: {delete_button.on_click}")

    disk_analyzer_tab = ft.Column(
        [
            ft.Row(
                [
                    directory_dropdown,
                    scan_button,
                    cancel_button,
                ],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            ft.Row([breadcrumb_row], alignment=ft.MainAxisAlignment.START),
            ft.Row([scan_progress_bar], alignment=ft.MainAxisAlignment.CENTER),
            ft.Row([scan_status_text], alignment=ft.MainAxisAlignment.CENTER),
            ft.Container(
                content=scan_results_list,
                border=ft.border.all(1, "#1F000000"),
                border_radius=5,
                padding=10,
                expand=True,
            ),
            confirmation_row,  # Add confirmation UI
            ft.Row(
                [delete_button],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
        ],
        spacing=10,
        alignment=ft.MainAxisAlignment.START,
        expand=True,
    )

    # --- Settings Tab --- #
    
    # API Key input fields
    gemini_api_key_field = ft.TextField(
        label="Gemini API Key",
        password=True,
        value=config_manager.get_gemini_api_key() or "",
        width=400,
        helper_text="Enter your Google Gemini API key for AI analysis"
    )
    
    openai_api_key_field = ft.TextField(
        label="OpenAI API Key",
        password=True,
        value=config_manager.get_openai_api_key() or "",
        width=400,
        helper_text="Enter your OpenAI API key for AI analysis"
    )
    
    # AI Provider selection
    ai_provider_dropdown = ft.Dropdown(
        label="AI Provider",
        options=[
            ft.dropdown.Option("gemini", "Google Gemini"),
            ft.dropdown.Option("openai", "OpenAI GPT"),
        ],
        value=config_manager.get_preferred_ai_provider(),
        width=200
    )
    
    # AI enabled checkbox
    ai_enabled_checkbox = ft.Checkbox(
        label="Enable AI Analysis",
        value=config_manager.is_ai_analysis_enabled(),
    )
    
    # Status text for settings
    settings_status_text = ft.Text("Configure your API keys to enable AI-powered safety analysis.")
    
    def save_settings(e):
        """Save settings to config file."""
        debug_log("Saving settings...")
        
        # Save API keys
        gemini_key = gemini_api_key_field.value.strip()
        openai_key = openai_api_key_field.value.strip()
        
        if gemini_key:
            config_manager.set_gemini_api_key(gemini_key)
        if openai_key:
            config_manager.set_openai_api_key(openai_key)
        
        # Save other settings
        config_manager.set_preferred_ai_provider(ai_provider_dropdown.value)
        config_manager.set_ai_analysis_enabled(ai_enabled_checkbox.value)
        
        settings_status_text.value = "✓ Settings saved successfully!"
        settings_status_text.color = ft.Colors.GREEN
        page.update()
        
        # Clear success message after 3 seconds
        def clear_status():
            time.sleep(3)
            settings_status_text.value = "Configure your API keys to enable AI-powered safety analysis."
            settings_status_text.color = None
            page.update()
        
        threading.Thread(target=clear_status, daemon=True).start()
    
    def test_api_key(provider):
        """Test API key functionality."""
        def test():
            settings_status_text.value = f"Testing {provider} API key..."
            settings_status_text.color = ft.Colors.BLUE
            page.update()
            
            try:
                # Test with a simple analysis
                result = ai_analyze_path("/tmp/test", force_provider=provider)
                if result and "error" not in result.get("reason", "").lower():
                    settings_status_text.value = f"✓ {provider} API key is working!"
                    settings_status_text.color = ft.Colors.GREEN
                else:
                    settings_status_text.value = f"✗ {provider} API key test failed."
                    settings_status_text.color = ft.Colors.RED
            except Exception as ex:
                settings_status_text.value = f"✗ {provider} API test error: {str(ex)}"
                settings_status_text.color = ft.Colors.RED
            
            page.update()
        
        threading.Thread(target=test, daemon=True).start()
    
    save_settings_button = ft.ElevatedButton(
        text="Save Settings",
        on_click=save_settings,
        bgcolor=ft.Colors.BLUE_400,
        color=ft.Colors.WHITE
    )
    
    test_gemini_button = ft.ElevatedButton(
        text="Test Gemini",
        on_click=lambda e: test_api_key("gemini"),
        bgcolor=ft.Colors.GREEN_400,
        color=ft.Colors.WHITE
    )
    
    test_openai_button = ft.ElevatedButton(
        text="Test OpenAI", 
        on_click=lambda e: test_api_key("openai"),
        bgcolor=ft.Colors.GREEN_400,
        color=ft.Colors.WHITE
    )
    
    settings_tab = ft.Column(
        controls=[
            ft.Text("AI Analysis Settings", size=24, weight=ft.FontWeight.BOLD),
            ft.Divider(),
            
            ft.Text("API Configuration", size=18, weight=ft.FontWeight.W_500),
            ai_enabled_checkbox,
            ai_provider_dropdown,
            
            ft.Container(height=20),  # Spacing
            
            ft.Text("API Keys", size=18, weight=ft.FontWeight.W_500),
            ft.Text("Get your API keys from:", size=14),
            ft.Text("• Gemini: https://makersuite.google.com/app/apikey", size=12),
            ft.Text("• OpenAI: https://platform.openai.com/api-keys", size=12),
            
            ft.Container(height=10),  # Spacing
            
            gemini_api_key_field,
            ft.Row([test_gemini_button], alignment=ft.MainAxisAlignment.START),
            
            ft.Container(height=10),  # Spacing
            
            openai_api_key_field,
            ft.Row([test_openai_button], alignment=ft.MainAxisAlignment.START),
            
            ft.Container(height=20),  # Spacing
            
            ft.Row([save_settings_button], alignment=ft.MainAxisAlignment.CENTER),
            settings_status_text,
            
            ft.Container(height=20),  # Spacing
            
            ft.Text("How it works:", size=16, weight=ft.FontWeight.W_500),
            ft.Text("• Files are first checked against a comprehensive built-in database", size=12),
            ft.Text("• Unknown files are analyzed using AI to determine safety level", size=12),
            ft.Text("• Results are cached locally to avoid repeated API calls", size=12),
            ft.Text("• AI analysis helps identify safe-to-delete files you might not know about", size=12),
        ],
        spacing=10,
        alignment=ft.MainAxisAlignment.START,
        scroll=ft.ScrollMode.AUTO,
    )

    # --- Settings Tab --- #
    
    # API Key input fields
    gemini_key_field = ft.TextField(
        label="Gemini API Key",
        password=True,
        value=config_manager.get_gemini_api_key(),
        width=400,
        hint_text="Enter your Google Gemini API key"
    )
    
    openai_key_field = ft.TextField(
        label="OpenAI API Key", 
        password=True,
        value=config_manager.get_openai_api_key(),
        width=400,
        hint_text="Enter your OpenAI API key"
    )
    
    # AI Provider selection
    ai_provider_dropdown = ft.Dropdown(
        label="Preferred AI Provider",
        width=200,
        value=config_manager.get_preferred_ai_provider(),
        options=[
            ft.dropdown.Option("gemini", "Google Gemini"),
            ft.dropdown.Option("openai", "OpenAI GPT"),
        ],
    )
    
    # AI Analysis toggle
    ai_analysis_switch = ft.Switch(
        label="Enable AI Analysis",
        value=config_manager.is_ai_analysis_enabled(),
    )
    
    # Status messages for settings
    settings_status = ft.Text("", color=ft.Colors.GREEN)
    
    def save_settings(e):
        """Save all settings to configuration."""
        try:
            # Save API keys
            config_manager.set_gemini_api_key(gemini_key_field.value or "")
            config_manager.set_openai_api_key(openai_key_field.value or "")
            
            # Save provider preference
            config_manager.set_preferred_ai_provider(ai_provider_dropdown.value)
            
            # Save AI analysis setting
            config_manager.set_ai_analysis_enabled(ai_analysis_switch.value)
            
            # Update status
            settings_status.value = "✓ Settings saved successfully!"
            settings_status.color = ft.Colors.GREEN
            
            debug_log("Settings saved successfully")
            
        except Exception as ex:
            settings_status.value = f"✗ Error saving settings: {str(ex)}"
            settings_status.color = ft.Colors.RED
            debug_log(f"Error saving settings: {ex}")
        
        page.update()
    
    def test_ai_connection(e):
        """Test the AI connection with current settings."""
        settings_status.value = "Testing AI connection..."
        settings_status.color = ft.Colors.BLUE
        page.update()
        
        try:
            # Save current settings first
            save_settings(None)
            
            # Test with a simple path
            test_path = "/tmp/test_file.txt"
            result = ai_analyze_path(test_path)
            
            if result and "reason" in result:
                settings_status.value = "✓ AI connection successful!"
                settings_status.color = ft.Colors.GREEN
                debug_log("AI connection test successful")
            else:
                settings_status.value = "✗ AI connection failed - check your API key"
                settings_status.color = ft.Colors.RED
                debug_log("AI connection test failed")
                
        except Exception as ex:
            settings_status.value = f"✗ AI connection error: {str(ex)}"
            settings_status.color = ft.Colors.RED
            debug_log(f"AI connection test error: {ex}")
        
        page.update()
    
    def clear_ai_cache(e):
        """Clear the AI analysis cache."""
        try:
            cache_size = config_manager.get_cache_size()
            config_manager.clear_cache()
            settings_status.value = f"✓ Cleared {cache_size} cached AI analysis results"
            settings_status.color = ft.Colors.GREEN
            debug_log(f"Cleared AI cache ({cache_size} items)")
        except Exception as ex:
            settings_status.value = f"✗ Error clearing cache: {str(ex)}"
            settings_status.color = ft.Colors.RED
            debug_log(f"Error clearing cache: {ex}")
        
        page.update()
    
    # Settings buttons
    save_button = ft.ElevatedButton(
        text="Save Settings",
        on_click=save_settings,
        bgcolor=ft.Colors.BLUE_400,
        color=ft.Colors.WHITE
    )
    
    test_button = ft.ElevatedButton(
        text="Test AI Connection",
        on_click=test_ai_connection
    )
    
    clear_cache_button = ft.ElevatedButton(
        text="Clear AI Cache",
        on_click=clear_ai_cache
    )
    
    # Information text
    api_info_text = ft.Text(
        "API Keys are stored locally in user_config.json and are not shared.\n\n" +
        "• Gemini: Get your API key from https://makersuite.google.com/app/apikey\n" +
        "• OpenAI: Get your API key from https://platform.openai.com/api-keys\n\n" +
        "AI analysis is used for unknown file types not in our safety database.",
        size=12,
        color=ft.Colors.GREY_700
    )
    
    settings_tab = ft.Column(
        controls=[
            ft.Text("AI Configuration", size=18, weight=ft.FontWeight.BOLD),
            ft.Divider(),
            
            # API Keys section
            ft.Text("API Keys", size=14, weight=ft.FontWeight.BOLD),
            gemini_key_field,
            openai_key_field,
            
            ft.Divider(),
            
            # Settings section
            ft.Text("Preferences", size=14, weight=ft.FontWeight.BOLD),
            ai_provider_dropdown,
            ai_analysis_switch,
            
            ft.Divider(),
            
            # Action buttons
            ft.Row(
                controls=[save_button, test_button, clear_cache_button],
                alignment=ft.MainAxisAlignment.START,
                spacing=10
            ),
            
            # Status and info
            settings_status,
            ft.Divider(),
            api_info_text,
        ],
        spacing=10,
        scroll=ft.ScrollMode.AUTO,
        alignment=ft.MainAxisAlignment.START,
    )

    # --- Main Layout --- #
    tabs = ft.Tabs(
        selected_index=0,
        animation_duration=300,
        tabs=[
            ft.Tab(text="Quick Clean", content=quick_clean_tab),
            ft.Tab(text="Disk Analyzer", content=disk_analyzer_tab),
            ft.Tab(text="Settings", content=settings_tab),
        ],
        expand=True,
    )

    page.add(tabs)


if __name__ == "__main__":
    ft.app(target=main)
