"""
OCR and Text Layer Detection

Detects presence of OCR/text layers in documents.
NOTE: Does NOT perform OCR. Only detects if OCR has been applied externally.
"""
from typing import Optional, Dict
from src.logging.event_monitor import EventMonitor


class OCRDetector:
    """
    Detects presence of OCR/text layers in documents.
    
    NOTE: Does NOT perform OCR. Only detects if OCR has been applied externally.
    """
    
    def __init__(self):
        self.monitor = EventMonitor()
    
    def check_pdf_text_layer(self, pdf_path: str) -> bool:
        """
        Check if PDF has embedded text layer.
        
        Returns True if >50% of pages have meaningful text (>50 chars).
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            True if text layer is present
        """
        try:
            import fitz  # PyMuPDF
            
            with fitz.open(pdf_path) as doc:
                total_pages = len(doc)
                
                if total_pages == 0:
                    self.monitor.log_event('ocr_detection_complete', {
                        'file': pdf_path,
                        'total_pages': 0,
                        'has_text_layer': False,
                        'reason': 'No pages in document'
                    }, severity='WARNING')
                    return False
                
                pages_with_text = 0
                for page in doc:
                    text = page.get_text().strip()
                    if len(text) > 50:  # Meaningful text threshold
                        pages_with_text += 1
                
                has_text = (pages_with_text / total_pages) > 0.5
                
                self.monitor.log_event('ocr_detection_complete', {
                    'file': pdf_path,
                    'total_pages': total_pages,
                    'pages_with_text': pages_with_text,
                    'text_coverage_ratio': round(pages_with_text / total_pages, 2),
                    'has_text_layer': has_text
                }, severity='INFO')
                
                return has_text
                
        except ImportError:
            self.monitor.log_event('ocr_detection_failed', {
                'file': pdf_path,
                'error': 'PyMuPDF (fitz) not installed'
            }, severity='ERROR')
            return False
        except Exception as e:
            self.monitor.log_event('ocr_detection_failed', {
                'file': pdf_path,
                'error': str(e),
                'error_type': type(e).__name__
            }, severity='ERROR')
            return False
    
    def check_image_text(self, image_path: str) -> bool:
        """
        Check if image has embedded text metadata (EXIF/XMP).
        
        Args:
            image_path: Path to image file
            
        Returns:
            True if text metadata found
        """
        try:
            from PIL import Image
            from PIL.ExifTags import TAGS
            
            with Image.open(image_path) as img:
                exif_data = img.getexif()
                
                if exif_data:
                    # Look for text-related EXIF tags
                    text_tags = ['ImageDescription', 'UserComment', 'XPComment', 'XPKeywords']
                    has_text = False
                    
                    for tag_id, value in exif_data.items():
                        tag_name = TAGS.get(tag_id, tag_id)
                        if tag_name in text_tags and value:
                            has_text = True
                            break
                    
                    self.monitor.log_event('image_text_check_complete', {
                        'file': image_path,
                        'has_text_metadata': has_text,
                        'exif_tags_found': len(exif_data)
                    }, severity='INFO')
                    
                    return has_text
                else:
                    self.monitor.log_event('image_text_check_complete', {
                        'file': image_path,
                        'has_text_metadata': False,
                        'reason': 'No EXIF data found'
                    }, severity='INFO')
                    return False
                    
        except ImportError:
            self.monitor.log_event('image_text_check_failed', {
                'file': image_path,
                'error': 'PIL not installed'
            }, severity='ERROR')
            return False
        except Exception as e:
            self.monitor.log_event('image_text_check_failed', {
                'file': image_path,
                'error': str(e),
                'error_type': type(e).__name__
            }, severity='ERROR')
            return False
    
    def get_text_coverage_ratio(self, pdf_path: str) -> float:
        """
        Calculate ratio of pages with text vs total pages.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Coverage ratio (0.0 to 1.0)
        """
        try:
            import fitz
            
            with fitz.open(pdf_path) as doc:
                total_pages = len(doc)
                
                if total_pages == 0:
                    return 0.0
                
                pages_with_text = sum(
                    1 for page in doc 
                    if len(page.get_text().strip()) > 50
                )
                
                return pages_with_text / total_pages
                
        except Exception as e:
            self.monitor.log_event('text_coverage_calculation_failed', {
                'file': pdf_path,
                'error': str(e)
            }, severity='ERROR')
            return 0.0
    
    def get_text_statistics(self, pdf_path: str) -> Dict:
        """
        Get detailed text statistics for PDF.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Dictionary with text statistics
        """
        try:
            import fitz
            
            stats = {
                'total_pages': 0,
                'pages_with_text': 0,
                'total_characters': 0,
                'average_chars_per_page': 0,
                'coverage_ratio': 0.0,
                'has_text_layer': False
            }
            
            with fitz.open(pdf_path) as doc:
                stats['total_pages'] = len(doc)
                
                for page in doc:
                    text = page.get_text().strip()
                    char_count = len(text)
                    stats['total_characters'] += char_count
                    
                    if char_count > 50:
                        stats['pages_with_text'] += 1
                
                if stats['total_pages'] > 0:
                    stats['average_chars_per_page'] = stats['total_characters'] / stats['total_pages']
                    stats['coverage_ratio'] = stats['pages_with_text'] / stats['total_pages']
                    stats['has_text_layer'] = stats['coverage_ratio'] > 0.5
            
            return stats
            
        except Exception as e:
            self.monitor.log_event('text_statistics_failed', {
                'file': pdf_path,
                'error': str(e)
            }, severity='ERROR')
            return {}
