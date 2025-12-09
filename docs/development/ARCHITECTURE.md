# Architecture Documentation

## Technology Decision Rationale

This document explains the architectural decisions and technology choices for the Universal File Converter.

---

## Core Design Principles

### 1. Modularity
- **Decision**: Separate converter classes for each format family
- **Rationale**: 
  - Easy to add new format support
  - Isolated failure domains
  - Clear separation of concerns
  - Testability

### 2. Event-Driven Logging
- **Decision**: Singleton Black Box Event Monitor
- **Rationale**:
  - Complete audit trail for AI debugging
  - Thread-safe for batch processing
  - Low overhead with deque-based memory management
  - Easy export to JSON/CSV for analysis

### 3. Abstract Base Class Pattern
- **Decision**: `BaseConverter` as parent for all converters
- **Rationale**:
  - Enforces consistent interface
  - Shared validation and metadata extraction
  - Reduces code duplication
  - Easy to extend

---

## Library Choices

### PDF Processing: PyMuPDF (fitz)

**Chosen**: PyMuPDF  
**Alternatives Considered**: PyPDF2, pdfplumber, pypdf

**Rationale**:
- ✅ Fast and efficient C++ core
- ✅ Excellent text extraction
- ✅ Image rendering capabilities
- ✅ Good maintenance and community
- ✅ Permissive license (AGPL/commercial)
- ❌ Larger binary size (acceptable tradeoff)

**Migration Notes**: If PyMuPDF licensing becomes an issue, pypdf is a pure-Python fallback with similar API.

---

### Image Processing: Pillow (PIL)

**Chosen**: Pillow  
**Alternatives Considered**: OpenCV, imageio

**Rationale**:
- ✅ Industry standard for Python
- ✅ Comprehensive format support
- ✅ EXIF metadata handling
- ✅ Small footprint
- ✅ Easy to use API
- ❌ Limited for advanced CV tasks (not needed here)

---

### Document Processing: python-docx

**Chosen**: python-docx  
**Alternatives Considered**: LibreOffice headless, docx2python

**Rationale**:
- ✅ Pure Python (no external dependencies)
- ✅ Good DOCX support
- ✅ Preserves formatting
- ✅ Active maintenance
- ❌ DOCX only (no DOC support without conversion)

**Note**: For legacy DOC files, recommend pre-conversion with LibreOffice or online tools.

---

### Spreadsheet Processing: openpyxl

**Chosen**: openpyxl  
**Alternatives Considered**: xlrd/xlwt, pandas

**Rationale**:
- ✅ Native XLSX support
- ✅ Formula preservation (as text)
- ✅ Style preservation
- ✅ No pandas dependency (lighter)
- ❌ Excel 2003 XLS requires xlrd

---

### Markdown: python-markdown

**Chosen**: python-markdown  
**Alternatives Considered**: mistune, commonmark

**Rationale**:
- ✅ Extensive extension ecosystem
- ✅ Tables, code highlighting support
- ✅ Mature and stable
- ✅ Good documentation

---

### Data Formats: PyYAML + stdlib

**Chosen**: PyYAML + stdlib (json, xml.etree, csv)  
**Alternatives Considered**: ruamel.yaml, xmltodict

**Rationale**:
- ✅ Standard library where possible
- ✅ PyYAML is lightweight and fast
- ✅ Minimal dependencies
- ✅ Good Python integration

---

### GUI: Streamlit

**Chosen**: Streamlit  
**Alternatives Considered**: Tkinter, PyQt, Electron

**Rationale**:
- ✅ Rapid development
- ✅ Modern, clean UI
- ✅ Built-in file upload/download
- ✅ Reactive programming model
- ✅ Easy deployment as web app
- ❌ Larger bundle size (acceptable for features)
- ❌ Requires browser (can bundle with PyInstaller)

**Tkinter Alternative**: Could be implemented for lighter weight, but Streamlit provides better UX out of the box.

---

## Packaging Strategy

### PyInstaller for Windows .exe

**Decision**: PyInstaller with onefile mode  
**Alternatives Considered**: cx_Freeze, py2exe, Nuitka

**Rationale**:
- ✅ Best compatibility with modern Python
- ✅ Good library detection
- ✅ Active maintenance
- ✅ Cross-platform (Linux, Mac also possible)
- ✅ Spec file for reproducible builds
- ❌ Large executable size (~50-100MB with all deps)

**Optimization**: UPX compression enabled to reduce size.

---

## Scalability Considerations

### Batch Processing
- **Design**: Sequential processing with per-file error isolation
- **Rationale**: Simple, reliable, good for 1000+ files
- **Future**: Could add multiprocessing for CPU-bound conversions

### Memory Management
- **Design**: Stream processing where possible
- **Rationale**: Handle large files without loading entirely into memory
- **Implementation**: PyMuPDF and Pillow both support streaming

### Error Recovery
- **Design**: Continue-on-error with detailed logging
- **Rationale**: One bad file shouldn't stop entire batch
- **Implementation**: Try/except blocks with event logging at each step

---

## Security Considerations

### Input Validation
- **Design**: File size limits, format validation, path sanitization
- **Rationale**: Prevent malicious files from causing issues
- **Implementation**: `BaseConverter.validate_input()`

### Dependency Management
- **Design**: Pin major versions, regular updates
- **Rationale**: Security patches while maintaining compatibility
- **Tools**: `pip-audit` for vulnerability scanning

### No External Calls
- **Design**: All processing local
- **Rationale**: Privacy, security, works offline
- **Note**: OCR detection only, no actual OCR performed

---

## Future Extensibility

### Adding New Formats
1. Create new converter class inheriting from `BaseConverter`
2. Implement `convert()` method
3. Add format mappings to `settings.py`
4. Update `main.py` routing logic
5. Add tests

### Plugin System (Future)
- Could implement plugin discovery in `converters/` directory
- Use entry points or directory scanning
- Allow third-party format support

---

## Performance Benchmarks (Target)

| Operation | Target Time | Notes |
|-----------|-------------|-------|
| PDF text extraction (10 pages) | < 2s | With text layer |
| PDF → DOCX (10 pages) | < 5s | Including formatting |
| Image → PDF (10 images, 2MB each) | < 10s | At 150 DPI |
| Batch (100 files) | < 5min | Average complexity |

Operations exceeding 2s are flagged as "slow operations" in event logs.

---

## Testing Strategy

### Unit Tests
- Each converter module
- OCR detector
- Event monitor
- File utilities

### Integration Tests
- End-to-end conversion flows
- Batch processing
- Error handling

### Compatibility Tests
- Clean Windows VM (no Python)
- Various file formats
- Large files (up to 100MB limit)

---

## References

- [PyMuPDF Documentation](https://pymupdf.readthedocs.io/)
- [Pillow Documentation](https://pillow.readthedocs.io/)
- [python-docx Documentation](https://python-docx.readthedocs.io/)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [PyInstaller Documentation](https://pyinstaller.org/)
- [Indexer-Julius Event Monitor Reference](https://github.com/JulHel-dev/Indexer-Julius/blob/main/src/event_monitor.py)
