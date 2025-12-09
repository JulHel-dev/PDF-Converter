"""
Output File Conflict Resolution

Handles cases where output file already exists.
Provides strategies: overwrite, skip, rename, prompt.

References:
- File handling best practices
"""

import os
from enum import Enum
from typing import Optional, Tuple

try:
    from src.logging.event_monitor import EventMonitor
except ImportError:
    from logging.event_monitor import EventMonitor

try:
    from src.security.filename_security import sanitize_filename
except ImportError:
    from security.filename_security import sanitize_filename


class ConflictResolution(Enum):
    """Strategies for resolving output file conflicts."""
    OVERWRITE = "overwrite"  # Replace existing file
    SKIP = "skip"  # Skip conversion if file exists
    RENAME = "rename"  # Auto-rename with counter (file_1.pdf, file_2.pdf, etc.)
    PROMPT = "prompt"  # Ask user (CLI only)
    ERROR = "error"  # Raise error


class OutputConflictResolver:
    """
    Resolves conflicts when output file already exists.
    
    Strategies:
    - OVERWRITE: Replace existing file
    - SKIP: Skip if exists
    - RENAME: Auto-rename (file.pdf -> file_1.pdf -> file_2.pdf)
    - PROMPT: Ask user (CLI mode)
    - ERROR: Raise error
    
    Usage:
        resolver = OutputConflictResolver(strategy=ConflictResolution.RENAME)
        output_path = resolver.resolve(desired_path)
    """
    
    def __init__(
        self,
        strategy: ConflictResolution = ConflictResolution.RENAME,
        max_attempts: int = 1000
    ):
        """
        Initialize the conflict resolver.
        
        Args:
            strategy: Resolution strategy to use
            max_attempts: Maximum rename attempts (for RENAME strategy)
        """
        self.strategy = strategy
        self.max_attempts = max_attempts
        self.monitor = EventMonitor()
    
    def resolve(self, output_path: str) -> Optional[str]:
        """
        Resolve output file conflict.
        
        Args:
            output_path: Desired output file path
            
        Returns:
            Resolved path to use, or None if should skip
            
        Raises:
            FileExistsError: If strategy is ERROR and file exists
        """
        if not os.path.exists(output_path):
            # No conflict
            return output_path
        
        self.monitor.log_event('output_conflict_detected', {
            'path': output_path,
            'strategy': self.strategy.value
        }, severity='INFO')
        
        if self.strategy == ConflictResolution.OVERWRITE:
            return self._handle_overwrite(output_path)
        
        elif self.strategy == ConflictResolution.SKIP:
            return self._handle_skip(output_path)
        
        elif self.strategy == ConflictResolution.RENAME:
            return self._handle_rename(output_path)
        
        elif self.strategy == ConflictResolution.PROMPT:
            return self._handle_prompt(output_path)
        
        elif self.strategy == ConflictResolution.ERROR:
            return self._handle_error(output_path)
        
        else:
            # Default to rename
            return self._handle_rename(output_path)
    
    def _handle_overwrite(self, output_path: str) -> str:
        """Handle OVERWRITE strategy."""
        self.monitor.log_event('conflict_overwrite', {
            'path': output_path
        }, severity='WARNING')
        
        return output_path
    
    def _handle_skip(self, output_path: str) -> None:
        """Handle SKIP strategy."""
        self.monitor.log_event('conflict_skip', {
            'path': output_path
        }, severity='INFO')
        
        return None
    
    def _handle_rename(self, output_path: str) -> str:
        """
        Handle RENAME strategy.
        
        Generates: file.pdf -> file_1.pdf -> file_2.pdf, etc.
        """
        directory = os.path.dirname(output_path)
        filename = os.path.basename(output_path)
        name, ext = os.path.splitext(filename)
        
        for i in range(1, self.max_attempts + 1):
            new_name = f"{name}_{i}{ext}"
            new_path = os.path.join(directory, new_name)
            
            if not os.path.exists(new_path):
                self.monitor.log_event('conflict_renamed', {
                    'original': output_path,
                    'renamed': new_path,
                    'attempt': i
                }, severity='INFO')
                
                return new_path
        
        # Exceeded max attempts
        self.monitor.log_event('conflict_rename_failed', {
            'path': output_path,
            'max_attempts': self.max_attempts
        }, severity='ERROR')
        
        raise FileExistsError(
            f"Could not find available name after {self.max_attempts} attempts"
        )
    
    def _handle_prompt(self, output_path: str) -> Optional[str]:
        """
        Handle PROMPT strategy.
        
        Asks user what to do (CLI mode only).
        """
        print(f"\n⚠️  Output file already exists: {output_path}")
        print("Choose action:")
        print("  1) Overwrite existing file")
        print("  2) Skip this conversion")
        print("  3) Auto-rename (file_1.pdf, file_2.pdf, etc.)")
        print("  4) Cancel")
        
        try:
            choice = input("Enter choice (1-4): ").strip()
            
            if choice == "1":
                self.monitor.log_event('conflict_prompt_overwrite', {
                    'path': output_path
                }, severity='INFO')
                return output_path
            
            elif choice == "2":
                self.monitor.log_event('conflict_prompt_skip', {
                    'path': output_path
                }, severity='INFO')
                return None
            
            elif choice == "3":
                return self._handle_rename(output_path)
            
            else:
                self.monitor.log_event('conflict_prompt_cancel', {
                    'path': output_path
                }, severity='INFO')
                return None
        
        except (EOFError, KeyboardInterrupt):
            self.monitor.log_event('conflict_prompt_interrupted', {
                'path': output_path
            }, severity='WARNING')
            return None
    
    def _handle_error(self, output_path: str) -> None:
        """Handle ERROR strategy."""
        self.monitor.log_event('conflict_error', {
            'path': output_path
        }, severity='ERROR')
        
        raise FileExistsError(f"Output file already exists: {output_path}")
    
    def batch_resolve(self, output_paths: list) -> dict:
        """
        Resolve conflicts for multiple output paths.
        
        Args:
            output_paths: List of desired output paths
            
        Returns:
            Dictionary mapping original paths to resolved paths
            (None value means skip)
        """
        resolved = {}
        
        for path in output_paths:
            try:
                resolved[path] = self.resolve(path)
            except Exception as e:
                self.monitor.log_event('batch_resolve_error', {
                    'path': path,
                    'error': str(e)
                }, severity='ERROR')
                resolved[path] = None
        
        return resolved


def resolve_output_conflict(
    output_path: str,
    strategy: ConflictResolution = ConflictResolution.RENAME
) -> Optional[str]:
    """
    Convenience function to resolve output file conflict.
    
    Args:
        output_path: Desired output file path
        strategy: Resolution strategy
        
    Returns:
        Resolved path or None if should skip
    """
    resolver = OutputConflictResolver(strategy=strategy)
    return resolver.resolve(output_path)


def get_unique_output_path(base_path: str, max_attempts: int = 1000) -> str:
    """
    Get a unique output path by auto-renaming if necessary.
    
    Args:
        base_path: Desired output path
        max_attempts: Maximum rename attempts
        
    Returns:
        Unique output path
    """
    if not os.path.exists(base_path):
        return base_path
    
    directory = os.path.dirname(base_path)
    filename = os.path.basename(base_path)
    name, ext = os.path.splitext(filename)
    
    for i in range(1, max_attempts + 1):
        new_name = f"{name}_{i}{ext}"
        new_path = os.path.join(directory, new_name)
        
        if not os.path.exists(new_path):
            return new_path
    
    raise FileExistsError(
        f"Could not find available name after {max_attempts} attempts"
    )


def check_output_writable(output_path: str) -> Tuple[bool, Optional[str]]:
    """
    Check if output path is writable.
    
    Args:
        output_path: Output file path
        
    Returns:
        Tuple of (is_writable, error_message)
    """
    directory = os.path.dirname(output_path) or '.'
    
    # Check if directory exists
    if not os.path.exists(directory):
        try:
            os.makedirs(directory, exist_ok=True)
        except Exception as e:
            return False, f"Cannot create directory: {e}"
    
    # Check if directory is writable
    if not os.access(directory, os.W_OK):
        return False, "Directory is not writable"
    
    # If file exists, check if it's writable
    if os.path.exists(output_path):
        if not os.access(output_path, os.W_OK):
            return False, "File exists and is not writable"
    
    return True, None
