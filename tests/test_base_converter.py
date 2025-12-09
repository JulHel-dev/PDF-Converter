"""
Tests for Base Converter

Validates BaseConverter functionality and interface.
"""
import pytest
import os
import tempfile
from src.converters.base_converter import BaseConverter


class TestConverter(BaseConverter):
    """Test implementation of BaseConverter."""
    
    def __init__(self):
        super().__init__()
        self.supported_input_formats = ['txt']
        self.supported_output_formats = ['md']
    
    def convert(self, input_path: str, output_path: str, output_format: str) -> bool:
        """Simple test conversion."""
        with open(input_path, 'r') as f:
            content = f.read()
        
        with open(output_path, 'w') as f:
            f.write(f"# Converted\n\n{content}")
        
        return True


def test_validate_input_missing_file():
    """Test validation with missing file."""
    converter = TestConverter()
    result = converter.validate_input('/nonexistent/file.txt')
    assert result is False


def test_validate_input_valid_file():
    """Test validation with valid file."""
    converter = TestConverter()
    
    # Create a temporary file
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp:
        tmp.write('test content')
        tmp_path = tmp.name
    
    try:
        result = converter.validate_input(tmp_path)
        assert result is True
    finally:
        os.unlink(tmp_path)


def test_validate_input_empty_file():
    """Test validation with empty file."""
    converter = TestConverter()
    
    # Create an empty temporary file
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp:
        tmp_path = tmp.name
    
    try:
        result = converter.validate_input(tmp_path)
        assert result is False
    finally:
        os.unlink(tmp_path)


def test_validate_output():
    """Test output path validation."""
    converter = TestConverter()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, 'output.txt')
        result = converter.validate_output(output_path)
        assert result is True


def test_extract_metadata():
    """Test metadata extraction."""
    converter = TestConverter()
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as tmp:
        tmp.write('test content')
        tmp_path = tmp.name
    
    try:
        metadata = converter.extract_metadata(tmp_path)
        
        assert 'filename' in metadata
        assert 'size_bytes' in metadata
        assert 'size_mb' in metadata
        assert 'extension' in metadata
        assert metadata['extension'] == 'txt'
    finally:
        os.unlink(tmp_path)


def test_get_supported_conversions():
    """Test supported conversion mappings."""
    converter = TestConverter()
    
    conversions = converter.get_supported_conversions()
    
    assert 'txt' in conversions
    assert 'md' in conversions['txt']


def test_is_format_supported():
    """Test format support checking."""
    converter = TestConverter()
    
    assert converter.is_format_supported('txt', 'md') is True
    assert converter.is_format_supported('pdf', 'txt') is False
    assert converter.is_format_supported('txt', 'pdf') is False


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
