"""
Tests for Event Monitor

Validates Black Box Event Monitor functionality.
"""
import pytest
import os
import json
import tempfile
from src.logging.event_monitor import EventMonitor


def test_event_monitor_singleton():
    """Test that EventMonitor is a singleton."""
    monitor1 = EventMonitor()
    monitor2 = EventMonitor()
    assert monitor1 is monitor2


def test_log_event():
    """Test basic event logging."""
    monitor = EventMonitor()
    
    monitor.log_event('test_event', {
        'test_key': 'test_value'
    }, severity='INFO', step='Test step')
    
    recent_events = monitor.get_recent_events(count=1)
    assert len(recent_events) > 0
    
    last_event = recent_events[-1]
    assert last_event['event'] == 'test_event'
    assert last_event['severity'] == 'INFO'
    assert last_event['details']['test_key'] == 'test_value'


def test_timer():
    """Test timer functionality."""
    import time
    
    monitor = EventMonitor()
    timer_id = monitor.start_timer('test_timer')
    
    assert timer_id is not None
    assert 'test_timer' in timer_id
    
    time.sleep(0.1)  # Sleep for 100ms
    
    monitor.end_timer(timer_id)
    
    # Check for timer_end event
    recent_events = monitor.get_recent_events(count=5)
    timer_events = [e for e in recent_events if e['event'] == 'timer_end']
    
    assert len(timer_events) > 0


def test_export_json():
    """Test JSON export functionality."""
    monitor = EventMonitor()
    
    # Log a test event
    monitor.log_event('export_test', {'data': 'test'}, severity='INFO')
    
    # Export to temporary file
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as tmp:
        export_path = monitor.export_log(format='json', output_path=tmp.name)
    
    try:
        # Verify file exists and contains valid JSON
        assert os.path.exists(export_path)
        
        with open(export_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            assert isinstance(data, list)
    finally:
        # Cleanup
        if os.path.exists(export_path):
            os.remove(export_path)


def test_anomaly_detection():
    """Test anomaly detection."""
    monitor = EventMonitor()
    
    # Log an error event (should be detected as anomaly)
    monitor.log_event('test_error', {
        'error': 'Test error message'
    }, severity='ERROR')
    
    anomalies = monitor.get_anomalies()
    
    # Should have at least one anomaly
    assert len(anomalies) > 0


def test_recent_events_filtering():
    """Test filtering events by severity."""
    monitor = EventMonitor()
    
    # Log events with different severities
    monitor.log_event('info_event', {}, severity='INFO')
    monitor.log_event('warning_event', {}, severity='WARNING')
    monitor.log_event('error_event', {}, severity='ERROR')
    
    # Get only ERROR events
    error_events = monitor.get_recent_events(count=100, severity='ERROR')
    
    # All returned events should be ERROR
    for event in error_events:
        assert event['severity'] == 'ERROR'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
