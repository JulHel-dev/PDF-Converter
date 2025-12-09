"""
Security module for PDF-Converter.
Contains all security-related validation functions.
"""

from .path_security import (
    PathValidator,
    PathSecurityError,
    is_path_safe,
    validate_path,
    safe_open,
    get_path_validator
)

from .size_security import (
    FileSizeValidator,
    FileSizeError,
    validate_file_size,
    get_size_validator
)

from .filename_security import (
    sanitize_filename,
    is_filename_safe,
    FilenameSecurityError
)

from .temp_file_security import (
    create_secure_temp_file,
    SecureTempFile,
    cleanup_temp_files
)

__all__ = [
    # Path security
    'PathValidator',
    'PathSecurityError',
    'is_path_safe',
    'validate_path',
    'safe_open',
    'get_path_validator',
    
    # Size security
    'FileSizeValidator',
    'FileSizeError',
    'validate_file_size',
    'get_size_validator',
    
    # Filename security
    'sanitize_filename',
    'is_filename_safe',
    'FilenameSecurityError',
    
    # Temp file security
    'create_secure_temp_file',
    'SecureTempFile',
    'cleanup_temp_files',
]
