"""
Event Monitor Configuration
Settings for Black Box Event Monitor logging system
"""

# Enable/disable event monitoring
MONITOR_ENABLED = True

# Logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_LEVEL = 'DEBUG'

# Log retention period in days
LOG_RETENTION_DAYS = 7

# Log folder path (relative to base directory)
LOG_FOLDER = 'Log/diagnostics/'

# Performance threshold in milliseconds - operations slower than this will be flagged
PERFORMANCE_THRESHOLD_MS = 2000

# Automatically snapshot application state on errors
AUTO_SNAPSHOT_ON_ERROR = True

# Maximum number of events to keep in memory before flushing
MAX_EVENTS_IN_MEMORY = 10000

# Enable anomaly detection (slow operations, repeated failures, etc.)
ENABLE_ANOMALY_DETECTION = True

# Thread safety settings
THREAD_SAFE = True

# Export formats
EXPORT_FORMATS = ['json', 'csv']

# Code context lines to capture (lines before and after the logged line)
CODE_CONTEXT_LINES = 5

# Maximum stack trace depth to capture on errors
MAX_STACK_TRACE_DEPTH = 10
