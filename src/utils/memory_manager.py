"""
Memory Management and Leak Prevention

Features:
- Resource cleanup tracking
- Memory usage monitoring
- Garbage collection hints
- Resource limit enforcement
- Memory leak detection helpers

References:
- Python gc module
- psutil for memory monitoring
- weakref for cleanup tracking
"""

import gc
import os
import sys
import weakref
from typing import Any, Callable, Optional, Dict, List
from contextlib import contextmanager

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

try:
    from src.logging.event_monitor import EventMonitor
except ImportError:
    try:
        from logging.event_monitor import EventMonitor
    except ImportError:
        EventMonitor = None


class MemoryManager:
    """
    Manages memory usage and cleanup.
    
    Features:
    - Track resource cleanup
    - Monitor memory usage
    - Force garbage collection when needed
    - Detect potential memory leaks
    
    Usage:
        manager = MemoryManager()
        
        # Register cleanup
        manager.register_cleanup(file.close)
        
        # Check memory
        if manager.is_memory_high():
            manager.cleanup_all()
    """
    
    def __init__(
        self,
        memory_limit_mb: Optional[int] = None,
        warning_threshold: float = 0.8
    ):
        """
        Initialize memory manager.
        
        Args:
            memory_limit_mb: Memory limit in MB (None = no limit)
            warning_threshold: Warn when memory exceeds this fraction of limit
        """
        self.memory_limit_mb = memory_limit_mb
        self.warning_threshold = warning_threshold
        
        self.monitor = EventMonitor() if EventMonitor else None
        
        # Track cleanup functions
        self._cleanup_callbacks: List[Callable] = []
        
        # Track weak references to objects
        self._tracked_objects: List[weakref.ref] = []
        
        self._log("Memory manager initialized", {
            'limit_mb': memory_limit_mb,
            'has_psutil': HAS_PSUTIL
        }, 'INFO')
    
    def register_cleanup(self, cleanup_func: Callable[[], None]):
        """
        Register a cleanup function to be called on shutdown.
        
        Args:
            cleanup_func: Function to call for cleanup
        """
        self._cleanup_callbacks.append(cleanup_func)
        self._log("Cleanup registered", {
            'function': cleanup_func.__name__ if hasattr(cleanup_func, '__name__') else str(cleanup_func)
        }, 'DEBUG')
    
    def cleanup_all(self):
        """Execute all registered cleanup functions."""
        self._log("Running all cleanups", {
            'count': len(self._cleanup_callbacks)
        }, 'INFO')
        
        for cleanup in self._cleanup_callbacks:
            try:
                cleanup()
            except Exception as e:
                self._log("Cleanup failed", {
                    'function': str(cleanup),
                    'error': str(e)
                }, 'ERROR')
        
        # Clear callbacks
        self._cleanup_callbacks.clear()
        
        # Force garbage collection
        self.force_gc()
    
    def force_gc(self) -> Dict[str, int]:
        """
        Force garbage collection.
        
        Returns:
            Dictionary with collection stats
        """
        self._log("Forcing garbage collection", {}, 'DEBUG')
        
        # Collect all generations
        collected = {
            'gen0': gc.collect(0),
            'gen1': gc.collect(1),
            'gen2': gc.collect(2)
        }
        
        total = sum(collected.values())
        
        self._log("Garbage collection completed", {
            'collected': total,
            'by_generation': collected
        }, 'INFO')
        
        return collected
    
    def get_memory_usage(self) -> Dict[str, float]:
        """
        Get current memory usage.
        
        Returns:
            Dictionary with memory stats (in MB)
        """
        if not HAS_PSUTIL:
            self._log("psutil not available", {}, 'WARNING')
            return {}
        
        try:
            process = psutil.Process()
            mem_info = process.memory_info()
            
            usage = {
                'rss_mb': mem_info.rss / (1024 * 1024),
                'vms_mb': mem_info.vms / (1024 * 1024)
            }
            
            # Add percentage if limit is set
            if self.memory_limit_mb:
                usage['percent_of_limit'] = (usage['rss_mb'] / self.memory_limit_mb) * 100
            
            return usage
        
        except Exception as e:
            self._log("Memory usage check failed", {'error': str(e)}, 'ERROR')
            return {}
    
    def is_memory_high(self) -> bool:
        """
        Check if memory usage is high.
        
        Returns:
            True if memory usage exceeds warning threshold
        """
        if not self.memory_limit_mb or not HAS_PSUTIL:
            return False
        
        usage = self.get_memory_usage()
        if not usage:
            return False
        
        rss_mb = usage.get('rss_mb', 0)
        threshold_mb = self.memory_limit_mb * self.warning_threshold
        
        if rss_mb > threshold_mb:
            self._log("Memory usage high", {
                'current_mb': round(rss_mb, 2),
                'threshold_mb': round(threshold_mb, 2),
                'limit_mb': self.memory_limit_mb
            }, 'WARNING')
            return True
        
        return False
    
    def track_object(self, obj: Any):
        """
        Track an object for leak detection.
        
        Args:
            obj: Object to track
        """
        try:
            self._tracked_objects.append(weakref.ref(obj))
        except TypeError:
            # Some objects don't support weak references (e.g., dict, str)
            # Store them directly (will prevent them from being GC'd)
            pass
    
    def check_leaks(self) -> List[str]:
        """
        Check for potential memory leaks.
        
        Returns:
            List of leak descriptions
        """
        leaks = []
        
        # Clean up dead references
        self._tracked_objects = [ref for ref in self._tracked_objects if ref() is not None]
        
        # Check if we have too many tracked objects
        if len(self._tracked_objects) > 1000:
            leaks.append(f"High number of tracked objects: {len(self._tracked_objects)}")
        
        # Get garbage collection stats
        gc_stats = gc.get_stats()
        
        # Check for uncollectable objects
        uncollectable = len(gc.garbage)
        if uncollectable > 0:
            leaks.append(f"Uncollectable garbage: {uncollectable} objects")
        
        if leaks:
            self._log("Potential memory leaks detected", {
                'leaks': leaks
            }, 'WARNING')
        
        return leaks
    
    def cleanup_and_check(self):
        """Cleanup and check for leaks."""
        self.cleanup_all()
        self.check_leaks()
    
    def _log(self, message: str, data: Dict[str, Any], severity: str = 'INFO'):
        """Log event if monitor available."""
        if self.monitor:
            self.monitor.log_event(
                f'memory_manager_{message.lower().replace(" ", "_")}',
                data,
                severity
            )


@contextmanager
def managed_resource(resource: Any, cleanup: Optional[Callable] = None):
    """
    Context manager for resource management with automatic cleanup.
    
    Args:
        resource: Resource to manage
        cleanup: Optional cleanup function (defaults to resource.close())
        
    Usage:
        with managed_resource(file_obj) as f:
            # Use resource
            content = f.read()
        # Resource is automatically cleaned up
    """
    manager = MemoryManager()
    
    try:
        # Register cleanup
        if cleanup:
            manager.register_cleanup(cleanup)
        elif hasattr(resource, 'close'):
            manager.register_cleanup(resource.close)
        
        # Track object
        manager.track_object(resource)
        
        yield resource
    
    finally:
        # Cleanup
        manager.cleanup_all()


def clear_memory():
    """
    Force memory cleanup and garbage collection.
    
    Convenience function for one-off cleanup.
    """
    manager = MemoryManager()
    manager.force_gc()


def get_current_memory_mb() -> float:
    """
    Get current process memory usage in MB.
    
    Returns:
        Memory usage in MB, or 0 if unavailable
    """
    if not HAS_PSUTIL:
        return 0.0
    
    try:
        process = psutil.Process()
        return process.memory_info().rss / (1024 * 1024)
    except Exception:
        return 0.0


class ResourceTracker:
    """
    Tracks resources and ensures cleanup.
    
    Usage:
        tracker = ResourceTracker()
        
        file = open('file.txt', 'r')
        tracker.track(file, file.close)
        
        # Later...
        tracker.cleanup_all()
    """
    
    def __init__(self):
        """Initialize tracker."""
        self.resources: Dict[int, tuple] = {}
    
    def track(self, resource: Any, cleanup: Optional[Callable] = None):
        """
        Track a resource.
        
        Args:
            resource: Resource to track
            cleanup: Cleanup function (defaults to resource.close())
        """
        cleanup_func = cleanup
        if cleanup_func is None and hasattr(resource, 'close'):
            cleanup_func = resource.close
        
        if cleanup_func:
            try:
                self.resources[id(resource)] = (weakref.ref(resource), cleanup_func)
            except TypeError:
                # Some objects don't support weak references
                # Store them directly with cleanup
                self.resources[id(resource)] = (resource, cleanup_func)
    
    def untrack(self, resource: Any):
        """
        Untrack a resource.
        
        Args:
            resource: Resource to untrack
        """
        self.resources.pop(id(resource), None)
    
    def cleanup_all(self):
        """Cleanup all tracked resources."""
        for resource_id, (ref_or_obj, cleanup) in list(self.resources.items()):
            try:
                # Check if it's a weak reference or direct reference
                if isinstance(ref_or_obj, weakref.ref):
                    if ref_or_obj() is not None:  # Resource still exists
                        cleanup()
                else:
                    # Direct reference
                    cleanup()
            except Exception:
                pass
            
            # Remove from tracking
            self.resources.pop(resource_id, None)
        
        # Force GC
        gc.collect()
    
    def __del__(self):
        """Cleanup on deletion."""
        self.cleanup_all()
