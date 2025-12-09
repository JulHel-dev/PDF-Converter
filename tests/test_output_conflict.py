"""Tests for output file conflict resolution."""

import pytest
import os
from pathlib import Path
from src.utils.output_conflict import (
    OutputConflictResolver,
    ConflictResolution,
    resolve_output_conflict,
    get_unique_output_path,
    check_output_writable
)


class TestConflictResolution:
    """Test conflict resolution strategies."""
    
    @pytest.fixture
    def temp_file(self, tmp_path):
        """Create a temporary existing file."""
        file_path = tmp_path / "existing.txt"
        file_path.write_text("Existing content")
        return str(file_path)
    
    def test_no_conflict(self, tmp_path):
        """Test when output file doesn't exist."""
        resolver = OutputConflictResolver(strategy=ConflictResolution.RENAME)
        
        nonexistent = str(tmp_path / "new.txt")
        result = resolver.resolve(nonexistent)
        
        assert result == nonexistent
    
    def test_overwrite_strategy(self, temp_file):
        """Test OVERWRITE strategy."""
        resolver = OutputConflictResolver(strategy=ConflictResolution.OVERWRITE)
        
        result = resolver.resolve(temp_file)
        
        # Should return same path (allowing overwrite)
        assert result == temp_file
    
    def test_skip_strategy(self, temp_file):
        """Test SKIP strategy."""
        resolver = OutputConflictResolver(strategy=ConflictResolution.SKIP)
        
        result = resolver.resolve(temp_file)
        
        # Should return None (skip)
        assert result is None
    
    def test_rename_strategy(self, temp_file):
        """Test RENAME strategy."""
        resolver = OutputConflictResolver(strategy=ConflictResolution.RENAME)
        
        result = resolver.resolve(temp_file)
        
        # Should return renamed path
        assert result is not None
        assert result != temp_file
        assert "_1" in result
        assert result.endswith(".txt")
    
    def test_rename_multiple_conflicts(self, tmp_path):
        """Test RENAME with multiple existing files."""
        base_file = tmp_path / "file.txt"
        base_file.write_text("Original")
        
        # Create file_1.txt and file_2.txt
        (tmp_path / "file_1.txt").write_text("Conflict 1")
        (tmp_path / "file_2.txt").write_text("Conflict 2")
        
        resolver = OutputConflictResolver(strategy=ConflictResolution.RENAME)
        result = resolver.resolve(str(base_file))
        
        # Should skip to file_3.txt
        assert "_3" in result
        assert not os.path.exists(result)
    
    def test_rename_max_attempts(self, tmp_path):
        """Test RENAME with max attempts exceeded."""
        resolver = OutputConflictResolver(
            strategy=ConflictResolution.RENAME,
            max_attempts=3
        )
        
        # Create base file and all numbered versions
        base_file = tmp_path / "file.txt"
        base_file.write_text("Original")
        
        for i in range(1, 4):
            (tmp_path / f"file_{i}.txt").write_text(f"Conflict {i}")
        
        # Should raise FileExistsError after max attempts
        with pytest.raises(FileExistsError):
            resolver.resolve(str(base_file))
    
    def test_error_strategy(self, temp_file):
        """Test ERROR strategy."""
        resolver = OutputConflictResolver(strategy=ConflictResolution.ERROR)
        
        # Should raise FileExistsError
        with pytest.raises(FileExistsError):
            resolver.resolve(temp_file)
    
    def test_batch_resolve(self, tmp_path):
        """Test batch conflict resolution."""
        # Create some existing files
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"
        file3 = tmp_path / "file3.txt"
        
        file1.write_text("Exists")
        file2.write_text("Exists")
        # file3 doesn't exist
        
        resolver = OutputConflictResolver(strategy=ConflictResolution.RENAME)
        
        paths = [str(file1), str(file2), str(file3)]
        resolved = resolver.batch_resolve(paths)
        
        # file1 and file2 should be renamed
        assert resolved[str(file1)] != str(file1)
        assert resolved[str(file2)] != str(file2)
        
        # file3 should stay the same
        assert resolved[str(file3)] == str(file3)


class TestConvenienceFunctions:
    """Test convenience functions."""
    
    def test_resolve_output_conflict(self, tmp_path):
        """Test resolve_output_conflict function."""
        existing = tmp_path / "existing.txt"
        existing.write_text("Content")
        
        # Test with RENAME
        result = resolve_output_conflict(
            str(existing),
            strategy=ConflictResolution.RENAME
        )
        
        assert result != str(existing)
        assert "_1" in result
    
    def test_get_unique_output_path_no_conflict(self, tmp_path):
        """Test get_unique_output_path with no conflict."""
        new_file = tmp_path / "new.txt"
        
        result = get_unique_output_path(str(new_file))
        
        assert result == str(new_file)
    
    def test_get_unique_output_path_with_conflict(self, tmp_path):
        """Test get_unique_output_path with conflict."""
        existing = tmp_path / "existing.txt"
        existing.write_text("Content")
        
        result = get_unique_output_path(str(existing))
        
        assert result != str(existing)
        assert "_1" in result
        assert not os.path.exists(result)
    
    def test_get_unique_output_path_multiple_conflicts(self, tmp_path):
        """Test with multiple numbered files."""
        base = tmp_path / "file.txt"
        base.write_text("Original")
        
        (tmp_path / "file_1.txt").write_text("Conflict 1")
        (tmp_path / "file_2.txt").write_text("Conflict 2")
        
        result = get_unique_output_path(str(base))
        
        assert "_3" in result


class TestOutputWritability:
    """Test output writability checks."""
    
    def test_writable_new_file(self, tmp_path):
        """Test writable path for new file."""
        new_file = tmp_path / "new.txt"
        
        is_writable, error = check_output_writable(str(new_file))
        
        assert is_writable is True
        assert error is None
    
    def test_writable_existing_file(self, tmp_path):
        """Test writable existing file."""
        existing = tmp_path / "existing.txt"
        existing.write_text("Content")
        
        is_writable, error = check_output_writable(str(existing))
        
        assert is_writable is True
        assert error is None
    
    def test_nonexistent_directory_created(self, tmp_path):
        """Test that nonexistent directory is created."""
        new_dir = tmp_path / "subdir" / "file.txt"
        
        is_writable, error = check_output_writable(str(new_dir))
        
        assert is_writable is True
        assert error is None
        assert os.path.exists(tmp_path / "subdir")
    
    def test_readonly_file(self, tmp_path):
        """Test read-only file (Unix only)."""
        if os.name == 'nt':
            pytest.skip("Read-only test for Unix")
        
        readonly = tmp_path / "readonly.txt"
        readonly.write_text("Content")
        
        # Make file read-only
        os.chmod(str(readonly), 0o444)
        
        is_writable, error = check_output_writable(str(readonly))
        
        # Should detect not writable
        assert is_writable is False
        assert error is not None


class TestEdgeCases:
    """Test edge cases."""
    
    def test_empty_directory_path(self, tmp_path):
        """Test with empty directory (current directory)."""
        resolver = OutputConflictResolver(strategy=ConflictResolution.RENAME)
        
        # Create file in current directory concept
        os.chdir(str(tmp_path))
        
        # Test with just filename
        Path("test.txt").write_text("Content")
        
        result = resolver.resolve("test.txt")
        
        assert result is not None
        assert "test_1.txt" == result
    
    def test_special_characters_in_filename(self, tmp_path):
        """Test filenames with spaces and special chars."""
        special = tmp_path / "file with spaces.txt"
        special.write_text("Content")
        
        resolver = OutputConflictResolver(strategy=ConflictResolution.RENAME)
        result = resolver.resolve(str(special))
        
        assert result is not None
        assert "_1" in result
    
    def test_no_extension_file(self, tmp_path):
        """Test file without extension."""
        no_ext = tmp_path / "README"
        no_ext.write_text("Content")
        
        resolver = OutputConflictResolver(strategy=ConflictResolution.RENAME)
        result = resolver.resolve(str(no_ext))
        
        assert result is not None
        assert result.endswith("_1")
    
    def test_multiple_dots_in_filename(self, tmp_path):
        """Test filename with multiple dots."""
        multi_dot = tmp_path / "file.backup.tar.gz"
        multi_dot.write_text("Content")
        
        resolver = OutputConflictResolver(strategy=ConflictResolution.RENAME)
        result = resolver.resolve(str(multi_dot))
        
        assert result is not None
        # Should preserve full extension
        assert result.endswith(".gz")
        assert "_1" in result
