"""
Format detection utilities
Auto-detect file formats and validate supported conversions
"""
import magic
from typing import Optional
from src.config.settings import CONVERSION_MATRIX, SUPPORTED_INPUT_FORMATS
from src.utils.file_utils import get_file_extension


def detect_format(filepath: str) -> Optional[str]:
    """
    Auto-detect file format from file extension and MIME type.
    
    Args:
        filepath: Path to file
        
    Returns:
        Detected format (lowercase) or None if unsupported
    """
    # First try by extension
    ext = get_file_extension(filepath)
    if ext in SUPPORTED_INPUT_FORMATS:
        return ext
    
    # Try using python-magic (libmagic) if available
    try:
        mime = magic.from_file(filepath, mime=True)
        format_map = {
            'application/pdf': 'pdf',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'docx',
            'application/msword': 'doc',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': 'xlsx',
            'application/vnd.ms-excel': 'xls',
            'text/plain': 'txt',
            'text/markdown': 'md',
            'text/html': 'html',
            'application/json': 'json',
            'application/xml': 'xml',
            'text/xml': 'xml',
            'text/csv': 'csv',
            'image/png': 'png',
            'image/jpeg': 'jpeg',
            'image/tiff': 'tiff',
            'image/bmp': 'bmp',
            'image/gif': 'gif',
            'image/webp': 'webp',
        }
        return format_map.get(mime)
    except Exception:
        # Failed to detect format via libmagic, fallback to extension
        pass
    
    return ext if ext in SUPPORTED_INPUT_FORMATS else None


def is_conversion_supported(input_format: str, output_format: str) -> bool:
    """
    Check if conversion from input to output format is supported.
    
    Args:
        input_format: Input file format
        output_format: Output file format
        
    Returns:
        True if conversion is supported
    """
    input_format = input_format.lower()
    output_format = output_format.lower()
    
    return output_format in CONVERSION_MATRIX.get(input_format, [])


def get_supported_conversions(input_format: str) -> list:
    """
    Get list of supported output formats for given input format.
    
    Args:
        input_format: Input file format
        
    Returns:
        List of supported output formats
    """
    return CONVERSION_MATRIX.get(input_format.lower(), [])


def validate_file_format(filepath: str, expected_format: Optional[str] = None) -> bool:
    """
    Validate that file format matches expected format.
    
    Args:
        filepath: Path to file
        expected_format: Expected format (if None, just checks if supported)
        
    Returns:
        True if valid
    """
    detected = detect_format(filepath)
    
    if detected is None:
        return False
    
    if expected_format is None:
        return True
    
    return detected == expected_format.lower()
