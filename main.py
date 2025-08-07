import flet as ft
import time
import random
import os
import math
import threading
import queue
from concurrent.futures import ThreadPoolExecutor

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
                files_to_delete.append(f"~/Library/Application Support/MobileSync/Backup/some_backup ({size} MB)")

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
                border=ft.border.all(1, '#1F000000'),
                border_radius=5,
                padding=10,
                height=250,
            )
        ],
        spacing=10,
        alignment=ft.MainAxisAlignment.START,
    )

    # --- Disk Analyzer Tab --- #

    scan_status_text = ft.Text("")
    scan_progress_bar = ft.ProgressBar(width=400, value=0)
    scan_results_list = ft.ListView(expand=True, spacing=5, auto_scroll=True)
    
    scan_thread_state = {"cancelled": False}

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
            return {"path": path, "size": 0} # Return 0 if not accessible
        return {"path": path, "size": total_size}

    def scan_directory_thread(selected_path):
        scan_thread_state["cancelled"] = False
        
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
            display_scan_results(results)
        
        reset_scan_ui()

    def display_scan_results(results):
        scan_results_list.controls.clear()
        for item in results:
            scan_results_list.controls.append(
                ft.Text(f"{item['path']} - {format_size(item['size'])}")
            )
        scan_status_text.value = f"Scan complete. Found {len(results)} items."
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
        selected_path = directory_dropdown.value
        scan_button.disabled = True
        cancel_button.disabled = False
        directory_dropdown.disabled = True
        scan_status_text.value = f"Scanning {selected_path}..."
        scan_results_list.controls.clear()
        page.update()
        
        threading.Thread(target=scan_directory_thread, args=(selected_path,), daemon=True).start()

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
            ft.Row([scan_progress_bar], alignment=ft.MainAxisAlignment.CENTER),
            ft.Row([scan_status_text], alignment=ft.MainAxisAlignment.CENTER),
            ft.Container(
                content=scan_results_list,
                border=ft.border.all(1, '#1F000000'),
                border_radius=5,
                padding=10,
                expand=True,
            )
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
''

