"""Tests for conversion verification."""

import pytest
import os
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from src.utils.conversion_verifier import (
    ConversionVerifier,
    verify_conversion,
    ConversionVerificationError
)


class TestBasicVerification:
    """Test basic verification checks."""
    
    def test_file_exists(self, tmp_path):
        """Test verification passes for existing file."""
        output_file = tmp_path / "output.txt"
        output_file.write_text("Test content")
        
        verifier = ConversionVerifier()
        is_valid, issues = verifier.verify(str(output_file), 'txt')
        
        assert is_valid is True
        assert len(issues) == 0
    
    def test_file_not_exists(self, tmp_path):
        """Test verification fails for nonexistent file."""
        nonexistent = tmp_path / "nonexistent.txt"
        
        verifier = ConversionVerifier()
        is_valid, issues = verifier.verify(str(nonexistent), 'txt')
        
        assert is_valid is False
        assert "does not exist" in issues[0].lower()
    
    def test_empty_file(self, tmp_path):
        """Test verification fails for empty file."""
        empty_file = tmp_path / "empty.txt"
        empty_file.touch()
        
        verifier = ConversionVerifier()
        is_valid, issues = verifier.verify(str(empty_file), 'txt')
        
        assert is_valid is False
        assert "empty" in issues[0].lower()
    
    def test_file_too_small(self, tmp_path):
        """Test verification warns for files below minimum size."""
        small_file = tmp_path / "small.pdf"
        small_file.write_bytes(b"tiny")  # Only 4 bytes, PDF needs ~100
        
        verifier = ConversionVerifier()
        is_valid, issues = verifier.verify(str(small_file), 'pdf')
        
        # Should have issue about size
        assert len(issues) > 0
        assert any("too small" in issue.lower() for issue in issues)
    
    def test_extension_mismatch(self, tmp_path):
        """Test verification detects extension mismatch."""
        wrong_ext = tmp_path / "file.txt"
        wrong_ext.write_text("Content")
        
        verifier = ConversionVerifier()
        is_valid, issues = verifier.verify(str(wrong_ext), 'pdf')
        
        # Should have issue about extension
        assert len(issues) > 0
        assert any("extension" in issue.lower() for issue in issues)


class TestFormatValidation:
    """Test format-specific validation."""
    
    def test_pdf_validation_invalid_header(self, tmp_path):
        """Test PDF validation with invalid header."""
        fake_pdf = tmp_path / "fake.pdf"
        fake_pdf.write_bytes(b"Not a PDF file content here")
        
        verifier = ConversionVerifier()
        is_valid, issues = verifier.verify(str(fake_pdf), 'pdf')
        
        assert len(issues) > 0
        assert any("header" in issue.lower() or "magic" in issue.lower() for issue in issues)
    
    def test_pdf_validation_valid_header(self, tmp_path):
        """Test PDF with valid header."""
        valid_pdf = tmp_path / "valid.pdf"
        # Minimal PDF structure
        pdf_content = b'%PDF-1.4\n1 0 obj\n<<>>\nendobj\nxref\n0 1\n0000000000 65535 f\ntrailer\n<<>>\nstartxref\n0\n%%EOF'
        valid_pdf.write_bytes(pdf_content)
        
        verifier = ConversionVerifier()
        is_valid, issues = verifier.verify(str(valid_pdf), 'pdf')
        
        # May have issues but should not have header issue
        header_issues = [i for i in issues if "header" in i.lower()]
        assert len(header_issues) == 0
    
    def test_json_validation_valid(self, tmp_path):
        """Test JSON validation with valid JSON."""
        json_file = tmp_path / "data.json"
        with open(json_file, 'w') as f:
            json.dump({"key": "value"}, f)
        
        verifier = ConversionVerifier()
        is_valid, issues = verifier.verify(str(json_file), 'json')
        
        assert is_valid is True
        assert len(issues) == 0
    
    def test_json_validation_invalid(self, tmp_path):
        """Test JSON validation with invalid JSON."""
        invalid_json = tmp_path / "invalid.json"
        invalid_json.write_text("{invalid json}")
        
        verifier = ConversionVerifier()
        is_valid, issues = verifier.verify(str(invalid_json), 'json')
        
        assert len(issues) > 0
        assert any("json" in issue.lower() for issue in issues)
    
    def test_xml_validation_valid(self, tmp_path):
        """Test XML validation with valid XML."""
        xml_file = tmp_path / "data.xml"
        root = ET.Element("root")
        tree = ET.ElementTree(root)
        tree.write(str(xml_file))
        
        verifier = ConversionVerifier()
        is_valid, issues = verifier.verify(str(xml_file), 'xml')
        
        assert is_valid is True
        assert len(issues) == 0
    
    def test_xml_validation_invalid(self, tmp_path):
        """Test XML validation with invalid XML."""
        invalid_xml = tmp_path / "invalid.xml"
        invalid_xml.write_text("<root><unclosed>")
        
        verifier = ConversionVerifier()
        is_valid, issues = verifier.verify(str(invalid_xml), 'xml')
        
        assert len(issues) > 0
        assert any("xml" in issue.lower() for issue in issues)
    
    def test_text_validation(self, tmp_path):
        """Test text file validation."""
        text_file = tmp_path / "text.txt"
        text_file.write_text("Valid text content\nMultiple lines")
        
        verifier = ConversionVerifier()
        is_valid, issues = verifier.verify(str(text_file), 'txt')
        
        assert is_valid is True
        assert len(issues) == 0
    
    def test_text_binary_content(self, tmp_path):
        """Test text validation with binary content."""
        binary_file = tmp_path / "binary.txt"
        binary_file.write_bytes(b"Text with\x00null byte")
        
        verifier = ConversionVerifier()
        is_valid, issues = verifier.verify(str(binary_file), 'txt')
        
        # Should have issue about null bytes
        assert len(issues) > 0


class TestInputComparison:
    """Test comparison with input file."""
    
    def test_output_much_smaller(self, tmp_path):
        """Test warning when output is much smaller than input."""
        input_file = tmp_path / "input.txt"
        input_file.write_text("x" * 10000)  # 10KB
        
        output_file = tmp_path / "output.txt"
        output_file.write_text("x" * 500)  # 500 bytes (5% of input)
        
        verifier = ConversionVerifier()
        is_valid, issues = verifier.verify(
            str(output_file),
            'txt',
            input_path=str(input_file)
        )
        
        # Should have warning about size difference
        assert len(issues) > 0
        assert any("smaller" in issue.lower() for issue in issues)
    
    def test_output_similar_size(self, tmp_path):
        """Test no warning when output size is reasonable."""
        input_file = tmp_path / "input.txt"
        input_file.write_text("x" * 1000)
        
        output_file = tmp_path / "output.txt"
        output_file.write_text("y" * 800)  # 80% of input
        
        verifier = ConversionVerifier()
        is_valid, issues = verifier.verify(
            str(output_file),
            'txt',
            input_path=str(input_file)
        )
        
        # Should not have size warning
        size_issues = [i for i in issues if "smaller" in i.lower()]
        assert len(size_issues) == 0


class TestBatchVerification:
    """Test batch verification."""
    
    def test_batch_verify(self, tmp_path):
        """Test verifying multiple files."""
        file1 = tmp_path / "file1.txt"
        file1.write_text("Content 1")
        
        file2 = tmp_path / "file2.txt"
        file2.write_text("Content 2")
        
        file3 = tmp_path / "empty.txt"
        file3.touch()  # Empty file
        
        verifier = ConversionVerifier()
        results = verifier.verify_batch(
            [str(file1), str(file2), str(file3)],
            expected_format='txt'
        )
        
        # file1 and file2 should be valid
        assert results[str(file1)][0] is True
        assert results[str(file2)][0] is True
        
        # file3 should be invalid (empty)
        assert results[str(file3)][0] is False


class TestConvenienceFunction:
    """Test convenience function."""
    
    def test_verify_conversion_function(self, tmp_path):
        """Test verify_conversion convenience function."""
        output_file = tmp_path / "output.txt"
        output_file.write_text("Test content")
        
        is_valid, issues = verify_conversion(str(output_file), 'txt')
        
        assert is_valid is True
        assert len(issues) == 0


class TestEdgeCases:
    """Test edge cases."""
    
    def test_no_format_specified(self, tmp_path):
        """Test verification without specifying format."""
        file = tmp_path / "file.txt"
        file.write_text("Content")
        
        verifier = ConversionVerifier()
        is_valid, issues = verifier.verify(str(file))
        
        # Should still do basic checks
        assert is_valid is True
    
    def test_unknown_format(self, tmp_path):
        """Test verification with unknown format."""
        file = tmp_path / "file.xyz"
        file.write_text("Content")
        
        verifier = ConversionVerifier()
        is_valid, issues = verifier.verify(str(file), 'xyz')
        
        # Should do basic checks, skip format-specific
        # File exists and is not empty, so should be valid
        assert is_valid is True
    
    def test_large_file(self, tmp_path):
        """Test verification with large file."""
        large_file = tmp_path / "large.txt"
        large_file.write_text("x" * 1000000)  # 1MB
        
        verifier = ConversionVerifier()
        is_valid, issues = verifier.verify(str(large_file), 'txt')
        
        assert is_valid is True
        assert len(issues) == 0
