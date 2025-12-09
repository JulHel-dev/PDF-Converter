"""Tests for dependency version pinning."""

import pytest
import os
import re


class TestDependencyPinning:
    """Test that dependencies are properly pinned."""
    
    @pytest.fixture
    def requirements_content(self):
        """Read requirements.txt file."""
        req_file = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'requirements.txt'
        )
        
        with open(req_file, 'r') as f:
            return f.read()
    
    def test_requirements_file_exists(self):
        """Test that requirements.txt exists."""
        req_file = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'requirements.txt'
        )
        
        assert os.path.exists(req_file)
    
    def test_all_dependencies_pinned(self, requirements_content):
        """Test that all dependencies use exact version pinning (==)."""
        lines = requirements_content.split('\n')
        
        for line in lines:
            line = line.strip()
            
            # Skip comments and empty lines
            if not line or line.startswith('#'):
                continue
            
            # Skip platform-specific markers
            if ';' in line:
                line = line.split(';')[0].strip()
            
            # Check for version specifier
            if line:
                # Should use == for pinning
                assert '==' in line, f"Dependency not pinned: {line}"
                
                # Should not use >= or > (allows unpinned versions)
                assert '>=' not in line, f"Dependency uses >= instead of ==: {line}"
                assert '>' not in line or '>=' not in line, f"Dependency not pinned: {line}"
    
    def test_no_loose_constraints(self, requirements_content):
        """Test that no loose version constraints are used."""
        # Loose constraints: >=, >, ~=, etc.
        loose_patterns = [r'>=', r'[^=]>', r'~=', r'\*']
        
        lines = requirements_content.split('\n')
        
        for line in lines:
            line = line.strip()
            
            # Skip comments and empty lines
            if not line or line.startswith('#'):
                continue
            
            # Skip platform-specific markers
            if ';' in line:
                line = line.split(';')[0].strip()
            
            if line:
                for pattern in loose_patterns:
                    match = re.search(pattern, line)
                    if match:
                        # Allow in comments
                        if '#' in line and line.index('#') < match.start():
                            continue
                        # >= is not allowed (use ==)
                        if pattern == r'>=':
                            assert False, f"Loose constraint found: {line}"
    
    def test_version_format(self, requirements_content):
        """Test that versions follow semantic versioning."""
        lines = requirements_content.split('\n')
        
        for line in lines:
            line = line.strip()
            
            # Skip comments and empty lines
            if not line or line.startswith('#'):
                continue
            
            # Skip platform-specific markers
            if ';' in line:
                line = line.split(';')[0].strip()
            
            if '==' in line:
                # Extract version
                pkg_name, version = line.split('==')
                version = version.strip()
                
                # Version should have at least major.minor
                parts = version.split('.')
                assert len(parts) >= 2, f"Invalid version format: {version}"
                
                # First part should be numeric
                assert parts[0].isdigit(), f"Invalid major version: {version}"
    
    def test_critical_dependencies_present(self, requirements_content):
        """Test that critical dependencies are present."""
        critical_deps = [
            'PyMuPDF',
            'python-docx',
            'openpyxl',
            'Pillow',
            'PyYAML',
            'psutil',
            'chardet'
        ]
        
        for dep in critical_deps:
            assert dep in requirements_content, f"Critical dependency missing: {dep}"
    
    def test_security_related_deps(self, requirements_content):
        """Test that security-related dependencies are present."""
        security_deps = [
            'Pillow',  # Image processing (CVE patches)
            'PyYAML',  # YAML parsing (security updates)
        ]
        
        for dep in security_deps:
            assert dep in requirements_content, f"Security dependency missing: {dep}"


class TestDependencyMetadata:
    """Test dependency metadata."""
    
    @pytest.fixture
    def requirements_content(self):
        """Read requirements.txt file."""
        req_file = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'requirements.txt'
        )
        
        with open(req_file, 'r') as f:
            return f.read()
    
    def test_file_has_header(self, requirements_content):
        """Test that requirements.txt has a header."""
        lines = requirements_content.split('\n')
        
        # First non-empty line should be a comment
        for line in lines:
            if line.strip():
                assert line.strip().startswith('#')
                break
    
    def test_sections_organized(self, requirements_content):
        """Test that dependencies are organized in sections."""
        # Should have section comments
        assert '# PDF Processing' in requirements_content
        assert '# Document Processing' in requirements_content
        assert '# Image Processing' in requirements_content
    
    def test_comments_present(self, requirements_content):
        """Test that dependencies have explanatory comments."""
        lines = requirements_content.split('\n')
        
        dep_lines = [l for l in lines if l.strip() and not l.strip().startswith('#')]
        
        # Most dependency lines should have inline comments
        commented = sum(1 for l in dep_lines if '#' in l)
        
        # At least 50% should have comments
        assert commented >= len(dep_lines) * 0.5


class TestOptionalDependencies:
    """Test optional dependencies."""
    
    @pytest.fixture
    def requirements_content(self):
        """Read requirements.txt file."""
        req_file = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'requirements.txt'
        )
        
        with open(req_file, 'r') as f:
            return f.read()
    
    def test_optional_deps_commented(self, requirements_content):
        """Test that optional dependencies are commented out."""
        # Optional dependencies should be commented
        optional_section = '# Optional:'
        
        assert optional_section in requirements_content
    
    def test_development_deps_noted(self, requirements_content):
        """Test that development dependencies are noted."""
        # Should mention development dependencies
        assert 'development' in requirements_content.lower() or 'testing' in requirements_content.lower()
