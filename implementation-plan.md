# Implementation Plan: Mac Cleaner & Analyzer

This document outlines the iterative steps to build the Mac Cleaner & Analyzer application. Each step represents a milestone that should be verified by the user before proceeding to the next.

This plan adheres to the specifications outlined in `GEMINI.md` and ` .github/copilot-instructions.md`.

## Development Steps

### Step 1: Quick Clean UI

-   **Goal:** Implement the user interface for the "Quick Clean" tab.
-   **Tasks:**
    -   Replace the placeholder content with a layout containing checkboxes for:
        -   User Cache
        -   System Logs
        -   Trash
        -   iOS Backups
    -   Add an "Analyze" button and a "Clean" button (initially disabled).
    -   Add a status text area to display information about the analysis.
-   **User Verification:** The user will run the application and confirm that the UI elements for the Quick Clean tab are present and laid out correctly.

### Step 2: Quick Clean Backend

-   **Goal:** Implement the logic for the "Analyze" and "Clean" buttons.
-   **Tasks:**
    -   Implement a function to analyze the selected categories and calculate the space that can be saved.
    -   Display the results of the analysis in the status area.
    -   Enable the "Clean" button after a successful analysis.
    -   Implement a function to delete the files in the selected categories.
-   **User Verification:** The user will test the "Analyze" and "Clean" functionality to ensure they work as expected.

### Step 3: Disk Analyzer UI (Scan Setup)

-   **Goal:** Implement the initial UI for the "Disk Analyzer" tab.
-   **Tasks:**
    -   Add a dropdown menu to select a directory to scan (e.g., Home, Downloads).
    -   Add a "Scan" button.
    -   Add a progress bar to provide feedback during the scan.
-   **User Verification:** The user will verify that the scan setup UI is present and functional.

### Step 4: Disk Analyzer Backend (Scanning)

-   **Goal:** Implement the directory scanning logic.
-   **Tasks:**
    -   Implement the `scan_directory(path)` function.
    -   The function should recursively scan the given path and return a list of files and folders, sorted by size in descending order.
-   **User Verification:** The user will trigger a scan and verify that the function correctly identifies files and folders and that the progress bar updates.

### Step 5: Disk Analyzer UI (File Explorer)

-   **Goal:** Display the results of the directory scan.
-   **Tasks:**
    -   Create a file explorer view to display the scanned files and folders.
    -   Each item in the list should have a checkbox, an icon, the file/folder name, and its size.
    -   Make directory entries clickable to allow for drilling down into subdirectories.
    -   Add a "Delete Selected" button at the bottom.
-   **User Verification:** The user will verify that the scan results are displayed correctly in the file explorer.

### Step 5.1: Drill-Down Navigation

-   **Goal:** Implement the logic for navigating into and out of directories.
-   **Tasks:**
    -   When a directory is clicked, the view should update to show the contents of that directory.
    -   Implement a breadcrumb navigation bar to show the current path and allow for easy navigation back to parent directories.
    -   Include a ".." entry at the top of the list to navigate up one level.
-   **User Verification:** The user will test the drill-down functionality, the breadcrumb navigation, and the ".." entry.

### Step 6: Safety Rules and AI Analysis

-   **Goal:** Integrate the safety analysis features.
-   **Tasks:**
    -   Implement the `get_safety_info(path)` function using the pre-defined rules from `GEMINI.md`.
    -   Implement the `ai_analyze_path(path)` function to use the Gemini API for unknown paths.
    -   Add a safety dot (green, orange, red) to each item in the file explorer based on the safety analysis.
    -   Add an icon to trigger the AI analysis for items with unknown safety.
-   **User Verification:** The user will verify that the safety dots are displayed correctly and that the AI analysis can be triggered.

### Step 7: Deletion Logic

-   **Goal:** Implement the file deletion functionality for the Disk Analyzer.
-   **Tasks:**
    -   Implement the `delete_selected_items(paths)` function.
    -   The "Delete Selected" button should be disabled if any of the selected items are marked as "red" (unsafe to delete).
-   **User Verification:** The user will test the deletion functionality, including the safety check.

### Step 8: CI/CD Setup

-   **Goal:** Set up the GitHub Actions workflow.
-   **Tasks:**
    -   Create the `.github/workflows/ci.yml` file.
    -   Configure the workflow to run linting (flake8, black), tests (placeholder), and the build script.
-   **User Verification:** The user will commit the changes, push to a test branch, and verify that the CI/CD pipeline runs successfully on GitHub.

### Step 9: Final Polish and README

-   **Goal:** Prepare the application for distribution.
-   **Tasks:**
    -   Review and refine the entire UI for consistency and aesthetics.
    -   Add comments to the code to improve readability.
    -   Generate a comprehensive `README.md` with instructions for users and developers.
-   **User Verification:** The user will review the final application, documentation, and code.
