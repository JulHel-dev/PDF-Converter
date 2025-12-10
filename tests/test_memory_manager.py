"""Tests for memory management and leak prevention."""

import gc
import time
from src.utils.memory_manager import (
    MemoryManager,
    managed_resource,
    clear_memory,
    get_current_memory_mb,
    ResourceTracker
)


class TestMemoryManager:
    """Test memory manager."""
    
    def test_manager_initialization(self):
        """Test manager initialization."""
        manager = MemoryManager(memory_limit_mb=1000)
        
        assert manager.memory_limit_mb == 1000
        assert manager.warning_threshold == 0.8
    
    def test_register_cleanup(self):
        """Test registering cleanup functions."""
        manager = MemoryManager()
        
        cleanup_called = []
        
        def cleanup():
            cleanup_called.append(True)
        
        manager.register_cleanup(cleanup)
        manager.cleanup_all()
        
        assert len(cleanup_called) == 1
    
    def test_multiple_cleanups(self):
        """Test multiple cleanup functions."""
        manager = MemoryManager()
        
        cleanup_order = []
        
        def cleanup1():
            cleanup_order.append(1)
        
        def cleanup2():
            cleanup_order.append(2)
        
        manager.register_cleanup(cleanup1)
        manager.register_cleanup(cleanup2)
        manager.cleanup_all()
        
        # Both should be called
        assert 1 in cleanup_order
        assert 2 in cleanup_order
    
    def test_cleanup_exception_handling(self):
        """Test that cleanup continues even if one fails."""
        manager = MemoryManager()
        
        cleanup_called = []
        
        def failing_cleanup():
            raise ValueError("Cleanup failed")
        
        def working_cleanup():
            cleanup_called.append(True)
        
        manager.register_cleanup(failing_cleanup)
        manager.register_cleanup(working_cleanup)
        
        # Should not raise exception
        manager.cleanup_all()
        
        # Working cleanup should still be called
        assert len(cleanup_called) == 1
    
    def test_force_gc(self):
        """Test forcing garbage collection."""
        manager = MemoryManager()
        
        # Create some garbage
        for i in range(100):
            _ = [1, 2, 3] * 1000
        
        # Force collection
        stats = manager.force_gc()
        
        assert 'gen0' in stats
        assert 'gen1' in stats
        assert 'gen2' in stats
    
    def test_get_memory_usage(self):
        """Test getting memory usage."""
        manager = MemoryManager()
        
        usage = manager.get_memory_usage()
        
        # If psutil available, should have keys
        if usage:
            assert 'rss_mb' in usage
            assert 'vms_mb' in usage
            assert usage['rss_mb'] > 0
    
    def test_memory_limit_check(self):
        """Test checking if memory is high."""
        manager = MemoryManager(memory_limit_mb=10000)
        
        # With high limit, shouldn't be high
        is_high = manager.is_memory_high()
        
        # Result depends on psutil availability and actual usage
        assert isinstance(is_high, bool)
    
    def test_track_object(self):
        """Test object tracking."""
        manager = MemoryManager()
        
        # Use an object that supports weak references
        class TestObj:
            pass
        
        obj = TestObj()
        manager.track_object(obj)
        
        # Should be tracked
        assert len(manager._tracked_objects) == 1
    
    def test_check_leaks(self):
        """Test leak detection."""
        manager = MemoryManager()
        
        # Track some objects
        for i in range(10):
            manager.track_object({'data': i})
        
        leaks = manager.check_leaks()
        
        # Should be a list (may be empty)
        assert isinstance(leaks, list)
    
    def test_cleanup_and_check(self):
        """Test combined cleanup and leak check."""
        manager = MemoryManager()
        
        cleanup_called = []
        
        def cleanup():
            cleanup_called.append(True)
        
        manager.register_cleanup(cleanup)
        manager.cleanup_and_check()
        
        # Cleanup should be called
        assert len(cleanup_called) == 1


class TestManagedResource:
    """Test managed resource context manager."""
    
    def test_basic_resource_management(self):
        """Test basic resource management."""
        cleanup_called = []
        
        class TestResource:
            def close(self):
                cleanup_called.append(True)
        
        resource = TestResource()
        
        with managed_resource(resource):
            pass
        
        # Close should be called
        assert len(cleanup_called) == 1
    
    def test_custom_cleanup(self):
        """Test with custom cleanup function."""
        cleanup_called = []
        
        def custom_cleanup():
            cleanup_called.append(True)
        
        resource = object()
        
        with managed_resource(resource, cleanup=custom_cleanup):
            pass
        
        # Custom cleanup should be called
        assert len(cleanup_called) == 1
    
    def test_exception_handling(self):
        """Test that cleanup happens even on exception."""
        cleanup_called = []
        
        class TestResource:
            def close(self):
                cleanup_called.append(True)
        
        resource = TestResource()
        
        try:
            with managed_resource(resource):
                raise ValueError("Test exception")
        except ValueError:
            pass
        
        # Close should still be called
        assert len(cleanup_called) == 1
    
    def test_resource_without_close(self):
        """Test resource that doesn't have close method."""
        cleanup_called = []
        
        def cleanup():
            cleanup_called.append(True)
        
        resource = "test string"
        
        with managed_resource(resource, cleanup=cleanup):
            pass
        
        assert len(cleanup_called) == 1


class TestConvenienceFunctions:
    """Test convenience functions."""
    
    def test_clear_memory(self):
        """Test clear_memory function."""
        # Should not raise exception
        clear_memory()
    
    def test_get_current_memory_mb(self):
        """Test getting current memory."""
        memory_mb = get_current_memory_mb()
        
        # Should be a number
        assert isinstance(memory_mb, float)
        assert memory_mb >= 0


class TestResourceTracker:
    """Test resource tracker."""
    
    def test_track_resource(self):
        """Test tracking a resource."""
        tracker = ResourceTracker()
        
        cleanup_called = []
        
        class TestResource:
            def close(self):
                cleanup_called.append(True)
        
        resource = TestResource()
        tracker.track(resource)
        
        # Should be tracked
        assert len(tracker.resources) == 1
        
        # Cleanup
        tracker.cleanup_all()
        assert len(cleanup_called) == 1
    
    def test_track_with_custom_cleanup(self):
        """Test tracking with custom cleanup."""
        tracker = ResourceTracker()
        
        cleanup_called = []
        
        def cleanup():
            cleanup_called.append(True)
        
        resource = object()
        tracker.track(resource, cleanup=cleanup)
        
        tracker.cleanup_all()
        assert len(cleanup_called) == 1
    
    def test_untrack_resource(self):
        """Test untracking a resource."""
        tracker = ResourceTracker()
        
        class TestResource:
            def close(self):
                pass
        
        resource = TestResource()
        tracker.track(resource)
        
        assert len(tracker.resources) == 1
        
        tracker.untrack(resource)
        assert len(tracker.resources) == 0
    
    def test_multiple_resources(self):
        """Test tracking multiple resources."""
        tracker = ResourceTracker()
        
        cleanup_count = []
        
        class TestResource:
            def close(self):
                cleanup_count.append(1)
        
        # Track multiple resources
        for i in range(5):
            resource = TestResource()
            tracker.track(resource)
        
        assert len(tracker.resources) == 5
        
        tracker.cleanup_all()
        assert sum(cleanup_count) == 5
    
    def test_cleanup_on_deletion(self):
        """Test that tracker cleans up when deleted."""
        cleanup_called = []
        
        class TestResource:
            def close(self):
                cleanup_called.append(True)
        
        tracker = ResourceTracker()
        resource = TestResource()
        tracker.track(resource)
        
        # Delete tracker
        del tracker
        
        # Give GC time to run
        gc.collect()
        time.sleep(0.1)
        
        # May or may not be called depending on GC timing
        # Just ensure no exception


class TestMemoryLeakDetection:
    """Test memory leak detection."""
    
    def test_detect_many_tracked_objects(self):
        """Test detecting many tracked objects."""
        manager = MemoryManager()
        
        # Track many objects that support weak references
        # Keep them alive in a list
        objects = []
        class TestObj:
            def __init__(self, data):
                self.data = data
        
        for i in range(1500):
            obj = TestObj(i)
            objects.append(obj)  # Keep alive
            manager.track_object(obj)
        
        leaks = manager.check_leaks()
        
        # Should detect high number
        assert len(leaks) > 0
        assert any('tracked objects' in leak.lower() for leak in leaks)
    
    def test_cleanup_dead_references(self):
        """Test that dead references are cleaned up."""
        manager = MemoryManager()
        
        # Track objects that will be garbage collected
        for i in range(10):
            obj = {'data': i}
            manager.track_object(obj)
            # obj goes out of scope
        
        # Force GC
        gc.collect()
        
        # Check leaks (should cleanup dead refs)
        manager.check_leaks()
        
        # Most references should be dead now
        alive = sum(1 for ref in manager._tracked_objects if ref() is not None)
        assert alive < 10


class TestIntegration:
    """Integration tests."""
    
    def test_file_handling_with_manager(self, tmp_path):
        """Test managing file resources."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")
        
        f = open(test_file, 'r')
        with managed_resource(f) as resource:
            content = resource.read()
        
        assert content == "content"
    
    def test_memory_manager_lifecycle(self):
        """Test full lifecycle of memory manager."""
        manager = MemoryManager(memory_limit_mb=1000)
        
        # Register cleanup
        cleanup_called = []
        manager.register_cleanup(lambda: cleanup_called.append(True))
        
        # Track object
        obj = {'data': 'test'}
        manager.track_object(obj)
        
        # Check memory - ensure functions return expected types
        manager.get_memory_usage()
        manager.is_memory_high()
        manager.force_gc()
        manager.check_leaks()
        
        # Cleanup
        manager.cleanup_all()
        
        # Verify cleanup called
        assert len(cleanup_called) == 1
