"""
Application Settings and Configuration
Handles folder paths, conversion matrix, and runtime settings
"""
import os
import sys

def get_base_path():
    """Get correct base path for both .py script and .exe executable."""
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        return os.path.dirname(sys.executable)
    else:
        # Running as Python script
        base = os.path.dirname(os.path.abspath(__file__))
        return os.path.dirname(os.path.dirname(base))  # Go up to project root

BASE_DIR = get_base_path()

# Folder paths
LOG_FOLDER = os.path.join(BASE_DIR, "Log")
INPUT_FOLDER = os.path.join(BASE_DIR, "Input")
OUTPUT_FOLDER = os.path.join(BASE_DIR, "Output")
TMP_FOLDER = os.path.join(BASE_DIR, "Temp")

def ensure_folders_exist():
    """Create required folders if they don't exist (critical for .exe distribution)."""
    required_folders = [
        LOG_FOLDER,
        os.path.join(LOG_FOLDER, 'diagnostics'),
        INPUT_FOLDER,
        OUTPUT_FOLDER,
        TMP_FOLDER,
    ]
    for folder in required_folders:
        os.makedirs(folder, exist_ok=True)

# Supported format conversion matrix
CONVERSION_MATRIX = {
    'pdf': ['txt', 'md', 'docx', 'html', 'png', 'jpeg'],
    'docx': ['pdf', 'txt', 'md', 'html'],
    'doc': ['pdf', 'txt', 'md', 'html', 'docx'],
    'xlsx': ['csv', 'json', 'txt', 'pdf'],
    'xls': ['csv', 'json', 'txt', 'pdf', 'xlsx'],
    'csv': ['xlsx', 'json', 'txt', 'pdf'],
    'txt': ['md', 'html', 'pdf', 'docx'],
    'md': ['html', 'txt', 'pdf', 'docx'],
    'html': ['md', 'txt', 'pdf'],
    'json': ['yaml', 'xml', 'csv', 'txt'],
    'yaml': ['json', 'xml', 'txt'],
    'yml': ['json', 'xml', 'txt'],
    'xml': ['json', 'yaml', 'txt'],
    'png': ['jpeg', 'pdf', 'webp', 'tiff', 'bmp'],
    'jpeg': ['png', 'pdf', 'webp', 'tiff', 'bmp'],
    'jpg': ['png', 'pdf', 'webp', 'tiff', 'bmp'],
    'tiff': ['png', 'jpeg', 'pdf', 'webp', 'bmp'],
    'tif': ['png', 'jpeg', 'pdf', 'webp', 'bmp'],
    'bmp': ['png', 'jpeg', 'pdf', 'webp', 'tiff'],
    'gif': ['png', 'jpeg', 'pdf', 'webp'],
    'webp': ['png', 'jpeg', 'pdf', 'tiff'],
    'rtf': ['txt', 'docx', 'pdf', 'html'],
    'odt': ['docx', 'pdf', 'txt', 'html'],
    'ods': ['xlsx', 'csv', 'pdf'],
    'ppt': ['pdf', 'txt'],
    'pptx': ['pdf', 'txt'],
}

# Rendering settings
DEFAULT_DPI = 150
IMAGE_QUALITY = 95

# Security settings
MAX_FILE_SIZE_MB = 100  # Maximum file size in megabytes
FILE_SIZE_WARN_MB = 50  # Warn threshold (log warning but allow)

# Batch processing settings
BATCH_MAX_CONCURRENT = 4  # Maximum concurrent batch conversion workers
BATCH_MEMORY_LIMIT_MB = 2000  # Pause batch if memory exceeds this (2GB)
BATCH_CHECKPOINT_INTERVAL = 10  # Save progress every N files

# Security: Allowed base folders for file operations
# CRITICAL: Only paths within these folders are permitted
ALLOWED_BASE_FOLDERS = [
    LOG_FOLDER,
    INPUT_FOLDER,
    OUTPUT_FOLDER,
    TMP_FOLDER,
]

# UI settings
WINDOW_TITLE = "Universal File Converter"
APP_VERSION = "2.0.0"  # Phase 2: Security & Robustness Complete
APP_BUILD_DATE = "2025-12-09"

# Version information logged on startup
def log_version_info():
    """Log version information on application startup."""
    try:
        from src.logging.event_monitor import EventMonitor
        monitor = EventMonitor()
        monitor.log_event('application_startup', {
            'version': APP_VERSION,
            'build_date': APP_BUILD_DATE,
            'python_version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            'platform': sys.platform
        }, severity='INFO')
    except Exception:
        # Ignore errors during version logging (EventMonitor may not be available)
        pass

# Supported input formats (all formats from conversion matrix)
SUPPORTED_INPUT_FORMATS = list(CONVERSION_MATRIX.keys())

def get_supported_output_formats(input_format: str):
    """Get list of supported output formats for a given input format."""
    return CONVERSION_MATRIX.get(input_format.lower(), [])
