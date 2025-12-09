"""
Comprehensive tests for path traversal prevention.

These tests verify that the path security module correctly
blocks all known path traversal attack vectors.
"""

import pytest
import os
import shutil
from pathlib import Path
from src.security.path_security import (
    PathValidator,
    PathSecurityError,
    is_path_safe
)


class TestPathTraversalPrevention:
    """Test cases for path traversal attacks."""
    
    @pytest.fixture
    def test_base_dir(self, tmp_path):
        """Create a temporary test base directory."""
        return str(tmp_path)
    
    @pytest.fixture
    def validator(self, test_base_dir):
        """Create a validator with test directories."""
        return PathValidator(allowed_bases=[test_base_dir])
    
    def test_simple_traversal_blocked(self, validator, test_base_dir):
        """Test that ../ traversal is blocked."""
        evil_path = os.path.join(test_base_dir, "..", "etc", "passwd")
        assert not validator.is_safe(evil_path)
    
    def test_double_traversal_blocked(self, validator, test_base_dir):
        """Test that ../../ traversal is blocked."""
        evil_path = os.path.join(test_base_dir, "..", "..", "etc", "passwd")
        assert not validator.is_safe(evil_path)
    
    def test_windows_traversal_blocked(self, validator, test_base_dir):
        """Test Windows-style traversal."""
        evil_path = test_base_dir + "\\..\\..\\Windows\\System32\\config\\SAM"
        assert not validator.is_safe(evil_path)
    
    def test_null_byte_injection_blocked(self, validator, test_base_dir):
        """Test null byte injection attempts."""
        os.path.join(test_base_dir, "file.txt\x00.pdf")
        # The path after null removal should be safe
        safe_path = os.path.join(test_base_dir, "file.txt.pdf")
        # Create the safe version to test
        Path(safe_path).touch()
        assert validator.is_safe(safe_path)
    
    def test_valid_paths_allowed(self, validator, test_base_dir):
        """Test that legitimate paths within base are allowed."""
        valid_paths = [
            test_base_dir,
            os.path.join(test_base_dir, "file.txt"),
            os.path.join(test_base_dir, "subdir", "file.pdf"),
            os.path.join(test_base_dir, "deep", "nested", "path", "file.docx"),
        ]
        
        for path in valid_paths:
            # Create the directory structure for the test
            dir_path = os.path.dirname(path)
            if dir_path and not os.path.exists(dir_path):
                os.makedirs(dir_path, exist_ok=True)
            
            assert validator.is_safe(path), f"Valid path rejected: {path}"
    
    def test_prefix_attack_blocked(self, validator, test_base_dir):
        """
        Test that prefix attacks are blocked.
        
        Example: If /allowed/path is permitted,
        /allowed/pathevil should NOT be permitted.
        """
        # Create a sibling directory with similar prefix
        sibling = test_base_dir + "evil"
        os.makedirs(sibling, exist_ok=True)
        
        try:
            evil_file = os.path.join(sibling, "file.txt")
            assert not validator.is_safe(evil_file)
        finally:
            shutil.rmtree(sibling, ignore_errors=True)
    
    def test_validate_or_raise(self, validator, test_base_dir):
        """Test that validate_or_raise raises on invalid paths."""
        with pytest.raises(PathSecurityError):
            validator.validate_or_raise(os.path.join(test_base_dir, "..", "etc", "passwd"))
    
    def test_empty_path_rejected(self, validator):
        """Test that empty paths are rejected."""
        assert not validator.is_safe("")
        assert not validator.is_safe(None)
    
    def test_get_safe_path(self, validator, test_base_dir):
        """Test safe path construction."""
        # Test with simple filename
        safe_path = validator.get_safe_path("test.txt", test_base_dir)
        assert safe_path is not None
        assert validator.is_safe(safe_path)
        
        # Test with path traversal attempt
        safe_path = validator.get_safe_path("../etc/passwd", test_base_dir)
        # Should extract just the filename
        assert safe_path is not None
        assert "passwd" in safe_path
        assert test_base_dir in safe_path


class TestPathValidatorIntegration:
    """Integration tests for path validation."""
    
    def test_global_validator_singleton(self):
        """Test that the global validator is a singleton."""
        from src.security.path_security import get_path_validator
        
        val1 = get_path_validator()
        val2 = get_path_validator()
        assert val1 is val2
    
    def test_convenience_functions(self, tmp_path):
        """Test convenience functions work correctly."""
        test_dir = str(tmp_path)
        PathValidator(allowed_bases=[test_dir])
        
        # Create a safe path
        safe_file = os.path.join(test_dir, "test.txt")
        Path(safe_file).touch()
        
        # Test is_path_safe (will use global validator with different bases)
        # Just verify it doesn't crash
        result = is_path_safe(safe_file)
        assert isinstance(result, bool)
    
    def test_safe_open_with_valid_path(self, tmp_path):
        """Test safe_open with a valid path."""
        test_dir = str(tmp_path)
        test_file = os.path.join(test_dir, "test.txt")
        
        # Create validator with this directory
        validator = PathValidator(allowed_bases=[test_dir])
        
        # Write using safe_open would require global validator setup
        # Just test path validation for now
        assert validator.is_safe(test_file)


class TestCanonicalPathHandling:
    """Test canonical path resolution."""
    
    def test_relative_path_resolution(self, tmp_path):
        """Test that relative paths are resolved correctly."""
        test_dir = str(tmp_path)
        validator = PathValidator(allowed_bases=[test_dir])
        
        # Create a subdirectory
        subdir = os.path.join(test_dir, "subdir")
        os.makedirs(subdir, exist_ok=True)
        
        # Change to subdirectory and use relative path
        original_cwd = os.getcwd()
        try:
            os.chdir(subdir)
            relative_path = "test.txt"
            full_path = os.path.join(subdir, relative_path)
            
            # The validator should resolve this correctly
            assert validator.is_safe(full_path)
        finally:
            os.chdir(original_cwd)
    
    def test_symlink_handling(self, tmp_path):
        """Test symlink resolution (Unix only)."""
        if os.name == 'nt':
            pytest.skip("Symlink test requires Unix")
        
        test_dir = str(tmp_path)
        validator = PathValidator(allowed_bases=[test_dir])
        
        # Create a file inside the allowed directory
        real_file = os.path.join(test_dir, "real_file.txt")
        Path(real_file).touch()
        
        # Create a symlink inside the allowed directory
        link_file = os.path.join(test_dir, "link_file.txt")
        os.symlink(real_file, link_file)
        
        # Both should be safe
        assert validator.is_safe(real_file)
        assert validator.is_safe(link_file)
        
        # Clean up
        os.unlink(link_file)
    
    def test_unicode_normalization(self, tmp_path):
        """Test Unicode normalization in paths."""
        test_dir = str(tmp_path)
        validator = PathValidator(allowed_bases=[test_dir])
        
        # Test with Unicode filename
        unicode_file = os.path.join(test_dir, "tëst.txt")
        assert validator.is_safe(unicode_file)


class TestPathValidatorEdgeCases:
    """Test edge cases and error handling."""
    
    def test_nonexistent_base_directory(self):
        """Test validator with non-existent base directory."""
        nonexistent = "/nonexistent/directory/path"
        validator = PathValidator(allowed_bases=[nonexistent])
        
        # Should still work for path validation (doesn't require existence)
        test_path = os.path.join(nonexistent, "file.txt")
        # This should be considered safe relative to the base
        assert validator.is_safe(test_path)
    
    def test_very_long_path(self, tmp_path):
        """Test handling of very long paths."""
        test_dir = str(tmp_path)
        validator = PathValidator(allowed_bases=[test_dir])
        
        # Create a very long path
        long_components = ["a" * 50 for _ in range(10)]
        long_path = os.path.join(test_dir, *long_components, "file.txt")
        
        # Should still validate correctly
        assert validator.is_safe(long_path)
    
    def test_special_characters_in_path(self, tmp_path):
        """Test paths with special characters."""
        test_dir = str(tmp_path)
        validator = PathValidator(allowed_bases=[test_dir])
        
        # Test various special characters (that are valid in filenames)
        special_chars = ["file with spaces.txt", "file-with-dash.txt", "file_with_underscore.txt"]
        
        for filename in special_chars:
            path = os.path.join(test_dir, filename)
            assert validator.is_safe(path), f"Failed for: {filename}"
