"""Tests for input validation framework."""

import pytest
from src.security.input_validation import (
    InputValidator,
    ValidationError,
    validate_string,
    validate_integer,
    validate_float,
    validate_boolean,
    validate_format,
    validate_dpi
)


class TestStringValidation:
    """Test string validation."""
    
    def test_valid_string(self):
        """Test valid string passes."""
        validator = InputValidator()
        result = validator.validate_string("test", field_name="test_field")
        assert result == "test"
    
    def test_min_length(self):
        """Test minimum length validation."""
        validator = InputValidator()
        
        # Should pass
        result = validator.validate_string("abc", min_length=3)
        assert result == "abc"
        
        # Should fail
        with pytest.raises(ValidationError) as exc:
            validator.validate_string("ab", min_length=3)
        assert "at least 3" in str(exc.value)
    
    def test_max_length(self):
        """Test maximum length validation."""
        validator = InputValidator()
        
        # Should pass
        result = validator.validate_string("ab", max_length=3)
        assert result == "ab"
        
        # Should fail
        with pytest.raises(ValidationError):
            validator.validate_string("abcd", max_length=3)
    
    def test_pattern_validation(self):
        """Test pattern matching."""
        validator = InputValidator()
        
        # Alphanumeric pattern
        result = validator.validate_string(
            "test123",
            pattern=r'^[a-zA-Z0-9]+$'
        )
        assert result == "test123"
        
        # Should fail with special chars
        with pytest.raises(ValidationError):
            validator.validate_string(
                "test@123",
                pattern=r'^[a-zA-Z0-9]+$'
            )
    
    def test_whitelist_validation(self):
        """Test whitelist validation."""
        validator = InputValidator()
        
        # Should pass
        result = validator.validate_string(
            "pdf",
            allowed_values=["pdf", "docx", "txt"]
        )
        assert result == "pdf"
        
        # Should fail
        with pytest.raises(ValidationError):
            validator.validate_string(
                "exe",
                allowed_values=["pdf", "docx", "txt"]
            )
    
    def test_type_coercion(self):
        """Test automatic type conversion."""
        validator = InputValidator()
        
        # Number to string
        result = validator.validate_string(123)
        assert result == "123"


class TestIntegerValidation:
    """Test integer validation."""
    
    def test_valid_integer(self):
        """Test valid integer passes."""
        validator = InputValidator()
        result = validator.validate_integer(42)
        assert result == 42
    
    def test_string_to_integer(self):
        """Test string conversion to integer."""
        validator = InputValidator()
        result = validator.validate_integer("42")
        assert result == 42
    
    def test_invalid_integer(self):
        """Test invalid integer fails."""
        validator = InputValidator()
        
        with pytest.raises(ValidationError):
            validator.validate_integer("not a number")
    
    def test_min_value(self):
        """Test minimum value validation."""
        validator = InputValidator()
        
        # Should pass
        result = validator.validate_integer(10, min_value=5)
        assert result == 10
        
        # Should fail
        with pytest.raises(ValidationError):
            validator.validate_integer(3, min_value=5)
    
    def test_max_value(self):
        """Test maximum value validation."""
        validator = InputValidator()
        
        # Should pass
        result = validator.validate_integer(5, max_value=10)
        assert result == 5
        
        # Should fail
        with pytest.raises(ValidationError):
            validator.validate_integer(15, max_value=10)
    
    def test_range_validation(self):
        """Test combined min/max validation."""
        validator = InputValidator()
        
        # Should pass
        result = validator.validate_integer(75, min_value=0, max_value=100)
        assert result == 75
        
        # Should fail - too low
        with pytest.raises(ValidationError):
            validator.validate_integer(-5, min_value=0, max_value=100)
        
        # Should fail - too high
        with pytest.raises(ValidationError):
            validator.validate_integer(150, min_value=0, max_value=100)


class TestFloatValidation:
    """Test float validation."""
    
    def test_valid_float(self):
        """Test valid float passes."""
        validator = InputValidator()
        result = validator.validate_float(3.14)
        assert result == 3.14
    
    def test_string_to_float(self):
        """Test string conversion to float."""
        validator = InputValidator()
        result = validator.validate_float("3.14")
        assert result == 3.14
    
    def test_integer_to_float(self):
        """Test integer conversion to float."""
        validator = InputValidator()
        result = validator.validate_float(42)
        assert result == 42.0
    
    def test_range_validation(self):
        """Test float range validation."""
        validator = InputValidator()
        
        # Should pass
        result = validator.validate_float(5.5, min_value=0.0, max_value=10.0)
        assert result == 5.5
        
        # Should fail
        with pytest.raises(ValidationError):
            validator.validate_float(15.5, min_value=0.0, max_value=10.0)


class TestBooleanValidation:
    """Test boolean validation."""
    
    def test_true_values(self):
        """Test various representations of true."""
        validator = InputValidator()
        
        true_values = [True, 1, "true", "True", "TRUE", "yes", "Yes", "on", "1"]
        
        for value in true_values:
            result = validator.validate_boolean(value)
            assert result is True
    
    def test_false_values(self):
        """Test various representations of false."""
        validator = InputValidator()
        
        false_values = [False, 0, "false", "False", "FALSE", "no", "No", "off", "0", ""]
        
        for value in false_values:
            result = validator.validate_boolean(value)
            assert result is False
    
    def test_invalid_boolean(self):
        """Test invalid boolean fails."""
        validator = InputValidator()
        
        with pytest.raises(ValidationError):
            validator.validate_boolean("maybe")


class TestFormatValidation:
    """Test file format validation."""
    
    def test_valid_formats(self):
        """Test valid format strings."""
        validator = InputValidator()
        
        valid_formats = ["pdf", "docx", "txt", "png", "jpeg", "csv"]
        
        for fmt in valid_formats:
            result = validator.validate_format(fmt)
            assert result == fmt.lower()
    
    def test_uppercase_conversion(self):
        """Test uppercase formats are converted to lowercase."""
        validator = InputValidator()
        
        result = validator.validate_format("PDF")
        assert result == "pdf"
    
    def test_invalid_format(self):
        """Test invalid format strings fail."""
        validator = InputValidator()
        
        # Too long
        with pytest.raises(ValidationError):
            validator.validate_format("verylongformat")
        
        # Invalid characters
        with pytest.raises(ValidationError):
            validator.validate_format("pdf@123")


class TestDPIValidation:
    """Test DPI validation."""
    
    def test_valid_dpi(self):
        """Test valid DPI values."""
        validator = InputValidator()
        
        valid_dpis = [72, 150, 300, 600, 1200]
        
        for dpi in valid_dpis:
            result = validator.validate_dpi(dpi)
            assert result == dpi
    
    def test_string_dpi(self):
        """Test DPI from string."""
        validator = InputValidator()
        
        result = validator.validate_dpi("300")
        assert result == 300
    
    def test_dpi_range(self):
        """Test DPI range limits."""
        validator = InputValidator()
        
        # Too low
        with pytest.raises(ValidationError):
            validator.validate_dpi(50)
        
        # Too high
        with pytest.raises(ValidationError):
            validator.validate_dpi(5000)


class TestQualityValidation:
    """Test quality percentage validation."""
    
    def test_valid_quality(self):
        """Test valid quality values."""
        validator = InputValidator()
        
        valid_qualities = [0, 50, 75, 95, 100]
        
        for quality in valid_qualities:
            result = validator.validate_quality(quality)
            assert result == quality
    
    def test_quality_range(self):
        """Test quality range limits."""
        validator = InputValidator()
        
        # Too low
        with pytest.raises(ValidationError):
            validator.validate_quality(-1)
        
        # Too high
        with pytest.raises(ValidationError):
            validator.validate_quality(101)


class TestDictionaryValidation:
    """Test dictionary validation."""
    
    def test_valid_dict(self):
        """Test valid dictionary passes."""
        validator = InputValidator()
        
        test_dict = {"key1": "value1", "key2": "value2"}
        result = validator.validate_dict(test_dict)
        assert result == test_dict
    
    def test_required_keys(self):
        """Test required keys validation."""
        validator = InputValidator()
        
        test_dict = {"key1": "value1", "key2": "value2"}
        
        # Should pass
        result = validator.validate_dict(test_dict, required_keys=["key1"])
        assert result == test_dict
        
        # Should fail
        with pytest.raises(ValidationError) as exc:
            validator.validate_dict(test_dict, required_keys=["key3"])
        assert "Missing required keys" in str(exc.value)
    
    def test_non_dict_fails(self):
        """Test non-dictionary fails."""
        validator = InputValidator()
        
        with pytest.raises(ValidationError):
            validator.validate_dict("not a dict")


class TestHTMLSanitization:
    """Test HTML sanitization."""
    
    def test_script_removal(self):
        """Test script tag removal."""
        validator = InputValidator()
        
        html = '<div>Test</div><script>alert("xss")</script>'
        result = validator.sanitize_html(html)
        
        assert '<script>' not in result
        assert '<div>Test</div>' in result
    
    def test_event_handler_removal(self):
        """Test event handler removal."""
        validator = InputValidator()
        
        html = '<button onclick="alert(1)">Click</button>'
        result = validator.sanitize_html(html)
        
        assert 'onclick' not in result
    
    def test_javascript_url_removal(self):
        """Test javascript: URL removal."""
        validator = InputValidator()
        
        html = '<a href="javascript:alert(1)">Link</a>'
        result = validator.sanitize_html(html)
        
        assert 'javascript:' not in result.lower()


class TestConvenienceFunctions:
    """Test convenience functions."""
    
    def test_validate_string_function(self):
        """Test global validate_string function."""
        result = validate_string("test", min_length=1, max_length=10)
        assert result == "test"
    
    def test_validate_integer_function(self):
        """Test global validate_integer function."""
        result = validate_integer("42")
        assert result == 42
    
    def test_validate_float_function(self):
        """Test global validate_float function."""
        result = validate_float("3.14")
        assert result == 3.14
    
    def test_validate_boolean_function(self):
        """Test global validate_boolean function."""
        result = validate_boolean("true")
        assert result is True
    
    def test_validate_format_function(self):
        """Test global validate_format function."""
        result = validate_format("PDF")
        assert result == "pdf"
    
    def test_validate_dpi_function(self):
        """Test global validate_dpi function."""
        result = validate_dpi(300)
        assert result == 300


class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_none_values(self):
        """Test handling of None values."""
        validator = InputValidator()
        
        # String validation should handle None
        with pytest.raises(ValidationError):
            validator.validate_string(None, min_length=1)
    
    def test_empty_string(self):
        """Test empty string handling."""
        validator = InputValidator()
        
        # Empty string with min_length should fail
        with pytest.raises(ValidationError):
            validator.validate_string("", min_length=1)
        
        # Empty string without min_length should pass
        result = validator.validate_string("")
        assert result == ""
    
    def test_whitespace_handling(self):
        """Test whitespace in validation."""
        validator = InputValidator()
        
        # Boolean validation should handle whitespace
        result = validator.validate_boolean("  true  ")
        assert result is True
