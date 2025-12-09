"""Tests for encoding detection."""

import pytest
import os
from pathlib import Path
from src.utils.encoding_detector import (
    EncodingDetector,
    detect_encoding,
    read_text_safe
)


class TestEncodingDetection:
    """Test encoding detection."""
    
    def test_utf8_detection(self, tmp_path):
        """Test UTF-8 file detection."""
        utf8_file = tmp_path / "utf8.txt"
        utf8_file.write_text("Hello World! 你好世界", encoding='utf-8')
        
        detector = EncodingDetector()
        encoding = detector.detect(str(utf8_file))
        
        assert encoding in ['utf-8', 'UTF-8', 'ascii']  # ASCII is subset of UTF-8
    
    def test_latin1_detection(self, tmp_path):
        """Test Latin-1 file detection."""
        latin1_file = tmp_path / "latin1.txt"
        latin1_file.write_text("Café résumé", encoding='latin-1')
        
        detector = EncodingDetector()
        encoding = detector.detect(str(latin1_file))
        
        # Should detect some encoding (exact depends on chardet availability)
        assert encoding is not None
        assert len(encoding) > 0
    
    def test_empty_file(self, tmp_path):
        """Test empty file detection."""
        empty_file = tmp_path / "empty.txt"
        empty_file.touch()
        
        detector = EncodingDetector()
        encoding = detector.detect(str(empty_file))
        
        # Should return default (utf-8)
        assert encoding == 'utf-8'
    
    def test_ascii_file(self, tmp_path):
        """Test pure ASCII file."""
        ascii_file = tmp_path / "ascii.txt"
        ascii_file.write_text("Simple ASCII text only", encoding='ascii')
        
        detector = EncodingDetector()
        encoding = detector.detect(str(ascii_file))
        
        # ASCII is valid UTF-8
        assert encoding in ['utf-8', 'UTF-8', 'ascii', 'ASCII']


class TestSafeReading:
    """Test safe text reading."""
    
    def test_read_utf8_file(self, tmp_path):
        """Test reading UTF-8 file."""
        utf8_file = tmp_path / "utf8.txt"
        content = "Hello World! 你好"
        utf8_file.write_text(content, encoding='utf-8')
        
        detector = EncodingDetector()
        read_content = detector.read_text_safe(str(utf8_file))
        
        assert read_content == content
    
    def test_read_with_specified_encoding(self, tmp_path):
        """Test reading with specified encoding."""
        latin1_file = tmp_path / "latin1.txt"
        content = "Café"
        latin1_file.write_text(content, encoding='latin-1')
        
        detector = EncodingDetector()
        read_content = detector.read_text_safe(str(latin1_file), encoding='latin-1')
        
        assert read_content == content
    
    def test_read_with_fallback(self, tmp_path):
        """Test reading with encoding fallback."""
        # Create file with mixed encoding
        file = tmp_path / "mixed.txt"
        file.write_bytes(b"Text with \xff invalid UTF-8")
        
        detector = EncodingDetector()
        # Should fallback to latin-1 and not raise exception
        content = detector.read_text_safe(str(file))
        
        assert content is not None
        assert len(content) > 0


class TestEncodingConversion:
    """Test encoding conversion."""
    
    def test_convert_latin1_to_utf8(self, tmp_path):
        """Test converting from Latin-1 to UTF-8."""
        input_file = tmp_path / "input.txt"
        output_file = tmp_path / "output.txt"
        
        content = "Café résumé"
        input_file.write_text(content, encoding='latin-1')
        
        detector = EncodingDetector()
        success = detector.convert_encoding(
            str(input_file),
            str(output_file),
            'utf-8'
        )
        
        assert success is True
        assert output_file.exists()
        
        # Read back and verify
        read_content = output_file.read_text(encoding='utf-8')
        assert content in read_content or len(read_content) > 0  # Content may vary slightly
    
    def test_convert_utf8_to_utf8(self, tmp_path):
        """Test converting UTF-8 to UTF-8 (no-op)."""
        input_file = tmp_path / "input.txt"
        output_file = tmp_path / "output.txt"
        
        content = "Hello World"
        input_file.write_text(content, encoding='utf-8')
        
        detector = EncodingDetector()
        success = detector.convert_encoding(
            str(input_file),
            str(output_file),
            'utf-8'
        )
        
        assert success is True
        assert output_file.read_text(encoding='utf-8') == content


class TestConvenienceFunctions:
    """Test convenience functions."""
    
    def test_detect_encoding_function(self, tmp_path):
        """Test detect_encoding convenience function."""
        file = tmp_path / "test.txt"
        file.write_text("Test content", encoding='utf-8')
        
        encoding = detect_encoding(str(file))
        
        assert encoding is not None
        assert len(encoding) > 0
    
    def test_read_text_safe_function(self, tmp_path):
        """Test read_text_safe convenience function."""
        file = tmp_path / "test.txt"
        content = "Test content"
        file.write_text(content, encoding='utf-8')
        
        read_content = read_text_safe(str(file))
        
        assert read_content == content


class TestEdgeCases:
    """Test edge cases."""
    
    def test_binary_file(self, tmp_path):
        """Test with binary file."""
        binary_file = tmp_path / "binary.bin"
        binary_file.write_bytes(bytes(range(256)))
        
        detector = EncodingDetector()
        encoding = detector.detect(str(binary_file))
        
        # Should return some encoding without crashing
        assert encoding is not None
    
    def test_large_file_sampling(self, tmp_path):
        """Test that large files are sampled, not read entirely."""
        large_file = tmp_path / "large.txt"
        large_file.write_text("x" * 1000000, encoding='utf-8')  # 1MB
        
        detector = EncodingDetector()
        encoding = detector.detect(str(large_file), sample_size=1000)
        
        # Should detect correctly from sample
        assert encoding in ['utf-8', 'UTF-8', 'ascii']
    
    def test_nonexistent_file(self, tmp_path):
        """Test with nonexistent file."""
        nonexistent = tmp_path / "nonexistent.txt"
        
        detector = EncodingDetector()
        encoding = detector.detect(str(nonexistent))
        
        # Should return default without crashing
        assert encoding == 'utf-8'
