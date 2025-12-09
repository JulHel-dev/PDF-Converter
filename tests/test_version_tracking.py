"""Tests for version tracking."""

import sys
from src.config.settings import APP_VERSION, APP_BUILD_DATE, log_version_info


class TestVersionTracking:
    """Test version tracking."""
    
    def test_version_defined(self):
        """Test that version is defined."""
        assert APP_VERSION is not None
        assert len(APP_VERSION) > 0
        assert isinstance(APP_VERSION, str)
    
    def test_version_format(self):
        """Test version follows semantic versioning."""
        # Should be in format X.Y.Z
        parts = APP_VERSION.split('.')
        assert len(parts) >= 2  # At least major.minor
        
        # First parts should be numbers
        assert parts[0].isdigit()
        assert parts[1].isdigit()
    
    def test_build_date_defined(self):
        """Test that build date is defined."""
        assert APP_BUILD_DATE is not None
        assert len(APP_BUILD_DATE) > 0
        assert isinstance(APP_BUILD_DATE, str)
    
    def test_build_date_format(self):
        """Test build date is in ISO format."""
        # Should be YYYY-MM-DD
        parts = APP_BUILD_DATE.split('-')
        assert len(parts) == 3
        
        year, month, day = parts
        assert len(year) == 4
        assert len(month) == 2
        assert len(day) == 2
        
        # Check they're all digits
        assert year.isdigit()
        assert month.isdigit()
        assert day.isdigit()
    
    def test_log_version_info(self):
        """Test logging version info doesn't crash."""
        # Should not raise exception
        log_version_info()
    
    def test_version_components(self):
        """Test version can be parsed into components."""
        parts = APP_VERSION.split('.')
        
        major = int(parts[0])
        minor = int(parts[1])
        
        assert major >= 0
        assert minor >= 0
        
        # Patch version if exists
        if len(parts) >= 3:
            # May have additional info like "1.0.0-beta"
            patch_part = parts[2].split('-')[0]
            if patch_part.isdigit():
                patch = int(patch_part)
                assert patch >= 0


class TestVersionComparison:
    """Test version comparison logic."""
    
    def test_version_string_ordering(self):
        """Test version strings can be compared."""
        v1 = "1.0.0"
        v2 = "2.0.0"
        v3 = "1.1.0"
        
        # Simple string comparison works for major versions
        assert v1 < v2
        assert v3 < v2
    
    def test_version_tuple_comparison(self):
        """Test version tuple comparison."""
        def version_tuple(v: str) -> tuple:
            """Convert version string to tuple."""
            parts = v.split('.')
            return tuple(int(p) for p in parts if p.isdigit())
        
        v1 = version_tuple("1.0.0")
        v2 = version_tuple("2.0.0")
        v3 = version_tuple("1.1.0")
        
        assert v1 < v2
        assert v1 < v3
        assert v3 < v2


class TestVersionMetadata:
    """Test version metadata."""
    
    def test_python_version_available(self):
        """Test Python version is available."""
        assert sys.version_info.major >= 3
        assert sys.version_info.minor >= 7  # Minimum Python 3.7
    
    def test_platform_available(self):
        """Test platform info is available."""
        assert sys.platform is not None
        assert len(sys.platform) > 0
