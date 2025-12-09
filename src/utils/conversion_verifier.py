"""
Conversion Verification and Validation

Validates that output files are valid and properly converted.
Performs format-specific checks to ensure conversion quality.

References:
- File format validation
- Data integrity checks
"""

import os
from typing import Optional, Dict, List, Tuple
from pathlib import Path
import mimetypes

try:
    from src.logging.event_monitor import EventMonitor
except ImportError:
    from logging.event_monitor import EventMonitor


class ConversionVerificationError(Exception):
    """Raised when conversion verification fails."""
    pass


class ConversionVerifier:
    """
    Verifies that file conversions completed successfully.
    
    Checks:
    - Output file exists
    - Output file is not empty
    - Output file has correct format/extension
    - Format-specific validation (PDF, images, etc.)
    
    Usage:
        verifier = ConversionVerifier()
        is_valid, issues = verifier.verify(output_path, expected_format='pdf')
    """
    
    def __init__(self):
        self.monitor = EventMonitor()
        
        # Minimum file sizes for different formats (bytes)
        self.min_sizes = {
            'pdf': 100,  # PDF header is ~100 bytes minimum
            'docx': 2000,  # DOCX is a zip file, minimum ~2KB
            'xlsx': 2000,  # XLSX is also a zip
            'txt': 1,  # Text can be very small
            'png': 67,  # Minimum PNG is 67 bytes
            'jpeg': 100,  # Minimum JPEG
            'jpg': 100,
            'csv': 1,
            'json': 2,  # At least {}
            'xml': 5,  # At least <?xml
        }
    
    def verify(
        self,
        output_path: str,
        expected_format: Optional[str] = None,
        input_path: Optional[str] = None
    ) -> Tuple[bool, List[str]]:
        """
        Verify conversion output.
        
        Args:
            output_path: Path to output file
            expected_format: Expected output format (e.g., 'pdf', 'docx')
            input_path: Optional input file for comparison
            
        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []
        
        # Check 1: File exists
        if not os.path.exists(output_path):
            issues.append("Output file does not exist")
            self.monitor.log_event('verification_failed', {
                'output_path': output_path,
                'issue': 'file_not_found'
            }, severity='ERROR')
            return False, issues
        
        # Check 2: File is not empty
        size = os.path.getsize(output_path)
        if size == 0:
            issues.append("Output file is empty (0 bytes)")
            self.monitor.log_event('verification_failed', {
                'output_path': output_path,
                'issue': 'empty_file',
                'size': 0
            }, severity='ERROR')
            return False, issues
        
        # Check 3: Minimum size check
        if expected_format:
            min_size = self.min_sizes.get(expected_format.lower(), 1)
            if size < min_size:
                issues.append(
                    f"Output file too small ({size} bytes, expected ≥{min_size})"
                )
                self.monitor.log_event('verification_warning', {
                    'output_path': output_path,
                    'issue': 'file_too_small',
                    'size': size,
                    'min_size': min_size
                }, severity='WARNING')
        
        # Check 4: Extension matches expected format
        if expected_format:
            actual_ext = Path(output_path).suffix.lstrip('.').lower()
            expected_ext = expected_format.lower()
            
            if actual_ext != expected_ext:
                issues.append(
                    f"Extension mismatch: got .{actual_ext}, expected .{expected_ext}"
                )
        
        # Check 5: Format-specific validation
        if expected_format:
            format_issues = self._validate_format(output_path, expected_format)
            issues.extend(format_issues)
        
        # Check 6: Compare with input (if provided)
        if input_path and os.path.exists(input_path):
            comparison_issues = self._compare_with_input(input_path, output_path)
            issues.extend(comparison_issues)
        
        # Determine overall validity
        is_valid = len(issues) == 0
        
        if is_valid:
            self.monitor.log_event('verification_success', {
                'output_path': output_path,
                'size': size,
                'format': expected_format
            }, severity='INFO')
        else:
            self.monitor.log_event('verification_failed', {
                'output_path': output_path,
                'issues': issues
            }, severity='ERROR')
        
        return is_valid, issues
    
    def _validate_format(self, file_path: str, format_type: str) -> List[str]:
        """
        Perform format-specific validation.
        
        Args:
            file_path: Path to file
            format_type: Format to validate (pdf, docx, etc.)
            
        Returns:
            List of issues found
        """
        issues = []
        format_type = format_type.lower()
        
        try:
            if format_type == 'pdf':
                issues.extend(self._validate_pdf(file_path))
            elif format_type in ['docx', 'xlsx', 'pptx']:
                issues.extend(self._validate_office(file_path))
            elif format_type in ['png', 'jpeg', 'jpg', 'gif', 'bmp']:
                issues.extend(self._validate_image(file_path))
            elif format_type == 'txt':
                issues.extend(self._validate_text(file_path))
            elif format_type == 'json':
                issues.extend(self._validate_json(file_path))
            elif format_type == 'xml':
                issues.extend(self._validate_xml(file_path))
            # Add more format validators as needed
            
        except Exception as e:
            issues.append(f"Validation error: {str(e)}")
        
        return issues
    
    def _validate_pdf(self, file_path: str) -> List[str]:
        """Validate PDF file."""
        issues = []
        
        try:
            # Check PDF magic bytes
            with open(file_path, 'rb') as f:
                header = f.read(5)
                if not header.startswith(b'%PDF-'):
                    issues.append("Invalid PDF header (magic bytes missing)")
            
            # Try to open with PyMuPDF if available
            try:
                import fitz
                with fitz.open(file_path) as doc:
                    if len(doc) == 0:
                        issues.append("PDF has 0 pages")
            except ImportError:
                # PyMuPDF not available, skip advanced check
                pass
            except Exception as e:
                issues.append(f"PDF validation failed: {str(e)}")
        
        except Exception as e:
            issues.append(f"Cannot read PDF: {str(e)}")
        
        return issues
    
    def _validate_office(self, file_path: str) -> List[str]:
        """Validate Office files (DOCX, XLSX, PPTX)."""
        issues = []
        
        try:
            # Office files are ZIP archives
            import zipfile
            
            if not zipfile.is_zipfile(file_path):
                issues.append("Office file is not a valid ZIP archive")
            else:
                # Check for required Office file structure
                with zipfile.ZipFile(file_path, 'r') as zf:
                    # Should contain [Content_Types].xml
                    if '[Content_Types].xml' not in zf.namelist():
                        issues.append("Missing [Content_Types].xml")
        
        except Exception as e:
            issues.append(f"Office file validation failed: {str(e)}")
        
        return issues
    
    def _validate_image(self, file_path: str) -> List[str]:
        """Validate image files."""
        issues = []
        
        try:
            from PIL import Image
            
            with Image.open(file_path) as img:
                # Verify image can be loaded
                img.verify()
                
                # Check image has reasonable dimensions
                if img.size[0] == 0 or img.size[1] == 0:
                    issues.append("Image has zero dimensions")
        
        except ImportError:
            # PIL not available, skip
            pass
        except Exception as e:
            issues.append(f"Image validation failed: {str(e)}")
        
        return issues
    
    def _validate_text(self, file_path: str) -> List[str]:
        """Validate text files."""
        issues = []
        
        try:
            # Try to read as text
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # Check if it's actually text (not binary)
                if '\x00' in content:
                    issues.append("File contains null bytes (may be binary)")
        
        except UnicodeDecodeError:
            # Try other encodings
            try:
                with open(file_path, 'r', encoding='latin-1') as f:
                    f.read()
            except Exception:
                issues.append("Cannot decode file as text")
        except Exception as e:
            issues.append(f"Text validation failed: {str(e)}")
        
        return issues
    
    def _validate_json(self, file_path: str) -> List[str]:
        """Validate JSON files."""
        issues = []
        
        try:
            import json
            
            with open(file_path, 'r') as f:
                json.load(f)
        
        except json.JSONDecodeError as e:
            issues.append(f"Invalid JSON: {str(e)}")
        except Exception as e:
            issues.append(f"JSON validation failed: {str(e)}")
        
        return issues
    
    def _validate_xml(self, file_path: str) -> List[str]:
        """Validate XML files."""
        issues = []
        
        try:
            import xml.etree.ElementTree as ET
            
            ET.parse(file_path)
        
        except ET.ParseError as e:
            issues.append(f"Invalid XML: {str(e)}")
        except Exception as e:
            issues.append(f"XML validation failed: {str(e)}")
        
        return issues
    
    def _compare_with_input(
        self,
        input_path: str,
        output_path: str
    ) -> List[str]:
        """
        Compare output with input for sanity checks.
        
        Args:
            input_path: Input file path
            output_path: Output file path
            
        Returns:
            List of issues
        """
        issues = []
        
        try:
            input_size = os.path.getsize(input_path)
            output_size = os.path.getsize(output_path)
            
            # Warn if output is significantly smaller than input
            # (might indicate data loss)
            if output_size < input_size * 0.1:
                issues.append(
                    f"Output is much smaller than input "
                    f"({output_size} vs {input_size} bytes)"
                )
        
        except Exception:
            pass
        
        return issues
    
    def verify_batch(
        self,
        output_paths: List[str],
        expected_format: Optional[str] = None
    ) -> Dict[str, Tuple[bool, List[str]]]:
        """
        Verify multiple conversion outputs.
        
        Args:
            output_paths: List of output file paths
            expected_format: Expected format for all files
            
        Returns:
            Dictionary mapping paths to (is_valid, issues) tuples
        """
        results = {}
        
        for path in output_paths:
            results[path] = self.verify(path, expected_format)
        
        return results


def verify_conversion(
    output_path: str,
    expected_format: Optional[str] = None,
    input_path: Optional[str] = None
) -> Tuple[bool, List[str]]:
    """
    Convenience function to verify a conversion.
    
    Args:
        output_path: Path to output file
        expected_format: Expected format
        input_path: Optional input file
        
    Returns:
        Tuple of (is_valid, list_of_issues)
    """
    verifier = ConversionVerifier()
    return verifier.verify(output_path, expected_format, input_path)
