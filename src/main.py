"""
Universal File Converter - Main Entry Point
Supports CLI and GUI modes.
"""
import argparse
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config.settings import ensure_folders_exist, CONVERSION_MATRIX
from src.logging.event_monitor import EventMonitor
from src.utils.format_detector import detect_format, is_conversion_supported
from src.utils.file_utils import list_files_in_directory, get_output_path


def get_converter(input_format: str):
    """Get appropriate converter instance for the input format."""
    input_format = input_format.lower()
    
    if input_format == 'pdf':
        from src.converters.pdf_converter import PDFConverter
        return PDFConverter()
    elif input_format in ['docx', 'doc']:
        from src.converters.docx_converter import DocxConverter
        return DocxConverter()
    elif input_format in ['xlsx', 'xls', 'ods']:
        from src.converters.xlsx_converter import XlsxConverter
        return XlsxConverter()
    elif input_format in ['png', 'jpeg', 'jpg', 'tiff', 'tif', 'bmp', 'gif', 'webp']:
        from src.converters.image_converter import ImageConverter
        return ImageConverter()
    elif input_format in ['md', 'markdown']:
        from src.converters.markdown_converter import MarkdownConverter
        return MarkdownConverter()
    elif input_format in ['json', 'yaml', 'yml', 'xml', 'csv']:
        from src.converters.data_converter import DataConverter
        return DataConverter()
    else:
        return None


def run_cli(args):
    """Run conversion in CLI mode."""
    monitor = EventMonitor()
    monitor.log_event('cli_start', {
        'input': args.input,
        'output': args.output,
        'from_format': args.from_format,
        'to_format': args.to_format
    }, severity='INFO', step='CLI conversion started')
    
    # Detect input format if not specified
    input_format = args.from_format
    if not input_format:
        input_format = detect_format(args.input)
        if not input_format:
            print(f"❌ Error: Could not detect format for {args.input}")
            monitor.log_event('format_detection_failed', {
                'file': args.input
            }, severity='ERROR')
            return False
        print(f"📝 Detected input format: {input_format.upper()}")
    
    # Validate conversion is supported
    if not is_conversion_supported(input_format, args.to_format):
        print(f"❌ Error: Conversion from {input_format.upper()} to {args.to_format.upper()} is not supported")
        monitor.log_event('unsupported_conversion', {
            'from': input_format,
            'to': args.to_format
        }, severity='ERROR')
        return False
    
    # Get converter
    converter = get_converter(input_format)
    if not converter:
        print(f"❌ Error: No converter available for {input_format.upper()}")
        monitor.log_event('converter_not_found', {
            'format': input_format
        }, severity='ERROR')
        return False
    
    # Run conversion
    print(f"🔄 Converting {os.path.basename(args.input)} from {input_format.upper()} to {args.to_format.upper()}...")
    
    success = converter.convert(args.input, args.output, args.to_format)
    
    if success:
        print(f"✅ Conversion complete: {args.output}")
        monitor.log_event('cli_complete', {'success': True, 'output': args.output}, severity='INFO')
        return True
    else:
        print(f"❌ Conversion failed. Check logs for details.")
        monitor.log_event('cli_failed', {'output': args.output}, severity='ERROR')
        return False


def run_batch(args):
    """Run batch conversion on folder."""
    monitor = EventMonitor()
    monitor.log_event('batch_start', {
        'input_folder': args.batch,
        'output_folder': args.output,
        'from_format': args.from_format,
        'to_format': args.to_format
    }, severity='INFO')
    
    # Get list of files
    if args.from_format:
        extensions = [args.from_format]
    else:
        # Process all supported formats
        extensions = list(CONVERSION_MATRIX.keys())
    
    files = list_files_in_directory(args.batch, extensions)
    
    if not files:
        print(f"❌ No files found in {args.batch}")
        return False
    
    print(f"📁 Found {len(files)} files to process")
    
    # Process each file
    success_count = 0
    fail_count = 0
    
    for file_path in files:
        # Detect format
        input_format = detect_format(file_path)
        if not input_format:
            print(f"⚠️  Skipping {os.path.basename(file_path)}: Unknown format")
            fail_count += 1
            continue
        
        # Check if conversion is supported
        if not is_conversion_supported(input_format, args.to_format):
            print(f"⚠️  Skipping {os.path.basename(file_path)}: {input_format.upper()} to {args.to_format.upper()} not supported")
            fail_count += 1
            continue
        
        # Generate output path
        output_path = get_output_path(file_path, args.output, args.to_format)
        
        # Get converter
        converter = get_converter(input_format)
        if not converter:
            print(f"⚠️  Skipping {os.path.basename(file_path)}: No converter available")
            fail_count += 1
            continue
        
        # Convert
        print(f"🔄 Converting {os.path.basename(file_path)}...")
        
        if converter.convert(file_path, output_path, args.to_format):
            print(f"   ✅ Success: {os.path.basename(output_path)}")
            success_count += 1
        else:
            print(f"   ❌ Failed: {os.path.basename(file_path)}")
            fail_count += 1
    
    # Summary
    print(f"\n📊 Batch conversion complete:")
    print(f"   ✅ Successful: {success_count}")
    print(f"   ❌ Failed: {fail_count}")
    print(f"   📁 Total: {len(files)}")
    
    monitor.log_event('batch_complete', {
        'total': len(files),
        'success': success_count,
        'failed': fail_count
    }, severity='INFO')
    
    return fail_count == 0


def run_gui():
    """Launch GUI mode."""
    monitor = EventMonitor()
    monitor.log_event('gui_launch', {}, severity='INFO')
    
    try:
        # Try to launch Streamlit UI
        from src.ui.app_ui import main as streamlit_main
        streamlit_main()
    except ImportError:
        print("❌ Error: Streamlit not installed")
        print("   Install with: pip install streamlit")
        monitor.log_event('gui_launch_failed', {
            'error': 'Streamlit not installed'
        }, severity='ERROR')
        return False
    except Exception as e:
        print(f"❌ Error launching GUI: {e}")
        monitor.log_event('gui_launch_failed', {
            'error': str(e)
        }, severity='ERROR')
        return False


def main():
    """Main entry point."""
    # CRITICAL: Ensure folders exist (for .exe distribution)
    ensure_folders_exist()
    
    parser = argparse.ArgumentParser(
        description='Universal File Converter with OCR Detection and Black Box Logging',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Single file conversion
  python main.py --input file.pdf --output file.docx --to docx
  
  # Batch conversion
  python main.py --batch ./Input --output ./Output --to txt
  
  # Launch GUI
  python main.py --gui
  
  # Auto-detect format
  python main.py -i document.pdf -o document.txt --to txt

Supported Formats:
  Documents: PDF, DOCX, DOC, TXT, MD, HTML, RTF, ODT
  Spreadsheets: XLSX, XLS, CSV, ODS
  Images: PNG, JPEG, TIFF, BMP, GIF, WEBP
  Data: JSON, YAML, XML, CSV
  Presentations: PPT, PPTX (limited)
        '''
    )
    
    parser.add_argument('--input', '-i', help='Input file path')
    parser.add_argument('--output', '-o', help='Output file/folder path')
    parser.add_argument('--from', dest='from_format', help='Source format (auto-detected if omitted)')
    parser.add_argument('--to', dest='to_format', help='Target format')
    parser.add_argument('--batch', help='Batch process entire folder')
    parser.add_argument('--gui', action='store_true', help='Launch GUI mode')
    parser.add_argument('--version', action='version', version='PDF-Converter 1.0.0')
    
    args = parser.parse_args()
    
    # Determine mode
    if args.gui or (not args.input and not args.batch):
        # GUI mode
        run_gui()
    elif args.batch:
        # Batch mode
        if not args.output:
            print("❌ Error: --output is required for batch mode")
            return 1
        if not args.to_format:
            print("❌ Error: --to is required for batch mode")
            return 1
        
        success = run_batch(args)
        return 0 if success else 1
    else:
        # CLI mode
        if not args.input:
            print("❌ Error: --input is required for CLI mode")
            return 1
        if not args.output:
            print("❌ Error: --output is required for CLI mode")
            return 1
        if not args.to_format:
            print("❌ Error: --to is required for CLI mode")
            return 1
        
        success = run_cli(args)
        return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
