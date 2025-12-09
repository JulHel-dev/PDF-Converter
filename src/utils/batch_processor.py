"""
Batch Processing with Resource Management

Features:
- Configurable max concurrent workers (BATCH_MAX_CONCURRENT from settings)
- Memory monitoring with psutil (pause if exceeds BATCH_MEMORY_LIMIT_MB)
- Progress tracking with statistics (success/fail counts)
- Batch state persistence for resume capability
- Graceful cancellation support
"""

import threading
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Callable, Dict, Any, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum

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

try:
    from src.config.settings import (
        BATCH_MAX_CONCURRENT,
        BATCH_MEMORY_LIMIT_MB,
        BATCH_CHECKPOINT_INTERVAL,
        TMP_FOLDER
    )
except ImportError:
    BATCH_MAX_CONCURRENT = 4
    BATCH_MEMORY_LIMIT_MB = 2000
    BATCH_CHECKPOINT_INTERVAL = 10
    TMP_FOLDER = "/tmp"

BATCH_PROGRESS_FILE = os.path.join(TMP_FOLDER, "batch_progress.json")


class BatchStatus(Enum):
    """Batch processing status."""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


@dataclass
class BatchProgress:
    """Tracks batch processing progress."""
    total: int = 0
    completed: int = 0
    success: int = 0
    failed: int = 0
    skipped: int = 0
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    status: str = BatchStatus.PENDING.value
    failed_items: List[Dict[str, str]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BatchProgress':
        """Create from dictionary."""
        return cls(**data)
    
    @property
    def completion_percentage(self) -> float:
        """Calculate completion percentage."""
        if self.total == 0:
            return 0.0
        return (self.completed / self.total) * 100
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.completed == 0:
            return 0.0
        return (self.success / self.completed) * 100


class BatchProcessor:
    """
    Processes multiple items concurrently with resource management.
    
    Features:
    - Thread pool execution with configurable workers
    - Memory monitoring (pauses if exceeds limit)
    - Progress tracking and persistence
    - Graceful cancellation
    
    Usage:
        processor = BatchProcessor(max_workers=4)
        
        def process_item(item):
            # Process single item
            return result
        
        results = processor.process_batch(items, process_item)
    """
    
    def __init__(
        self,
        max_workers: Optional[int] = None,
        memory_limit_mb: Optional[int] = None,
        checkpoint_interval: Optional[int] = None,
        progress_file: Optional[str] = None
    ):
        """
        Initialize batch processor.
        
        Args:
            max_workers: Maximum concurrent workers (default from settings)
            memory_limit_mb: Memory limit in MB (default from settings)
            checkpoint_interval: Save progress every N items
            progress_file: Path to progress file for persistence
        """
        self.max_workers = max_workers or BATCH_MAX_CONCURRENT
        self.memory_limit_mb = memory_limit_mb or BATCH_MEMORY_LIMIT_MB
        self.checkpoint_interval = checkpoint_interval or BATCH_CHECKPOINT_INTERVAL
        self.progress_file = progress_file or BATCH_PROGRESS_FILE
        
        self.monitor = EventMonitor() if EventMonitor else None
        self.progress = BatchProgress()
        self._cancelled = False
        self._pause_event = threading.Event()
        self._pause_event.set()  # Initially not paused
        
        self._lock = threading.Lock()
        
        self._log("Batch processor initialized", {
            'max_workers': self.max_workers,
            'memory_limit_mb': self.memory_limit_mb,
            'has_psutil': HAS_PSUTIL
        }, 'INFO')
    
    def _log(self, message: str, data: Dict[str, Any], severity: str = 'INFO'):
        """Log event if monitor available."""
        if self.monitor:
            self.monitor.log_event(f'batch_processor_{message.lower().replace(" ", "_")}', data, severity)
    
    def process_batch(
        self,
        items: List[Any],
        process_func: Callable[[Any], Any],
        resume: bool = False
    ) -> Dict[str, Any]:
        """
        Process a batch of items concurrently.
        
        Args:
            items: List of items to process
            process_func: Function to process each item
            resume: Whether to resume from saved progress
            
        Returns:
            Dictionary with results and statistics
        """
        # Initialize or resume progress
        if resume and os.path.exists(self.progress_file):
            self._load_progress()
            self._log("Resuming batch processing", {'completed': self.progress.completed}, 'INFO')
        else:
            self.progress = BatchProgress(
                total=len(items),
                start_time=datetime.now().isoformat(),
                status=BatchStatus.RUNNING.value
            )
        
        self._cancelled = False
        results = []
        
        try:
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Submit all tasks
                future_to_item = {}
                for i, item in enumerate(items):
                    if resume and i < self.progress.completed:
                        continue  # Skip already processed
                    
                    future = executor.submit(self._process_with_monitoring, item, process_func)
                    future_to_item[future] = (i, item)
                
                # Process completed tasks
                for future in as_completed(future_to_item):
                    if self._cancelled:
                        self._log("Batch processing cancelled", {}, 'WARNING')
                        break
                    
                    # Wait if paused
                    self._pause_event.wait()
                    
                    # Check memory before processing result
                    self._check_memory()
                    
                    item_index, item = future_to_item[future]
                    
                    try:
                        result = future.result()
                        results.append(result)
                        
                        with self._lock:
                            self.progress.completed += 1
                            self.progress.success += 1
                        
                        self._log("Item processed", {
                            'index': item_index,
                            'success': True
                        }, 'DEBUG')
                    
                    except Exception as e:
                        with self._lock:
                            self.progress.completed += 1
                            self.progress.failed += 1
                            self.progress.failed_items.append({
                                'index': item_index,
                                'item': str(item),
                                'error': str(e)
                            })
                        
                        self._log("Item processing failed", {
                            'index': item_index,
                            'error': str(e)
                        }, 'ERROR')
                    
                    # Checkpoint progress
                    if self.progress.completed % self.checkpoint_interval == 0:
                        self._save_progress()
        
        finally:
            # Finalize progress
            self.progress.end_time = datetime.now().isoformat()
            self.progress.status = (
                BatchStatus.CANCELLED.value if self._cancelled
                else BatchStatus.COMPLETED.value
            )
            self._save_progress()
        
        return {
            'results': results,
            'progress': self.progress.to_dict(),
            'success': self.progress.failed == 0
        }
    
    def _process_with_monitoring(
        self,
        item: Any,
        process_func: Callable[[Any], Any]
    ) -> Any:
        """
        Process item with monitoring wrapper.
        
        Args:
            item: Item to process
            process_func: Processing function
            
        Returns:
            Processing result
        """
        try:
            return process_func(item)
        except Exception as e:
            self._log("Processing error", {
                'item': str(item),
                'error': str(e)
            }, 'ERROR')
            raise
    
    def _check_memory(self):
        """Check memory usage and pause if exceeds limit."""
        if not HAS_PSUTIL:
            return
        
        try:
            process = psutil.Process()
            memory_mb = process.memory_info().rss / (1024 * 1024)
            
            if memory_mb > self.memory_limit_mb:
                self._log("Memory limit exceeded", {
                    'current_mb': round(memory_mb, 2),
                    'limit_mb': self.memory_limit_mb
                }, 'WARNING')
                
                # Pause processing
                self._pause_event.clear()
                
                # Wait for memory to drop
                while memory_mb > self.memory_limit_mb * 0.8:
                    time.sleep(1)
                    memory_mb = process.memory_info().rss / (1024 * 1024)
                
                # Resume processing
                self._pause_event.set()
                self._log("Memory usage normalized", {
                    'current_mb': round(memory_mb, 2)
                }, 'INFO')
        
        except Exception as e:
            self._log("Memory check failed", {'error': str(e)}, 'WARNING')
    
    def _save_progress(self):
        """Save progress to file."""
        try:
            with open(self.progress_file, 'w') as f:
                json.dump(self.progress.to_dict(), f, indent=2)
            
            self._log("Progress saved", {
                'completed': self.progress.completed,
                'total': self.progress.total
            }, 'DEBUG')
        
        except Exception as e:
            self._log("Failed to save progress", {'error': str(e)}, 'ERROR')
    
    def _load_progress(self):
        """Load progress from file."""
        try:
            with open(self.progress_file, 'r') as f:
                data = json.load(f)
                self.progress = BatchProgress.from_dict(data)
            
            self._log("Progress loaded", {
                'completed': self.progress.completed,
                'total': self.progress.total
            }, 'INFO')
        
        except Exception as e:
            self._log("Failed to load progress", {'error': str(e)}, 'ERROR')
            self.progress = BatchProgress()
    
    def cancel(self):
        """Cancel batch processing."""
        self._cancelled = True
        self._log("Cancellation requested", {}, 'WARNING')
    
    def pause(self):
        """Pause batch processing."""
        self._pause_event.clear()
        self._log("Processing paused", {}, 'INFO')
    
    def resume(self):
        """Resume batch processing."""
        self._pause_event.set()
        self._log("Processing resumed", {}, 'INFO')
    
    def get_progress(self) -> BatchProgress:
        """Get current progress."""
        return self.progress
    
    def clear_progress(self):
        """Clear saved progress file."""
        try:
            if os.path.exists(self.progress_file):
                os.remove(self.progress_file)
                self._log("Progress cleared", {}, 'INFO')
        except Exception as e:
            self._log("Failed to clear progress", {'error': str(e)}, 'ERROR')


def process_batch_simple(
    items: List[Any],
    process_func: Callable[[Any], Any],
    max_workers: Optional[int] = None
) -> List[Any]:
    """
    Simple batch processing convenience function.
    
    Args:
        items: Items to process
        process_func: Processing function
        max_workers: Maximum concurrent workers
        
    Returns:
        List of results
    """
    processor = BatchProcessor(max_workers=max_workers)
    result = processor.process_batch(items, process_func)
    return result['results']
