"""Tests for internationalization support."""

import pytest
from src.i18n.messages import (
    MESSAGES,
    get_message,
    get_supported_languages,
    DEFAULT_LANGUAGE
)


class TestI18nMessages:
    """Test i18n message system."""
    
    def test_default_language_exists(self):
        """Test that default language is defined."""
        assert DEFAULT_LANGUAGE in MESSAGES
        assert len(MESSAGES[DEFAULT_LANGUAGE]) > 0
    
    def test_all_languages_have_app_title(self):
        """Test that all languages have app_title."""
        for lang, messages in MESSAGES.items():
            assert 'app_title' in messages, f"Missing app_title in {lang}"
    
    def test_get_message_english(self):
        """Test getting message in English."""
        message = get_message('app_title', 'en')
        assert message == 'Universal File Converter'
    
    def test_get_message_spanish(self):
        """Test getting message in Spanish."""
        message = get_message('app_title', 'es')
        assert 'Conversor' in message
    
    def test_get_message_french(self):
        """Test getting message in French."""
        message = get_message('app_title', 'fr')
        assert 'Convertisseur' in message
    
    def test_get_message_with_formatting(self):
        """Test message with format parameters."""
        message = get_message('file_too_large', 'en', max_mb=100)
        assert '100' in message
    
    def test_get_message_fallback_to_english(self):
        """Test fallback to English for unsupported language."""
        message = get_message('app_title', 'de')  # German not supported
        assert message == 'Universal File Converter'  # Falls back to English
    
    def test_get_message_missing_key(self):
        """Test behavior with missing key."""
        message = get_message('nonexistent_key', 'en')
        assert message == 'nonexistent_key'  # Returns key itself
    
    def test_get_supported_languages(self):
        """Test getting list of supported languages."""
        languages = get_supported_languages()
        
        assert 'en' in languages
        assert 'es' in languages
        assert 'fr' in languages
        assert len(languages) >= 3
    
    def test_all_languages_have_core_messages(self):
        """Test that all languages have core messages."""
        core_keys = [
            'app_title',
            'choose_file',
            'convert_button',
            'error',
            'success'
        ]
        
        for lang in MESSAGES.keys():
            for key in core_keys:
                assert key in MESSAGES[lang], f"Missing {key} in {lang}"
    
    def test_error_messages_consistent(self):
        """Test that all languages have same error messages."""
        error_keys = [
            'no_file_selected',
            'invalid_format',
            'file_not_found'
        ]
        
        english_errors = set(error_keys)
        
        for lang in MESSAGES.keys():
            lang_errors = set(k for k in MESSAGES[lang].keys() if k in error_keys)
            assert lang_errors == english_errors, f"Inconsistent errors in {lang}"


class TestMessageFormatting:
    """Test message formatting."""
    
    def test_format_with_single_param(self):
        """Test formatting with single parameter."""
        message = get_message('processing', 'en', filename='test.pdf')
        assert 'test.pdf' in message
    
    def test_format_with_multiple_params(self):
        """Test formatting with multiple parameters."""
        message = get_message('batch_summary', 'en', total=10, success=8, failed=2)
        assert '10' in message
        assert '8' in message
        assert '2' in message
    
    def test_format_missing_param(self):
        """Test formatting with missing parameter."""
        # Should not crash if parameter is missing
        message = get_message('file_too_large', 'en')
        assert isinstance(message, str)


class TestLanguageCoverage:
    """Test language coverage."""
    
    def test_minimum_messages_per_language(self):
        """Test that each language has minimum number of messages."""
        for lang, messages in MESSAGES.items():
            assert len(messages) >= 10, f"{lang} has too few messages"
    
    def test_no_empty_messages(self):
        """Test that no messages are empty strings."""
        for lang, messages in MESSAGES.items():
            for key, value in messages.items():
                assert value.strip(), f"Empty message: {lang}.{key}"
