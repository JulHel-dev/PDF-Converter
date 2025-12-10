"""
Internationalization (i18n) Support

Centralized message strings for easy translation.
"""

# Default language
DEFAULT_LANGUAGE = 'en'

# Message strings organized by language
MESSAGES = {
    'en': {
        # General
        'app_title': 'Universal File Converter',
        'welcome': 'Welcome to PDF Converter',
        
        # File operations
        'choose_file': 'Choose a file to convert',
        'select_output_format': 'Select output format',
        'convert_button': 'Convert File',
        'download_button': 'Download Converted File',
        
        # Status messages
        'converting': 'Converting file...',
        'conversion_complete': 'Conversion complete!',
        'conversion_failed': 'Conversion failed',
        'file_too_large': 'File is too large (max {max_mb} MB)',
        'invalid_format': 'Invalid file format',
        
        # Errors
        'error': 'Error',
        'no_file_selected': 'No file selected',
        'unsupported_conversion': 'Conversion from {from_fmt} to {to_fmt} is not supported',
        'file_not_found': 'File not found: {path}',
        'permission_denied': 'Permission denied: {path}',
        
        # CLI messages
        'processing': 'Processing: {filename}',
        'success': 'Success',
        'failed': 'Failed',
        'batch_summary': 'Processed {total} files: {success} succeeded, {failed} failed',
    },
    
    'es': {
        # Spanish translations
        'app_title': 'Conversor Universal de Archivos',
        'welcome': 'Bienvenido al Convertidor de PDF',
        
        'choose_file': 'Elige un archivo para convertir',
        'select_output_format': 'Selecciona formato de salida',
        'convert_button': 'Convertir Archivo',
        'download_button': 'Descargar Archivo Convertido',
        
        'converting': 'Convirtiendo archivo...',
        'conversion_complete': '¡Conversión completa!',
        'conversion_failed': 'Conversión fallida',
        'file_too_large': 'El archivo es demasiado grande (máx {max_mb} MB)',
        'invalid_format': 'Formato de archivo inválido',
        
        'error': 'Error',
        'no_file_selected': 'Ningún archivo seleccionado',
        'unsupported_conversion': 'La conversión de {from_fmt} a {to_fmt} no está soportada',
        'file_not_found': 'Archivo no encontrado: {path}',
        'permission_denied': 'Permiso denegado: {path}',
        
        'processing': 'Procesando: {filename}',
        'success': 'Éxito',
        'failed': 'Fallido',
        'batch_summary': 'Procesados {total} archivos: {success} exitosos, {failed} fallidos',
    },
    
    'fr': {
        # French translations
        'app_title': 'Convertisseur de Fichiers Universel',
        'welcome': 'Bienvenue dans le Convertisseur PDF',
        
        'choose_file': 'Choisir un fichier à convertir',
        'select_output_format': 'Sélectionnez le format de sortie',
        'convert_button': 'Convertir le Fichier',
        'download_button': 'Télécharger le Fichier Converti',
        
        'converting': 'Conversion du fichier...',
        'conversion_complete': 'Conversion terminée!',
        'conversion_failed': 'Échec de la conversion',
        'file_too_large': 'Le fichier est trop volumineux (max {max_mb} MB)',
        'invalid_format': 'Format de fichier invalide',
        
        'error': 'Erreur',
        'no_file_selected': 'Aucun fichier sélectionné',
        'unsupported_conversion': 'La conversion de {from_fmt} vers {to_fmt} n\'est pas supportée',
        'file_not_found': 'Fichier introuvable: {path}',
        'permission_denied': 'Permission refusée: {path}',
        
        'processing': 'Traitement: {filename}',
        'success': 'Succès',
        'failed': 'Échoué',
        'batch_summary': 'Traité {total} fichiers: {success} réussis, {failed} échoués',
    }
}


def get_message(key: str, language: str = DEFAULT_LANGUAGE, **kwargs) -> str:
    """
    Get a translated message.
    
    Args:
        key: Message key
        language: Language code (default: English)
        **kwargs: Format parameters
        
    Returns:
        Translated message string
    """
    # Get messages for language (fallback to English)
    messages = MESSAGES.get(language, MESSAGES[DEFAULT_LANGUAGE])
    
    # Get specific message (fallback to key if not found)
    message = messages.get(key, key)
    
    # Format with parameters if provided
    if kwargs:
        try:
            message = message.format(**kwargs)
        except KeyError:
            pass  # If formatting fails, return unformatted
    
    return message


def get_supported_languages():
    """Get list of supported language codes."""
    return list(MESSAGES.keys())
