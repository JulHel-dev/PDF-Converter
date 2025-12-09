"""Tests for architecture documentation and compliance."""

import pytest
import os


class TestArchitectureDocumentation:
    """Test that architecture documentation exists."""
    
    def test_architecture_doc_exists(self):
        """Test that ARCHITECTURE.md exists."""
        doc_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'docs',
            'ARCHITECTURE.md'
        )
        assert os.path.exists(doc_path)
    
    def test_accessibility_doc_exists(self):
        """Test that ACCESSIBILITY.md exists."""
        doc_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'docs',
            'ACCESSIBILITY.md'
        )
        assert os.path.exists(doc_path)


class TestImportResilience:
    """Test import resilience pattern."""
    
    def test_security_modules_import(self):
        """Test that security modules can be imported."""
        # These should all work with fallback imports
        from src.security import path_security
        from src.security import size_security
        from src.security import filename_security
        from src.security import temp_file_security
        from src.security import input_validation
        
        assert path_security is not None
        assert size_security is not None
        assert filename_security is not None
        assert temp_file_security is not None
        assert input_validation is not None
    
    def test_utils_modules_import(self):
        """Test that utils modules can be imported."""
        from src.utils import batch_processor
        from src.utils import file_lock
        from src.utils import memory_manager
        from src.utils import output_conflict
        from src.utils import conversion_verifier
        from src.utils import encoding_detector
        
        assert batch_processor is not None
        assert file_lock is not None
        assert memory_manager is not None
        assert output_conflict is not None
        assert conversion_verifier is not None
        assert encoding_detector is not None
    
    def test_i18n_module_import(self):
        """Test that i18n module can be imported."""
        from src.i18n import messages
        
        assert messages is not None
        assert hasattr(messages, 'get_message')
        assert hasattr(messages, 'MESSAGES')


class TestModuleStructure:
    """Test module structure."""
    
    def test_src_structure(self):
        """Test that src directory has expected structure."""
        base_dir = os.path.dirname(os.path.dirname(__file__))
        src_dir = os.path.join(base_dir, 'src')
        
        expected_dirs = [
            'config',
            'converters',
            'security',
            'utils',
            'logging',
            'i18n'
        ]
        
        for dir_name in expected_dirs:
            dir_path = os.path.join(src_dir, dir_name)
            assert os.path.exists(dir_path), f"Missing directory: {dir_name}"
    
    def test_docs_structure(self):
        """Test that docs directory exists."""
        base_dir = os.path.dirname(os.path.dirname(__file__))
        docs_dir = os.path.join(base_dir, 'docs')
        
        assert os.path.exists(docs_dir)
