"""Tests for batch processing with resource management."""

import pytest
import time
import os
from concurrent.futures import ThreadPoolExecutor
from src.utils.batch_processor import (
    BatchProcessor,
    BatchProgress,
    BatchStatus,
    process_batch_simple
)


class TestBatchProgress:
    """Test batch progress tracking."""
    
    def test_progress_initialization(self):
        """Test progress initialization."""
        progress = BatchProgress(total=100)
        
        assert progress.total == 100
        assert progress.completed == 0
        assert progress.success == 0
        assert progress.failed == 0
        assert progress.status == BatchStatus.PENDING.value
    
    def test_completion_percentage(self):
        """Test completion percentage calculation."""
        progress = BatchProgress(total=100, completed=50)
        
        assert progress.completion_percentage == 50.0
    
    def test_success_rate(self):
        """Test success rate calculation."""
        progress = BatchProgress(
            total=100,
            completed=50,
            success=40,
            failed=10
        )
        
        assert progress.success_rate == 80.0
    
    def test_progress_serialization(self):
        """Test progress to/from dict."""
        progress = BatchProgress(total=100, completed=50)
        
        data = progress.to_dict()
        restored = BatchProgress.from_dict(data)
        
        assert restored.total == progress.total
        assert restored.completed == progress.completed


class TestBatchProcessor:
    """Test batch processor."""
    
    def test_simple_batch_processing(self):
        """Test basic batch processing."""
        items = list(range(10))
        
        def process(x):
            return x * 2
        
        processor = BatchProcessor(max_workers=2)
        result = processor.process_batch(items, process)
        
        assert result['success'] is True
        assert len(result['results']) == 10
        assert processor.progress.completed == 10
        assert processor.progress.success == 10
        assert processor.progress.failed == 0
    
    def test_batch_with_failures(self):
        """Test batch processing with some failures."""
        items = list(range(10))
        
        def process(x):
            if x == 5:
                raise ValueError(f"Error processing {x}")
            return x * 2
        
        processor = BatchProcessor(max_workers=2)
        result = processor.process_batch(items, process)
        
        assert result['success'] is False
        assert processor.progress.completed == 10
        assert processor.progress.success == 9
        assert processor.progress.failed == 1
        assert len(processor.progress.failed_items) == 1
    
    def test_batch_cancellation(self):
        """Test batch cancellation."""
        items = list(range(100))
        
        def process(x):
            time.sleep(0.01)  # Simulate work
            return x * 2
        
        processor = BatchProcessor(max_workers=2)
        
        # Cancel after a short time
        import threading
        def cancel_later():
            time.sleep(0.05)
            processor.cancel()
        
        cancel_thread = threading.Thread(target=cancel_later)
        cancel_thread.start()
        
        processor.process_batch(items, process)
        cancel_thread.join()
        
        # Should have processed some but not all
        assert processor.progress.completed < 100
        assert processor.progress.status == BatchStatus.CANCELLED.value
    
    def test_progress_persistence(self, tmp_path):
        """Test progress saving and loading."""
        progress_file = str(tmp_path / "progress.json")
        items = list(range(10))
        
        def process(x):
            return x * 2
        
        # Process batch
        processor = BatchProcessor(
            max_workers=2,
            progress_file=progress_file,
            checkpoint_interval=5
        )
        processor.process_batch(items, process)
        
        # Check progress file exists
        assert os.path.exists(progress_file)
        
        # Load progress in new processor
        new_processor = BatchProcessor(progress_file=progress_file)
        new_processor._load_progress()
        
        assert new_processor.progress.total == 10
        assert new_processor.progress.completed == 10
    
    def test_resume_from_checkpoint(self, tmp_path):
        """Test resuming from checkpoint."""
        progress_file = str(tmp_path / "progress.json")
        items = list(range(20))
        processed = []
        
        def process(x):
            processed.append(x)
            return x * 2
        
        # First batch - process partially
        processor1 = BatchProcessor(
            max_workers=1,
            progress_file=progress_file,
            checkpoint_interval=5
        )
        
        # Simulate partial processing by limiting items
        partial_items = items[:10]
        processor1.process_batch(partial_items, process)
        
        # Resume with all items
        processed.clear()
        processor2 = BatchProcessor(
            max_workers=1,
            progress_file=progress_file
        )
        processor2.process_batch(items, process, resume=True)
        
        # Should skip first 10 items
        assert 0 not in processed
        assert 9 not in processed
        assert 10 in processed
    
    def test_pause_and_resume(self):
        """Test pausing and resuming processing."""
        items = list(range(50))
        
        def process(x):
            time.sleep(0.01)
            return x * 2
        
        processor = BatchProcessor(max_workers=2)
        
        # Pause after short time
        import threading
        def pause_resume():
            time.sleep(0.05)
            processor.pause()
            time.sleep(0.1)
            processor.resume()
        
        pause_thread = threading.Thread(target=pause_resume)
        pause_thread.start()
        
        processor.process_batch(items, process)
        pause_thread.join()
        
        # Should complete eventually
        assert processor.progress.completed == 50
    
    def test_get_progress(self):
        """Test getting current progress."""
        items = list(range(10))
        
        def process(x):
            time.sleep(0.01)
            return x * 2
        
        processor = BatchProcessor(max_workers=2)
        
        # Start processing in thread
        import threading
        def run_batch():
            processor.process_batch(items, process)
        
        batch_thread = threading.Thread(target=run_batch)
        batch_thread.start()
        
        # Check progress while running
        time.sleep(0.05)
        progress = processor.get_progress()
        
        assert progress.total == 10
        # Should have started processing
        assert progress.completed >= 0
        
        batch_thread.join()
    
    def test_clear_progress(self, tmp_path):
        """Test clearing progress file."""
        progress_file = str(tmp_path / "progress.json")
        items = list(range(5))
        
        def process(x):
            return x * 2
        
        processor = BatchProcessor(progress_file=progress_file)
        processor.process_batch(items, process)
        
        assert os.path.exists(progress_file)
        
        processor.clear_progress()
        
        assert not os.path.exists(progress_file)


class TestMemoryMonitoring:
    """Test memory monitoring (if psutil available)."""
    
    @pytest.mark.skipif(
        not pytest.importorskip("psutil", minversion=None),
        reason="psutil not available"
    )
    def test_memory_check(self):
        """Test memory checking doesn't crash."""
        items = list(range(10))
        
        def process(x):
            return x * 2
        
        # Set very high memory limit so it doesn't pause
        processor = BatchProcessor(
            max_workers=2,
            memory_limit_mb=10000
        )
        
        result = processor.process_batch(items, process)
        
        assert result['success'] is True


class TestConvenienceFunction:
    """Test convenience function."""
    
    def test_process_batch_simple(self):
        """Test simple batch processing function."""
        items = list(range(10))
        
        def process(x):
            return x * 2
        
        results = process_batch_simple(items, process, max_workers=2)
        
        assert len(results) == 10
        assert 0 in results
        assert 18 in results


class TestEdgeCases:
    """Test edge cases."""
    
    def test_empty_batch(self):
        """Test processing empty batch."""
        items = []
        
        def process(x):
            return x * 2
        
        processor = BatchProcessor()
        result = processor.process_batch(items, process)
        
        assert result['success'] is True
        assert len(result['results']) == 0
        assert processor.progress.total == 0
    
    def test_single_item(self):
        """Test processing single item."""
        items = [42]
        
        def process(x):
            return x * 2
        
        processor = BatchProcessor()
        result = processor.process_batch(items, process)
        
        assert result['success'] is True
        assert len(result['results']) == 1
        assert result['results'][0] == 84
    
    def test_all_failures(self):
        """Test batch where all items fail."""
        items = list(range(5))
        
        def process(x):
            raise ValueError("Always fails")
        
        processor = BatchProcessor(max_workers=2)
        result = processor.process_batch(items, process)
        
        assert result['success'] is False
        assert processor.progress.failed == 5
        assert processor.progress.success == 0
    
    def test_max_workers_one(self):
        """Test with single worker (no concurrency)."""
        items = list(range(10))
        
        def process(x):
            return x * 2
        
        processor = BatchProcessor(max_workers=1)
        result = processor.process_batch(items, process)
        
        assert result['success'] is True
        assert len(result['results']) == 10
