# 🔄 Universal File Type Converter

A comprehensive, robust file converter with OCR detection, black box logging, and standalone Windows executable support.

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey)](https://github.com/JulHel-dev/PDF-Converter)

Convert between **20+ file formats** with intelligent OCR detection, comprehensive logging, and easy-to-use interfaces (CLI & GUI).

---

## ✨ Features

### 🔁 **Universal Format Support**
- **Documents**: PDF, DOCX, DOC, TXT, MD, HTML, RTF, ODT
- **Spreadsheets**: XLSX, XLS, CSV, ODS
- **Images**: PNG, JPEG, TIFF, BMP, GIF, WEBP
- **Data**: JSON, YAML, XML, CSV
- **Presentations**: PPT, PPTX (text extraction)

### 🤖 **Intelligent OCR Detection**
- Automatically detects text layers in PDFs
- Identifies scanned/image-based documents
- Provides recommendations for external OCR when needed
- **Note**: Detection only - does not perform OCR

### 📊 **Black Box Event Monitor**
- Logs every conversion event with full context
- Captures code location, stack traces, and execution time
- Anomaly detection for slow operations and repeated failures
- Export logs to JSON/CSV for AI-powered debugging
- Thread-safe for batch processing

### 🎨 **Dual Interface**
- **CLI**: Fast, scriptable command-line interface
- **GUI**: Modern web-based Streamlit interface
- Batch processing support for 1000+ files

### 📦 **Standalone Executable**
- Windows .exe with all dependencies bundled
- No Python installation required
- One-click deployment
- Portable - runs from USB drive

### 🛡️ **Robust Error Handling**
- Graceful error recovery
- Continue-on-error for batch operations
- Partial data extraction for corrupt files
- Detailed error logging

---

## 🚀 Quick Start

### Option 1: Download Standalone .exe (Windows)

1. **Download** `PDF-Converter.exe` from [Releases](https://github.com/JulHel-dev/PDF-Converter/releases)
2. **Run** the executable
3. **Choose mode**:
   - GUI: `PDF-Converter.exe --gui`
   - CLI: `PDF-Converter.exe -i input.pdf -o output.txt --to txt`

### Option 2: Run from Source

```bash
# Clone repository
git clone https://github.com/JulHel-dev/PDF-Converter.git
cd PDF-Converter

# Install dependencies
pip install -r requirements.txt

# Launch GUI
python src/main.py --gui

# Or use CLI
python src/main.py -i document.pdf -o document.txt --to txt
```

---

## 📖 Usage Guide

### Command Line Interface (CLI)

#### Single File Conversion

```bash
# PDF to text
python src/main.py -i document.pdf -o document.txt --to txt

# Image to PDF
python src/main.py -i photo.jpg -o photo.pdf --to pdf

# Excel to CSV
python src/main.py -i data.xlsx -o data.csv --to csv

# Markdown to HTML
python src/main.py -i README.md -o README.html --to html

# Auto-detect input format
python src/main.py -i file.pdf -o file.docx --to docx
```

#### Batch Conversion

```bash
# Convert all PDFs in folder to text
python src/main.py --batch ./Input --output ./Output --to txt

# Convert all images to PDF
python src/main.py --batch ./Photos --output ./PDFs --to pdf

# Specify input format for batch
python src/main.py --batch ./Documents --output ./Text --from docx --to txt
```

#### Help & Version

```bash
# Show help
python src/main.py --help

# Show version
python src/main.py --version
```

---

### Graphical User Interface (GUI)

```bash
# Launch GUI
python src/main.py --gui
```

**Features**:
- 📤 **File Upload**: Drag & drop or browse
- 🔍 **File Analysis**: Format, size, text layer status, page count
- 🎯 **Format Selection**: Choose from supported output formats
- ⚡ **One-Click Convert**: Start conversion with progress indicator
- 📥 **Download**: Instant download of converted files
- 📋 **Event Logs**: View recent events and export logs
- 📜 **Conversion History**: Track all conversions in session

---

## 📁 Folder Structure

```
PDF-Converter/
├── src/
│   ├── converters/         # Format-specific converter modules
│   ├── detection/          # OCR detection logic
│   ├── logging/            # Black Box Event Monitor
│   ├── config/             # Configuration files
│   ├── ui/                 # Streamlit GUI
│   ├── utils/              # Utility functions
│   └── main.py             # Application entry point
├── tests/                  # Unit and integration tests
├── docs/                   # Comprehensive documentation
│   ├── development/        # ARCHITECTURE.md
│   ├── implementation/     # CONVERSION_MATRIX.md
│   └── troubleshooting/    # COMMON_ERRORS.md
├── Log/                    # Event logs (auto-created)
├── Input/                  # Default input folder
├── Output/                 # Default output folder
├── requirements.txt        # Python dependencies
├── build.bat               # Windows build script
└── PDF-Converter.spec      # PyInstaller configuration
```

---

## 🔧 Building from Source

### Prerequisites

- Python 3.9 or higher
- pip (Python package manager)
- Git

### Build Windows .exe

```bash
# Windows
build.bat

# The .exe will be created in dist/ folder
```

**Manual Build**:

```bash
pip install -r requirements.txt
pip install pyinstaller
pyinstaller PDF-Converter.spec
```

---

## 🧪 Testing

```bash
# Run all tests
pytest tests/

# Run specific test module
pytest tests/test_pdf_converter.py

# Run with coverage
pytest --cov=src tests/
```

---

## 🔍 Supported Conversions

### Most Popular

| From → To | Quality | Notes |
|-----------|---------|-------|
| PDF → TXT | ⭐⭐⭐⭐⭐ | Best with text layer |
| PDF → DOCX | ⭐⭐⭐⭐ | Good formatting |
| DOCX → PDF | ⭐⭐⭐ | Requires external tool |
| Image → PDF | ⭐⭐⭐⭐⭐ | Multi-page support |
| Excel → CSV | ⭐⭐⭐⭐⭐ | All sheets |
| JSON ↔ YAML | ⭐⭐⭐⭐⭐ | Lossless |
| MD → HTML | ⭐⭐⭐⭐⭐ | Full styling |

**See full matrix**: [docs/implementation/CONVERSION_MATRIX.md](docs/implementation/CONVERSION_MATRIX.md)

---

## ⚙️ Configuration

### Settings (`src/config/settings.py`)

```python
# File size limit
MAX_FILE_SIZE_MB = 100

# Image rendering
DEFAULT_DPI = 150
IMAGE_QUALITY = 95

# Folders
INPUT_FOLDER = "./Input"
OUTPUT_FOLDER = "./Output"
LOG_FOLDER = "./Log/diagnostics"
```

### Event Monitor (`src/config/monitor_config.py`)

```python
# Logging
LOG_LEVEL = 'DEBUG'
LOG_RETENTION_DAYS = 7

# Performance
PERFORMANCE_THRESHOLD_MS = 2000

# Anomaly detection
ENABLE_ANOMALY_DETECTION = True
```

---

## 🐛 Troubleshooting

### Common Issues

**PDF has no text layer?**
- Use external OCR tool first (Adobe Acrobat, Foxit, online services)
- Or convert to images, then OCR, then back to PDF

**Conversion failed?**
- Check event logs: `Log/diagnostics/event_log_*.jsonl`
- Export logs from GUI for detailed analysis
- See [docs/troubleshooting/COMMON_ERRORS.md](docs/troubleshooting/COMMON_ERRORS.md)

**Missing dependencies?**
```bash
pip install -r requirements.txt
```

**Permission denied?**
- Run as administrator (Windows)
- Check folder permissions
- Use different output location

---

## 📚 Documentation

- **[ARCHITECTURE.md](docs/development/ARCHITECTURE.md)**: Technology decisions and design rationale
- **[CONVERSION_MATRIX.md](docs/implementation/CONVERSION_MATRIX.md)**: Complete format support reference
- **[COMMON_ERRORS.md](docs/troubleshooting/COMMON_ERRORS.md)**: Troubleshooting guide

---

## 🔐 Security & Privacy

- ✅ **100% Local Processing**: No data sent to external servers
- ✅ **No Internet Required**: Works completely offline
- ✅ **Input Validation**: File size limits, format validation
- ✅ **Dependency Scanning**: Regular security audits with `pip-audit`
- ✅ **Safe Error Handling**: No sensitive data in logs

---

## 🚦 Performance

| Operation | Expected Time |
|-----------|---------------|
| PDF text extraction (10 pages) | < 2s |
| PDF → DOCX (10 pages) | < 5s |
| Image → PDF (10 images) | < 10s |
| Batch (100 files) | < 5 min |

Operations exceeding 2s are flagged in event logs for analysis.

---

## 🤝 Contributing

Contributions welcome! To add support for new formats:

1. Create converter class inheriting from `BaseConverter`
2. Add format mappings to `settings.py`
3. Update routing in `main.py`
4. Add tests
5. Update documentation

See [ARCHITECTURE.md](docs/development/ARCHITECTURE.md) for details.

---

## 📄 License

MIT License - See [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgments

- [PyMuPDF](https://pymupdf.readthedocs.io/) - PDF processing
- [Pillow](https://pillow.readthedocs.io/) - Image handling
- [python-docx](https://python-docx.readthedocs.io/) - Word documents
- [Streamlit](https://streamlit.io/) - Modern UI framework
- [Indexer-Julius](https://github.com/JulHel-dev/Indexer-Julius) - Event monitor inspiration

---

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/JulHel-dev/PDF-Converter/issues)
- **Documentation**: [docs/](docs/)
- **Discussions**: [GitHub Discussions](https://github.com/JulHel-dev/PDF-Converter/discussions)

---

## 🗺️ Roadmap

- [ ] Multi-threaded batch processing
- [ ] Cloud storage integration (optional)
- [ ] Additional format support (CAD, 3D)
- [ ] Plugin system for custom converters
- [ ] macOS and Linux .app/.AppImage builds
- [ ] REST API mode
- [ ] Docker container

---

**Made with ❤️ by [JulHel-dev](https://github.com/JulHel-dev)**
