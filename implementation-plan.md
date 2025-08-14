# Implementation Plan: CoffeeCleaner

This document outlines the iterative steps to build the CoffeeCleaner application. Each step represents a milestone that should be verified by the user before proceeding to the next.

This plan adheres to the specifications outlined in `GEMINI.md` and `.github/copilot-instructions.md`.

## Development Steps

### Step 1: Quick Clean UI ✅ **COMPLETED**

-   **Goal:** Implement the user interface for the "Quick Clean" tab.
-   **Tasks:**
    -   Replace the placeholder content with a layout containing checkboxes for:
        -   User Cache
        -   System Logs
        -   Trash
        -   iOS Backups
    -   Add an "Analyze" button and a "Clean" button (initially disabled).
    -   Add a status text area to display information about the analysis.
-   **Status:** ✅ Verified and working - UI elements are present and functional

### Step 2: Quick Clean Backend ✅ **COMPLETED**

-   **Goal:** Implement the logic for the "Analyze" and "Clean" buttons.
-   **Tasks:**
    -   Implement a function to analyze the selected categories and calculate the space that can be saved.
    -   Display the results of the analysis in the status area.
    -   Enable the "Clean" button after a successful analysis.
    -   Implement a function to delete the files in the selected categories.
-   **Status:** ✅ Verified and working - Mock implementation with simulated file analysis and cleanup

### Step 3: Disk Analyzer UI (Scan Setup) ✅ **COMPLETED**

-   **Goal:** Implement the initial UI for the "Disk Analyzer" tab.
-   **Tasks:**
    -   Add a dropdown menu to select a directory to scan (e.g., Home, Downloads).
    -   Add a "Scan" button.
    -   Add a progress bar to provide feedback during the scan.
-   **Status:** ✅ Verified and working - Scan setup UI is functional

### Step 4: Disk Analyzer Backend (Scanning) ✅ **COMPLETED**

-   **Goal:** Implement the directory scanning logic.
-   **Tasks:**
    -   Implement the `scan_directory(path)` function.
    -   The function should recursively scan the given path and return a list of files and folders, sorted by size in descending order.
-   **Status:** ✅ Verified and working - Multi-threaded scanning with progress updates

### Step 5: Disk Analyzer UI (File Explorer) ✅ **COMPLETED**

-   **Goal:** Display the results of the directory scan.
-   **Tasks:**
    -   Create a file explorer view to display the scanned files and folders.
    -   Each item in the list should have a checkbox, an icon, the file/folder name, and its size.
    -   Make directory entries clickable to allow for drilling down into subdirectories.
    -   Add a "Delete Selected" button at the bottom.
-   **Status:** ✅ Basic file listing is working, but drill-down navigation needs testing

### Step 5.1: Drill-Down Navigation ✅ **COMPLETED**

-   **Goal:** Implement the logic for navigating into and out of directories.
-   **Tasks:**
    -   ✅ When a directory is clicked, the view should update to show the contents of that directory.
    -   ✅ Implement a breadcrumb navigation bar to show the current path and allow for easy navigation back to parent directories.
    -   ✅ Include a ".." entry at the top of the list to navigate up one level.
    -   ✅ Fixed lambda closure issues preventing directory navigation
-   **Status:** ✅ **COMPLETED AND VERIFIED** - Directory clicking, breadcrumbs, and ".." navigation working properly.

### Step 6: Safety Rules and AI Analysis ✅ **COMPLETED** 

-   **Goal:** Integrate the safety analysis features.
-   **Tasks:**
    -   ✅ Implement the `get_safety_info(path)` function using the pre-defined rules from `GEMINI.md`.
    -   ✅ Implement the `ai_analyze_path(path)` function to use the Gemini API for unknown paths.
    -   ✅ Add a safety dot (green, orange, red) to each item in the file explorer based on the safety analysis.
    -   ✅ Add an icon to trigger the AI analysis for items with unknown safety.
    -   ✅ Comprehensive macOS safety database with 50+ predefined rules
    -   ✅ Local configuration management for API keys
    -   ✅ Settings UI tab for AI configuration
    -   ✅ AI response parsing (handles markdown code blocks)
    -   ✅ Result caching to minimize API calls
-   **Status:** ✅ **COMPLETED AND VERIFIED** - AI analysis working with real Gemini API integration. Fixed threading issues and drill-down navigation.

### Step 7: Deletion Logic ✅ **COMPLETED**

-   **Goal:** Implement the file deletion functionality for the Disk Analyzer.
-   **Tasks:**
    -   Implement the `delete_selected_items(paths)` function.
    -   The "Delete Selected" button should be disabled if any of the selected items are marked as "red" (unsafe to delete).
    -   ~~Use AlertDialog for deletion confirmation~~ **ISSUE:** Flet AlertDialog not displaying properly across different versions
    -   **IMPLEMENTED:** Use inline confirmation UI with Yes/No buttons at the bottom instead of modal dialog
    -   When "Delete Selected" is clicked, show confirmation row with selected file count and Yes/No buttons
    -   Only show confirmation UI when deletion is requested, hide it after confirmation or cancellation
-   **Status:** ✅ **COMPLETED AND VERIFIED** - Inline confirmation UI working properly, file deletion functional with safety checks.

### Step 8: CI/CD Setup ✅ **COMPLETED**

-   **Goal:** Set up the GitHub Actions workflow.
-   **Tasks:**
    -   Create the `.github/workflows/ci.yml` file.
    -   Configure the workflow to run linting (flake8, black), tests (placeholder), and the build script.
-   **Status:** ✅ GitHub Actions workflow created and configured

### Step 9: Final Polish and README 🚧 **IN PROGRESS**

-   **Goal:** Prepare the application for distribution.
-   **Tasks:**
    -   ✅ Review and refine the entire UI for consistency and aesthetics.
    -   🚧 Add comments to the code to improve readability.
    -   🚧 Generate a comprehensive `README.md` with instructions for users and developers.
    -   ✅ Updated documentation to prevent Flet case sensitivity issues
    -   ✅ Fixed threading compatibility issues
    -   ✅ Enhanced error handling and debug logging
-   **Status:** 🚧 **IN PROGRESS** - Core functionality complete, working on documentation and code polish.

## Next Steps - Priority Order

**IMMEDIATE PRIORITY: Complete AI Analysis Implementation**

### 1. Enhanced Safety Database (Step 6 - Priority 1)
- Expand the predefined safety rules database with comprehensive macOS paths
- Include system directories, user directories, application paths, and common file types
- Ensure coverage of all critical macOS locations to minimize AI API calls

### 2. AI Integration (Step 6 - Priority 2)  
- Implement actual Gemini API integration for unknown paths
- Add user configuration for AI API tokens
- Implement fallback heuristic analysis when API is unavailable
- Cache AI analysis results to avoid repeated API calls

**SECONDARY PRIORITY: User Verification Required**

### 3. Test All Features (Steps 5.1, 6, 7)
- Test drill-down navigation, safety analysis, and deletion functionality
- Verify the expanded safety database provides good coverage
- Test AI analysis for truly unknown file types

### 3. Test Deletion Logic (Step 7) - **UPDATED APPROACH**
- Select files/folders using checkboxes in the file list
- Verify the "Delete Selected" button enables when items are selected
- Verify the button is disabled when unsafe (red) items are selected
- ~~Test the deletion confirmation dialog~~ **ISSUE FOUND:** Flet dialog not displaying
- **NEW:** Test inline confirmation UI with Yes/No buttons at bottom of screen
- Test actual file deletion (use caution - start with test files)

**NEXT DEVELOPMENT PRIORITY:**

### 4. Fix Any Issues Found During Testing
Based on user verification results, fix any broken functionality before proceeding.

### 5. Complete Step 9: Final Polish and README
- Add comprehensive code comments
- Create user and developer documentation
- Review UI for consistency and polish
