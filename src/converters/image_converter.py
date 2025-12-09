"""
Image Converter

Handles image format conversions.
Supported formats: PNG, JPEG, TIFF, BMP, GIF, WEBP
Also supports Images → PDF
"""
from typing import List
from src.converters.base_converter import BaseConverter


class ImageConverter(BaseConverter):
    """
    Handles image format conversions.
    
    Supported formats: PNG, JPEG, TIFF, BMP, GIF, WEBP
    Also supports: Images → PDF
    """
    
    def __init__(self):
        super().__init__()
        self.supported_input_formats = ['png', 'jpeg', 'jpg', 'tiff', 'tif', 'bmp', 'gif', 'webp']
        self.supported_output_formats = ['png', 'jpeg', 'jpg', 'tiff', 'tif', 'bmp', 'webp', 'pdf']
    
    def convert(self, input_path: str, output_path: str, output_format: str) -> bool:
        """Convert image to target format."""
        timer_id = self.monitor.start_timer('image_conversion')
        
        try:
            # Step 1: Validate
            self.monitor.log_event('conversion_start', {
                'input': input_path,
                'output_format': output_format,
                'output_path': output_path
            }, severity='INFO', step='Step 1/3: Validating input')
            
            if not self.validate_input(input_path):
                return False
            
            if not self.validate_output(output_path):
                return False
            
            # Step 2: Load image
            self.monitor.log_event('image_load', {
                'input': input_path
            }, severity='INFO', step='Step 2/3: Loading image')
            
            from PIL import Image
            
            img = Image.open(input_path)
            original_mode = img.mode
            original_format = img.format
            
            self.monitor.log_event('image_loaded', {
                'size': img.size,
                'mode': original_mode,
                'format': original_format
            }, severity='INFO')
            
            # Step 3: Convert and save
            self.monitor.log_event('image_conversion', {
                'output_format': output_format
            }, severity='INFO', step='Step 3/3: Converting image')
            
            output_format = output_format.lower()
            
            if output_format == 'pdf':
                result = self._convert_to_pdf(img, output_path)
            else:
                result = self._convert_image(img, output_path, output_format, original_mode)
            
            img.close()
            
            self.monitor.log_event('conversion_complete', {
                'input': input_path,
                'output': output_path,
                'success': result
            }, severity='INFO', step='Conversion complete')
            
            return result
            
        except ImportError:
            self.monitor.log_event('dependency_missing', {
                'library': 'Pillow',
                'install_command': 'pip install Pillow'
            }, severity='ERROR')
            return False
        except Exception as e:
            self.monitor.log_event('conversion_failed', {
                'input': input_path,
                'output_format': output_format,
                'error': str(e),
                'error_type': type(e).__name__
            }, severity='ERROR')
            return False
        finally:
            self.monitor.end_timer(timer_id)
    
    def _convert_image(self, img, output_path: str, output_format: str, original_mode: str) -> bool:
        """Convert image to another image format."""
        try:
            from PIL import Image
            from src.config.settings import IMAGE_QUALITY
            
            # Handle format-specific requirements
            save_kwargs = {}
            
            if output_format in ['jpeg', 'jpg']:
                # JPEG doesn't support transparency
                if img.mode in ('RGBA', 'LA', 'P'):
                    # Convert to RGB with white background
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                    img = background
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
                
                save_kwargs['quality'] = IMAGE_QUALITY
                save_kwargs['optimize'] = True
                output_format = 'JPEG'
            
            elif output_format == 'png':
                # PNG supports transparency
                if img.mode == 'P':
                    img = img.convert('RGBA')
                save_kwargs['optimize'] = True
                output_format = 'PNG'
            
            elif output_format in ['tiff', 'tif']:
                output_format = 'TIFF'
            
            elif output_format == 'bmp':
                # BMP doesn't support transparency
                if img.mode in ('RGBA', 'LA'):
                    img = img.convert('RGB')
                output_format = 'BMP'
            
            elif output_format == 'webp':
                save_kwargs['quality'] = IMAGE_QUALITY
                output_format = 'WEBP'
            
            # Preserve EXIF data if available
            exif = img.info.get('exif')
            if exif and output_format in ['JPEG', 'PNG']:
                save_kwargs['exif'] = exif
            
            img.save(output_path, format=output_format, **save_kwargs)
            return True
            
        except Exception as e:
            self.monitor.log_event('image_conversion_failed', {
                'output_format': output_format,
                'error': str(e)
            }, severity='ERROR')
            return False
    
    def _convert_to_pdf(self, img, output_path: str) -> bool:
        """Convert image to PDF."""
        try:
            from PIL import Image
            
            # Convert RGBA to RGB for PDF
            if img.mode in ('RGBA', 'LA'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[-1])
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            img.save(output_path, 'PDF', resolution=100.0)
            return True
            
        except Exception as e:
            self.monitor.log_event('pdf_conversion_failed', {
                'error': str(e)
            }, severity='ERROR')
            return False
    
    def batch_convert_to_pdf(self, image_paths: List[str], output_path: str) -> bool:
        """
        Convert multiple images into a single PDF.
        
        Args:
            image_paths: List of image file paths
            output_path: Output PDF path
            
        Returns:
            True if successful
        """
        try:
            from PIL import Image
            
            if not image_paths:
                return False
            
            images = []
            for img_path in image_paths:
                img = Image.open(img_path)
                
                # Convert to RGB for PDF
                if img.mode in ('RGBA', 'LA'):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    background.paste(img, mask=img.split()[-1])
                    img = background
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
                
                images.append(img)
            
            # Save first image with append_images for multi-page PDF
            if len(images) == 1:
                images[0].save(output_path, 'PDF', resolution=100.0)
            else:
                images[0].save(output_path, 'PDF', resolution=100.0, 
                             save_all=True, append_images=images[1:])
            
            # Close all images
            for img in images:
                img.close()
            
            self.monitor.log_event('batch_pdf_created', {
                'image_count': len(image_paths),
                'output': output_path
            }, severity='INFO')
            
            return True
            
        except Exception as e:
            self.monitor.log_event('batch_pdf_failed', {
                'error': str(e)
            }, severity='ERROR')
            return False
    
    def resize_image(self, input_path: str, output_path: str, size: tuple) -> bool:
        """
        Resize image to specific dimensions.
        
        Args:
            input_path: Input image path
            output_path: Output image path
            size: Target size as (width, height)
            
        Returns:
            True if successful
        """
        try:
            from PIL import Image
            
            img = Image.open(input_path)
            # Use backward-compatible resampling method
            try:
                resample = Image.Resampling.LANCZOS
            except AttributeError:
                resample = Image.LANCZOS
            img_resized = img.resize(size, resample)
            
            # Preserve format
            output_format = img.format or 'PNG'
            img_resized.save(output_path, format=output_format)
            
            img.close()
            img_resized.close()
            
            return True
            
        except Exception as e:
            self.monitor.log_event('resize_failed', {
                'error': str(e)
            }, severity='ERROR')
            return False
