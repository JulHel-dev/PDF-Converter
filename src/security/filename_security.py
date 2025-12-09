"""
Filename Security Module

Sanitizes filenames to prevent security issues and ensure cross-platform compatibility.
"""

import os
import re
import unicodedata
from typing import Optional

try:
    from src.logging.event_monitor import EventMonitor
except ImportError:
    from logging.event_monitor import EventMonitor


class FilenameSecurityError(Exception):
    """Raised when a filename cannot be safely sanitized."""
    pass


# Windows reserved names
WINDOWS_RESERVED_NAMES = {
    'CON', 'PRN', 'AUX', 'NUL',
    'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
    'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
}

# Characters not allowed in filenames (Windows + Unix)
INVALID_CHARS = r'[<>:"/\\|?*\x00-\x1f]'

# Maximum filename length (most filesystems)
MAX_FILENAME_LENGTH = 255


def sanitize_filename(filename: str, replacement: str = '_', max_length: int = MAX_FILENAME_LENGTH) -> str:
    """
    Sanitize a filename to be safe across all platforms.
    
    This function:
    - Removes path separators
    - Removes invalid characters
    - Handles Windows reserved names
    - Normalizes Unicode
    - Truncates to maximum length
    - Prevents empty/hidden filenames
    
    Args:
        filename: The filename to sanitize
        replacement: Character to use for invalid characters
        max_length: Maximum filename length
        
    Returns:
        Sanitized filename
        
    Raises:
        FilenameSecurityError: If filename cannot be sanitized safely
    """
    if not filename:
        raise FilenameSecurityError("Empty filename provided")
    
    monitor = EventMonitor()
    original_filename = filename
    
    # Step 1: Unicode normalization (NFC form)
    filename = unicodedata.normalize('NFC', filename)
    
    # Step 2: Remove null bytes
    filename = filename.replace('\x00', '')
    
    # Step 3: Strip path components (security critical!)
    # Use multiple strategies to extract just the filename
    filename = filename.replace('\\', '/')  # Normalize separators
    if '/' in filename:
        filename = filename.split('/')[-1]  # Get last component
    
    # Step 4: Remove ".." sequences (path traversal prevention)
    filename = filename.replace('..', '')
    
    # Step 5: Remove/replace invalid characters
    filename = re.sub(INVALID_CHARS, replacement, filename)
    
    # Step 6: Remove control characters
    filename = ''.join(char for char in filename if ord(char) >= 32 or char in '\t\n')
    
    # Step 7: Remove leading/trailing dots and spaces (Windows compatibility)
    filename = filename.strip('. ')
    
    # Step 8: Handle Windows reserved names
    name_without_ext = os.path.splitext(filename)[0].upper()
    if name_without_ext in WINDOWS_RESERVED_NAMES:
        filename = replacement + filename
        monitor.log_event('reserved_filename_modified', {
            'original': original_filename,
            'sanitized': filename,
            'reason': 'Windows reserved name'
        }, severity='WARNING')
    
    # Step 9: Ensure filename is not empty or just extension
    if not filename or filename.startswith('.') or filename == replacement * len(filename):
        # If empty, only dots, or only replacement characters, provide a default
        filename = 'file' + (filename if filename.startswith('.') and len(filename) > 1 else '.txt')
        monitor.log_event('empty_filename_replaced', {
            'original': original_filename,
            'sanitized': filename
        }, severity='WARNING')
    
    # Step 11: Truncate to max length (preserve extension if possible)
    if len(filename) > max_length:
        name, ext = os.path.splitext(filename)
        if ext:
            # Keep extension, truncate name
            max_name_length = max_length - len(ext)
            filename = name[:max_name_length] + ext
        else:
            filename = filename[:max_length]
        
        monitor.log_event('filename_truncated', {
            'original': original_filename,
            'sanitized': filename,
            'original_length': len(original_filename),
            'new_length': len(filename)
        }, severity='INFO')
    
    # Step 12: Final validation
    if not filename or len(filename) == 0:
        raise FilenameSecurityError(f"Could not create valid filename from: {original_filename}")
    
    # Log if filename was modified
    if filename != original_filename:
        monitor.log_event('filename_sanitized', {
            'original': original_filename,
            'sanitized': filename
        }, severity='DEBUG')
    
    return filename


def is_filename_safe(filename: str) -> bool:
    """
    Check if a filename is safe without modifying it.
    
    Args:
        filename: The filename to check
        
    Returns:
        True if filename is safe, False otherwise
    """
    try:
        sanitized = sanitize_filename(filename)
        return sanitized == filename
    except FilenameSecurityError:
        return False


def validate_filename_or_raise(filename: str) -> str:
    """
    Validate and sanitize filename, raising exception if it cannot be made safe.
    
    Args:
        filename: The filename to validate
        
    Returns:
        Sanitized filename
        
    Raises:
        FilenameSecurityError: If filename cannot be sanitized
    """
    if not filename:
        raise FilenameSecurityError("Empty filename provided")
    
    sanitized = sanitize_filename(filename)
    
    if not sanitized:
        raise FilenameSecurityError(f"Could not sanitize filename: {filename}")
    
    return sanitized


def get_safe_filename(original_path: str, base_name: Optional[str] = None) -> str:
    """
    Extract and sanitize a filename from a path.
    
    Args:
        original_path: Original file path
        base_name: Optional base name to use instead of extracting from path
        
    Returns:
        Safe filename
    """
    if base_name:
        filename = base_name
    else:
        filename = os.path.basename(original_path)
    
    return sanitize_filename(filename)
