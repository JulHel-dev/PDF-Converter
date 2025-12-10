"""
Graceful Shutdown Handler

Handles SIGINT, SIGTERM, and other termination signals for graceful cleanup.
Ensures temporary files are cleaned up and resources are released properly.

References:
- Signal handling: https://docs.python.org/3/library/signal.html
"""

import signal
import sys
import atexit
from typing import Callable, List, Optional
import threading

try:
    from src.logging.event_monitor import EventMonitor
except ImportError:
    from logging.event_monitor import EventMonitor

try:
    from src.security.temp_file_security import cleanup_temp_files
except ImportError:
    from security.temp_file_security import cleanup_temp_files


class ShutdownHandler:
    """
    Manages graceful shutdown of the application.
    
    Features:
    - Handles SIGINT (Ctrl+C) and SIGTERM signals
    - Executes cleanup callbacks in reverse order
    - Prevents duplicate shutdown
    - Thread-safe
    
    Usage:
        handler = ShutdownHandler()
        handler.register_cleanup(cleanup_function)
        handler.install_handlers()
    """
    
    def __init__(self):
        self.monitor = EventMonitor()
        self._cleanup_callbacks: List[Callable] = []
        self._shutdown_in_progress = False
        self._lock = threading.Lock()
        self._original_handlers = {}
    
    def register_cleanup(self, callback: Callable, description: str = ""):
        """
        Register a cleanup callback to be executed on shutdown.
        
        Callbacks are executed in reverse order (LIFO).
        
        Args:
            callback: Function to call on shutdown
            description: Description of the cleanup task
        """
        with self._lock:
            self._cleanup_callbacks.append((callback, description))
            
            self.monitor.log_event('cleanup_registered', {
                'callback': callback.__name__,
                'description': description,
                'total_callbacks': len(self._cleanup_callbacks)
            }, severity='DEBUG')
    
    def _execute_cleanup(self, reason: str = "shutdown"):
        """
        Execute all registered cleanup callbacks.
        
        Args:
            reason: Reason for cleanup (for logging)
        """
        with self._lock:
            if self._shutdown_in_progress:
                return
            self._shutdown_in_progress = True
        
        self.monitor.log_event('shutdown_initiated', {
            'reason': reason,
            'callback_count': len(self._cleanup_callbacks)
        }, severity='INFO')
        
        # Execute callbacks in reverse order (LIFO)
        for callback, description in reversed(self._cleanup_callbacks):
            try:
                self.monitor.log_event('cleanup_executing', {
                    'callback': callback.__name__,
                    'description': description
                }, severity='DEBUG')
                
                callback()
                
                self.monitor.log_event('cleanup_success', {
                    'callback': callback.__name__,
                    'description': description
                }, severity='DEBUG')
                
            except Exception as e:
                self.monitor.log_event('cleanup_failed', {
                    'callback': callback.__name__,
                    'description': description,
                    'error': str(e),
                    'error_type': type(e).__name__
                }, severity='ERROR')
        
        # Clean up temp files
        try:
            cleanup_temp_files()
        except Exception as e:
            self.monitor.log_event('temp_cleanup_failed', {
                'error': str(e)
            }, severity='WARNING')
        
        self.monitor.log_event('shutdown_complete', {
            'reason': reason
        }, severity='INFO')
    
    def _signal_handler(self, signum, frame):
        """
        Handle termination signals.
        
        Args:
            signum: Signal number
            frame: Current stack frame
        """
        signal_name = signal.Signals(signum).name
        
        self.monitor.log_event('signal_received', {
            'signal': signal_name,
            'signal_number': signum
        }, severity='WARNING')
        
        print(f"\n⚠️  Received {signal_name}, shutting down gracefully...")
        
        self._execute_cleanup(reason=f"signal_{signal_name}")
        
        # Call original handler if it exists
        if signum in self._original_handlers and self._original_handlers[signum] not in (None, signal.SIG_DFL, signal.SIG_IGN):
            self._original_handlers[signum](signum, frame)
        else:
            # Exit cleanly
            sys.exit(0)
    
    def install_handlers(self):
        """
        Install signal handlers for graceful shutdown.
        
        Handles:
        - SIGINT (Ctrl+C)
        - SIGTERM (kill command)
        - On Windows: also registers atexit handler
        """
        try:
            # Store original handlers
            self._original_handlers[signal.SIGINT] = signal.signal(signal.SIGINT, self._signal_handler)
            self._original_handlers[signal.SIGTERM] = signal.signal(signal.SIGTERM, self._signal_handler)
            
            # Register atexit handler as fallback
            atexit.register(lambda: self._execute_cleanup(reason="atexit"))
            
            self.monitor.log_event('shutdown_handlers_installed', {
                'signals': ['SIGINT', 'SIGTERM'],
                'atexit_registered': True
            }, severity='INFO')
            
        except Exception as e:
            self.monitor.log_event('handler_installation_failed', {
                'error': str(e)
            }, severity='ERROR')
    
    def shutdown(self):
        """Manually trigger shutdown."""
        self._execute_cleanup(reason="manual")


# Global shutdown handler instance
_shutdown_handler: Optional[ShutdownHandler] = None
_handler_lock = threading.Lock()


def get_shutdown_handler() -> ShutdownHandler:
    """Get or create the global shutdown handler instance."""
    global _shutdown_handler
    
    with _handler_lock:
        if _shutdown_handler is None:
            _shutdown_handler = ShutdownHandler()
        return _shutdown_handler


def register_cleanup(callback: Callable, description: str = ""):
    """
    Register a cleanup callback for graceful shutdown.
    
    Args:
        callback: Function to call on shutdown
        description: Description of cleanup task
    """
    get_shutdown_handler().register_cleanup(callback, description)


def install_shutdown_handlers():
    """Install signal handlers for graceful shutdown."""
    get_shutdown_handler().install_handlers()


def trigger_shutdown():
    """Manually trigger graceful shutdown."""
    get_shutdown_handler().shutdown()
