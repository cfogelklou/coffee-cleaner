# Vibe Code Request: macOS Cleaner & Analyzer GUI (v5)

## 1. Core Idea
Create a multi-functional macOS utility with two main features:
- **Quick Clean tool**: Removes common junk files.
- **Disk Analyzer**: Uses AI-powered safety analysis to help users identify and delete large, unnecessary files.

## 2. Technology Stack
- **Language**: Python 3
- **GUI Framework**: Flet
- **AI Integration**: Gemini API
- **Build Tool**: PyInstaller
- **CI/CD**: GitHub Actions
- **Target OS**: macOS

## 3. Application UI Specification
The application will use a tabbed interface.

### Window
- **Title**: Mac Cleaner & Analyzer
- **Initial Dimensions**: 600px width, 700px height
- **Resizable**

### Tab 1: Quick Clean
A simple, checkbox-based cleaning tool for user caches, logs, disk images, and iOS backups. The flow remains **Analyze → Clean**.

### Tab 2: Disk Analyzer
An advanced file explorer for disk management.
- **Scan Setup**: Allows the user to select a directory (Home, Downloads, custom, etc.) and start a scan.
- **File Explorer**: A post-scan view showing a breadcrumb path and a list of files/folders sorted by size. Each item includes:
    - A safety dot (green/orange/red/grey)
    - A checkbox
    - An AI analysis icon for unknown items
- A **"Delete Selected"** button is available at the bottom, disabled if unsafe items are selected.

## 4. Backend Logic Specification

### Pre-Generated Safety Rules
A built-in Python dictionary will map known paths to their safety level and provide a brief explanation to minimize API calls.

#### Example of the pre-generated safety map:
```python
PREDEFINED_RULES = {
        "~/Library/Caches/*": {"safety": "green", "reason": "Application cache files. Generally safe to delete."},
        "~/Downloads": {"safety": "green", "reason": "User-downloaded files. User should verify before deleting."},
        "~/Library/Application Support/MobileSync/Backup": {"safety": "orange", "reason": "iOS device backups. Safe to delete if you have recent cloud backups, but deletion is permanent."},
        "/System": {"safety": "red", "reason": "Critical macOS system files. Do not delete."},
        "/Applications": {"safety": "red", "reason": "Installed applications. Do not delete this folder directly."},
        "~/Library": {"safety": "orange", "reason": "Contains important user settings and data. Be very careful."},
}
```

### Functions
- `scan_directory(path)`: Scans a directory using 4 worker threads to improve performance and returns its contents sorted by size. The scan can be cancelled by the user.
- `get_safety_info(path)`: Checks pre-defined rules and a local cache to determine a path's safety.
- `ai_analyze_path(path)`: Uses the Gemini API to analyze unknown paths and caches the result.
- `delete_selected_items(paths)`: Deletes user-selected files and folders safely.

## 5. Distribution & Installation

### 5.1. Installation from Source (README.md)
Generate a README.md with clear, step-by-step instructions for:
- Cloning the repository
- Setting up a virtual environment
- Installing dependencies from `requirements.txt`
- Running the application

### 5.2. Build Process (Executable)
- Include a configuration and a build script (`build.sh`) for PyInstaller to create a standalone macOS application bundle (.app).
- Document details for running this script in the README.md.

## 6. Style Guide & Coding Guidelines
- **Code Formatter**: Black (default settings).
- **Linter**: Flake8 to catch common errors and enforce style.
- **Configuration**: Settings for both Black and Flake8 stored in the `pyproject.toml` file for consistency.

### Important Flet Framework Notes
- **Case Sensitivity**: Always use uppercase for Flet constants:
  - ✅ Correct: `ft.Icons.FOLDER`, `ft.Colors.RED`, `ft.MainAxisAlignment.CENTER`
  - ❌ Incorrect: `ft.icons.FOLDER`, `ft.colors.RED`, `ft.mainaxisalignment.CENTER`
- **Reason**: Newer versions of Flet use uppercase naming conventions. Using lowercase will cause `AttributeError`.

## 7. CI/CD with GitHub Actions

### Directory
- Create a `.github/workflows/` directory in the project root.

### Workflow File
- Place a `ci.yml` file inside the workflows directory.

### Triggers
- The workflow runs on every push to the main branch and on every pull request targeting main.

### Jobs
- **Linting**: Installs dependencies and runs `flake8 .` and `black --check .` to ensure code meets the style guidelines.
- **Testing**: A placeholder job for running unit tests (e.g., pytest), to be expanded later.
- **Build**: Runs on a macOS runner to execute the `build.sh` script. The resulting .app file will be uploaded as a build artifact.

## 8. Final Polish
- Ensure all UI elements have appropriate spacing and padding for a clean, organized look.
- Add comments to Python code to explain the purpose of each function and the UI state management logic.
