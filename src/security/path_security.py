"""
Path Security Module for PDF-Converter

Prevents path traversal attacks by validating all file paths
against allowed base directories before any I/O operation.

References:
- OWASP Path Traversal: https://owasp.org/www-community/attacks/Path_Traversal
- CWE-22: https://cwe.mitre.org/data/definitions/22.html
"""

import os
import sys
import unicodedata
from typing import List, Optional

# Import will work with current logging module name
try:
    from src.logging.event_monitor import EventMonitor
except ImportError:
    from logging.event_monitor import EventMonitor

try:
    from src.config.settings import BASE_DIR
except ImportError:
    from config.settings import BASE_DIR


class PathSecurityError(Exception):
    """Raised when a path security violation is detected."""
    pass


class PathValidator:
    """
    Centralized path validation for all file operations.
    
    Usage:
        validator = PathValidator()
        
        # Validate before any file operation
        if validator.is_safe(user_path):
            with open(user_path, 'r') as f:
                ...
        else:
            raise PathSecurityError(f"Blocked: {user_path}")
    
    Or use the decorator:
        @validator.require_safe_path
        def read_file(path: str) -> str:
            ...
    """
    
    def __init__(self, allowed_bases: Optional[List[str]] = None):
        """
        Initialize the path validator.
        
        Args:
            allowed_bases: List of allowed base directories.
                          Defaults to dynamically determined folders from settings.
        """
        self.monitor = EventMonitor()
        
        # If no allowed bases provided, use default folders from settings
        if allowed_bases is None:
            # Dynamically get folders from settings
            try:
                from src.config.settings import LOG_FOLDER, INPUT_FOLDER, OUTPUT_FOLDER
                self.allowed_bases = [LOG_FOLDER, INPUT_FOLDER, OUTPUT_FOLDER]
                
                # Add temp folder if it exists in settings
                try:
                    from src.config.settings import TMP_FOLDER
                    self.allowed_bases.append(TMP_FOLDER)
                except (ImportError, AttributeError):
                    # TMP_FOLDER not yet in settings, use default
                    tmp_folder = os.path.join(BASE_DIR, "Temp")
                    self.allowed_bases.append(tmp_folder)
                
                # Add system temp directory for testing and temporary operations
                import tempfile
                system_temp = tempfile.gettempdir()
                self.allowed_bases.append(system_temp)
                
            except ImportError:
                # Fallback to BASE_DIR if settings not available
                self.allowed_bases = [BASE_DIR]
        else:
            self.allowed_bases = allowed_bases
        
        # Pre-compute canonical forms of allowed bases
        self._canonical_bases = []
        for base in self.allowed_bases:
            try:
                canonical = self._canonicalize(base)
                self._canonical_bases.append(canonical)
            except Exception as e:
                self.monitor.log_event('path_validator_init_warning', {
                    'base': str(base),
                    'error': str(e)
                }, severity='WARNING')
    
    def _canonicalize(self, path: str) -> str:
        """
        Convert path to canonical form.
        
        This resolves:
        - Relative paths (../, ./)
        - Symlinks
        - Case normalization (Windows)
        - Unicode normalization
        """
        # Step 1: Unicode normalization (NFC form)
        # Prevents attacks using different Unicode representations
        normalized = unicodedata.normalize('NFC', str(path))
        
        # Step 2: Remove null bytes (prevents null byte injection)
        normalized = normalized.replace('\x00', '')
        
        # Step 3: Convert to absolute path
        absolute = os.path.abspath(normalized)
        
        # Step 4: Resolve all symlinks
        real = os.path.realpath(absolute)
        
        # Step 5: Normalize case on Windows
        if sys.platform == 'win32':
            real = os.path.normcase(real)
        
        return real
    
    def _normalize_for_comparison(self, path: str) -> str:
        """Normalize path for safe comparison."""
        canonical = self._canonicalize(path)
        
        # Ensure consistent trailing separator handling
        if os.path.isdir(canonical) and not canonical.endswith(os.sep):
            canonical += os.sep
        
        return canonical
    
    def is_within_base(self, path: str, base: str) -> bool:
        """
        Check if path is within the given base directory.
        
        This is more robust than simple string prefix checking
        because it handles edge cases like:
        - /allowed/path vs /allowed/pathevil
        - Symlinks pointing outside
        - Case sensitivity differences
        """
        try:
            canonical_path = self._canonicalize(path)
            canonical_base = self._canonicalize(base)
            
            # Ensure base ends with separator to prevent prefix attacks
            if not canonical_base.endswith(os.sep):
                canonical_base += os.sep
            
            # Check if path starts with base
            # Also allow exact match (path == base without trailing sep)
            return (canonical_path + os.sep).startswith(canonical_base) or \
                   canonical_path == canonical_base.rstrip(os.sep)
                   
        except Exception:
            return False
    
    def is_safe(self, path: str, operation: str = 'access') -> bool:
        """
        Validate that a path is safe to use.
        
        Args:
            path: The path to validate
            operation: Description of the operation (for logging)
            
        Returns:
            True if path is within allowed directories, False otherwise
        """
        if not path:
            self.monitor.log_event('path_validation_failed', {
                'path': '<empty>',
                'reason': 'Empty path provided',
                'operation': operation
            }, severity='WARNING')
            return False
        
        try:
            canonical_path = self._canonicalize(path)
            
            # Check against each allowed base
            for base in self._canonical_bases:
                if self.is_within_base(canonical_path, base):
                    # Log successful validation at DEBUG level
                    self.monitor.log_event('path_validation_passed', {
                        'path': path,
                        'canonical': canonical_path,
                        'matched_base': base,
                        'operation': operation
                    }, severity='DEBUG')
                    return True
            
            # Path is outside all allowed bases - SECURITY VIOLATION
            self.monitor.log_event('path_traversal_blocked', {
                'path': path,
                'canonical_path': canonical_path,
                'allowed_bases': self._canonical_bases,
                'operation': operation,
                'threat_type': 'PATH_TRAVERSAL'
            }, severity='CRITICAL')
            
            return False
            
        except Exception as e:
            self.monitor.log_event('path_validation_error', {
                'path': path,
                'error': str(e),
                'error_type': type(e).__name__,
                'operation': operation
            }, severity='ERROR')
            return False
    
    def validate_or_raise(self, path: str, operation: str = 'access') -> str:
        """
        Validate path and raise exception if invalid.
        
        Args:
            path: The path to validate
            operation: Description of the operation
            
        Returns:
            The canonical (safe) path
            
        Raises:
            PathSecurityError: If path is outside allowed directories
        """
        if not self.is_safe(path, operation):
            raise PathSecurityError(
                f"Security violation: Path '{path}' is outside allowed directories. "
                f"Operation '{operation}' blocked."
            )
        return self._canonicalize(path)
    
    def require_safe_path(self, func):
        """
        Decorator to require safe paths for function arguments.
        
        Assumes the first argument is a path to validate.
        
        Usage:
            @validator.require_safe_path
            def read_file(path: str) -> str:
                with open(path, 'r') as f:
                    return f.read()
        """
        from functools import wraps
        
        @wraps(func)
        def wrapper(path, *args, **kwargs):
            safe_path = self.validate_or_raise(path, operation=func.__name__)
            return func(safe_path, *args, **kwargs)
        
        return wrapper
    
    def get_safe_path(self, path: str, base_folder: str) -> Optional[str]:
        """
        Construct a safe path within the given base folder.
        
        This is useful for constructing output paths from user input.
        
        Args:
            path: The user-provided path or filename
            base_folder: The base folder to use
            
        Returns:
            A safe canonical path, or None if construction failed
        """
        try:
            # Extract just the filename (strip any directory components)
            filename = os.path.basename(path)
            
            # Sanitize the filename (call to S3 sanitization)
            try:
                from src.security.filename_security import sanitize_filename
                safe_filename = sanitize_filename(filename)
            except ImportError:
                # Fallback: basic sanitization
                safe_filename = filename.replace('..', '').replace('/', '').replace('\\', '')
            
            # Construct full path within base
            full_path = os.path.join(base_folder, safe_filename)
            
            # Validate the constructed path
            if self.is_safe(full_path):
                return self._canonicalize(full_path)
            
            return None
            
        except Exception as e:
            self.monitor.log_event('safe_path_construction_failed', {
                'path': path,
                'base_folder': base_folder,
                'error': str(e)
            }, severity='ERROR')
            return None


# Global validator instance
_path_validator = None

def get_path_validator() -> PathValidator:
    """Get the global PathValidator instance."""
    global _path_validator
    if _path_validator is None:
        _path_validator = PathValidator()
    return _path_validator


# Convenience functions
def is_path_safe(path: str, operation: str = 'access') -> bool:
    """Check if a path is safe to access."""
    return get_path_validator().is_safe(path, operation)


def validate_path(path: str, operation: str = 'access') -> str:
    """Validate path and return canonical form, or raise exception."""
    return get_path_validator().validate_or_raise(path, operation)


def safe_open(path: str, mode: str = 'r', **kwargs):
    """
    Safely open a file after validating the path.
    
    This is a drop-in replacement for open() with security validation.
    """
    operation = 'read' if 'r' in mode else 'write'
    safe_path = validate_path(path, operation)
    return open(safe_path, mode, **kwargs)
