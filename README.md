# Mac Cleaner & Analyzer

A powerful macOS utility application that provides two essential disk management features:
- **Quick Clean**: Remove common junk files with a simple checkbox interface
- **Disk Analyzer**: Advanced file explorer with AI-powered safety analysis for smart disk cleanup

## Features

### Quick Clean
- ✅ One-click analysis and cleanup of common junk files
- ✅ Selective cleaning with checkboxes for different file types:
  - User Cache files
  - System Logs
  - Trash contents
  - iOS and local system (macOS) backups
- ✅ Real-time size calculation and preview of files to be deleted

### Disk Analyzer
- ✅ Multi-threaded directory scanning with progress indication
- ✅ Interactive file explorer with drill-down navigation
- ✅ Breadcrumb navigation for easy directory traversal
- ✅ Safety-coded file analysis with colored indicators:
  - 🟢 Green: Safe to delete
  - 🟠 Orange: Caution advised
  - 🔴 Red: Do not delete (system files)
  - ⚪ Grey: Unknown (AI analysis available)
- ✅ AI-powered analysis for unknown file types (placeholder implementation)
- ✅ Checkbox-based file selection with smart safety controls
- ✅ Inline confirmation UI for safe file deletion
- ✅ Real-time deletion feedback and directory refresh
- ✅ Breadcrumb navigation for easy path traversal
- ✅ **Smart Safety Analysis** with color-coded indicators:
  - 🟢 **Green**: Safe to delete
  - 🟠 **Orange**: Use caution
  - 🔴 **Red**: Do not delete (system files)
  - ⚪ **Grey**: Unknown (AI analysis available)
- ✅ **AI-Powered Analysis**: Click the brain icon for unknown files to get AI recommendations
- ✅ **Safe Deletion**: Cannot delete items marked as unsafe (red)
- ✅ Checkbox selection with bulk deletion capability
- ✅ Real-time file size display with human-readable formatting

## Safety Features

The application includes comprehensive safety measures to prevent accidental deletion of important files:

### Pre-defined Safety Rules
The app includes built-in knowledge of macOS file system structure:
- System directories (`/System`, `/usr`, `/bin`) are marked as **red** (unsafe)
- User data directories (`~/Documents`, `~/Pictures`) are marked as **orange** (caution)
- Cache and temporary files are marked as **green** (safe)
- And many more predefined rules...

### AI Analysis
For unknown files and directories, the application can perform AI analysis to provide intelligent safety recommendations and explanations.

## Installation

### Option 1: From Source (Recommended for Development)

#### Prerequisites
- Python 3.10 or later
- Git

#### Setup Instructions

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-username/mac-cleaner.git
   cd mac-cleaner
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application:**
   ```bash
   python main.py
   ```
   
   Or use the virtual environment directly:
   ```bash
   venv/bin/python main.py
   ```

### Option 2: Standalone Application (Coming Soon)

A standalone `.app` bundle will be available for download from the releases page.

## Building from Source

To create a standalone application bundle:

1. **Make sure you're in the project directory with virtual environment activated:**
   ```bash
   source venv/bin/activate
   ```

2. **Run the build script:**
   ```bash
   chmod +x build.sh
   ./build.sh
   ```

3. **Find the built application:**
   The application will be created in `build/Mac Cleaner & Analyzer/Mac Cleaner & Analyzer.app`

## Development

### Code Style
This project follows these coding standards:
- **Formatter**: Black (88 character line length)
- **Linter**: Flake8
- **Configuration**: Settings stored in `pyproject.toml`

### Running Code Quality Checks

```bash
# Format code with Black
black .

# Check formatting
black --check .

# Run linting
flake8 .
```

### Project Structure
```
mac-cleaner/
├── main.py                 # Main application entry point
├── requirements.txt        # Python dependencies
├── build.sh               # Build script for creating .app bundle
├── pyproject.toml         # Code formatting and linting configuration
├── .github/workflows/     # CI/CD pipeline
├── GEMINI.md             # Project specification
└── README.md             # This file
```

## Technology Stack

- **GUI Framework**: [Flet](https://flet.dev/) - Modern Python UI framework
- **AI Integration**: Google Gemini API for intelligent file analysis
- **Build Tool**: PyInstaller for creating standalone applications
- **Multi-threading**: Concurrent file scanning with ThreadPoolExecutor
- **Target Platform**: macOS

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes following the coding standards
4. Run tests and code quality checks
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

### Development Guidelines

- Follow the specifications in `GEMINI.md`
- Maintain consistency with existing code style
- Add comments for complex logic
- Test your changes thoroughly
- Update documentation as needed

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Disclaimer

⚠️ **Important Safety Notice**: While this application includes comprehensive safety measures, always be cautious when deleting files. The AI analysis is for guidance only and should not be the sole basis for deletion decisions. Always verify before deleting important files, and ensure you have backups of critical data.

## Support

If you encounter any issues or have questions:
1. Check the existing [Issues](https://github.com/your-username/mac-cleaner/issues)
2. Create a new issue with detailed information about your problem
3. Include your macOS version and Python version in bug reports

## Roadmap

- [ ] Integration with actual Gemini API (currently simulated)
- [ ] More sophisticated file type recognition
- [ ] Scheduled cleaning capabilities
- [ ] Advanced filtering and search options
- [ ] Export scan results to CSV/JSON
- [ ] Integration with macOS Spotlight for enhanced file metadata

---

**Made with ❤️ for macOS users who want to keep their systems clean and organized.**
