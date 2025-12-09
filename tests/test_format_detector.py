"""
Tests for Format Detector

Validates format detection functionality.
"""
import pytest
import os
import tempfile
from src.utils.format_detector import (
    detect_format, 
    is_conversion_supported, 
    get_supported_conversions,
    validate_file_format
)


def test_detect_format_by_extension():
    """Test format detection by file extension."""
    # Create temporary files with different extensions
    test_cases = [
        ('test.pdf', 'pdf'),
        ('test.txt', 'txt'),
        ('test.docx', 'docx'),
        ('test.xlsx', 'xlsx'),
        ('test.png', 'png'),
        ('test.jpg', 'jpeg'),
        ('test.json', 'json'),
    ]
    
    for filename, expected_format in test_cases:
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix=os.path.splitext(filename)[1]) as tmp:
            tmp.write('test content')
            tmp_path = tmp.name
        
        try:
            detected = detect_format(tmp_path)
            assert detected == expected_format, f"Expected {expected_format}, got {detected} for {filename}"
        finally:
            os.unlink(tmp_path)


def test_is_conversion_supported():
    """Test conversion support checking."""
    # Supported conversions
    assert is_conversion_supported('pdf', 'txt') is True
    assert is_conversion_supported('docx', 'pdf') is True
    assert is_conversion_supported('png', 'jpeg') is True
    
    # Unsupported conversions
    assert is_conversion_supported('pdf', 'mp3') is False
    assert is_conversion_supported('unknown', 'txt') is False


def test_get_supported_conversions():
    """Test getting supported output formats."""
    pdf_outputs = get_supported_conversions('pdf')
    assert 'txt' in pdf_outputs
    assert 'docx' in pdf_outputs
    assert 'png' in pdf_outputs
    
    docx_outputs = get_supported_conversions('docx')
    assert 'pdf' in docx_outputs
    assert 'txt' in docx_outputs
    
    # Unknown format
    unknown_outputs = get_supported_conversions('unknown_format')
    assert len(unknown_outputs) == 0


def test_validate_file_format():
    """Test file format validation."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as tmp:
        tmp.write('test content')
        tmp_path = tmp.name
    
    try:
        # Should detect as txt
        assert validate_file_format(tmp_path, 'txt') is True
        
        # Should fail for wrong format
        assert validate_file_format(tmp_path, 'pdf') is False
        
        # Should succeed without expected format (just checks if supported)
        assert validate_file_format(tmp_path, None) is True
    finally:
        os.unlink(tmp_path)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
