"""
Temporary File Security Module

Provides secure temporary file creation with proper permissions and automatic cleanup.
"""

import os
import sys
import tempfile
import atexit
from typing import Optional, List

try:
    from src.logging.event_monitor import EventMonitor
except ImportError:
    from logging.event_monitor import EventMonitor

try:
    from src.config.settings import BASE_DIR
except ImportError:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))


# Global list of temp files to clean up
_temp_files: List[str] = []
_cleanup_registered = False


def _cleanup_all_temp_files():
    """Clean up all temporary files on exit."""
    monitor = EventMonitor()
    
    for temp_file in _temp_files:
        try:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
                monitor.log_event('temp_file_cleaned', {
                    'file': temp_file
                }, severity='DEBUG')
        except Exception as e:
            monitor.log_event('temp_file_cleanup_failed', {
                'file': temp_file,
                'error': str(e)
            }, severity='WARNING')


def _register_cleanup():
    """Register cleanup handler on first use."""
    global _cleanup_registered
    if not _cleanup_registered:
        atexit.register(_cleanup_all_temp_files)
        _cleanup_registered = True


class SecureTempFile:
    """
    Context manager for secure temporary files.
    
    Usage:
        with SecureTempFile(suffix='.pdf') as temp_file:
            # Use temp_file.path
            with open(temp_file.path, 'wb') as f:
                f.write(data)
        # File is automatically cleaned up
    """
    
    def __init__(self, suffix: str = '', prefix: str = 'pdfconv_', 
                 dir: Optional[str] = None, keep: bool = False):
        """
        Initialize secure temp file.
        
        Args:
            suffix: File suffix (e.g., '.pdf')
            prefix: File prefix
            dir: Directory for temp file (defaults to system temp)
            keep: If True, don't auto-delete on exit
        """
        self.suffix = suffix
        self.prefix = prefix
        self.dir = dir
        self.keep = keep
        self.path: Optional[str] = None
        self.fd: Optional[int] = None
        self.monitor = EventMonitor()
    
    def __enter__(self):
        """Create the temp file with secure permissions."""
        _register_cleanup()
        
        # Create temp file with restricted permissions (owner read/write only)
        # This prevents other users from accessing sensitive data
        try:
            self.fd, self.path = tempfile.mkstemp(
                suffix=self.suffix,
                prefix=self.prefix,
                dir=self.dir
            )
            
            # Set restrictive permissions (0o600 = owner read/write only)
            # On Windows, this is best-effort as permissions work differently
            if sys.platform != 'win32':
                os.chmod(self.path, 0o600)
            
            # Add to cleanup list if not keeping
            if not self.keep:
                _temp_files.append(self.path)
            
            self.monitor.log_event('temp_file_created', {
                'path': self.path,
                'suffix': self.suffix,
                'keep': self.keep
            }, severity='DEBUG')
            
            return self
            
        except Exception as e:
            self.monitor.log_event('temp_file_creation_failed', {
                'suffix': self.suffix,
                'error': str(e)
            }, severity='ERROR')
            raise
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Close and optionally delete the temp file."""
        try:
            # Close file descriptor if still open
            if self.fd is not None:
                try:
                    os.close(self.fd)
                except OSError:
                    pass  # Already closed
                self.fd = None
            
            # Delete file if not keeping
            if not self.keep and self.path and os.path.exists(self.path):
                try:
                    os.unlink(self.path)
                    if self.path in _temp_files:
                        _temp_files.remove(self.path)
                    
                    self.monitor.log_event('temp_file_deleted', {
                        'path': self.path
                    }, severity='DEBUG')
                except Exception as e:
                    self.monitor.log_event('temp_file_deletion_failed', {
                        'path': self.path,
                        'error': str(e)
                    }, severity='WARNING')
        except Exception as e:
            self.monitor.log_event('temp_file_cleanup_error', {
                'error': str(e)
            }, severity='WARNING')
    
    def write_bytes(self, data: bytes):
        """Write bytes to the temp file."""
        if not self.path:
            raise RuntimeError("Temp file not created")
        
        with open(self.path, 'wb') as f:
            f.write(data)
    
    def write_text(self, text: str, encoding: str = 'utf-8'):
        """Write text to the temp file."""
        if not self.path:
            raise RuntimeError("Temp file not created")
        
        with open(self.path, 'w', encoding=encoding) as f:
            f.write(text)
    
    def read_bytes(self) -> bytes:
        """Read bytes from the temp file."""
        if not self.path:
            raise RuntimeError("Temp file not created")
        
        with open(self.path, 'rb') as f:
            return f.read()
    
    def read_text(self, encoding: str = 'utf-8') -> str:
        """Read text from the temp file."""
        if not self.path:
            raise RuntimeError("Temp file not created")
        
        with open(self.path, 'r', encoding=encoding) as f:
            return f.read()


def create_secure_temp_file(suffix: str = '', prefix: str = 'pdfconv_', 
                            dir: Optional[str] = None) -> str:
    """
    Create a secure temporary file and return its path.
    
    The file is created with restricted permissions and registered for cleanup.
    
    Args:
        suffix: File suffix (e.g., '.pdf')
        prefix: File prefix
        dir: Directory for temp file
        
    Returns:
        Path to the created temp file
    """
    _register_cleanup()
    monitor = EventMonitor()
    
    try:
        fd, path = tempfile.mkstemp(suffix=suffix, prefix=prefix, dir=dir)
        
        # Set restrictive permissions
        if sys.platform != 'win32':
            os.chmod(path, 0o600)
        
        # Close the file descriptor (caller will open it themselves)
        os.close(fd)
        
        # Register for cleanup
        _temp_files.append(path)
        
        monitor.log_event('temp_file_created', {
            'path': path,
            'suffix': suffix
        }, severity='DEBUG')
        
        return path
        
    except Exception as e:
        monitor.log_event('temp_file_creation_failed', {
            'suffix': suffix,
            'error': str(e)
        }, severity='ERROR')
        raise


def create_secure_temp_dir(prefix: str = 'pdfconv_', dir: Optional[str] = None) -> str:
    """
    Create a secure temporary directory and return its path.
    
    Args:
        prefix: Directory prefix
        dir: Parent directory
        
    Returns:
        Path to the created temp directory
    """
    _register_cleanup()
    monitor = EventMonitor()
    
    try:
        path = tempfile.mkdtemp(prefix=prefix, dir=dir)
        
        # Set restrictive permissions
        if sys.platform != 'win32':
            os.chmod(path, 0o700)
        
        # Register for cleanup
        _temp_files.append(path)
        
        monitor.log_event('temp_dir_created', {
            'path': path
        }, severity='DEBUG')
        
        return path
        
    except Exception as e:
        monitor.log_event('temp_dir_creation_failed', {
            'error': str(e)
        }, severity='ERROR')
        raise


def cleanup_temp_files():
    """Manually trigger cleanup of all temporary files."""
    _cleanup_all_temp_files()
    _temp_files.clear()
