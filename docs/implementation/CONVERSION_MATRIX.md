# Conversion Matrix

Complete reference for supported file format conversions.

---

## Format Support Overview

### Input Formats Supported

| Category | Formats |
|----------|---------|
| **Documents** | PDF, DOC, DOCX, TXT, MD, HTML, RTF, ODT |
| **Spreadsheets** | XLSX, XLS, CSV, ODS |
| **Images** | PNG, JPEG/JPG, TIFF/TIF, BMP, GIF, WEBP |
| **Data** | JSON, YAML/YML, XML, CSV |
| **Presentations** | PPT, PPTX (limited) |

---

## Detailed Conversion Support

### PDF Conversions

| From | To | Quality | Notes |
|------|----|---------| ------|
| PDF | TXT | ⭐⭐⭐⭐⭐ | Best with text layer |
| PDF | MD | ⭐⭐⭐⭐ | Preserves structure |
| PDF | DOCX | ⭐⭐⭐⭐ | Good formatting |
| PDF | HTML | ⭐⭐⭐⭐ | Includes metadata |
| PDF | PNG | ⭐⭐⭐⭐⭐ | Renders each page |
| PDF | JPEG | ⭐⭐⭐⭐⭐ | Renders each page |

**Requirements**: Text layer needed for text-based conversions. Images generated at configurable DPI (default 150).

---

### DOCX Conversions

| From | To | Quality | Notes |
|------|----|---------| ------|
| DOCX | PDF | ⭐⭐⭐ | Requires external tool |
| DOCX | TXT | ⭐⭐⭐⭐⭐ | Removes formatting |
| DOCX | MD | ⭐⭐⭐⭐ | Preserves headings |
| DOCX | HTML | ⭐⭐⭐⭐ | Good structure |
| DOC | * | ⭐⭐⭐ | Via DOCX conversion |

**Note**: PDF conversion requires external tools (LibreOffice, Word automation, or cloud services).

---

### XLSX Conversions

| From | To | Quality | Notes |
|------|----|---------| ------|
| XLSX | CSV | ⭐⭐⭐⭐⭐ | First sheet or all |
| XLSX | JSON | ⭐⭐⭐⭐ | Structured data |
| XLSX | TXT | ⭐⭐⭐⭐ | Readable format |
| XLSX | PDF | ⭐⭐⭐ | Requires external tool |
| XLS | * | ⭐⭐⭐⭐ | Via XLSX conversion |
| ODS | * | ⭐⭐⭐⭐ | Via XLSX conversion |

**Note**: Formulas preserved as calculated values. Multi-sheet workbooks supported.

---

### Image Conversions

| From | To | Quality | Notes |
|------|----|---------| ------|
| PNG | JPEG | ⭐⭐⭐⭐⭐ | Removes transparency |
| PNG | PDF | ⭐⭐⭐⭐⭐ | Single or multi-page |
| PNG | WEBP | ⭐⭐⭐⭐⭐ | Modern format |
| PNG | TIFF | ⭐⭐⭐⭐⭐ | High quality |
| PNG | BMP | ⭐⭐⭐⭐⭐ | Uncompressed |
| JPEG | PNG | ⭐⭐⭐⭐⭐ | Lossless conversion |
| JPEG | PDF | ⭐⭐⭐⭐⭐ | Single or multi-page |
| JPEG | WEBP | ⭐⭐⭐⭐⭐ | Smaller size |
| TIFF | PNG/JPEG | ⭐⭐⭐⭐⭐ | Multi-page support |
| BMP | PNG/JPEG | ⭐⭐⭐⭐⭐ | Compression |
| GIF | PNG/JPEG | ⭐⭐⭐⭐ | Loses animation |
| WEBP | PNG/JPEG | ⭐⭐⭐⭐⭐ | Universal compat |

**Note**: EXIF metadata preserved where supported. Default quality: 95%.

---

### Markdown Conversions

| From | To | Quality | Notes |
|------|----|---------| ------|
| MD | HTML | ⭐⭐⭐⭐⭐ | Full styling |
| MD | TXT | ⭐⭐⭐⭐ | Removes syntax |
| MD | PDF | ⭐⭐⭐ | Via HTML intermediate |
| MD | DOCX | ⭐⭐⭐⭐ | Basic formatting |
| HTML | MD | ⭐⭐⭐ | Reverse conversion |

**Note**: Supports tables, code blocks, and GitHub-flavored Markdown extensions.

---

### Data Format Conversions

| From | To | Quality | Notes |
|------|----|---------| ------|
| JSON | YAML | ⭐⭐⭐⭐⭐ | Lossless |
| JSON | XML | ⭐⭐⭐⭐⭐ | Structured |
| JSON | CSV | ⭐⭐⭐⭐ | Tabular data only |
| JSON | TXT | ⭐⭐⭐⭐⭐ | Pretty-printed |
| YAML | JSON | ⭐⭐⭐⭐⭐ | Lossless |
| YAML | XML | ⭐⭐⭐⭐⭐ | Structured |
| YAML | TXT | ⭐⭐⭐⭐⭐ | Pretty-printed |
| XML | JSON | ⭐⭐⭐⭐ | Attribute mapping |
| XML | YAML | ⭐⭐⭐⭐ | Attribute mapping |
| XML | TXT | ⭐⭐⭐⭐ | Pretty-printed |
| CSV | JSON | ⭐⭐⭐⭐⭐ | Row-based |
| CSV | XLSX | ⭐⭐⭐⭐⭐ | Single sheet |
| CSV | TXT | ⭐⭐⭐⭐⭐ | Formatted |

---

## Special Cases

### Multi-Page PDFs to Images
- Creates multiple image files (one per page)
- Naming: `filename_page_1.png`, `filename_page_2.png`, etc.
- DPI configurable (default: 150)

### Multi-Sheet Excel to CSV
- Primary sheet saved as specified filename
- Additional sheets: `filename_sheet2.csv`, `filename_sheet3.csv`, etc.

### Multi-Image to PDF
- Use batch converter with multiple input files
- Creates single multi-page PDF

---

## Limitations

### Known Limitations

1. **PDF → DOCX**: Complex layouts may lose fidelity
2. **Scanned PDFs**: Require external OCR before conversion
3. **Legacy Formats**: DOC, XLS require pre-conversion
4. **Presentations**: PPT/PPTX support is read-only for text extraction
5. **Encrypted Files**: Not supported (decrypt first)
6. **Very Large Files**: Default limit 100MB (configurable)

### Not Supported

- ❌ Video formats (MP4, AVI, etc.)
- ❌ Audio formats (MP3, WAV, etc.)
- ❌ Archives (ZIP, RAR, etc.)
- ❌ Executable formats
- ❌ Database files (without export)
- ❌ CAD files (DWG, DXF, etc.)

---

## Quality Ratings Legend

| Rating | Description |
|--------|-------------|
| ⭐⭐⭐⭐⭐ | Excellent - Lossless or near-lossless |
| ⭐⭐⭐⭐ | Good - Minor quality loss acceptable |
| ⭐⭐⭐ | Fair - Noticeable limitations |
| ⭐⭐ | Limited - Use with caution |
| ⭐ | Poor - Not recommended |

---

## Usage Examples

### Command Line

```bash
# PDF to text
python main.py -i document.pdf -o document.txt --to txt

# Image to PDF
python main.py -i photo.jpg -o photo.pdf --to pdf

# Excel to CSV
python main.py -i data.xlsx -o data.csv --to csv

# Markdown to HTML
python main.py -i readme.md -o readme.html --to html

# JSON to YAML
python main.py -i config.json -o config.yaml --to yaml
```

### Batch Conversion

```bash
# Convert all PDFs in folder to TXT
python main.py --batch ./Input --output ./Output --to txt

# Convert all images to PDF
python main.py --batch ./Photos --output ./Output --to pdf
```

---

## Adding Custom Conversions

To add support for new format conversions:

1. **Create Converter Class**:
   - Inherit from `BaseConverter`
   - Implement `convert()` method
   - Add to `src/converters/`

2. **Update Configuration**:
   - Add format mappings to `src/config/settings.py` → `CONVERSION_MATRIX`

3. **Update Routing**:
   - Add format detection in `src/main.py` → `get_converter()`

4. **Add Tests**:
   - Create test file in `tests/`
   - Test with real sample files

5. **Update Documentation**:
   - Add entry to this matrix
   - Document any limitations

---

## See Also

- [ARCHITECTURE.md](../development/ARCHITECTURE.md) - Technology choices
- [COMMON_ERRORS.md](../troubleshooting/COMMON_ERRORS.md) - Troubleshooting
- [README.md](../../README.md) - Usage guide
