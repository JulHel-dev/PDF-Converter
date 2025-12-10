"""
Color themes and styling constants for Tkinter UI.
"""

# Light Theme
THEME_LIGHT = {
    'bg_primary': '#FFFFFF',
    'bg_secondary': '#F5F5F5',
    'bg_tertiary': '#E8E8E8',
    'fg_primary': '#1A1A1A',
    'fg_secondary': '#666666',
    'accent': '#0066CC',
    'accent_hover': '#0052A3',
    'success': '#28A745',
    'success_text': '#FFFFFF',
    'warning': '#FFC107',
    'warning_text': '#000000',
    'error': '#DC3545',
    'error_text': '#FFFFFF',
    'border': '#CCCCCC',
    'canvas_bg': '#E8E8E8',
    'log_bg': '#1E1E1E',
    'log_fg': '#FFFFFF',
}

# Dark Theme
THEME_DARK = {
    'bg_primary': '#1E1E1E',
    'bg_secondary': '#252526',
    'bg_tertiary': '#333333',
    'fg_primary': '#FFFFFF',
    'fg_secondary': '#AAAAAA',
    'accent': '#0078D4',
    'accent_hover': '#1084D8',
    'success': '#4CAF50',
    'success_text': '#FFFFFF',
    'warning': '#FF9800',
    'warning_text': '#000000',
    'error': '#F44336',
    'error_text': '#FFFFFF',
    'border': '#444444',
    'canvas_bg': '#2D2D2D',
    'log_bg': '#1E1E1E',
    'log_fg': '#FFFFFF',
}

# Platform-specific font specifications with fallbacks
import platform

_system = platform.system()

if _system == 'Darwin':  # macOS
    FONTS = {
        'heading': ('SF Pro Display', 14, 'bold'),
        'subheading': ('SF Pro Display', 11, 'bold'),
        'body': ('SF Pro Text', 10),
        'small': ('SF Pro Text', 9),
        'monospace': ('Menlo', 10),
    }
elif _system == 'Linux':
    FONTS = {
        'heading': ('Ubuntu', 14, 'bold'),
        'subheading': ('Ubuntu', 11, 'bold'),
        'body': ('Ubuntu', 10),
        'small': ('Ubuntu', 9),
        'monospace': ('Ubuntu Mono', 10),
    }
else:  # Windows and others
    FONTS = {
        'heading': ('Segoe UI', 14, 'bold'),
        'subheading': ('Segoe UI', 11, 'bold'),
        'body': ('Segoe UI', 10),
        'small': ('Segoe UI', 9),
        'monospace': ('Consolas', 10),
    }

# Icons (Unicode/Emoji - work on all platforms)
ICONS = {
    'file': '📄',
    'folder': '📁',
    'folder_open': '📂',
    'convert': '🔄',
    'rocket': '🚀',
    'success': '✅',
    'error': '❌',
    'warning': '⚠️',
    'info': 'ℹ️',
    'settings': '⚙️',
    'export': '📥',
    'clear': '🗑️',
    'zoom_in': '➕',
    'zoom_out': '➖',
    'prev': '◀',
    'next': '▶',
    'pdf': '📕',
    'image': '🖼️',
    'document': '📝',
    'spreadsheet': '📊',
    'eye': '👁️',
    'log': '📋',
    'history': '📜',
}

# Log severity colors (for text widget tags)
LOG_COLORS = {
    'INFO': '#4CAF50',      # Green
    'WARNING': '#FFC107',   # Yellow/Amber
    'ERROR': '#DC3545',     # Red
    'CRITICAL': '#FF0000',  # Bright Red
    'DEBUG': '#888888',     # Gray
}
