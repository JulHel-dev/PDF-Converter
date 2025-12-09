"""
Tests for File Utils

Validates file utility functions.
"""
import pytest
import os
import tempfile
from src.utils.file_utils import (
    get_file_extension,
    get_file_size,
    get_file_size_mb,
    ensure_directory_exists,
    is_valid_file,
    get_output_path,
    list_files_in_directory,
    generate_unique_filename
)


def test_get_file_extension():
    """Test file extension extraction."""
    assert get_file_extension('test.pdf') == 'pdf'
    assert get_file_extension('document.DOCX') == 'docx'
    assert get_file_extension('/path/to/file.txt') == 'txt'
    assert get_file_extension('file.tar.gz') == 'gz'


def test_get_file_size():
    """Test file size calculation."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp:
        tmp.write('x' * 1000)  # Write 1000 bytes
        tmp_path = tmp.name
    
    try:
        size = get_file_size(tmp_path)
        assert size == 1000
    finally:
        os.unlink(tmp_path)


def test_get_file_size_mb():
    """Test file size in MB."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp:
        tmp.write('x' * 1024 * 1024)  # Write 1 MB
        tmp_path = tmp.name
    
    try:
        size_mb = get_file_size_mb(tmp_path)
        assert 0.9 < size_mb < 1.1  # Allow small margin
    finally:
        os.unlink(tmp_path)


def test_ensure_directory_exists():
    """Test directory creation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        new_dir = os.path.join(tmpdir, 'test_dir')
        
        ensure_directory_exists(new_dir)
        
        assert os.path.exists(new_dir)
        assert os.path.isdir(new_dir)


def test_is_valid_file():
    """Test file validation."""
    # Valid file
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp:
        tmp.write('content')
        tmp_path = tmp.name
    
    try:
        assert is_valid_file(tmp_path) is True
    finally:
        os.unlink(tmp_path)
    
    # Nonexistent file
    assert is_valid_file('/nonexistent/file.txt') is False
    
    # Empty file
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp:
        tmp_path = tmp.name
    
    try:
        assert is_valid_file(tmp_path) is False
    finally:
        os.unlink(tmp_path)


def test_get_output_path():
    """Test output path generation."""
    result = get_output_path('/input/test.pdf', '/output', 'txt')
    assert result == '/output/test.txt'
    
    result = get_output_path('document.docx', './output/', 'pdf')
    assert 'document.pdf' in result


def test_list_files_in_directory():
    """Test directory file listing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test files
        open(os.path.join(tmpdir, 'file1.txt'), 'w').close()
        open(os.path.join(tmpdir, 'file2.pdf'), 'w').close()
        open(os.path.join(tmpdir, 'file3.txt'), 'w').close()
        
        # List all files
        all_files = list_files_in_directory(tmpdir)
        assert len(all_files) == 3
        
        # List only txt files
        txt_files = list_files_in_directory(tmpdir, extensions=['txt'])
        assert len(txt_files) == 2
        
        # List only pdf files
        pdf_files = list_files_in_directory(tmpdir, extensions=['pdf'])
        assert len(pdf_files) == 1


def test_generate_unique_filename():
    """Test unique filename generation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # First file
        filename1 = generate_unique_filename(tmpdir, 'test', 'txt')
        assert filename1 == 'test.txt'
        
        # Create the file
        open(os.path.join(tmpdir, filename1), 'w').close()
        
        # Second file (should get _1 suffix)
        filename2 = generate_unique_filename(tmpdir, 'test', 'txt')
        assert filename2 == 'test_1.txt'
        
        # Create the second file
        open(os.path.join(tmpdir, filename2), 'w').close()
        
        # Third file (should get _2 suffix)
        filename3 = generate_unique_filename(tmpdir, 'test', 'txt')
        assert filename3 == 'test_2.txt'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
