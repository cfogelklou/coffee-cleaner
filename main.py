"""
CoffeeCleaner - Main Application
A multi-functional macOS utility for cleaning junk files and analyzing disk usage.
"""

import flet as ft
import os
import math
import threading
import logging
import shutil
from concurrent.futures import ThreadPoolExecutor

# Import our custom modules
from config import debug_log
from safety_analysis import get_safety_info, get_safety_color, ai_analyze_path
from deletion import create_deletion_manager
from config_manager import config_manager
from settings_ui import create_settings_tab
from quick_clean import (
    USER_CACHE,
    SYSTEM_LOGS,
    TRASH,
    IOS_BACKUPS,
    MACOS_INSTALLERS,
    XCODE_DERIVED_DATA,
    IOS_SIMULATORS,
    CRASH_REPORTS,
    TEMP_FILES,
    APP_SUPPORT_CACHES,
    format_size as qc_format_size,
)


def main(page: ft.Page):
    page.title = "CoffeeCleaner"
    page.window_width = 600
    page.window_height = 700
    page.window_resizable = True
    
    # Get the absolute path to the icon file
    icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.icns")
    if os.path.exists(icon_path):
        page.window_icon = icon_path
    else:
        debug_log(f"Icon file not found at: {icon_path}")
    
    # Prevent bouncing icon on macOS
    page.window_always_on_top = False
    page.window_skip_task_bar = False
    page.window_focused = True
    page.window_prevent_close = False

    # Set up logging
    log_filename = os.path.join(os.path.expanduser("~"), "Desktop", "mac_cleaner.log")
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.FileHandler(log_filename), logging.StreamHandler()],  # Also log to console
    )
    logger = logging.getLogger(__name__)
    logger.info("CoffeeCleaner started")

    # Status text for file events
    status_text = ft.Text("Ready", size=10, color=ft.Colors.GREY_600)

    def update_status(message):
        """Update the status text and log the message"""
        status_text.value = message
        logger.info(message)
        page.update()

    page.appbar = ft.AppBar(
        title=ft.Text("CoffeeCleaner"),
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
    ios_backups_checkbox = ft.Checkbox(label="iOS Backups", value=True)
    macos_installers_checkbox = ft.Checkbox(label="macOS Installers", value=True)
    xcode_derived_data_checkbox = ft.Checkbox(label="Xcode Derived Data", value=True)
    ios_simulators_checkbox = ft.Checkbox(label="iOS Simulators", value=True)
    crash_reports_checkbox = ft.Checkbox(label="Crash Reports", value=True)
    temp_files_checkbox = ft.Checkbox(label="Temporary Files", value=True)
    app_support_caches_checkbox = ft.Checkbox(label="App Support Caches", value=True)

    analyze_button = ft.ElevatedButton(text="Analyze")
    clean_button = ft.ElevatedButton(text="Clean", disabled=True)
    analysis_results_text = ft.Text("Select categories and click Analyze")
    quick_clean_file_list = ft.ListView(height=260, spacing=2, auto_scroll=False)
    summary_text = ft.Text("", size=12, color=ft.Colors.GREY_700)
    progress_bar = ft.ProgressBar(width=400, value=0, visible=False)
    current_result = {"items": [], "category_map": {}, "selected": set(), "total_size": 0}
    category_folded = {}

    def selected_categories():
        cats = []
        if user_cache_checkbox.value:
            cats.append(USER_CACHE)
        if system_logs_checkbox.value:
            cats.append(SYSTEM_LOGS)
        if trash_checkbox.value:
            cats.append(TRASH)
        if ios_backups_checkbox.value:
            cats.append(IOS_BACKUPS)
        if macos_installers_checkbox.value:
            cats.append(MACOS_INSTALLERS)
        if xcode_derived_data_checkbox.value:
            cats.append(XCODE_DERIVED_DATA)
        if ios_simulators_checkbox.value:
            cats.append(IOS_SIMULATORS)
        if crash_reports_checkbox.value:
            cats.append(CRASH_REPORTS)
        if temp_files_checkbox.value:
            cats.append(TEMP_FILES)
        if app_support_caches_checkbox.value:
            cats.append(APP_SUPPORT_CACHES)
        return cats

    def rebuild_list_ui():
        quick_clean_file_list.controls.clear()
        # Category grouping
        # Sort categories by total size (largest first)
        cat_sizes = []
        for cat, items in current_result["category_map"].items():
            total_cat_size = sum(i.size for i in items)
            cat_sizes.append((cat, total_cat_size))
        cat_sizes.sort(key=lambda x: x[1], reverse=True)
        for cat, _ in cat_sizes:
            items = current_result["category_map"][cat]
            sorted_items = sorted(items, key=lambda i: i.size, reverse=True)
            subtotal = sum(i.size for i in sorted_items if i.path in current_result["selected"])
            total_cat_size = sum(i.size for i in sorted_items)
            is_folded = category_folded.get(cat, True)  # Default to folded
            chevron_icon = ft.Icons.KEYBOARD_ARROW_RIGHT if is_folded else ft.Icons.KEYBOARD_ARROW_DOWN

            def make_fold_toggle(category):
                def handler(e):
                    category_folded[category] = not category_folded.get(category, True)
                    rebuild_list_ui()
                    page.update()

                return handler

            cat_checkbox = ft.Checkbox(
                value=all(i.path in current_result["selected"] for i in sorted_items) and len(sorted_items) > 0,
                label=f"{cat.replace('_', ' ').title()} ({qc_format_size(subtotal)}/{qc_format_size(total_cat_size)})",
            )

            def make_cat_toggle(category, category_items, cb):
                def handler(e):
                    if cb.value:
                        for it in category_items:
                            current_result["selected"].add(it.path)
                    else:
                        for it in category_items:
                            current_result["selected"].discard(it.path)
                    update_summary()
                    rebuild_list_ui()
                    page.update()

                return handler

            cat_checkbox.on_change = make_cat_toggle(cat, sorted_items, cat_checkbox)
            quick_clean_file_list.controls.append(
                ft.Row(
                    [ft.IconButton(icon=chevron_icon, on_click=make_fold_toggle(cat), icon_size=18), cat_checkbox],
                    spacing=4,
                    alignment=ft.MainAxisAlignment.START,
                )
            )
            if not is_folded:
                for it in sorted_items:
                    item_cb = ft.Checkbox(value=it.path in current_result["selected"], label=None)

                    def make_item_toggle(path):
                        def handler(e):
                            if e.control.value:
                                current_result["selected"].add(path)
                            else:
                                current_result["selected"].discard(path)
                            update_summary()
                            rebuild_list_ui()
                            page.update()

                        return handler

                    item_cb.on_change = make_item_toggle(it.path)
                    rel = os.path.relpath(it.path, os.path.expanduser("~"))

                    def create_quick_clean_ai_handler(path):
                        def handler(e):
                            e.control.icon = ft.Icons.HOURGLASS_EMPTY
                            e.control.tooltip = "Analyzing..."
                            page.update()

                            def analyze():
                                result = ai_analyze_path(path)

                                def update_ui():
                                    for control in quick_clean_file_list.controls:
                                        if isinstance(control, ft.Row) and len(control.controls) >= 4:
                                            if len(control.controls) > 2 and hasattr(control.controls[2], "tooltip"):
                                                if control.controls[2].tooltip == path:
                                                    ai_icon = control.controls[3]
                                                    ai_icon.icon = ft.Icons.PSYCHOLOGY
                                                    ai_icon.tooltip = result["reason"]
                                                    ai_icon.icon_color = get_safety_color(result["safety"])
                                                    page.update()
                                                    break

                                update_ui()

                            threading.Thread(target=analyze, daemon=True).start()

                        return handler

                    normalized_path = it.path
                    cached_ai = config_manager.get_cached_analysis(normalized_path)
                    if cached_ai:
                        ai_icon_color = get_safety_color(cached_ai.get("safety", "grey"))
                        ai_icon_tooltip = cached_ai.get("reason", "AI analysis available")
                        ai_icon_icon = ft.Icons.PSYCHOLOGY
                    else:
                        ai_icon_color = None
                        ai_icon_tooltip = "Click for AI analysis"
                        ai_icon_icon = ft.Icons.PSYCHOLOGY_OUTLINED
                    ai_icon = ft.IconButton(
                        icon=ai_icon_icon,
                        tooltip=ai_icon_tooltip,
                        icon_size=16,
                        on_click=create_quick_clean_ai_handler(it.path),
                        icon_color=ai_icon_color,
                    )
                    quick_clean_file_list.controls.append(
                        ft.Row(
                            [
                                ft.Container(width=48, content=item_cb),
                                ft.Text(qc_format_size(it.size), width=90),
                                ft.Text(rel, expand=True, tooltip=it.path),
                                ai_icon,
                            ],
                            spacing=6,
                            alignment=ft.MainAxisAlignment.START,
                        )
                    )

    def update_summary():
        total_selected_size = sum(i.size for i in current_result["items"] if i.path in current_result["selected"])
        summary_text.value = (
            f"Selected: {len(current_result['selected'])} items • {qc_format_size(total_selected_size)}"
        )
        clean_button.disabled = total_selected_size == 0

    def analyze_files(e):
        analysis_results_text.value = "Analyzing... (streaming)"
        summary_text.value = ""
        quick_clean_file_list.controls.clear()
        clean_button.disabled = True
        progress_bar.visible = True
        progress_bar.value = 0
        current_result["items"] = []
        current_result["category_map"] = {}
        current_result["selected"].clear()
        page.update()

        cats = selected_categories()
        total_cats = len(cats)
        if total_cats == 0:
            analysis_results_text.value = "No categories selected"
            progress_bar.visible = False
            page.update()
            return

        from quick_clean import analyze_quick_clean_iter

        def run_analysis():
            # After analysis, fold all categories by default
            category_folded.clear()
            for idx, (cat, items, cat_size) in enumerate(analyze_quick_clean_iter(cats)):
                current_result["category_map"][cat] = items
                current_result["items"].extend(items)
                # Don't automatically select items - let user choose explicitly
                category_folded[cat] = True  # Folded by default
                # Update UI incrementally
                try:
                    progress_bar.value = (idx + 1) / total_cats
                    rebuild_list_ui()
                    update_summary()
                    analysis_results_text.value = f"Loaded {cat.replace('_', ' ')} ({qc_format_size(cat_size)})"
                    page.update()
                except Exception as ex:
                    analysis_results_text.value = f"Streaming error: {ex}"
                    page.update()
            # Final summary
            try:
                total_size = sum(i.size for i in current_result["items"])
                analysis_results_text.value = f"Found {qc_format_size(total_size)} of removable data. Expand to see details."
                progress_bar.visible = False
                page.update()
            except Exception:
                pass

        threading.Thread(target=run_analysis, daemon=True).start()

    def clean_files(e):
        # Build list of selected items as dicts with 'path' key (to match perform_deletion signature)
        selected_items = [i.path for i in current_result["items"] if i.path in current_result["selected"]]
        if not selected_items:
            return
        analysis_results_text.value = f"Deleting {len(selected_items)} selected items..."
        update_status(f"Starting quick clean deletion of {len(selected_items)} items")
        page.update()

        def run_delete():
            from deletion import perform_deletion as deletion_perform_deletion

            deleted, errors = deletion_perform_deletion(selected_items)
            try:
                analysis_results_text.value = f"Deleted {deleted} items with {errors} errors"
                update_status(f"Quick clean complete: {deleted} deleted, {errors} errors")
                clean_button.disabled = True
                quick_clean_file_list.controls.clear()
                summary_text.value = ""
                page.update()
            except Exception as ex:
                analysis_results_text.value = f"Deletion UI error: {ex}"
                update_status(f"Quick clean error: {ex}")
                page.update()

        threading.Thread(target=run_delete, daemon=True).start()

    analyze_button.on_click = analyze_files
    clean_button.on_click = clean_files

    quick_clean_tab = ft.Column(
        [
            ft.Text("Quick Clean", size=20, weight=ft.FontWeight.BOLD),
            progress_bar,
            ft.Text("Select categories to clean:", size=14, weight=ft.FontWeight.W_500),
            ft.Row(
                [
                    ft.Column(
                        [
                            user_cache_checkbox,
                            system_logs_checkbox,
                            trash_checkbox,
                            ios_backups_checkbox,
                        ],
                        spacing=5,
                    ),
                    ft.Column(
                        [
                            macos_installers_checkbox,
                            xcode_derived_data_checkbox,
                            ios_simulators_checkbox,
                            crash_reports_checkbox,
                        ],
                        spacing=5,
                    ),
                    ft.Column(
                        [
                            temp_files_checkbox,
                            app_support_caches_checkbox,
                        ],
                        spacing=5,
                    ),
                ],
                spacing=20,
                alignment=ft.MainAxisAlignment.START,
            ),
            ft.Row(
                [
                    analyze_button,
                    clean_button,
                ],
                spacing=10,
            ),
            analysis_results_text,
            ft.Container(
                content=quick_clean_file_list,
                border=ft.border.all(1, "#1F000000"),
                border_radius=5,
                padding=8,
                expand=True,
            ),
            ft.Row([summary_text], alignment=ft.MainAxisAlignment.START),
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

    # Directory scan cache - stores scan results to avoid rescanning
    directory_cache = {}
    MAX_CACHE_SIZE = 50  # Limit cache to 50 directories

    def manage_cache():
        """Keep cache size under control by removing oldest entries"""
        if len(directory_cache) > MAX_CACHE_SIZE:
            # Remove oldest 10 entries (simple FIFO)
            oldest_keys = list(directory_cache.keys())[:10]
            for key in oldest_keys:
                del directory_cache[key]
            debug_log(f"[DiskAnalyzer] Cache trimmed, now has {len(directory_cache)} entries")

    def get_size_threaded(path_info):
        path = path_info["path"]
        if scan_thread_state["cancelled"]:
            return None

        update_status(f"Scanning: {os.path.basename(path)}")

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
        except OSError as e:
            update_status(f"Error scanning: {os.path.basename(path)} - {str(e)}")
            return {
                "path": path,
                "size": 0,
                "is_dir": path_info["is_dir"],
            }  # Return 0 if not accessible
        return {"path": path, "size": total_size, "is_dir": path_info["is_dir"]}

    def scan_directory_thread(selected_path):
        debug_log(f"[DiskAnalyzer] Starting scan of directory: {selected_path}")
        update_status(f"Starting scan of: {selected_path}")
        scan_thread_state["cancelled"] = False
        scan_thread_state["current_path"] = selected_path

        try:
            entries = [
                {"path": entry.path, "is_dir": entry.is_dir(follow_symlinks=False)}
                for entry in os.scandir(selected_path)
            ]
            update_status(f"Found {len(entries)} items in {os.path.basename(selected_path)}")
        except OSError as e:
            scan_status_text.value = f"Error: {e.strerror}"
            debug_log(f"[DiskAnalyzer] Error scanning directory {selected_path}: {e.strerror}")
            update_status(f"Error accessing: {selected_path} - {e.strerror}")
            # --- FIX: Update breadcrumbs and add ".." entry even on error ---
            update_breadcrumbs(selected_path)
            scan_results_list.controls.clear()
            if selected_path != "/":
                parent_dir = os.path.dirname(selected_path)
                scan_results_list.controls.append(
                    ft.ListTile(
                        title=ft.Text(".."),
                        leading=ft.Icon(ft.Icons.ARROW_UPWARD),
                        on_click=lambda _, p=parent_dir: scan_and_display(p),
                    )
                )
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

                if i % 10 == 0 or i == len(futures) - 1:
                    print(f"[DiskAnalyzer] Processed {i+1}/{len(futures)} entries in {selected_path}")

                progress = (i + 1) / len(entries)
                scan_progress_bar.value = progress
                page.update()

        if not scan_thread_state["cancelled"]:
            results.sort(key=lambda x: x["size"], reverse=True)
            update_status(f"Scan complete: {len(results)} items found in {os.path.basename(selected_path)}")

            # Cache the results for future navigation
            directory_cache[selected_path] = results
            debug_log(f"[DiskAnalyzer] Cached results for: {selected_path}")
            manage_cache()  # Keep cache size under control

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
        debug_log(
            f"Button state: has_selection={has_selection}, has_unsafe={has_unsafe}, enabled={button_should_be_enabled}"
        )

        delete_button.disabled = not button_should_be_enabled
        delete_button.visible = has_selection
        page.update()
        debug_log(f"Delete button disabled state is now: {delete_button.disabled}, visible: {delete_button.visible}")

    # Forward declaration of scan_and_display function
    def scan_and_display(path):
        debug_log(f"[DiskAnalyzer] Entering directory for scan: {path}")
        update_status(f"Entering directory: {path}")

        # Check if we have cached results for this directory
        if path in directory_cache:
            debug_log(f"[DiskAnalyzer] Using cached results for: {path}")
            update_status(f"Loading cached results for: {os.path.basename(path)}")
            scan_thread_state["current_path"] = path
            cached_results = directory_cache[path]
            display_scan_results(cached_results, path)
            scan_status_text.value = f"📋 Loaded cached scan of {path}. Found {len(cached_results)} items."
            page.update()
            return

        # No cache, perform new scan
        scan_button.disabled = True
        cancel_button.disabled = False
        directory_dropdown.disabled = True
        scan_status_text.value = f"Scanning {path}..."
        scan_results_list.controls.clear()
        page.update()

        threading.Thread(target=scan_directory_thread, args=(path,), daemon=True).start()

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
        update_status(f"Starting deletion of {len(selected_items)} items")

        deletion_results = []
        deleted_count = 0
        error_count = 0
        for item in selected_items:
            try:
                path = item["path"]
                filename = os.path.basename(path)
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)
                deletion_results.append(f"✓ Deleted: {filename}")
                debug_log(f"Successfully deleted: {path}")
                update_status(f"Deleted: {filename}")
                deleted_count += 1
            except Exception as ex:
                error_msg = f"✗ Failed to delete {os.path.basename(item['path'])}: {str(ex)}"
                deletion_results.append(error_msg)
                debug_log(f"Failed to delete {item['path']}: {ex}")
                update_status(f"Error deleting: {os.path.basename(item['path'])} - {str(ex)}")
                error_count += 1

        # Show results in scan status
        scan_status_text.value = "Deletion complete. " + "\n".join(deletion_results[:3])
        if len(deletion_results) > 3:
            scan_status_text.value += f"\n... and {len(deletion_results) - 3} more results"

        update_status(f"Deletion complete: {deleted_count} deleted, {error_count} errors")

        # Invalidate cache for the current directory since files were deleted
        if scan_thread_state["current_path"] in directory_cache:
            del directory_cache[scan_thread_state["current_path"]]
            debug_log(f"[DiskAnalyzer] Invalidated cache for: {scan_thread_state['current_path']}")

        # Refresh the current directory
        scan_and_display(scan_thread_state["current_path"])
        return deleted_count, error_count

    def simple_delete_selected_handler(e):
        """Handle delete button click with inline confirmation."""
        debug_log("Delete button clicked")

        selected_items = []
        unsafe_items = []

        # Collect selected items and check safety
        for control in scan_results_list.controls:
            if hasattr(control, "trailing") and hasattr(control.trailing, "controls"):
                trailing_controls = control.trailing.controls
                if len(trailing_controls) > 0 and isinstance(trailing_controls[0], ft.Checkbox):
                    checkbox = trailing_controls[0]
                    if checkbox.value and hasattr(control, "data"):
                        path = control.data
                        safety_info = get_safety_info(path)
                        selected_items.append({"path": path, "safety": safety_info["safety"]})

                        if safety_info["safety"] == "red":
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
                                        control.leading.controls[0].bgcolor = get_safety_color(result["safety"])
                                    # Update AI icon
                                    if len(control.trailing.controls) > 1:
                                        ai_icon = control.trailing.controls[1]
                                        ai_icon.icon = ft.Icons.PSYCHOLOGY
                                        ai_icon.tooltip = result["reason"]
                                        ai_icon.icon_color = get_safety_color(result["safety"])
                                        # ai_icon.bgcolor = get_safety_color(result["safety"])
                                    page.update()

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

            # Check for cached AI analysis
            normalized_path = item["path"]
            cached_ai = config_manager.get_cached_analysis(normalized_path)
            if cached_ai:
                ai_icon_color = get_safety_color(cached_ai.get("safety", "grey"))
                ai_icon_tooltip = cached_ai.get("reason", "AI analysis available")
                ai_icon_icon = ft.Icons.PSYCHOLOGY
            else:
                ai_icon_color = None
                ai_icon_tooltip = "Click for AI analysis"
                ai_icon_icon = ft.Icons.PSYCHOLOGY_OUTLINED

            ai_icon = ft.IconButton(
                icon=ai_icon_icon,
                tooltip=ai_icon_tooltip,
                icon_size=16,
                on_click=create_ai_analyze_handler(item["path"]),
                icon_color=ai_icon_color,
            )

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

        scan_status_text.value = f"Scan of {current_path} complete. Found {len(results)} items."
        delete_button.visible = False
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
        scan_thread_state["cancelled"] = False
        scan_progress_bar.value = 0
        page.update()

    def scan_directory_handler(e):
        selected_path = directory_dropdown.value
        if selected_path == "clear_cache":
            # Clear cache option selected
            directory_cache.clear()
            update_status(f"Directory cache cleared ({len(directory_cache)} entries)")
            debug_log("[DiskAnalyzer] Directory cache manually cleared")
            directory_dropdown.value = scan_thread_state["current_path"]  # Reset to current path
            page.update()
            return
        scan_and_display(selected_path)

    def cancel_scan_handler(e):
        scan_thread_state["cancelled"] = True
        scan_status_text.value = "Cancelling..."
        page.update()

    directory_dropdown = ft.Dropdown(
        value=os.path.expanduser("~"),
        options=[
            ft.dropdown.Option("/", "System Root (/)"),
            ft.dropdown.Option("/System", "System Files"),
            ft.dropdown.Option("/Applications", "Applications"),
            ft.dropdown.Option("/Users", "All Users"),
            ft.dropdown.Option(os.path.expanduser("~"), "My Home"),
            ft.dropdown.Option(os.path.expanduser("~/Library"), "My Library"),
            ft.dropdown.Option(os.path.expanduser("~/Downloads"), "Downloads"),
            ft.dropdown.Option(os.path.expanduser("~/Documents"), "Documents"),
            ft.dropdown.Option(os.path.expanduser("~/Desktop"), "Desktop"),
            ft.dropdown.Option(os.path.expanduser("~/Pictures"), "Pictures"),
            ft.dropdown.Option(os.path.expanduser("~/Movies"), "Movies"),
            ft.dropdown.Option(os.path.expanduser("~/Music"), "Music"),
            ft.dropdown.Option("clear_cache", "🗑️ Clear Cache"),
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
        visible=False,  # Start hidden
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
    settings_tab = create_settings_tab(page)

    # --- License Tab --- #
    def create_license_tab():
        # Read the license file
        license_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "LICENSE")
        license_text = ""
        try:
            with open(license_path, 'r', encoding='utf-8') as f:
                license_text = f.read()
        except Exception as e:
            license_text = f"Error reading license file: {e}"
        
        return ft.Column(
            [
                ft.Text("License", size=20, weight=ft.FontWeight.BOLD),
                ft.Container(
                    content=ft.Text(
                        license_text,
                        size=12,
                        selectable=True,
                        color=ft.Colors.BLACK87,
                    ),
                    border=ft.border.all(1, "#1F000000"),
                    border_radius=5,
                    padding=15,
                    expand=True,
                ),
            ],
            spacing=10,
            alignment=ft.MainAxisAlignment.START,
            expand=True,
        )

    license_tab = create_license_tab()

    # --- Main Layout --- #
    tabs = ft.Tabs(
        selected_index=0,
        animation_duration=300,
        tabs=[
            ft.Tab(text="Quick Clean", content=quick_clean_tab),
            ft.Tab(text="Disk Analyzer", content=disk_analyzer_tab),
            ft.Tab(text="Settings", content=settings_tab),
            ft.Tab(text="License", content=license_tab),
        ],
        expand=True,
    )

    # Add the main content and status text at the bottom
    page.add(
        ft.Column(
            [
                tabs,
                ft.Container(
                    content=status_text,
                    padding=ft.padding.all(5),
                    bgcolor=ft.Colors.GREY_100,
                    border_radius=3,
                ),
            ],
            expand=True,
        )
    )


if __name__ == "__main__":
    ft.app(
        target=main,
        view=ft.AppView.FLET_APP,
        port=0,  # Use random available port
        web_renderer=ft.WebRenderer.HTML,
    )
