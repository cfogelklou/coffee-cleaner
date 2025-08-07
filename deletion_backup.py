"""
Deletion functionality for the Mac Cleaner & Analyzer.
"""

import os
import shutil
import flet as ft
from safety_analysis import get_safety_info
from config import debug_log


def create_deletion_manager(page, scan_results_list, scan_thread_state, scan_and_display_func):
    """
    Create and return deletion management functions.
    This factory function provides closure over the UI components.
    """
    
    def show_dialog(title, content):
        """Show an information dialog."""
        debug_log(f"=== SHOWING DIALOG: {title} ===")

        def close_dialog(e):
            debug_log("User clicked OK on dialog")
            page.dialog.open = False
            page.update()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(title),
            content=ft.Text(content),
            actions=[ft.TextButton("OK", on_click=close_dialog)],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        debug_log("Setting info dialog and opening")
        page.dialog = dialog
        dialog.open = True
        page.update()
        debug_log("Info dialog should now be visible")

    def delete_selected_items():
        """Delete selected files and folders safely."""
        debug_log("=== ENTERING delete_selected_items ===")
        
        selected_items = []
        unsafe_items = []

        debug_log(f"scan_results_list has {len(scan_results_list.controls)} controls")
        
        # Collect selected items and check safety
        for i, control in enumerate(scan_results_list.controls):
            debug_log(f"Control {i}: type={type(control).__name__}")
            
            if not hasattr(control, "trailing"):
                debug_log(f"  Control {i}: No 'trailing' attribute")
                continue
                
            if not hasattr(control.trailing, "controls"):
                debug_log(f"  Control {i}: trailing has no 'controls' attribute")
                continue
                
            trailing_controls = control.trailing.controls
            debug_log(f"  Control {i}: {len(trailing_controls)} trailing controls")
            
            if len(trailing_controls) == 0:
                debug_log(f"  Control {i}: No trailing controls")
                continue
                
            checkbox = trailing_controls[0]
            debug_log(f"  Control {i}: first trailing control type={type(checkbox).__name__}")
            
            if not isinstance(checkbox, ft.Checkbox):
                debug_log(f"  Control {i}: first trailing control is not a Checkbox")
                continue
                
            debug_log(f"  Control {i}: checkbox.value={checkbox.value}")
            
            if not checkbox.value:
                debug_log(f"  Control {i}: checkbox not selected")
                continue
                
            if not hasattr(control, "data"):
                debug_log(f"  Control {i}: control has no 'data' attribute")
                continue
                
            path = control.data
            debug_log(f"  Control {i}: SELECTED! path={path}")
            
            safety_info = get_safety_info(path)
            selected_items.append({"path": path, "safety": safety_info["safety"]})

            if safety_info["safety"] == "red":
                unsafe_items.append(path)
                debug_log(f"  Control {i}: UNSAFE item detected")

        debug_log(f"=== SELECTION SUMMARY ===")
        debug_log(f"Selected items: {len(selected_items)}")
        debug_log(f"Unsafe items: {len(unsafe_items)}")
        
        for item in selected_items:
            debug_log(f"  Selected: {item['path']} (safety: {item['safety']})")

        if not selected_items:
            debug_log("No items selected - showing dialog")
            show_dialog("No items selected", "Please select items to delete.")
            return

        if unsafe_items:
            debug_log("Unsafe items detected - showing dialog")
            show_dialog(
                "Unsafe items selected",
                f"Cannot delete items marked as unsafe (red): {', '.join([os.path.basename(p) for p in unsafe_items])}",
            )
            return

        debug_log("Proceeding to confirmation dialog")
        show_confirmation_dialog(selected_items)
        
def show_confirmation_dialog(page, items_to_delete, on_confirm_callback):
    """Show confirmation dialog for file deletion."""
    debug_log(f"=== CREATING CONFIRMATION DIALOG ===")
    debug_log(f"Items to delete: {len(items_to_delete)}")
    
    if not items_to_delete:
        debug_log("No items to delete - returning early")
        return

    def handle_yes(e):
        debug_log("User clicked YES in confirmation dialog")
        page.close_dialog()
        on_confirm_callback(items_to_delete)

def show_confirmation_dialog(page, items_to_delete, on_confirm_callback):
    """Show confirmation dialog for file deletion."""
    debug_log(f"=== CREATING CONFIRMATION DIALOG ===")
    debug_log(f"Items to delete: {len(items_to_delete)}")
    
    if not items_to_delete:
        debug_log("No items to delete - returning early")
        return

    def handle_yes(e):
        debug_log("User clicked YES in confirmation dialog")
        page.close_dialog()
        on_confirm_callback(items_to_delete)

    def handle_no(e):
        debug_log("User clicked NO in confirmation dialog")
        page.close_dialog()

    # Create file list text
    file_list = "\n".join([f"• {os.path.basename(item)}" for item in items_to_delete[:10]])
    if len(items_to_delete) > 10:
        file_list += f"\n... and {len(items_to_delete) - 10} more files"

    content_text = f"Are you sure you want to delete the following {len(items_to_delete)} item(s)?\n\n{file_list}\n\nThis action cannot be undone."

    debug_log(f"Dialog content: {content_text[:100]}...")

    confirmation_dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("Confirm Deletion"),
        content=ft.Text(content_text),
        actions=[
            ft.TextButton("Cancel", on_click=handle_no),
            ft.TextButton("Delete", on_click=handle_yes),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )

    debug_log("Showing dialog with page.show_dialog()...")
    page.show_dialog(confirmation_dialog)
    debug_log("Confirmation dialog should now be visible")
    debug_log(f"Dialog object: {confirmation_dialog}")
    debug_log(f"Dialog modal: {confirmation_dialog.modal}")


def delete_selected_handler(e):
        debug_log("=== DELETE BUTTON CLICKED ===")
        debug_log(f"Event: {e}")
        debug_log(f"Event control: {e.control if hasattr(e, 'control') else 'No control'}")
        try:
            delete_selected_items()
        except Exception as ex:
            debug_log(f"ERROR in delete_selected_handler: {ex}")
            import traceback
            debug_log(f"Traceback: {traceback.format_exc()}")

    return delete_selected_handler, delete_selected_items
