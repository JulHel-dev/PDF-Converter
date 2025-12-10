"""Tests for log rotation."""

import pytest
import os
import time
from src.utils.log_rotation import (
    LogRotationManager,
    LogRotationConfig,
    setup_log_rotation
)


class TestLogRotation:
    """Test log rotation functionality."""
    
    @pytest.fixture
    def log_dir(self, tmp_path):
        """Create temporary log directory."""
        return str(tmp_path / "logs")
    
    @pytest.fixture
    def manager(self, log_dir):
        """Create log rotation manager."""
        os.makedirs(log_dir, exist_ok=True)
        config = LogRotationConfig(
            max_bytes=1024,  # 1 KB for testing
            backup_count=3,
            retention_days=7,
            compress_old_logs=False  # Disable for simpler tests
        )
        return LogRotationManager(log_dir, config)
    
    def test_should_rotate_small_file(self, manager, log_dir):
        """Test that small files are not rotated."""
        log_file = os.path.join(log_dir, "test.log")
        
        # Create small file
        with open(log_file, 'w') as f:
            f.write("Small log")
        
        assert not manager.should_rotate(log_file)
    
    def test_should_rotate_large_file(self, manager, log_dir):
        """Test that large files should be rotated."""
        log_file = os.path.join(log_dir, "test.log")
        
        # Create file larger than max_bytes (1 KB)
        with open(log_file, 'w') as f:
            f.write("x" * 2000)  # 2 KB
        
        assert manager.should_rotate(log_file)
    
    def test_rotate_log(self, manager, log_dir):
        """Test log rotation."""
        log_file = os.path.join(log_dir, "test.log")
        
        # Create log file
        with open(log_file, 'w') as f:
            f.write("Original log")
        
        # Rotate
        success = manager.rotate_log(log_file)
        assert success
        
        # Check backup exists
        backup_file = f"{log_file}.1"
        assert os.path.exists(backup_file)
        
        # Check original is gone
        assert not os.path.exists(log_file)
    
    def test_multiple_rotations(self, manager, log_dir):
        """Test multiple rotations create numbered backups."""
        log_file = os.path.join(log_dir, "test.log")
        
        # Create and rotate 3 times
        for i in range(3):
            with open(log_file, 'w') as f:
                f.write(f"Log iteration {i}")
            manager.rotate_log(log_file)
        
        # Check all backups exist
        assert os.path.exists(f"{log_file}.1")
        assert os.path.exists(f"{log_file}.2")
        assert os.path.exists(f"{log_file}.3")
    
    def test_backup_count_limit(self, manager, log_dir):
        """Test that old backups are removed."""
        log_file = os.path.join(log_dir, "test.log")
        
        # Rotate more than backup_count (3)
        for i in range(5):
            with open(log_file, 'w') as f:
                f.write(f"Log {i}")
            manager.rotate_log(log_file)
        
        # Should only have 3 backups
        assert os.path.exists(f"{log_file}.1")
        assert os.path.exists(f"{log_file}.2")
        assert os.path.exists(f"{log_file}.3")
        assert not os.path.exists(f"{log_file}.4")
    
    def test_rotate_if_needed(self, manager, log_dir):
        """Test rotate_if_needed convenience method."""
        log_file = os.path.join(log_dir, "test.log")
        
        # Small file - should not rotate
        with open(log_file, 'w') as f:
            f.write("Small")
        
        assert not manager.rotate_if_needed(log_file)
        assert os.path.exists(log_file)
        
        # Large file - should rotate
        with open(log_file, 'w') as f:
            f.write("x" * 2000)
        
        assert manager.rotate_if_needed(log_file)
        assert not os.path.exists(log_file)
        assert os.path.exists(f"{log_file}.1")
    
    def test_cleanup_old_logs(self, manager, log_dir):
        """Test cleanup of old log files."""
        # Create old log file
        old_log = os.path.join(log_dir, "old.log")
        with open(old_log, 'w') as f:
            f.write("Old log")
        
        # Set modification time to 10 days ago
        old_time = time.time() - (10 * 24 * 60 * 60)
        os.utime(old_log, (old_time, old_time))
        
        # Create recent log file
        recent_log = os.path.join(log_dir, "recent.log")
        with open(recent_log, 'w') as f:
            f.write("Recent log")
        
        # Cleanup with 7 day retention
        removed = manager.cleanup_old_logs()
        
        # Old file should be removed
        assert not os.path.exists(old_log)
        
        # Recent file should still exist
        assert os.path.exists(recent_log)
        
        # Should have removed 1 file
        assert removed == 1
    
    def test_get_log_stats(self, manager, log_dir):
        """Test log statistics."""
        # Create a few log files
        for i in range(3):
            log_file = os.path.join(log_dir, f"test{i}.log")
            with open(log_file, 'w') as f:
                f.write("x" * 100)
        
        stats = manager.get_log_stats()
        
        assert stats['file_count'] == 3
        assert stats['total_size_bytes'] == 300
        assert 'total_size_mb' in stats


class TestLogRotationConfig:
    """Test log rotation configuration."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = LogRotationConfig()
        
        assert config.max_bytes == 10 * 1024 * 1024  # 10 MB
        assert config.backup_count == 5
        assert config.retention_days == 30
        assert config.compress_old_logs is True
    
    def test_custom_config(self):
        """Test custom configuration values."""
        config = LogRotationConfig(
            max_bytes=1024,
            backup_count=10,
            retention_days=7,
            compress_old_logs=False
        )
        
        assert config.max_bytes == 1024
        assert config.backup_count == 10
        assert config.retention_days == 7
        assert config.compress_old_logs is False


class TestSetupLogRotation:
    """Test setup function."""
    
    def test_setup_log_rotation(self, tmp_path):
        """Test setup_log_rotation helper function."""
        log_dir = str(tmp_path / "logs")
        os.makedirs(log_dir, exist_ok=True)
        
        manager = setup_log_rotation(
            log_dir=log_dir,
            max_bytes=2048,
            backup_count=3,
            retention_days=14
        )
        
        assert isinstance(manager, LogRotationManager)
        assert manager.config.max_bytes == 2048
        assert manager.config.backup_count == 3
        assert manager.config.retention_days == 14
