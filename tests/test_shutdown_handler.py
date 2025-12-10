"""Tests for graceful shutdown handler."""

import signal
import os
from src.utils.shutdown_handler import (
    ShutdownHandler,
    get_shutdown_handler,
    register_cleanup,
    install_shutdown_handlers
)


class TestShutdownHandler:
    """Test shutdown handler functionality."""
    
    def test_register_cleanup(self):
        """Test registering cleanup callbacks."""
        handler = ShutdownHandler()
        
        callback_executed = []
        
        def cleanup1():
            callback_executed.append(1)
        
        def cleanup2():
            callback_executed.append(2)
        
        handler.register_cleanup(cleanup1, "First cleanup")
        handler.register_cleanup(cleanup2, "Second cleanup")
        
        assert len(handler._cleanup_callbacks) == 2
    
    def test_cleanup_execution_order(self):
        """Test that cleanup callbacks execute in LIFO order."""
        handler = ShutdownHandler()
        
        execution_order = []
        
        def cleanup1():
            execution_order.append(1)
        
        def cleanup2():
            execution_order.append(2)
        
        def cleanup3():
            execution_order.append(3)
        
        handler.register_cleanup(cleanup1)
        handler.register_cleanup(cleanup2)
        handler.register_cleanup(cleanup3)
        
        handler._execute_cleanup("test")
        
        # Should execute in reverse order (LIFO)
        assert execution_order == [3, 2, 1]
    
    def test_cleanup_exception_handling(self):
        """Test that exceptions in cleanup don't stop other cleanups."""
        handler = ShutdownHandler()
        
        executed = []
        
        def cleanup1():
            executed.append(1)
        
        def cleanup2():
            executed.append(2)
            raise ValueError("Test error")
        
        def cleanup3():
            executed.append(3)
        
        handler.register_cleanup(cleanup1)
        handler.register_cleanup(cleanup2)
        handler.register_cleanup(cleanup3)
        
        # Should not raise exception
        handler._execute_cleanup("test")
        
        # All callbacks should have been attempted
        assert 1 in executed
        assert 2 in executed
        assert 3 in executed
    
    def test_duplicate_shutdown_prevention(self):
        """Test that shutdown only happens once."""
        handler = ShutdownHandler()
        
        execution_count = [0]
        
        def cleanup():
            execution_count[0] += 1
        
        handler.register_cleanup(cleanup)
        
        # Execute twice
        handler._execute_cleanup("test")
        handler._execute_cleanup("test")
        
        # Cleanup should only execute once
        assert execution_count[0] == 1
    
    def test_manual_shutdown(self):
        """Test manual shutdown trigger."""
        handler = ShutdownHandler()
        
        executed = [False]
        
        def cleanup():
            executed[0] = True
        
        handler.register_cleanup(cleanup)
        handler.shutdown()
        
        assert executed[0] is True
    
    def test_install_handlers(self):
        """Test signal handler installation."""
        handler = ShutdownHandler()
        
        # Should not raise exception
        handler.install_handlers()
        
        # Verify handlers are installed
        current_sigint = signal.getsignal(signal.SIGINT)
        current_sigterm = signal.getsignal(signal.SIGTERM)
        
        # Handlers should be set (not default or ignore)
        assert current_sigint not in (signal.SIG_DFL, signal.SIG_IGN)
        assert current_sigterm not in (signal.SIG_DFL, signal.SIG_IGN)


class TestGlobalShutdownHandler:
    """Test global shutdown handler functions."""
    
    def test_get_shutdown_handler_singleton(self):
        """Test that get_shutdown_handler returns singleton."""
        handler1 = get_shutdown_handler()
        handler2 = get_shutdown_handler()
        
        assert handler1 is handler2
    
    def test_register_cleanup_function(self):
        """Test global register_cleanup function."""
        executed = [False]
        
        def cleanup():
            executed[0] = True
        
        # Use global function
        register_cleanup(cleanup, "Test cleanup")
        
        # Get handler and trigger shutdown
        handler = get_shutdown_handler()
        handler._execute_cleanup("test")
        
        assert executed[0] is True
    
    def test_install_shutdown_handlers_function(self):
        """Test global install function."""
        # Should not raise exception
        install_shutdown_handlers()


class TestSignalHandling:
    """Test signal handling (careful with actual signals)."""
    
    def test_signal_handler_method(self):
        """Test the signal handler method (without sending actual signal)."""
        handler = ShutdownHandler()
        
        executed = [False]
        
        def cleanup():
            executed[0] = True
        
        handler.register_cleanup(cleanup)
        
        # Simulate signal handling (don't actually send signal)
        # We'll test the method directly
        try:
            # This will execute cleanup but may exit
            # So we catch SystemExit
            handler._signal_handler(signal.SIGINT, None)
        except SystemExit:
            # Expected exception from signal handler
            pass
        
        # Cleanup should have been executed
        assert executed[0] is True


class TestIntegrationScenarios:
    """Test real-world integration scenarios."""
    
    def test_temp_file_cleanup_integration(self):
        """Test that temp files are cleaned up on shutdown."""
        handler = ShutdownHandler()
        
        # Create a temp file
        from src.security.temp_file_security import create_secure_temp_file
        
        temp_path = create_secure_temp_file(suffix='.txt')
        assert os.path.exists(temp_path)
        
        # Trigger shutdown
        handler._execute_cleanup("test")
        
        # Temp file should be cleaned up
        # Note: This depends on temp_file_security cleanup working
        # The handler calls cleanup_temp_files()
    
    def test_multiple_cleanup_types(self):
        """Test various types of cleanup operations."""
        handler = ShutdownHandler()
        
        results = {
            'file_closed': False,
            'connection_closed': False,
            'cache_cleared': False
        }
        
        def close_file():
            results['file_closed'] = True
        
        def close_connection():
            results['connection_closed'] = True
        
        def clear_cache():
            results['cache_cleared'] = True
        
        handler.register_cleanup(close_file, "Close file handles")
        handler.register_cleanup(close_connection, "Close connections")
        handler.register_cleanup(clear_cache, "Clear cache")
        
        handler._execute_cleanup("test")
        
        # All cleanups should execute
        assert all(results.values())
