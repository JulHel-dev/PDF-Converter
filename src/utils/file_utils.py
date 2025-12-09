"""
File utility functions for file operations
"""
import os
import shutil
from typing import Optional, List
from pathlib import Path


def get_file_extension(filepath: str) -> str:
    """Get file extension without the dot, in lowercase."""
    return Path(filepath).suffix.lstrip('.').lower()


def get_file_size(filepath: str) -> int:
    """Get file size in bytes."""
    return os.path.getsize(filepath)


def get_file_size_mb(filepath: str) -> float:
    """Get file size in megabytes."""
    return get_file_size(filepath) / (1024 * 1024)


def ensure_directory_exists(directory: str):
    """Create directory if it doesn't exist."""
    os.makedirs(directory, exist_ok=True)


def is_valid_file(filepath: str) -> bool:
    """Check if file exists and is not empty."""
    return os.path.exists(filepath) and os.path.isfile(filepath) and os.path.getsize(filepath) > 0


def get_output_path(input_path: str, output_dir: str, new_extension: str) -> str:
    """
    Generate output file path based on input path and new extension.
    
    Args:
        input_path: Path to input file
        output_dir: Directory for output file
        new_extension: New file extension (without dot)
        
    Returns:
        Complete output file path
    """
    input_filename = Path(input_path).stem
    return os.path.join(output_dir, f"{input_filename}.{new_extension}")


def list_files_in_directory(directory: str, extensions: Optional[List[str]] = None) -> List[str]:
    """
    List all files in directory, optionally filtered by extension.
    
    Args:
        directory: Directory to scan
        extensions: Optional list of extensions to filter (without dots)
        
    Returns:
        List of file paths
    """
    files = []
    
    if not os.path.exists(directory):
        return files
    
    for item in os.listdir(directory):
        filepath = os.path.join(directory, item)
        if os.path.isfile(filepath):
            if extensions is None:
                files.append(filepath)
            else:
                ext = get_file_extension(filepath)
                if ext in extensions:
                    files.append(filepath)
    
    return files


def safe_copy_file(source: str, destination: str) -> bool:
    """
    Safely copy a file with error handling.
    
    Args:
        source: Source file path
        destination: Destination file path
        
    Returns:
        True if successful, False otherwise
    """
    try:
        ensure_directory_exists(os.path.dirname(destination))
        shutil.copy2(source, destination)
        return True
    except Exception:
        return False


def safe_remove_file(filepath: str) -> bool:
    """
    Safely remove a file with error handling.
    
    Args:
        filepath: File to remove
        
    Returns:
        True if successful, False otherwise
    """
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
        return True
    except Exception:
        return False


def generate_unique_filename(directory: str, base_name: str, extension: str) -> str:
    """
    Generate a unique filename by appending numbers if file exists.
    
    Args:
        directory: Target directory
        base_name: Base filename without extension
        extension: File extension (without dot)
        
    Returns:
        Unique filename
    """
    counter = 1
    filename = f"{base_name}.{extension}"
    filepath = os.path.join(directory, filename)
    
    while os.path.exists(filepath):
        filename = f"{base_name}_{counter}.{extension}"
        filepath = os.path.join(directory, filename)
        counter += 1
    
    return filename
