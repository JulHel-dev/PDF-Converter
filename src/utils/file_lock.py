"""
Cross-Platform File Locking

Prevents concurrent access to files during operations.
Uses fcntl on Unix and msvcrt on Windows.

References:
- fcntl documentation for Unix
- msvcrt documentation for Windows
"""

import os
import sys
import time
from typing import Optional
from contextlib import contextmanager

try:
    from src.logging.event_monitor import EventMonitor
except ImportError:
    try:
        from logging.event_monitor import EventMonitor
    except ImportError:
        EventMonitor = None

# Platform-specific imports
if os.name == 'nt':  # Windows
    import msvcrt
    HAS_WINDOWS_LOCK = True
    HAS_UNIX_LOCK = False
else:  # Unix/Linux/macOS
    try:
        import fcntl
        HAS_UNIX_LOCK = True
    except ImportError:
        HAS_UNIX_LOCK = False
    HAS_WINDOWS_LOCK = False


class FileLockError(Exception):
    """Raised when file locking fails."""
    pass


class FileLock:
    """
    Cross-platform file locking.
    
    Provides exclusive or shared locks on files to prevent
    concurrent access issues.
    
    Usage:
        lock = FileLock('file.txt')
        
        with lock:
            # File is locked
            with open('file.txt', 'r') as f:
                content = f.read()
        # File is unlocked
    
    Or:
        lock = FileLock('file.txt')
        if lock.acquire(timeout=5):
            try:
                # Do work with file
                pass
            finally:
                lock.release()
    """
    
    def __init__(
        self,
        file_path: str,
        timeout: Optional[float] = None,
        shared: bool = False
    ):
        """
        Initialize file lock.
        
        Args:
            file_path: Path to file to lock
            timeout: Maximum time to wait for lock (None = wait forever)
            shared: If True, use shared lock (allows multiple readers)
        """
        self.file_path = file_path
        self.timeout = timeout
        self.shared = shared
        self.lock_file = None
        self.is_locked = False
        
        self.monitor = EventMonitor() if EventMonitor else None
        
        # Create lock file path (.lock extension)
        self.lock_file_path = f"{file_path}.lock"
    
    def acquire(self, timeout: Optional[float] = None) -> bool:
        """
        Acquire file lock.
        
        Args:
            timeout: Override timeout for this acquisition
            
        Returns:
            True if lock acquired, False otherwise
        """
        if self.is_locked:
            return True
        
        timeout = timeout if timeout is not None else self.timeout
        start_time = time.time()
        
        try:
            # Create lock file
            self.lock_file = open(self.lock_file_path, 'w')
            
            while True:
                try:
                    if HAS_UNIX_LOCK:
                        self._acquire_unix()
                    elif HAS_WINDOWS_LOCK:
                        self._acquire_windows()
                    else:
                        # Fallback: No real locking available
                        self._log("No locking mechanism available", {}, 'WARNING')
                    
                    self.is_locked = True
                    self._log("Lock acquired", {'file': self.file_path}, 'DEBUG')
                    return True
                
                except (IOError, OSError) as e:
                    # Lock is held by another process
                    if timeout is not None and (time.time() - start_time) >= timeout:
                        self._log("Lock timeout", {
                            'file': self.file_path,
                            'timeout': timeout
                        }, 'WARNING')
                        return False
                    
                    # Wait a bit and retry
                    time.sleep(0.1)
        
        except Exception as e:
            self._log("Lock acquisition failed", {
                'file': self.file_path,
                'error': str(e)
            }, 'ERROR')
            return False
    
    def _acquire_unix(self):
        """Acquire lock on Unix systems."""
        if not HAS_UNIX_LOCK:
            raise NotImplementedError("Unix locking not available")
        
        flag = fcntl.LOCK_SH if self.shared else fcntl.LOCK_EX
        flag |= fcntl.LOCK_NB  # Non-blocking
        
        fcntl.flock(self.lock_file.fileno(), flag)
    
    def _acquire_windows(self):
        """Acquire lock on Windows systems."""
        if not HAS_WINDOWS_LOCK:
            raise NotImplementedError("Windows locking not available")
        
        # Windows doesn't have shared locks in msvcrt
        # Lock 1 byte at the beginning of file
        self.lock_file.seek(0)
        msvcrt.locking(self.lock_file.fileno(), msvcrt.LK_NBLCK, 1)
    
    def release(self):
        """Release file lock."""
        if not self.is_locked:
            return
        
        try:
            if HAS_UNIX_LOCK:
                self._release_unix()
            elif HAS_WINDOWS_LOCK:
                self._release_windows()
            
            self.is_locked = False
            self._log("Lock released", {'file': self.file_path}, 'DEBUG')
        
        except Exception as e:
            self._log("Lock release failed", {
                'file': self.file_path,
                'error': str(e)
            }, 'ERROR')
        
        finally:
            # Close and remove lock file
            if self.lock_file:
                try:
                    self.lock_file.close()
                except Exception:
                    pass
            
            try:
                if os.path.exists(self.lock_file_path):
                    os.remove(self.lock_file_path)
            except Exception:
                pass
    
    def _release_unix(self):
        """Release lock on Unix systems."""
        if not HAS_UNIX_LOCK:
            return
        
        fcntl.flock(self.lock_file.fileno(), fcntl.LOCK_UN)
    
    def _release_windows(self):
        """Release lock on Windows systems."""
        if not HAS_WINDOWS_LOCK:
            return
        
        # Unlock the byte
        self.lock_file.seek(0)
        msvcrt.locking(self.lock_file.fileno(), msvcrt.LK_UNLCK, 1)
    
    def __enter__(self):
        """Context manager entry."""
        if not self.acquire():
            raise FileLockError(f"Could not acquire lock on {self.file_path}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.release()
        return False
    
    def _log(self, message: str, data: dict, severity: str = 'INFO'):
        """Log event if monitor available."""
        if self.monitor:
            self.monitor.log_event(f'file_lock_{message.lower().replace(" ", "_")}', data, severity)


@contextmanager
def file_lock(file_path: str, timeout: Optional[float] = None, shared: bool = False):
    """
    Context manager for file locking.
    
    Args:
        file_path: Path to file to lock
        timeout: Maximum time to wait for lock
        shared: If True, use shared lock
        
    Usage:
        with file_lock('file.txt'):
            # File is locked
            with open('file.txt', 'r') as f:
                content = f.read()
    """
    lock = FileLock(file_path, timeout=timeout, shared=shared)
    try:
        if not lock.acquire():
            raise FileLockError(f"Could not acquire lock on {file_path}")
        yield lock
    finally:
        lock.release()


def is_file_locked(file_path: str) -> bool:
    """
    Check if a file is currently locked.
    
    Args:
        file_path: Path to file
        
    Returns:
        True if file is locked
    """
    lock = FileLock(file_path, timeout=0)
    acquired = lock.acquire()
    if acquired:
        lock.release()
        return False
    return True
