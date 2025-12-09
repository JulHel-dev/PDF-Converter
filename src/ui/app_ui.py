"""
Streamlit UI for Universal File Converter

Modern web-based interface for file conversion with OCR detection and logging.
"""
import streamlit as st
import os
from pathlib import Path
from datetime import datetime
from src.config import settings
from src.logging.event_monitor import EventMonitor
from src.utils.format_detector import detect_format, get_supported_conversions
from src.utils.file_utils import get_file_size_mb
from src.detection.ocr_detector import OCRDetector


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


def init_session_state():
    """Initialize session state variables."""
    if 'conversion_history' not in st.session_state:
        st.session_state.conversion_history = []
    if 'monitor' not in st.session_state:
        st.session_state.monitor = EventMonitor()


def main():
    """Main Streamlit UI."""
    st.set_page_config(
        page_title=settings.WINDOW_TITLE,
        page_icon="🔄",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    init_session_state()
    monitor = st.session_state.monitor
    
    # Header
    st.title("🔄 Universal File Converter")
    st.markdown(f"**Version {settings.APP_VERSION}** | AI-Powered with OCR Detection & Black Box Logging")
    
    monitor.log_event('ui_loaded', {'ui_type': 'streamlit'}, severity='INFO')
    
    # Sidebar
    with st.sidebar:
        st.header("📊 System Info")
        st.info(f"**Input Folder:** `{settings.INPUT_FOLDER}`\n\n"
                f"**Output Folder:** `{settings.OUTPUT_FOLDER}`\n\n"
                f"**Log Folder:** `{settings.LOG_FOLDER}`")
        
        st.header("📋 Event Logs")
        
        if st.button("📥 Export Logs (JSON)", use_container_width=True):
            try:
                export_path = monitor.export_log(format='json')
                st.success(f"✅ Exported to:\n`{export_path}`")
            except Exception as e:
                st.error(f"❌ Export failed: {e}")
        
        if st.button("📥 Export Logs (CSV)", use_container_width=True):
            try:
                export_path = monitor.export_log(format='csv')
                st.success(f"✅ Exported to:\n`{export_path}`")
            except Exception as e:
                st.error(f"❌ Export failed: {e}")
        
        # Recent events
        st.subheader("Recent Events")
        recent_events = monitor.get_recent_events(count=5)
        for event in reversed(recent_events):
            severity_icon = {
                'INFO': 'ℹ️',
                'WARNING': '⚠️',
                'ERROR': '❌',
                'CRITICAL': '🚨'
            }.get(event.get('severity', 'INFO'), 'ℹ️')
            
            st.caption(f"{severity_icon} {event.get('event', 'unknown')}")
        
        # Anomalies
        anomalies = monitor.get_anomalies()
        if anomalies:
            st.warning(f"⚠️ {len(anomalies)} anomalies detected")
    
    # Main content area
    st.header("📁 File Conversion")
    
    # File upload
    uploaded_file = st.file_uploader(
        "Upload a file to convert",
        type=list(settings.SUPPORTED_INPUT_FORMATS),
        help="Supported formats: PDF, DOCX, XLSX, PNG, JPEG, MD, JSON, YAML, XML, CSV, and more"
    )
    
    if uploaded_file:
        # Save uploaded file temporarily
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix) as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            temp_path = tmp_file.name
        
        # Detect format
        input_format = detect_format(temp_path)
        
        if not input_format:
            st.error("❌ Could not detect file format. Please ensure the file is valid.")
            os.unlink(temp_path)
        else:
            # File analysis panel
            st.subheader("📊 File Analysis")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Format", input_format.upper())
            
            with col2:
                file_size = get_file_size_mb(temp_path)
                st.metric("Size", f"{file_size:.2f} MB")
            
            with col3:
                # Text layer check for PDFs
                text_status = "N/A"
                if input_format == 'pdf':
                    with st.spinner("Checking text layer..."):
                        ocr_detector = OCRDetector()
                        has_text = ocr_detector.check_pdf_text_layer(temp_path)
                        text_status = "✅ Present" if has_text else "❌ Missing"
                st.metric("Text Layer", text_status)
            
            with col4:
                # Page count for PDFs
                page_count = "N/A"
                if input_format == 'pdf':
                    try:
                        import fitz
                        with fitz.open(temp_path) as doc:
                            page_count = str(len(doc))
                    except Exception:
                        # Failed to open PDF, keep default page_count value
                        pass
                st.metric("Pages", page_count)
            
            # Warning for PDFs without text layer
            if input_format == 'pdf' and text_status == "❌ Missing":
                st.warning("💡 **No text layer detected!** This PDF appears to be scanned or image-based. "
                          "For best results, run OCR first using tools like:\n"
                          "- Foxit PDF Compressor\n"
                          "- Adobe Acrobat Pro\n"
                          "- Online OCR services")
            
            # Output format selection
            st.subheader("🎯 Conversion Settings")
            
            available_outputs = get_supported_conversions(input_format)
            
            if available_outputs:
                output_format = st.selectbox(
                    "Convert to:",
                    available_outputs,
                    help="Select target format for conversion"
                )
                
                # Advanced options (expandable)
                with st.expander("⚙️ Advanced Options"):
                    # Note: These options are placeholders for future enhancements
                    _ = st.checkbox("Preserve metadata", value=True)
                    if input_format in ['png', 'jpeg', 'jpg']:
                        _ = st.slider("Image DPI", min_value=72, max_value=300, value=150)
                
                # Convert button
                col1, col2 = st.columns([1, 3])
                with col1:
                    convert_button = st.button("🚀 Convert", type="primary", use_container_width=True)
                
                if convert_button:
                    # Perform conversion
                    output_filename = f"{Path(uploaded_file.name).stem}.{output_format}"
                    output_path = os.path.join(settings.OUTPUT_FOLDER, output_filename)
                    
                    # Get converter
                    converter = get_converter(input_format)
                    
                    if not converter:
                        st.error(f"❌ No converter available for {input_format.upper()}")
                    else:
                        with st.spinner(f"Converting to {output_format.upper()}..."):
                            success = converter.convert(temp_path, output_path, output_format)
                        
                        if success:
                            st.success(f"✅ Conversion complete!")
                            
                            # Provide download button
                            try:
                                with open(output_path, 'rb') as f:
                                    file_data = f.read()
                                
                                st.download_button(
                                    label="📥 Download Converted File",
                                    data=file_data,
                                    file_name=output_filename,
                                    mime='application/octet-stream',
                                    use_container_width=True
                                )
                                
                                # Add to history
                                st.session_state.conversion_history.append({
                                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                    'input': uploaded_file.name,
                                    'output': output_filename,
                                    'from': input_format,
                                    'to': output_format,
                                    'status': 'success'
                                })
                                
                            except Exception as e:
                                st.error(f"❌ Could not read output file: {e}")
                        else:
                            st.error("❌ Conversion failed. Check event logs for details.")
                            
                            # Add to history
                            st.session_state.conversion_history.append({
                                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                'input': uploaded_file.name,
                                'output': output_filename,
                                'from': input_format,
                                'to': output_format,
                                'status': 'failed'
                            })
            else:
                st.warning(f"⚠️ No conversions available for {input_format.upper()}")
            
            # Clean up temp file
            try:
                os.unlink(temp_path)
            except Exception:
                # Temp file cleanup failed, not critical
                pass
    
    # Conversion history
    if st.session_state.conversion_history:
        st.header("📜 Conversion History")
        
        for i, item in enumerate(reversed(st.session_state.conversion_history[-10:])):
            status_icon = "✅" if item['status'] == 'success' else "❌"
            
            with st.expander(f"{status_icon} {item['input']} → {item['output']} ({item['timestamp']})"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**From:** {item['from'].upper()}")
                    st.write(f"**To:** {item['to'].upper()}")
                with col2:
                    st.write(f"**Status:** {item['status'].upper()}")
                    st.write(f"**Time:** {item['timestamp']}")
    
    # Footer
    st.markdown("---")
    st.caption("🔒 All conversions are processed locally. No data is sent to external servers.")
    st.caption("📋 Event logs are automatically saved for debugging and monitoring.")


if __name__ == "__main__":
    main()
