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
        
    def show_confirmation_dialog(selected_items):
        """Show the deletion confirmation dialog."""
        debug_log(f"=== CREATING CONFIRMATION DIALOG for {len(selected_items)} items ===")
        
        # Confirm deletion
        def confirm_delete(e):
            debug_log("User clicked CONFIRM DELETE")
            page.dialog.open = False
            page.update()

            # Perform deletion
            debug_log("Starting actual deletion process")
            deletion_results = []
            for item in selected_items:
                try:
                    path = item["path"]
                    debug_log(f"Attempting to delete: {path}")
                    if os.path.isdir(path):
                        shutil.rmtree(path)
                        debug_log(f"Successfully deleted directory: {path}")
                    else:
                        os.remove(path)
                        debug_log(f"Successfully deleted file: {path}")
                    deletion_results.append(f"✓ Deleted: {os.path.basename(path)}")
                except Exception as ex:
                    debug_log(f"Failed to delete {path}: {ex}")
                    deletion_results.append(f"✗ Failed to delete {os.path.basename(item['path'])}: {str(ex)}")

            # Show results and refresh the current directory
            debug_log("Showing deletion results")
            show_dialog("Deletion Complete", "\n".join(deletion_results))
            debug_log("Refreshing directory view")
            scan_and_display_func(scan_thread_state["current_path"])

        def cancel_delete(e):
            debug_log("User clicked CANCEL DELETE")
            page.dialog.open = False
            page.update()

        confirmation_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Confirm Deletion"),
            content=ft.Text(
                f"Are you sure you want to delete {len(selected_items)} selected item(s)? This action cannot be undone."
            ),
            actions=[
                ft.TextButton("Cancel", on_click=cancel_delete),
                ft.TextButton("Delete", on_click=confirm_delete),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        debug_log("Setting confirmation dialog and opening")
        page.dialog = confirmation_dialog
        confirmation_dialog.open = True
        page.update()
        debug_log("Confirmation dialog should now be visible")
        
        # Force page update again just in case
        page.update()
        debug_log("Second page update completed")

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
