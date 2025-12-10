"""
Encoding Detection and Unicode Safety

Automatically detects text file encoding for safe processing.
Prevents encoding errors and data corruption.

References:
- chardet library for encoding detection
- Unicode best practices
"""

from typing import Optional

try:
    from src.logging.event_monitor import EventMonitor
except ImportError:
    from logging.event_monitor import EventMonitor


class EncodingDetector:
    """
    Detects text file encoding automatically.
    
    Uses chardet library if available, falls back to simple detection.
    
    Usage:
        detector = EncodingDetector()
        encoding = detector.detect('file.txt')
        with open('file.txt', 'r', encoding=encoding) as f:
            content = f.read()
    """
    
    def __init__(self):
        self.monitor = EventMonitor()
        
        # Check if chardet is available
        try:
            import chardet
            self.chardet_available = True
        except ImportError:
            self.chardet_available = False
            self.monitor.log_event('chardet_unavailable', {
                'fallback': 'simple detection'
            }, severity='WARNING')
    
    def detect(
        self,
        file_path: str,
        sample_size: int = 10000
    ) -> str:
        """
        Detect file encoding.
        
        Args:
            file_path: Path to text file
            sample_size: Bytes to sample for detection
            
        Returns:
            Detected encoding (e.g., 'utf-8', 'latin-1')
        """
        try:
            # Read sample
            with open(file_path, 'rb') as f:
                sample = f.read(sample_size)
            
            if not sample:
                return 'utf-8'  # Default for empty files
            
            # Try chardet first
            if self.chardet_available:
                return self._detect_with_chardet(sample)
            else:
                return self._detect_simple(sample)
        
        except Exception as e:
            self.monitor.log_event('encoding_detection_failed', {
                'file': file_path,
                'error': str(e)
            }, severity='ERROR')
            return 'utf-8'  # Safe default
    
    def _detect_with_chardet(self, sample: bytes) -> str:
        """Detect encoding using chardet library."""
        import chardet
        
        result = chardet.detect(sample)
        encoding = result['encoding']
        confidence = result['confidence']
        
        self.monitor.log_event('encoding_detected', {
            'encoding': encoding,
            'confidence': confidence,
            'method': 'chardet'
        }, severity='DEBUG')
        
        # Use detected encoding if confidence is high
        if confidence > 0.7 and encoding:
            return encoding
        else:
            return 'utf-8'  # Default fallback
    
    def _detect_simple(self, sample: bytes) -> str:
        """Simple encoding detection without chardet."""
        # Try UTF-8 first
        try:
            sample.decode('utf-8')
            return 'utf-8'
        except UnicodeDecodeError:
            pass
        
        # Try UTF-16
        try:
            sample.decode('utf-16')
            return 'utf-16'
        except UnicodeDecodeError:
            pass
        
        # Try Latin-1 (never fails)
        return 'latin-1'
    
    def read_text_safe(
        self,
        file_path: str,
        encoding: Optional[str] = None
    ) -> str:
        """
        Safely read text file with automatic encoding detection.
        
        Args:
            file_path: Path to text file
            encoding: Optional encoding (auto-detect if None)
            
        Returns:
            File content as string
        """
        if encoding is None:
            encoding = self.detect(file_path)
        
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                return f.read()
        except UnicodeDecodeError:
            # Fallback to latin-1
            self.monitor.log_event('encoding_fallback', {
                'file': file_path,
                'tried': encoding,
                'fallback': 'latin-1'
            }, severity='WARNING')
            
            with open(file_path, 'r', encoding='latin-1') as f:
                return f.read()
    
    def convert_encoding(
        self,
        input_path: str,
        output_path: str,
        target_encoding: str = 'utf-8'
    ) -> bool:
        """
        Convert file from detected encoding to target encoding.
        
        Args:
            input_path: Input file path
            output_path: Output file path
            target_encoding: Target encoding (default: utf-8)
            
        Returns:
            True if successful
        """
        try:
            # Detect source encoding
            source_encoding = self.detect(input_path)
            
            # Read with source encoding
            with open(input_path, 'r', encoding=source_encoding) as f:
                content = f.read()
            
            # Write with target encoding
            with open(output_path, 'w', encoding=target_encoding) as f:
                f.write(content)
            
            self.monitor.log_event('encoding_converted', {
                'input': input_path,
                'output': output_path,
                'from': source_encoding,
                'to': target_encoding
            }, severity='INFO')
            
            return True
        
        except Exception as e:
            self.monitor.log_event('encoding_conversion_failed', {
                'input': input_path,
                'output': output_path,
                'error': str(e)
            }, severity='ERROR')
            return False


# Global detector instance
_encoding_detector: Optional[EncodingDetector] = None


def get_encoding_detector() -> EncodingDetector:
    """Get the global encoding detector instance."""
    global _encoding_detector
    if _encoding_detector is None:
        _encoding_detector = EncodingDetector()
    return _encoding_detector


def detect_encoding(file_path: str) -> str:
    """
    Convenience function to detect file encoding.
    
    Args:
        file_path: Path to text file
        
    Returns:
        Detected encoding
    """
    return get_encoding_detector().detect(file_path)


def read_text_safe(file_path: str, encoding: Optional[str] = None) -> str:
    """
    Convenience function to safely read text file.
    
    Args:
        file_path: Path to text file
        encoding: Optional encoding (auto-detect if None)
        
    Returns:
        File content
    """
    return get_encoding_detector().read_text_safe(file_path, encoding)
