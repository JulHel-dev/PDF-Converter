"""Tests for filename sanitization and security."""

import pytest
from src.security.filename_security import (
    sanitize_filename,
    is_filename_safe,
    validate_filename_or_raise,
    get_safe_filename,
    FilenameSecurityError,
    WINDOWS_RESERVED_NAMES
)


class TestFilenameSanitization:
    """Test filename sanitization."""
    
    def test_simple_filename(self):
        """Test that simple filenames pass through unchanged."""
        safe_names = [
            "test.txt",
            "document.pdf",
            "image.png",
            "data_file.csv"
        ]
        
        for name in safe_names:
            assert sanitize_filename(name) == name
    
    def test_path_separator_removal(self):
        """Test that path separators are removed."""
        assert "/" not in sanitize_filename("path/to/file.txt")
        assert "\\" not in sanitize_filename("path\\to\\file.txt")
        # Should keep just the filename part
        assert sanitize_filename("path/to/file.txt") == "file.txt"
    
    def test_invalid_characters_replaced(self):
        """Test that invalid characters are replaced."""
        test_cases = [
            ("file<name>.txt", "file_name_.txt"),
            ("file>name.txt", "file_name.txt"),
            ("file:name.txt", "file_name.txt"),
            ('file"name.txt', "file_name.txt"),
            ("file|name.txt", "file_name.txt"),
            ("file?name.txt", "file_name.txt"),
            ("file*name.txt", "file_name.txt"),
        ]
        
        for input_name, expected_pattern in test_cases:
            result = sanitize_filename(input_name)
            # Should not contain invalid characters
            assert "<" not in result
            assert ">" not in result
            assert ":" not in result
            assert '"' not in result
            assert "|" not in result
            assert "?" not in result
            assert "*" not in result
    
    def test_windows_reserved_names(self):
        """Test handling of Windows reserved names."""
        for reserved in WINDOWS_RESERVED_NAMES:
            # Test lowercase
            result = sanitize_filename(reserved.lower())
            assert result != reserved.lower()
            assert result.startswith("_") or not result.upper().startswith(reserved)
            
            # Test with extension
            result = sanitize_filename(f"{reserved}.txt")
            assert result != f"{reserved}.txt"
    
    def test_leading_trailing_dots_spaces(self):
        """Test removal of leading/trailing dots and spaces."""
        test_cases = [
            ("  filename.txt  ", "filename.txt"),
            ("...filename.txt", "filename.txt"),
            ("filename.txt...", "filename.txt"),
            (". hidden.txt", "hidden.txt"),
        ]
        
        for input_name, expected in test_cases:
            result = sanitize_filename(input_name)
            assert not result.startswith(".")
            assert not result.startswith(" ")
            assert not result.endswith(" ")
    
    def test_null_byte_removal(self):
        """Test that null bytes are removed."""
        result = sanitize_filename("file\x00name.txt")
        assert "\x00" not in result
    
    def test_unicode_normalization(self):
        """Test Unicode normalization."""
        # Test with accented characters
        result = sanitize_filename("tëst.txt")
        assert result == "tëst.txt"  # Should be normalized but preserved
        
        # Test with various Unicode forms
        # NFC normalization should make these equivalent
        name1 = "café.txt"  # é as single character
        name2 = "cafe\u0301.txt"  # é as e + combining acute
        
        result1 = sanitize_filename(name1)
        result2 = sanitize_filename(name2)
        # Both should normalize to the same form
        assert result1 == result2
    
    def test_empty_filename_handling(self):
        """Test handling of empty or invalid filenames."""
        with pytest.raises(FilenameSecurityError):
            sanitize_filename("")
        
        with pytest.raises(FilenameSecurityError):
            sanitize_filename(None)
        
        # Just dots should be replaced
        result = sanitize_filename("...")
        assert result.startswith("file")
        
        # Just extension should get a name
        result = sanitize_filename(".txt")
        assert not result.startswith(".")
        assert ".txt" in result or "txt" in result
    
    def test_length_truncation(self):
        """Test that overly long filenames are truncated."""
        # Create a very long filename
        long_name = "a" * 300 + ".txt"
        result = sanitize_filename(long_name)
        
        # Should be truncated to max length
        assert len(result) <= 255
        
        # Should preserve extension if possible
        assert result.endswith(".txt")
    
    def test_length_truncation_without_extension(self):
        """Test truncation of long filenames without extension."""
        long_name = "a" * 300
        result = sanitize_filename(long_name)
        
        assert len(result) <= 255
    
    def test_custom_replacement_char(self):
        """Test using custom replacement character."""
        result = sanitize_filename("file:name.txt", replacement="-")
        assert "-" in result
        assert ":" not in result


class TestFilenameSafetyChecking:
    """Test filename safety checking."""
    
    def test_is_filename_safe_valid(self):
        """Test is_filename_safe with valid names."""
        safe_names = [
            "test.txt",
            "document.pdf",
            "my_file.csv"
        ]
        
        for name in safe_names:
            assert is_filename_safe(name)
    
    def test_is_filename_safe_invalid(self):
        """Test is_filename_safe with invalid names."""
        unsafe_names = [
            "path/to/file.txt",
            "file<name>.txt",
            "CON.txt",
            "  filename.txt  "
        ]
        
        for name in unsafe_names:
            assert not is_filename_safe(name)
    
    def test_validate_filename_or_raise_valid(self):
        """Test validate_filename_or_raise with valid name."""
        result = validate_filename_or_raise("test.txt")
        assert result == "test.txt"
    
    def test_validate_filename_or_raise_invalid(self):
        """Test validate_filename_or_raise with invalid name."""
        # Should sanitize, not raise (unless completely invalid)
        result = validate_filename_or_raise("file:name.txt")
        assert ":" not in result
        
        # Empty filename should raise
        with pytest.raises(FilenameSecurityError):
            validate_filename_or_raise("")


class TestGetSafeFilename:
    """Test get_safe_filename function."""
    
    def test_get_safe_filename_from_path(self):
        """Test extracting safe filename from path."""
        result = get_safe_filename("/path/to/file.txt")
        assert result == "file.txt"
        
        result = get_safe_filename("C:\\Windows\\System32\\file.txt")
        assert result == "file.txt"
    
    def test_get_safe_filename_with_base_name(self):
        """Test using custom base name."""
        result = get_safe_filename("/path/to/file.txt", base_name="custom.pdf")
        assert result == "custom.pdf"
    
    def test_get_safe_filename_sanitizes(self):
        """Test that get_safe_filename sanitizes the result."""
        result = get_safe_filename("/path/to/file:name.txt")
        assert ":" not in result


class TestEdgeCases:
    """Test edge cases and special scenarios."""
    
    def test_all_invalid_characters(self):
        """Test filename with all invalid characters."""
        result = sanitize_filename("<>:\"/\\|?*")
        # Should get a valid filename
        assert len(result) > 0
        assert result.startswith("file")
    
    def test_mixed_valid_invalid(self):
        """Test filename with mix of valid and invalid characters."""
        result = sanitize_filename("valid_file<invalid>.txt")
        assert "valid" in result
        assert ".txt" in result
        assert "<" not in result
        assert ">" not in result
    
    def test_international_characters(self):
        """Test filenames with international characters."""
        test_names = [
            "файл.txt",  # Russian
            "文件.txt",   # Chinese
            "ファイル.txt", # Japanese
            "archivo.txt"  # Spanish
        ]
        
        for name in test_names:
            result = sanitize_filename(name)
            # Should preserve the characters
            assert len(result) > 0
            assert ".txt" in result
    
    def test_control_characters(self):
        """Test removal of control characters."""
        # Test with various control characters
        result = sanitize_filename("file\x01\x02\x03name.txt")
        # Control characters should be removed
        assert "\x01" not in result
        assert "\x02" not in result
        assert "\x03" not in result
        # Valid parts should remain
        assert "file" in result
        assert "name" in result
    
    def test_multiple_dots(self):
        """Test filenames with multiple dots."""
        result = sanitize_filename("file.name.with.dots.txt")
        # Multiple dots in the middle should be preserved
        assert result == "file.name.with.dots.txt"
    
    def test_no_extension(self):
        """Test filenames without extension."""
        result = sanitize_filename("filename")
        assert result == "filename"
    
    def test_only_extension(self):
        """Test filenames that are only an extension."""
        result = sanitize_filename(".txt")
        # Should add a name
        assert not result.startswith(".")
        assert "txt" in result


class TestSecurityVulnerabilities:
    """Test for specific security vulnerabilities."""
    
    def test_path_traversal_prevention(self):
        """Test that path traversal attempts are neutralized."""
        dangerous_names = [
            "../../etc/passwd",
            "..\\..\\Windows\\System32\\config\\SAM",
            "../../../sensitive",
        ]
        
        for name in dangerous_names:
            result = sanitize_filename(name)
            # Should not contain path separators
            assert "/" not in result
            assert "\\" not in result
            # Should not contain ..
            assert ".." not in result
    
    def test_hidden_file_prevention(self):
        """Test that hidden files are handled properly."""
        result = sanitize_filename(".hidden")
        # Should not remain hidden (on Unix)
        assert not result.startswith(".")
    
    def test_executable_extension_allowed(self):
        """Test that executable extensions are allowed (but logged)."""
        # This tests that we don't accidentally block legitimate files
        # while the filename_security module doesn't block extensions
        result = sanitize_filename("script.sh")
        assert result == "script.sh"
        
        result = sanitize_filename("program.exe")
        assert result == "program.exe"
