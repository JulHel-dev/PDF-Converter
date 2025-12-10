"""
Input Validation Framework

Centralized validation for all user inputs to prevent injection attacks,
malformed data, and ensure data integrity.

References:
- OWASP Input Validation: https://cheatsheetseries.owasp.org/cheatsheets/Input_Validation_Cheat_Sheet.html
- CWE-20: Improper Input Validation
"""

import re
from typing import Any, Dict, List, Optional
from enum import Enum

try:
    from src.logging.event_monitor import EventMonitor
except ImportError:
    from logging.event_monitor import EventMonitor


class ValidationError(Exception):
    """Raised when input validation fails."""
    pass


class InputType(Enum):
    """Enumeration of supported input types for validation."""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    PATH = "path"
    EMAIL = "email"
    URL = "url"
    FORMAT = "format"
    DPI = "dpi"


class InputValidator:
    """
    Centralized input validation framework.
    
    Provides type checking, range validation, pattern matching,
    and sanitization for all user inputs.
    
    Usage:
        validator = InputValidator()
        
        # Validate a string
        safe_name = validator.validate_string(
            user_input,
            min_length=1,
            max_length=255,
            pattern=r'^[a-zA-Z0-9_-]+$'
        )
        
        # Validate a number
        safe_dpi = validator.validate_integer(
            dpi_input,
            min_value=72,
            max_value=300
        )
    """
    
    def __init__(self):
        self.monitor = EventMonitor()
        
        # Common regex patterns
        self.patterns = {
            'alphanumeric': r'^[a-zA-Z0-9]+$',
            'alphanumeric_extended': r'^[a-zA-Z0-9_\-\.]+$',
            'filename_safe': r'^[a-zA-Z0-9_\-\. ]+$',
            'format': r'^[a-z]{2,10}$',
            'email': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
            'url': r'^https?://[^\s<>"{}|\\^`\[\]]+$',
        }
    
    def validate_string(
        self,
        value: Any,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        pattern: Optional[str] = None,
        allowed_values: Optional[List[str]] = None,
        field_name: str = "input"
    ) -> str:
        """
        Validate and sanitize string input.
        
        Args:
            value: Input value to validate
            min_length: Minimum allowed length
            max_length: Maximum allowed length
            pattern: Regex pattern the string must match
            allowed_values: List of explicitly allowed values (whitelist)
            field_name: Name of the field (for logging)
            
        Returns:
            Validated string
            
        Raises:
            ValidationError: If validation fails
        """
        # Handle None
        if value is None:
            self.monitor.log_event('validation_none_value', {
                'field': field_name
            }, severity='WARNING')
            raise ValidationError(f"{field_name}: Cannot be None")
        
        # Type check
        if not isinstance(value, str):
            try:
                value = str(value)
            except Exception as e:
                self.monitor.log_event('validation_type_error', {
                    'field': field_name,
                    'expected': 'string',
                    'got': type(value).__name__,
                    'error': str(e)
                }, severity='WARNING')
                raise ValidationError(f"{field_name}: Must be a string")
        
        # Whitelist check (if provided)
        if allowed_values is not None:
            if value not in allowed_values:
                self.monitor.log_event('validation_whitelist_failed', {
                    'field': field_name,
                    'value': value,
                    'allowed': allowed_values
                }, severity='WARNING')
                raise ValidationError(
                    f"{field_name}: Value must be one of {allowed_values}"
                )
            return value
        
        # Length validation
        if min_length is not None and len(value) < min_length:
            self.monitor.log_event('validation_length_error', {
                'field': field_name,
                'length': len(value),
                'min_length': min_length
            }, severity='WARNING')
            raise ValidationError(
                f"{field_name}: Must be at least {min_length} characters"
            )
        
        if max_length is not None and len(value) > max_length:
            self.monitor.log_event('validation_length_error', {
                'field': field_name,
                'length': len(value),
                'max_length': max_length
            }, severity='WARNING')
            raise ValidationError(
                f"{field_name}: Must not exceed {max_length} characters"
            )
        
        # Pattern validation
        if pattern is not None:
            if not re.match(pattern, value):
                self.monitor.log_event('validation_pattern_failed', {
                    'field': field_name,
                    'value': value[:50],  # Log first 50 chars only
                    'pattern': pattern
                }, severity='WARNING')
                raise ValidationError(
                    f"{field_name}: Does not match required pattern"
                )
        
        return value
    
    def validate_integer(
        self,
        value: Any,
        min_value: Optional[int] = None,
        max_value: Optional[int] = None,
        field_name: str = "input"
    ) -> int:
        """
        Validate integer input.
        
        Args:
            value: Input value to validate
            min_value: Minimum allowed value
            max_value: Maximum allowed value
            field_name: Name of the field (for logging)
            
        Returns:
            Validated integer
            
        Raises:
            ValidationError: If validation fails
        """
        # Type conversion
        try:
            value = int(value)
        except (ValueError, TypeError) as e:
            self.monitor.log_event('validation_type_error', {
                'field': field_name,
                'expected': 'integer',
                'got': type(value).__name__,
                'value': str(value)
            }, severity='WARNING')
            raise ValidationError(f"{field_name}: Must be an integer")
        
        # Range validation
        if min_value is not None and value < min_value:
            self.monitor.log_event('validation_range_error', {
                'field': field_name,
                'value': value,
                'min_value': min_value
            }, severity='WARNING')
            raise ValidationError(
                f"{field_name}: Must be at least {min_value}"
            )
        
        if max_value is not None and value > max_value:
            self.monitor.log_event('validation_range_error', {
                'field': field_name,
                'value': value,
                'max_value': max_value
            }, severity='WARNING')
            raise ValidationError(
                f"{field_name}: Must not exceed {max_value}"
            )
        
        return value
    
    def validate_float(
        self,
        value: Any,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
        field_name: str = "input"
    ) -> float:
        """
        Validate float input.
        
        Args:
            value: Input value to validate
            min_value: Minimum allowed value
            max_value: Maximum allowed value
            field_name: Name of the field (for logging)
            
        Returns:
            Validated float
            
        Raises:
            ValidationError: If validation fails
        """
        try:
            value = float(value)
        except (ValueError, TypeError):
            raise ValidationError(f"{field_name}: Must be a number")
        
        if min_value is not None and value < min_value:
            raise ValidationError(f"{field_name}: Must be at least {min_value}")
        
        if max_value is not None and value > max_value:
            raise ValidationError(f"{field_name}: Must not exceed {max_value}")
        
        return value
    
    def validate_boolean(self, value: Any, field_name: str = "input") -> bool:
        """
        Validate boolean input.
        
        Accepts: True/False, 1/0, "true"/"false", "yes"/"no", "on"/"off"
        
        Args:
            value: Input value to validate
            field_name: Name of the field (for logging)
            
        Returns:
            Validated boolean
            
        Raises:
            ValidationError: If validation fails
        """
        if isinstance(value, bool):
            return value
        
        if isinstance(value, (int, float)):
            return bool(value)
        
        if isinstance(value, str):
            lower = value.lower().strip()
            if lower in ('true', 'yes', 'on', '1'):
                return True
            if lower in ('false', 'no', 'off', '0', ''):
                return False
        
        raise ValidationError(f"{field_name}: Must be a boolean value")
    
    def validate_format(self, value: Any, field_name: str = "format") -> str:
        """
        Validate file format string.
        
        Args:
            value: Format string (e.g., "pdf", "docx", "PDF", "DOCX")
            field_name: Name of the field (for logging)
            
        Returns:
            Validated format string (lowercase)
            
        Raises:
            ValidationError: If validation fails
        """
        # Convert to lowercase first
        if isinstance(value, str):
            value = value.lower()
        
        format_str = self.validate_string(
            value,
            min_length=2,
            max_length=10,
            pattern=self.patterns['format'],
            field_name=field_name
        )
        return format_str.lower()
    
    def validate_dpi(self, value: Any, field_name: str = "dpi") -> int:
        """
        Validate DPI (dots per inch) value.
        
        Common DPI values: 72 (screen), 150 (draft), 300 (standard), 600 (high quality)
        
        Args:
            value: DPI value
            field_name: Name of the field (for logging)
            
        Returns:
            Validated DPI
            
        Raises:
            ValidationError: If validation fails
        """
        return self.validate_integer(
            value,
            min_value=72,
            max_value=2400,
            field_name=field_name
        )
    
    def validate_quality(self, value: Any, field_name: str = "quality") -> int:
        """
        Validate quality percentage (0-100).
        
        Args:
            value: Quality value
            field_name: Name of the field (for logging)
            
        Returns:
            Validated quality
            
        Raises:
            ValidationError: If validation fails
        """
        return self.validate_integer(
            value,
            min_value=0,
            max_value=100,
            field_name=field_name
        )
    
    def validate_dict(
        self,
        value: Any,
        required_keys: Optional[List[str]] = None,
        field_name: str = "input"
    ) -> Dict:
        """
        Validate dictionary input.
        
        Args:
            value: Input value to validate
            required_keys: List of required keys
            field_name: Name of the field (for logging)
            
        Returns:
            Validated dictionary
            
        Raises:
            ValidationError: If validation fails
        """
        if not isinstance(value, dict):
            raise ValidationError(f"{field_name}: Must be a dictionary")
        
        if required_keys:
            missing = set(required_keys) - set(value.keys())
            if missing:
                raise ValidationError(
                    f"{field_name}: Missing required keys: {missing}"
                )
        
        return value
    
    def sanitize_html(self, value: str) -> str:
        """
        Sanitize HTML input to prevent XSS attacks.
        
        This is a basic sanitizer - for production use, consider
        a library like bleach or html5lib.
        
        Args:
            value: HTML string to sanitize
            
        Returns:
            Sanitized HTML string
        """
        # Remove script tags
        value = re.sub(r'<script[^>]*>.*?</script>', '', value, flags=re.IGNORECASE | re.DOTALL)
        
        # Remove event handlers
        value = re.sub(r'\s+on\w+\s*=\s*["\'][^"\']*["\']', '', value, flags=re.IGNORECASE)
        
        # Remove javascript: URLs
        value = re.sub(r'javascript:', '', value, flags=re.IGNORECASE)
        
        return value


# Global validator instance
_input_validator = None

def get_input_validator() -> InputValidator:
    """Get the global InputValidator instance."""
    global _input_validator
    if _input_validator is None:
        _input_validator = InputValidator()
    return _input_validator


# Convenience functions
def validate_string(value: Any, **kwargs) -> str:
    """Validate string input."""
    return get_input_validator().validate_string(value, **kwargs)


def validate_integer(value: Any, **kwargs) -> int:
    """Validate integer input."""
    return get_input_validator().validate_integer(value, **kwargs)


def validate_float(value: Any, **kwargs) -> float:
    """Validate float input."""
    return get_input_validator().validate_float(value, **kwargs)


def validate_boolean(value: Any, **kwargs) -> bool:
    """Validate boolean input."""
    return get_input_validator().validate_boolean(value, **kwargs)


def validate_format(value: Any, **kwargs) -> str:
    """Validate file format."""
    return get_input_validator().validate_format(value, **kwargs)


def validate_dpi(value: Any, **kwargs) -> int:
    """Validate DPI value."""
    return get_input_validator().validate_dpi(value, **kwargs)
