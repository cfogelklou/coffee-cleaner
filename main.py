import flet as ft

def main(page: ft.Page):
    page.title = "Mac Cleaner & Analyzer"
    page.window_width = 600
    page.window_height = 700
    page.window_resizable = True

    page.appbar = ft.AppBar(
        title=ft.Text("Mac Cleaner & Analyzer"),
        center_title=True,
    )

    quick_clean_tab = ft.Column(
        controls=[
            ft.Checkbox(label="User Cache", value=True),
            ft.Checkbox(label="System Logs", value=True),
            ft.Checkbox(label="Trash", value=True),
            ft.Checkbox(label="iOS Backups", value=False),
            ft.Row(
                controls=[
                    ft.ElevatedButton(text="Analyze"),
                    ft.ElevatedButton(text="Clean", disabled=True),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            ft.Text("Analysis results will be shown here."),
        ],
        spacing=10,
        alignment=ft.MainAxisAlignment.START,
    )

    disk_analyzer_tab = ft.Container(
        content=ft.Text("Disk Analyzer content goes here"),
        padding=20
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
