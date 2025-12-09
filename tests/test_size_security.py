"""Tests for file size validation."""

import pytest
import os
import tempfile
from pathlib import Path
from src.security.size_security import (
    FileSizeValidator,
    FileSizeError,
    validate_file_size,
    get_size_validator
)


class TestFileSizeValidation:
    """Test file size validation functionality."""
    
    @pytest.fixture
    def validator(self):
        """Create validator with 10 MB limit for tests."""
        return FileSizeValidator(max_mb=10)
    
    def test_small_file_allowed(self, validator, tmp_path):
        """Test that small files are allowed."""
        small_file = tmp_path / "small.txt"
        small_file.write_bytes(b"x" * 1000)  # 1 KB
        assert validator.is_valid(small_file)
    
    def test_large_file_blocked(self, validator, tmp_path):
        """Test that oversized files are blocked."""
        # Create a file larger than 10 MB limit
        large_file = tmp_path / "large.bin"
        large_file.write_bytes(b"x" * (11 * 1024 * 1024))  # 11 MB
        assert not validator.is_valid(large_file)
    
    def test_exact_limit_allowed(self, validator, tmp_path):
        """Test that files at exactly the limit are allowed."""
        exact_file = tmp_path / "exact.bin"
        exact_file.write_bytes(b"x" * (10 * 1024 * 1024))  # 10 MB
        assert validator.is_valid(exact_file)
    
    def test_validate_or_raise_success(self, validator, tmp_path):
        """Test validate_or_raise with valid file."""
        small_file = tmp_path / "small.txt"
        small_file.write_bytes(b"test")
        
        size_mb = validator.validate_or_raise(small_file)
        assert size_mb < 10
    
    def test_validate_or_raise_failure(self, validator, tmp_path):
        """Test validate_or_raise with oversized file."""
        large_file = tmp_path / "large.bin"
        large_file.write_bytes(b"x" * (11 * 1024 * 1024))  # 11 MB
        
        with pytest.raises(FileSizeError) as exc_info:
            validator.validate_or_raise(large_file)
        
        assert "exceeds maximum" in str(exc_info.value)
        assert exc_info.value.size_mb > 10
        assert exc_info.value.max_mb == 10
    
    def test_get_size_mb(self, validator, tmp_path):
        """Test get_size_mb calculation."""
        test_file = tmp_path / "test.bin"
        # Create 5 MB file
        test_file.write_bytes(b"x" * (5 * 1024 * 1024))
        
        size_mb = validator.get_size_mb(test_file)
        assert 4.9 < size_mb < 5.1  # Allow for small rounding differences
    
    def test_nonexistent_file(self, validator, tmp_path):
        """Test validation of non-existent file."""
        nonexistent = tmp_path / "nonexistent.txt"
        assert not validator.is_valid(nonexistent)
    
    def test_override_max_size(self, validator, tmp_path):
        """Test overriding max size for specific validation."""
        # Create 8 MB file
        test_file = tmp_path / "test.bin"
        test_file.write_bytes(b"x" * (8 * 1024 * 1024))
        
        # Should fail with default 10 MB limit... wait, 8 < 10
        # Let's make it 12 MB
        test_file = tmp_path / "test2.bin"
        test_file.write_bytes(b"x" * (12 * 1024 * 1024))
        
        # Should fail with validator's 10 MB limit
        assert not validator.is_valid(test_file)
        
        # Should pass with overridden 15 MB limit
        assert validator.is_valid(test_file, max_mb=15)


class TestFileSizeValidatorUpload:
    """Test upload validation functionality."""
    
    def test_validate_upload_within_limit(self):
        """Test validation of uploaded file within limit."""
        from io import BytesIO
        
        validator = FileSizeValidator(max_mb=10)
        
        # Create file-like object with 5 MB of data
        file_obj = BytesIO(b"x" * (5 * 1024 * 1024))
        
        assert validator.validate_upload(file_obj, "test.pdf")
        
        # Verify position is restored
        assert file_obj.tell() == 0
    
    def test_validate_upload_exceeds_limit(self):
        """Test validation of uploaded file exceeding limit."""
        from io import BytesIO
        
        validator = FileSizeValidator(max_mb=10)
        
        # Create file-like object with 15 MB of data
        file_obj = BytesIO(b"x" * (15 * 1024 * 1024))
        
        assert not validator.validate_upload(file_obj, "large.pdf")
    
    def test_validate_upload_at_limit(self):
        """Test validation of uploaded file at exact limit."""
        from io import BytesIO
        
        validator = FileSizeValidator(max_mb=10)
        
        # Create file-like object with exactly 10 MB of data
        file_obj = BytesIO(b"x" * (10 * 1024 * 1024))
        
        assert validator.validate_upload(file_obj, "exact.pdf")
    
    def test_validate_upload_override_limit(self):
        """Test overriding limit for upload validation."""
        from io import BytesIO
        
        validator = FileSizeValidator(max_mb=10)
        
        # Create file-like object with 12 MB of data
        file_obj = BytesIO(b"x" * (12 * 1024 * 1024))
        
        # Should fail with default limit
        assert not validator.validate_upload(file_obj, "test.pdf")
        
        # Reset position
        file_obj.seek(0)
        
        # Should pass with overridden limit
        assert validator.validate_upload(file_obj, "test.pdf", max_mb=15)


class TestFileSizeConvenienceFunctions:
    """Test convenience functions."""
    
    def test_validate_file_size(self, tmp_path):
        """Test the convenience function."""
        test_file = tmp_path / "test.txt"
        test_file.write_bytes(b"x" * 1000)  # 1 KB
        
        # Should pass with default limit (100 MB from settings)
        assert validate_file_size(test_file)
    
    def test_validate_file_size_with_override(self, tmp_path):
        """Test convenience function with override."""
        # Create 5 MB file
        test_file = tmp_path / "test.bin"
        test_file.write_bytes(b"x" * (5 * 1024 * 1024))
        
        # Should fail with 1 MB limit
        assert not validate_file_size(test_file, max_mb=1)
        
        # Should pass with 10 MB limit
        assert validate_file_size(test_file, max_mb=10)
    
    def test_get_size_validator_singleton(self):
        """Test that get_size_validator returns singleton."""
        val1 = get_size_validator()
        val2 = get_size_validator()
        assert val1 is val2


class TestFileSizeError:
    """Test FileSizeError exception."""
    
    def test_file_size_error_attributes(self):
        """Test that FileSizeError has correct attributes."""
        error = FileSizeError("test.pdf", 150.5, 100.0)
        
        assert error.path == "test.pdf"
        assert error.size_mb == 150.5
        assert error.max_mb == 100.0
        assert "test.pdf" in str(error)
        assert "150.5" in str(error) or "150.50" in str(error)
        assert "100" in str(error)


class TestFileSizeEdgeCases:
    """Test edge cases."""
    
    def test_empty_file(self, tmp_path):
        """Test validation of empty file."""
        validator = FileSizeValidator(max_mb=10)
        
        empty_file = tmp_path / "empty.txt"
        empty_file.touch()
        
        # Empty file should be valid
        assert validator.is_valid(empty_file)
        
        size_mb = validator.get_size_mb(empty_file)
        assert size_mb == 0.0
    
    def test_very_small_file(self, tmp_path):
        """Test validation of very small file."""
        validator = FileSizeValidator(max_mb=10)
        
        tiny_file = tmp_path / "tiny.txt"
        tiny_file.write_bytes(b"x")  # 1 byte
        
        assert validator.is_valid(tiny_file)
        
        size_mb = validator.get_size_mb(tiny_file)
        assert size_mb < 0.001  # Less than 1 KB
    
    def test_pathlib_path_support(self, tmp_path):
        """Test that Path objects are supported."""
        validator = FileSizeValidator(max_mb=10)
        
        test_file = tmp_path / "test.txt"
        test_file.write_bytes(b"test")
        
        # Should work with Path object
        assert validator.is_valid(test_file)
        
        # Should also work with string
        assert validator.is_valid(str(test_file))
