"""Tests for temporary file security."""

import pytest
import os
import sys
from pathlib import Path
from src.security.temp_file_security import (
    SecureTempFile,
    create_secure_temp_file,
    create_secure_temp_dir,
    cleanup_temp_files
)


class TestSecureTempFile:
    """Test SecureTempFile context manager."""
    
    def test_basic_creation(self):
        """Test basic temp file creation."""
        with SecureTempFile(suffix='.txt') as temp_file:
            assert temp_file.path is not None
            assert os.path.exists(temp_file.path)
            assert temp_file.path.endswith('.txt')
        
        # File should be deleted after context
        assert not os.path.exists(temp_file.path)
    
    def test_write_and_read_bytes(self):
        """Test writing and reading bytes."""
        test_data = b"Test data content"
        
        with SecureTempFile(suffix='.bin') as temp_file:
            temp_file.write_bytes(test_data)
            read_data = temp_file.read_bytes()
            assert read_data == test_data
    
    def test_write_and_read_text(self):
        """Test writing and reading text."""
        test_text = "Hello, World! 你好"
        
        with SecureTempFile(suffix='.txt') as temp_file:
            temp_file.write_text(test_text)
            read_text = temp_file.read_text()
            assert read_text == test_text
    
    def test_keep_file(self):
        """Test keeping temp file after context."""
        with SecureTempFile(suffix='.txt', keep=True) as temp_file:
            path = temp_file.path
            temp_file.write_text("Keep me")
        
        # File should still exist
        assert os.path.exists(path)
        
        # Clean up manually
        os.unlink(path)
    
    def test_custom_prefix(self):
        """Test custom prefix."""
        with SecureTempFile(prefix='myprefix_', suffix='.txt') as temp_file:
            filename = os.path.basename(temp_file.path)
            assert filename.startswith('myprefix_')
    
    def test_custom_directory(self, tmp_path):
        """Test creating temp file in custom directory."""
        custom_dir = str(tmp_path)
        
        with SecureTempFile(suffix='.txt', dir=custom_dir) as temp_file:
            assert temp_file.path.startswith(custom_dir)
            assert os.path.exists(temp_file.path)
    
    def test_permissions_unix(self):
        """Test that file has restrictive permissions on Unix."""
        if sys.platform == 'win32':
            pytest.skip("Permission test for Unix only")
        
        with SecureTempFile(suffix='.txt') as temp_file:
            # Get file permissions
            stat_info = os.stat(temp_file.path)
            mode = stat_info.st_mode
            
            # Check that only owner has read/write (0o600)
            # The actual mode includes file type bits, so we mask those
            perms = mode & 0o777
            assert perms == 0o600, f"Expected 0o600, got {oct(perms)}"
    
    def test_file_descriptor_closed(self):
        """Test that file descriptor is properly closed."""
        with SecureTempFile(suffix='.txt') as temp_file:
            path = temp_file.path
            # Write using the path
            with open(path, 'w') as f:
                f.write("test")
        
        # Should not raise error about unclosed files


class TestCreateSecureTempFile:
    """Test create_secure_temp_file function."""
    
    def test_basic_creation(self):
        """Test basic temp file creation."""
        path = create_secure_temp_file(suffix='.pdf')
        
        assert path is not None
        assert os.path.exists(path)
        assert path.endswith('.pdf')
        
        # File is registered for cleanup but we'll clean it now
        os.unlink(path)
    
    def test_custom_prefix(self):
        """Test with custom prefix."""
        path = create_secure_temp_file(prefix='test_', suffix='.txt')
        
        filename = os.path.basename(path)
        assert filename.startswith('test_')
        
        os.unlink(path)
    
    def test_custom_directory(self, tmp_path):
        """Test creating in custom directory."""
        custom_dir = str(tmp_path)
        path = create_secure_temp_file(suffix='.txt', dir=custom_dir)
        
        assert path.startswith(custom_dir)
        assert os.path.exists(path)
        
        os.unlink(path)
    
    def test_multiple_files(self):
        """Test creating multiple temp files."""
        paths = []
        
        for i in range(5):
            path = create_secure_temp_file(suffix=f'.{i}.txt')
            paths.append(path)
            assert os.path.exists(path)
        
        # All should be unique
        assert len(set(paths)) == 5
        
        # Clean up
        for path in paths:
            os.unlink(path)


class TestCreateSecureTempDir:
    """Test create_secure_temp_dir function."""
    
    def test_basic_creation(self):
        """Test basic temp directory creation."""
        path = create_secure_temp_dir()
        
        assert path is not None
        assert os.path.exists(path)
        assert os.path.isdir(path)
        
        # Clean up
        os.rmdir(path)
    
    def test_custom_prefix(self):
        """Test with custom prefix."""
        path = create_secure_temp_dir(prefix='testdir_')
        
        dirname = os.path.basename(path)
        assert dirname.startswith('testdir_')
        
        os.rmdir(path)
    
    def test_permissions_unix(self):
        """Test directory permissions on Unix."""
        if sys.platform == 'win32':
            pytest.skip("Permission test for Unix only")
        
        path = create_secure_temp_dir()
        
        stat_info = os.stat(path)
        mode = stat_info.st_mode
        perms = mode & 0o777
        
        # Should have 0o700 (owner read/write/execute only)
        assert perms == 0o700, f"Expected 0o700, got {oct(perms)}"
        
        os.rmdir(path)
    
    def test_create_file_in_temp_dir(self):
        """Test creating files within the temp directory."""
        dir_path = create_secure_temp_dir()
        
        # Create a file in the directory
        file_path = os.path.join(dir_path, 'test.txt')
        with open(file_path, 'w') as f:
            f.write('test')
        
        assert os.path.exists(file_path)
        
        # Clean up
        os.unlink(file_path)
        os.rmdir(dir_path)


class TestCleanupTempFiles:
    """Test cleanup functionality."""
    
    def test_cleanup_registered_files(self):
        """Test that cleanup removes registered files."""
        # Create some temp files
        paths = []
        for i in range(3):
            path = create_secure_temp_file(suffix='.txt')
            paths.append(path)
        
        # All should exist
        for path in paths:
            assert os.path.exists(path)
        
        # Run cleanup
        cleanup_temp_files()
        
        # All should be gone
        for path in paths:
            assert not os.path.exists(path)
    
    def test_cleanup_handles_missing_files(self):
        """Test that cleanup handles already-deleted files."""
        path = create_secure_temp_file(suffix='.txt')
        
        # Manually delete it
        os.unlink(path)
        
        # Cleanup should not raise error
        cleanup_temp_files()


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_exception_during_context(self):
        """Test that temp file is cleaned up even if exception occurs."""
        path = None
        
        try:
            with SecureTempFile(suffix='.txt') as temp_file:
                path = temp_file.path
                temp_file.write_text("test")
                raise ValueError("Test exception")
        except ValueError:
            pass
        
        # File should still be cleaned up
        assert not os.path.exists(path)
    
    def test_write_before_enter(self):
        """Test that operations fail before entering context."""
        temp_file = SecureTempFile(suffix='.txt')
        
        with pytest.raises(RuntimeError):
            temp_file.write_text("test")
    
    def test_nested_contexts(self):
        """Test nested temp file contexts."""
        with SecureTempFile(suffix='.txt') as temp1:
            path1 = temp1.path
            temp1.write_text("file 1")
            
            with SecureTempFile(suffix='.txt') as temp2:
                path2 = temp2.path
                temp2.write_text("file 2")
                
                # Both should exist
                assert os.path.exists(path1)
                assert os.path.exists(path2)
                assert path1 != path2
            
            # temp2 should be gone, temp1 should exist
            assert os.path.exists(path1)
            assert not os.path.exists(path2)
        
        # Both should be gone
        assert not os.path.exists(path1)
        assert not os.path.exists(path2)
    
    def test_large_file_write(self):
        """Test writing large amounts of data."""
        large_data = b"x" * (10 * 1024 * 1024)  # 10 MB
        
        with SecureTempFile(suffix='.bin') as temp_file:
            temp_file.write_bytes(large_data)
            read_data = temp_file.read_bytes()
            assert len(read_data) == len(large_data)
    
    def test_unicode_content(self):
        """Test writing Unicode content."""
        unicode_text = "Hello 世界 🌍 Привет"
        
        with SecureTempFile(suffix='.txt') as temp_file:
            temp_file.write_text(unicode_text)
            read_text = temp_file.read_text()
            assert read_text == unicode_text


class TestSecurityProperties:
    """Test security-specific properties."""
    
    def test_no_world_readable_files(self):
        """Test that temp files are not world-readable (Unix)."""
        if sys.platform == 'win32':
            pytest.skip("Unix-specific test")
        
        with SecureTempFile(suffix='.txt') as temp_file:
            temp_file.write_text("sensitive data")
            
            stat_info = os.stat(temp_file.path)
            mode = stat_info.st_mode
            
            # Check that world/group have no permissions
            assert (mode & 0o077) == 0, "File has group or world permissions"
    
    def test_predictable_names_avoided(self):
        """Test that temp file names are unpredictable."""
        paths = set()
        
        for i in range(10):
            path = create_secure_temp_file(suffix='.txt')
            paths.add(os.path.basename(path))
            os.unlink(path)
        
        # All should be unique (very unlikely to collide)
        assert len(paths) == 10
        
        # Names should contain random component
        for path in paths:
            # Should have more than just prefix and suffix
            assert len(path) > len('pdfconv_.txt')
