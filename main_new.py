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
from concurrent.futures import ThreadPoolExecutor

# Import our custom modules
from config import debug_log
from safety_analysis import get_safety_info, get_safety_color, ai_analyze_path
from deletion import create_deletion_manager


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

                        page.run_thread_safe(update_ui)

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

            list_tile = ft.ListTile(
                title=ft.Text(os.path.basename(item["path"])),
                subtitle=ft.Text(format_size(item["size"])),
                leading=leading_row,
                trailing=trailing_row,
                on_click=lambda _, p=item["path"]: (scan_and_display(p) if is_dir else None),
                data=item["path"],  # Store path for reference
            )

            # Only make directories clickable for navigation
            if not is_dir:
                list_tile.on_click = None

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
    
    debug_log("Creating delete button with handler")
    delete_button = ft.ElevatedButton(
        text="Delete Selected",
        on_click=delete_selected_handler,
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
            ft.Row(
                [delete_button],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
        ],
        spacing=10,
        alignment=ft.MainAxisAlignment.START,
        expand=True,
    )

    # --- Main Layout --- #
    tabs = ft.Tabs(
        selected_index=0,
        animation_duration=300,
        tabs=[
            ft.Tab(text="Quick Clean", content=quick_clean_tab),
            ft.Tab(text="Disk Analyzer", content=disk_analyzer_tab),
        ],
        expand=True,
    )

    page.add(tabs)


if __name__ == "__main__":
    ft.app(target=main)
