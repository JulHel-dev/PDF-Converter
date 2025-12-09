"""
File Size Security Module

Prevents denial-of-service attacks via oversized files.
"""

import os
from typing import Optional, Union
from pathlib import Path

try:
    from src.logging.event_monitor import EventMonitor
except ImportError:
    from logging.event_monitor import EventMonitor

try:
    from src.config.settings import MAX_FILE_SIZE_MB
except (ImportError, AttributeError):
    # Default if not in settings yet
    MAX_FILE_SIZE_MB = 100


class FileSizeError(Exception):
    """Raised when a file exceeds the maximum allowed size."""
    def __init__(self, path: str, size_mb: float, max_mb: float):
        self.path = path
        self.size_mb = size_mb
        self.max_mb = max_mb
        super().__init__(
            f"File '{path}' ({size_mb:.2f} MB) exceeds maximum "
            f"allowed size ({max_mb} MB)"
        )


class FileSizeValidator:
    """
    Validates file sizes against configured limits.
    
    Usage:
        validator = FileSizeValidator()
        
        if validator.is_valid(file_path):
            process_file(file_path)
        else:
            handle_oversized_file(file_path)
    """
    
    def __init__(self, max_mb: Optional[float] = None):
        """
        Initialize the validator.
        
        Args:
            max_mb: Maximum file size in megabytes.
                   Defaults to MAX_FILE_SIZE_MB from settings.
        """
        self.monitor = EventMonitor()
        self.max_mb = max_mb if max_mb is not None else MAX_FILE_SIZE_MB
    
    def get_size_mb(self, path: Union[str, Path]) -> float:
        """Get file size in megabytes."""
        try:
            size_bytes = os.path.getsize(str(path))
            return size_bytes / (1024 * 1024)
        except OSError as e:
            self.monitor.log_event('file_size_check_failed', {
                'path': str(path),
                'error': str(e)
            }, severity='WARNING')
            raise
    
    def is_valid(self, path: Union[str, Path], max_mb: Optional[float] = None) -> bool:
        """
        Check if file size is within limits.
        
        Args:
            path: Path to the file
            max_mb: Override maximum size for this check
            
        Returns:
            True if file is within size limit
        """
        limit = max_mb if max_mb is not None else self.max_mb
        
        try:
            size_mb = self.get_size_mb(path)
            
            if size_mb > limit:
                self.monitor.log_event('file_too_large', {
                    'file': str(path),
                    'size_mb': round(size_mb, 2),
                    'max_mb': limit,
                    'excess_mb': round(size_mb - limit, 2)
                }, severity='ERROR')
                return False
            
            self.monitor.log_event('file_size_valid', {
                'file': str(path),
                'size_mb': round(size_mb, 2),
                'max_mb': limit
            }, severity='DEBUG')
            return True
            
        except OSError:
            return False
    
    def validate_or_raise(self, path: Union[str, Path], max_mb: Optional[float] = None) -> float:
        """
        Validate file size and raise exception if too large.
        
        Returns:
            The file size in MB if valid
            
        Raises:
            FileSizeError: If file exceeds limit
        """
        limit = max_mb if max_mb is not None else self.max_mb
        size_mb = self.get_size_mb(path)
        
        if size_mb > limit:
            raise FileSizeError(str(path), size_mb, limit)
        
        return size_mb
    
    def validate_upload(self, file_obj, filename: str, max_mb: Optional[float] = None) -> bool:
        """
        Validate an uploaded file object (e.g., from Streamlit or Flask).
        
        For file objects that support seek/tell, this checks actual content size.
        
        Args:
            file_obj: File-like object with read/seek/tell
            filename: Original filename (for logging)
            max_mb: Override maximum size
            
        Returns:
            True if upload is within limits
        """
        limit = max_mb if max_mb is not None else self.max_mb
        
        try:
            # Get file size by seeking to end
            current_pos = file_obj.tell()
            file_obj.seek(0, 2)  # Seek to end
            size_bytes = file_obj.tell()
            file_obj.seek(current_pos)  # Restore position
            
            size_mb = size_bytes / (1024 * 1024)
            
            if size_mb > limit:
                self.monitor.log_event('upload_too_large', {
                    'filename': filename,
                    'size_mb': round(size_mb, 2),
                    'max_mb': limit
                }, severity='ERROR')
                return False
            
            return True
            
        except Exception as e:
            self.monitor.log_event('upload_size_check_failed', {
                'filename': filename,
                'error': str(e)
            }, severity='WARNING')
            return False


# Global instance
_size_validator = None

def get_size_validator() -> FileSizeValidator:
    """Get the global FileSizeValidator instance."""
    global _size_validator
    if _size_validator is None:
        _size_validator = FileSizeValidator()
    return _size_validator


def validate_file_size(path: Union[str, Path], max_mb: Optional[float] = None) -> bool:
    """Convenience function to validate file size."""
    return get_size_validator().is_valid(path, max_mb)
