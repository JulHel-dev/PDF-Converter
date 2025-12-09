"""
Black Box Event Monitor for PDF Converter

Singleton pattern, thread-safe. Logs all events with full context.
Adapted from Indexer-Julius implementation with enhancements.
"""
import threading
import logging
import inspect
import json
import time
import os
import csv
from collections import deque
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from src.config import monitor_config

class EventMonitor:
    """Singleton event monitor for comprehensive application logging."""
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._init()
        self._initialized = True

    def _init(self):
        """Initialize the event monitor."""
        from src.config.settings import BASE_DIR
        
        self.log_folder = os.path.join(BASE_DIR, monitor_config.LOG_FOLDER)
        os.makedirs(self.log_folder, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.log_file = os.path.join(self.log_folder, f"event_log_{timestamp}.jsonl")
        self.events = deque(maxlen=monitor_config.MAX_EVENTS_IN_MEMORY)
        self.timers = {}
        self.anomalies = []
        self._thread_lock = threading.Lock()
        
        # Setup logger
        self.logger = logging.getLogger("EventMonitor")
        self.logger.setLevel(getattr(logging, monitor_config.LOG_LEVEL))
        self.logger.handlers.clear()
        
        handler = logging.FileHandler(self.log_file, mode='a', encoding='utf-8')
        handler.setFormatter(logging.Formatter('%(message)s'))
        self.logger.addHandler(handler)
        self.logger.propagate = False
        
        # Log initialization
        self.log_event('monitor_initialized', {
            'log_file': self.log_file,
            'config': {
                'log_level': monitor_config.LOG_LEVEL,
                'retention_days': monitor_config.LOG_RETENTION_DAYS,
                'performance_threshold_ms': monitor_config.PERFORMANCE_THRESHOLD_MS,
                'anomaly_detection': monitor_config.ENABLE_ANOMALY_DETECTION
            }
        }, severity='INFO')

    def log_event(self, event_type: str, details: Optional[Dict] = None, 
                  severity: str = 'INFO', step: Optional[str] = None):
        """
        Log an event with full context.
        
        Args:
            event_type: Type of event (e.g., 'conversion_start', 'error')
            details: Additional event details
            severity: Event severity (INFO, WARNING, ERROR, CRITICAL)
            step: Optional step description for multi-step operations
        """
        if not monitor_config.MONITOR_ENABLED:
            return
        
        frame = inspect.currentframe().f_back
        location = {
            "file": inspect.getfile(frame),
            "line": frame.f_lineno,
            "function": frame.f_code.co_name,
            "step": step or ""
        }
        
        event = {
            "timestamp": datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3],
            "event": event_type,
            "location": location,
            "details": details or {},
            "severity": severity,
            "code_context": self._get_code_context(location["file"], location["line"]),
            "stack_trace": self._get_stack_trace() if severity == 'ERROR' else []
        }
        
        with self._thread_lock:
            self.events.append(event)
            self.logger.debug(json.dumps(event, ensure_ascii=False))
        
        if monitor_config.ENABLE_ANOMALY_DETECTION:
            self._detect_anomaly(event)

    def start_timer(self, name: str) -> str:
        """
        Start a performance timer.
        
        Args:
            name: Timer name/identifier
            
        Returns:
            Timer ID for use with end_timer()
        """
        timer_id = f"{name}-{time.time()}"
        with self._thread_lock:
            self.timers[timer_id] = time.time()
        return timer_id

    def end_timer(self, timer_id: Optional[str], extra: Optional[Dict] = None):
        """
        End timer and log duration. Flag slow operations.
        
        Args:
            timer_id: Timer ID from start_timer()
            extra: Optional extra details to log
        """
        if not timer_id:
            return
        
        with self._thread_lock:
            start = self.timers.pop(timer_id, None)
        
        if not start:
            return
        
        duration = time.time() - start
        self.log_event('timer_end', {
            'timer_id': timer_id,
            'duration_seconds': round(duration, 3),
            'extra': extra or {}
        })
        
        threshold = monitor_config.PERFORMANCE_THRESHOLD_MS / 1000
        if duration > threshold:
            self.log_event('slow_operation', {
                'timer_id': timer_id,
                'duration_seconds': round(duration, 3),
                'threshold_seconds': threshold
            }, severity='WARNING')

    def export_log(self, format: str = 'json', output_path: Optional[str] = None) -> str:
        """
        Export events to JSON or CSV file.
        
        Args:
            format: Export format ('json' or 'csv')
            output_path: Optional custom output path
            
        Returns:
            Path to exported file
        """
        if not output_path:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = os.path.join(self.log_folder, f"export_{timestamp}.{format}")
        
        with self._thread_lock:
            events_list = list(self.events)
        
        if format == 'json':
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(events_list, f, indent=2, ensure_ascii=False)
        elif format == 'csv':
            if events_list:
                with open(output_path, 'w', encoding='utf-8', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=self._get_csv_fieldnames(events_list[0]))
                    writer.writeheader()
                    for event in events_list:
                        writer.writerow(self._flatten_event(event))
        
        self.log_event('log_exported', {
            'format': format,
            'output_path': output_path,
            'event_count': len(events_list)
        }, severity='INFO')
        
        return output_path

    def get_anomalies(self) -> List[Dict]:
        """Get list of detected anomalies."""
        with self._thread_lock:
            return list(self.anomalies)

    def get_recent_events(self, count: int = 100, severity: Optional[str] = None) -> List[Dict]:
        """
        Get recent events, optionally filtered by severity.
        
        Args:
            count: Number of recent events to return
            severity: Optional severity filter
            
        Returns:
            List of events
        """
        with self._thread_lock:
            events = list(self.events)
        
        if severity:
            events = [e for e in events if e.get('severity') == severity]
        
        return events[-count:]

    def clear_old_logs(self):
        """Remove log files older than retention period."""
        cutoff_date = datetime.now() - timedelta(days=monitor_config.LOG_RETENTION_DAYS)
        
        for filename in os.listdir(self.log_folder):
            filepath = os.path.join(self.log_folder, filename)
            if os.path.isfile(filepath):
                file_time = datetime.fromtimestamp(os.path.getmtime(filepath))
                if file_time < cutoff_date:
                    try:
                        os.remove(filepath)
                        self.log_event('old_log_removed', {
                            'file': filename,
                            'age_days': (datetime.now() - file_time).days
                        }, severity='INFO')
                    except Exception as e:
                        self.log_event('log_cleanup_failed', {
                            'file': filename,
                            'error': str(e)
                        }, severity='WARNING')

    def _get_code_context(self, file_path: str, line_num: int) -> List[str]:
        """Get lines of code context around the logged line."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            context = []
            context_range = monitor_config.CODE_CONTEXT_LINES // 2
            
            for i in range(max(0, line_num - context_range - 1), 
                          min(len(lines), line_num + context_range)):
                prefix = monitor_config.CODE_CONTEXT_MARKER if i == line_num - 1 else monitor_config.CODE_CONTEXT_INDENT
                context.append(f"{prefix}{i + 1}: {lines[i].rstrip()}")
            
            return context
        except Exception:
            return []

    def _get_stack_trace(self) -> List[Dict]:
        """Get current stack trace for error events."""
        stack = []
        max_depth = monitor_config.MAX_STACK_TRACE_DEPTH
        
        for frame in inspect.stack()[2:2+max_depth]:  # Skip this method and log_event
            stack.append({
                "file": frame.filename,
                "line": frame.lineno,
                "function": frame.function,
                "code": frame.code_context[0].strip() if frame.code_context else ""
            })
        
        return stack

    def _detect_anomaly(self, event: Dict):
        """Detect and flag anomalous events."""
        is_anomaly = False
        
        if event.get('severity') in ['ERROR', 'CRITICAL']:
            is_anomaly = True
        
        if event.get('event') == 'slow_operation':
            is_anomaly = True
        
        # Check for repeated failures
        if event.get('event') == 'conversion_failed':
            recent_failures = [e for e in self.events 
                             if e.get('event') == 'conversion_failed']
            if len(recent_failures) >= 3:
                is_anomaly = True
                event['anomaly_reason'] = 'repeated_failures'
        
        if is_anomaly:
            with self._thread_lock:
                self.anomalies.append(event)

    def _flatten_event(self, event: Dict) -> Dict:
        """Flatten nested event structure for CSV export."""
        flat = {
            'timestamp': event.get('timestamp', ''),
            'event': event.get('event', ''),
            'severity': event.get('severity', ''),
            'file': event.get('location', {}).get('file', ''),
            'line': event.get('location', {}).get('line', ''),
            'function': event.get('location', {}).get('function', ''),
            'step': event.get('location', {}).get('step', ''),
            'details': json.dumps(event.get('details', {})),
        }
        return flat

    def _get_csv_fieldnames(self, event: Dict) -> List[str]:
        """Get CSV fieldnames from event structure."""
        return ['timestamp', 'event', 'severity', 'file', 'line', 'function', 'step', 'details']
