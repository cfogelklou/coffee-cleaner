import flet as ft
import time
import random
import os

def main(page: ft.Page):
    page.title = "Mac Cleaner & Analyzer"
    page.window_width = 600
    page.window_height = 700
    page.window_resizable = True

    page.appbar = ft.AppBar(
        title=ft.Text("Mac Cleaner & Analyzer"),
        center_title=True,
    )

    # --- Quick Clean Tab --- #

    user_cache_checkbox = ft.Checkbox(label="User Cache", value=True)
    system_logs_checkbox = ft.Checkbox(label="System Logs", value=True)
    trash_checkbox = ft.Checkbox(label="Trash", value=True)
    ios_backups_checkbox = ft.Checkbox(label="iOS Backups", value=False)

    analyze_button = ft.ElevatedButton(text="Analyze")
    clean_button = ft.ElevatedButton(text="Clean", disabled=True)
    analysis_results_text = ft.Text("Analysis results will be shown here.")
    file_list = ft.ListView(height=200, spacing=5)

    def analyze_files(e):
        analysis_results_text.value = "Analyzing..."
        file_list.controls.clear()
        page.update()
        time.sleep(2)  # Simulate analysis time

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
            file_list.controls.append(ft.Text(file_path))
        
        clean_button.disabled = False
        page.update()

    def clean_files(e):
        analysis_results_text.value = "Cleaning..."
        file_list.controls.clear()
        page.update()
        time.sleep(2)  # Simulate cleaning time

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
                controls=[
                    analyze_button,
                    clean_button,
                ],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            analysis_results_text,
            file_list,
        ],
        spacing=10,
        alignment=ft.MainAxisAlignment.START,
    )

    # --- Disk Analyzer Tab --- #

    scan_status_text = ft.Text("")

    def scan_directory_handler(e):
        scan_button.disabled = True
        directory_dropdown.disabled = True
        progress_bar.value = None  # Indeterminate progress
        scan_status_text.value = f"Scanning {directory_dropdown.value}..."
        page.update()

        # Simulate a scan
        time.sleep(3)

        progress_bar.value = 1  # Complete
        scan_status_text.value = "Scan complete!"
        scan_button.disabled = False
        directory_dropdown.disabled = False
        page.update()

    directory_dropdown = ft.Dropdown(
        value=os.path.expanduser("~"),
        options=[
            ft.dropdown.Option("/"),
            ft.dropdown.Option(os.path.expanduser("~")),
            ft.dropdown.Option(os.path.expanduser("~/Downloads")),
            ft.dropdown.Option(os.path.expanduser("~/Documents")),
        ],
        width=400,
    )

    scan_button = ft.ElevatedButton(text="Scan", on_click=scan_directory_handler)
    progress_bar = ft.ProgressBar(width=400, value=0)

    disk_analyzer_tab = ft.Column(
        [
            ft.Row(
                [
                    ft.Text("Select a directory to scan:"),
                    directory_dropdown,
                    scan_button,
                ],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            ft.Row(
                [progress_bar],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            ft.Row(
                [scan_status_text],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
        ],
        spacing=20,
        alignment=ft.MainAxisAlignment.START,
    )

    tabs = ft.Tabs(
        selected_index=0,
        animation_duration=300,
        tabs=[
            ft.Tab(
                text="Quick Clean",
                content=quick_clean_tab,
            ),
            ft.Tab(
                text="Disk Analyzer",
                content=disk_analyzer_tab,
            ),
        ],
        expand=1,
    )

    page.add(tabs)

if __name__ == "__main__":
    ft.app(target=main)
