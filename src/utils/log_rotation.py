"""
Log Rotation and Retention Management

Automatic log rotation based on size and age, with retention policies.
Prevents disk space exhaustion from log accumulation.

References:
- Logging Best Practices: https://docs.python.org/3/howto/logging.html
"""

import os
import gzip
import shutil
from datetime import datetime, timedelta
from typing import Optional, List
from pathlib import Path
import glob

try:
    from src.logging.event_monitor import EventMonitor
except ImportError:
    from logging.event_monitor import EventMonitor


class LogRotationConfig:
    """Configuration for log rotation."""
    
    def __init__(
        self,
        max_bytes: int = 10 * 1024 * 1024,  # 10 MB default
        backup_count: int = 5,
        retention_days: int = 30,
        compress_old_logs: bool = True
    ):
        """
        Initialize log rotation configuration.
        
        Args:
            max_bytes: Maximum size of a log file before rotation
            backup_count: Number of backup files to keep
            retention_days: Days to keep old logs
            compress_old_logs: Whether to compress rotated logs
        """
        self.max_bytes = max_bytes
        self.backup_count = backup_count
        self.retention_days = retention_days
        self.compress_old_logs = compress_old_logs


class LogRotationManager:
    """
    Manages log file rotation and retention.
    
    Features:
    - Size-based rotation (rotate when file exceeds max size)
    - Time-based retention (delete logs older than retention period)
    - Compression of old logs (saves disk space)
    - Automatic cleanup
    
    Usage:
        manager = LogRotationManager(log_dir="/path/to/logs")
        manager.rotate_if_needed("app.log")
        manager.cleanup_old_logs()
    """
    
    def __init__(
        self,
        log_dir: str,
        config: Optional[LogRotationConfig] = None
    ):
        """
        Initialize the log rotation manager.
        
        Args:
            log_dir: Directory containing log files
            config: Rotation configuration
        """
        self.log_dir = log_dir
        self.config = config or LogRotationConfig()
        self.monitor = EventMonitor()
    
    def get_log_size(self, log_file: str) -> int:
        """Get size of log file in bytes."""
        try:
            return os.path.getsize(log_file)
        except OSError:
            return 0
    
    def should_rotate(self, log_file: str) -> bool:
        """
        Check if log file should be rotated.
        
        Args:
            log_file: Path to log file
            
        Returns:
            True if file should be rotated
        """
        if not os.path.exists(log_file):
            return False
        
        size = self.get_log_size(log_file)
        return size >= self.config.max_bytes
    
    def rotate_log(self, log_file: str) -> bool:
        """
        Rotate a log file.
        
        Renames log_file to log_file.1, log_file.1 to log_file.2, etc.
        Compresses old logs if configured.
        
        Args:
            log_file: Path to log file to rotate
            
        Returns:
            True if rotation succeeded
        """
        try:
            if not os.path.exists(log_file):
                return False
            
            # Shift existing backups
            for i in range(self.config.backup_count - 1, 0, -1):
                old_backup = f"{log_file}.{i}"
                new_backup = f"{log_file}.{i + 1}"
                
                # Remove oldest backup if it exists
                if i == self.config.backup_count - 1:
                    if os.path.exists(new_backup):
                        os.remove(new_backup)
                    if os.path.exists(f"{new_backup}.gz"):
                        os.remove(f"{new_backup}.gz")
                
                # Shift backup
                if os.path.exists(old_backup):
                    shutil.move(old_backup, new_backup)
                elif os.path.exists(f"{old_backup}.gz"):
                    shutil.move(f"{old_backup}.gz", f"{new_backup}.gz")
            
            # Rotate current log to .1
            backup_file = f"{log_file}.1"
            shutil.move(log_file, backup_file)
            
            # Compress if configured
            if self.config.compress_old_logs:
                self._compress_log(backup_file)
            
            self.monitor.log_event('log_rotated', {
                'log_file': log_file,
                'size_bytes': self.get_log_size(log_file),
                'backup_file': backup_file
            }, severity='INFO')
            
            return True
            
        except Exception as e:
            self.monitor.log_event('log_rotation_failed', {
                'log_file': log_file,
                'error': str(e)
            }, severity='ERROR')
            return False
    
    def _compress_log(self, log_file: str):
        """
        Compress a log file with gzip.
        
        Args:
            log_file: Path to log file to compress
        """
        try:
            compressed_file = f"{log_file}.gz"
            
            with open(log_file, 'rb') as f_in:
                with gzip.open(compressed_file, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            # Remove uncompressed file
            os.remove(log_file)
            
            self.monitor.log_event('log_compressed', {
                'original_file': log_file,
                'compressed_file': compressed_file,
                'original_size': os.path.getsize(log_file) if os.path.exists(log_file) else 0,
                'compressed_size': os.path.getsize(compressed_file)
            }, severity='DEBUG')
            
        except Exception as e:
            self.monitor.log_event('log_compression_failed', {
                'log_file': log_file,
                'error': str(e)
            }, severity='WARNING')
    
    def rotate_if_needed(self, log_file: str) -> bool:
        """
        Check and rotate log file if needed.
        
        Args:
            log_file: Path to log file
            
        Returns:
            True if rotation was performed
        """
        if self.should_rotate(log_file):
            return self.rotate_log(log_file)
        return False
    
    def cleanup_old_logs(self) -> int:
        """
        Remove log files older than retention period.
        
        Returns:
            Number of files removed
        """
        if not os.path.exists(self.log_dir):
            return 0
        
        cutoff_date = datetime.now() - timedelta(days=self.config.retention_days)
        removed_count = 0
        
        try:
            # Find all log files
            log_files = glob.glob(os.path.join(self.log_dir, "*"))
            
            for log_file in log_files:
                if not os.path.isfile(log_file):
                    continue
                
                try:
                    # Check file modification time
                    mtime = datetime.fromtimestamp(os.path.getmtime(log_file))
                    
                    if mtime < cutoff_date:
                        os.remove(log_file)
                        removed_count += 1
                        
                        self.monitor.log_event('old_log_removed', {
                            'file': log_file,
                            'age_days': (datetime.now() - mtime).days,
                            'retention_days': self.config.retention_days
                        }, severity='INFO')
                
                except Exception as e:
                    self.monitor.log_event('log_cleanup_failed', {
                        'file': log_file,
                        'error': str(e)
                    }, severity='WARNING')
            
            if removed_count > 0:
                self.monitor.log_event('log_cleanup_complete', {
                    'removed_count': removed_count,
                    'log_dir': self.log_dir
                }, severity='INFO')
            
            return removed_count
            
        except Exception as e:
            self.monitor.log_event('log_cleanup_error', {
                'log_dir': self.log_dir,
                'error': str(e)
            }, severity='ERROR')
            return removed_count
    
    def get_log_stats(self) -> dict:
        """
        Get statistics about log files in the directory.
        
        Returns:
            Dictionary with log statistics
        """
        try:
            log_files = glob.glob(os.path.join(self.log_dir, "*"))
            
            total_size = 0
            file_count = 0
            oldest_file = None
            newest_file = None
            
            for log_file in log_files:
                if not os.path.isfile(log_file):
                    continue
                
                file_count += 1
                total_size += os.path.getsize(log_file)
                
                mtime = datetime.fromtimestamp(os.path.getmtime(log_file))
                
                if oldest_file is None or mtime < oldest_file:
                    oldest_file = mtime
                
                if newest_file is None or mtime > newest_file:
                    newest_file = mtime
            
            return {
                'file_count': file_count,
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'oldest_file_age_days': (datetime.now() - oldest_file).days if oldest_file else None,
                'newest_file_age_days': (datetime.now() - newest_file).days if newest_file else None
            }
            
        except Exception as e:
            self.monitor.log_event('log_stats_error', {
                'log_dir': self.log_dir,
                'error': str(e)
            }, severity='WARNING')
            return {}
    
    def rotate_all_logs(self, pattern: str = "*") -> int:
        """
        Rotate all log files matching pattern if they need rotation.
        
        Args:
            pattern: Glob pattern for log files
            
        Returns:
            Number of files rotated
        """
        rotated_count = 0
        
        try:
            log_files = glob.glob(os.path.join(self.log_dir, pattern))
            
            for log_file in log_files:
                if not os.path.isfile(log_file):
                    continue
                
                if self.rotate_if_needed(log_file):
                    rotated_count += 1
            
            return rotated_count
            
        except Exception as e:
            self.monitor.log_event('batch_rotation_error', {
                'log_dir': self.log_dir,
                'pattern': pattern,
                'error': str(e)
            }, severity='ERROR')
            return rotated_count


def setup_log_rotation(
    log_dir: str,
    max_bytes: int = 10 * 1024 * 1024,
    backup_count: int = 5,
    retention_days: int = 30
) -> LogRotationManager:
    """
    Set up log rotation for a directory.
    
    Args:
        log_dir: Directory containing log files
        max_bytes: Maximum size before rotation
        backup_count: Number of backups to keep
        retention_days: Days to retain logs
        
    Returns:
        Configured LogRotationManager
    """
    config = LogRotationConfig(
        max_bytes=max_bytes,
        backup_count=backup_count,
        retention_days=retention_days
    )
    
    return LogRotationManager(log_dir, config)
