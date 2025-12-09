"""
Abstract base class for all format converters
Provides common functionality and interface for all converters
"""
from abc import ABC, abstractmethod
from typing import Dict, List
import os
from src.logging.event_monitor import EventMonitor
from src.utils.file_utils import get_file_size_mb
from src.security.path_security import validate_path, PathSecurityError
from src.security.size_security import validate_file_size


class BaseConverter(ABC):
    """Abstract base class for all format converters."""
    
    def __init__(self):
        self.monitor = EventMonitor()
        self.supported_input_formats: List[str] = []
        self.supported_output_formats: List[str] = []
    
    @abstractmethod
    def convert(self, input_path: str, output_path: str, output_format: str) -> bool:
        """
        Convert input file to target format.
        
        Args:
            input_path: Path to input file
            output_path: Path for output file
            output_format: Target format (without dot)
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    def validate_input(self, input_path: str) -> bool:
        """
        Validate input file exists, is readable, and not zero-byte.
        Includes security validation for path traversal and file size.
        
        Args:
            input_path: Path to input file
            
        Returns:
            True if valid, False otherwise
        """
        # Security: Validate path to prevent traversal attacks
        try:
            safe_path = validate_path(input_path, 'read_input')
            input_path = safe_path  # Use the canonical safe path
        except PathSecurityError as e:
            self.monitor.log_event('path_security_violation', 
                {'file': input_path, 'reason': str(e)}, 
                severity='CRITICAL')
            return False
        
        if not os.path.exists(input_path):
            self.monitor.log_event('validation_failed', 
                {'file': input_path, 'reason': 'File not found'}, 
                severity='ERROR')
            return False
        
        if not os.path.isfile(input_path):
            self.monitor.log_event('validation_failed', 
                {'file': input_path, 'reason': 'Path is not a file'}, 
                severity='ERROR')
            return False
        
        if os.path.getsize(input_path) == 0:
            self.monitor.log_event('validation_failed', 
                {'file': input_path, 'reason': 'Zero-byte file'}, 
                severity='ERROR')
            return False
        
        # Security: Validate file size to prevent DoS
        if not validate_file_size(input_path):
            from src.config.settings import MAX_FILE_SIZE_MB
            file_size_mb = get_file_size_mb(input_path)
            self.monitor.log_event('file_size_exceeded', 
                {'file': input_path, 
                 'size_mb': file_size_mb,
                 'max_size_mb': MAX_FILE_SIZE_MB}, 
                severity='ERROR')
            return False
        
        return True
    
    def validate_output(self, output_path: str) -> bool:
        """
        Validate output path is writable and secure.
        Includes security validation for path traversal.
        
        Args:
            output_path: Path for output file
            
        Returns:
            True if valid, False otherwise
        """
        # Security: Validate output path to prevent traversal attacks
        try:
            safe_path = validate_path(output_path, 'write_output')
            output_path = safe_path  # Use the canonical safe path
        except PathSecurityError as e:
            self.monitor.log_event('path_security_violation', 
                {'file': output_path, 'reason': str(e)}, 
                severity='CRITICAL')
            return False
        
        # Validate output directory exists and is writable
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir, exist_ok=True)
            except Exception as e:
                self.monitor.log_event('output_directory_creation_failed', 
                    {'directory': output_dir, 'error': str(e)}, 
                    severity='ERROR')
                return False
        
        # Check if output file already exists (warn but allow)
        if os.path.exists(output_path):
            self.monitor.log_event('output_file_exists', 
                {'file': output_path, 'action': 'will_overwrite'}, 
                severity='WARNING')
        
        return True
    
    def extract_metadata(self, input_path: str) -> Dict:
        """
        Extract and return file metadata.
        
        Args:
            input_path: Path to input file
            
        Returns:
            Dictionary of metadata
        """
        metadata = {
            'filename': os.path.basename(input_path),
            'size_bytes': os.path.getsize(input_path),
            'size_mb': get_file_size_mb(input_path),
            'extension': os.path.splitext(input_path)[1].lstrip('.'),
        }
        
        return metadata
    
    def get_supported_conversions(self) -> Dict[str, List[str]]:
        """
        Return dict of supported input→output format mappings.
        
        Returns:
            Dictionary mapping input formats to list of output formats
        """
        result = {}
        for input_fmt in self.supported_input_formats:
            result[input_fmt] = self.supported_output_formats
        return result
    
    def is_format_supported(self, input_format: str, output_format: str) -> bool:
        """
        Check if conversion between formats is supported.
        
        Args:
            input_format: Input format
            output_format: Output format
            
        Returns:
            True if supported
        """
        return (input_format.lower() in self.supported_input_formats and 
                output_format.lower() in self.supported_output_formats)
