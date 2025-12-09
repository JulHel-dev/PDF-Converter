# Common Errors and Troubleshooting

Quick reference for resolving common issues with the Universal File Converter.

---

## Installation Issues

### Error: "No module named 'fitz'"

**Problem**: PyMuPDF not installed

**Solution**:
```bash
pip install PyMuPDF
```

---

### Error: "No module named 'PIL'"

**Problem**: Pillow not installed

**Solution**:
```bash
pip install Pillow
```

---

### Error: "python-magic not working on Windows"

**Problem**: libmagic binary not found

**Solution**:
```bash
pip install python-magic-bin
```

---

## Conversion Errors

### Error: "No text layer detected" (PDF)

**Problem**: PDF is scanned/image-based

**Solutions**:
1. **Use OCR tool first**:
   - Adobe Acrobat Pro (Action Wizard → Recognize Text)
   - Foxit PDF Compressor
   - Online OCR: [ocr.space](https://ocr.space/), [onlineocr.net](https://onlineocr.net/)

2. **Convert to images first**, then use OCR tool:
   ```bash
   python main.py -i scanned.pdf -o output_folder/ --to png
   # Run OCR on images
   # Convert back to PDF with text layer
   ```

3. **Accept limited conversion**:
   - PDF → image formats still work
   - Text extraction will be empty/incomplete

---

### Error: "Unsupported conversion"

**Problem**: Requested conversion not in matrix

**Check**: See [CONVERSION_MATRIX.md](../implementation/CONVERSION_MATRIX.md)

**Examples of unsupported conversions**:
- PDF → Excel (no standard)
- Image → Text (requires OCR)
- Audio/Video conversions

---

### Error: "File too large"

**Problem**: File exceeds 100MB limit

**Solutions**:
1. **Increase limit** in `src/config/settings.py`:
   ```python
   MAX_FILE_SIZE_MB = 500  # Increase as needed
   ```

2. **Split large files**:
   - For PDFs: Use PDF splitter tools
   - For images: Process in batches

3. **Use streaming mode** (for developers):
   - Implement chunked processing
   - Reduce memory usage

---

### Error: "Permission denied"

**Problem**: Cannot write to output folder

**Solutions**:
1. **Check folder permissions**:
   ```bash
   # Windows: Right-click folder → Properties → Security
   # Linux/Mac: chmod 755 Output/
   ```

2. **Use different output location**:
   ```bash
   python main.py -i input.pdf -o C:/Users/YourName/Desktop/output.txt --to txt
   ```

3. **Run as administrator** (Windows):
   - Right-click executable → "Run as administrator"

---

## Format-Specific Issues

### PDF Issues

#### Problem: Garbled text extraction

**Causes**:
- Font embedding issues
- Non-standard encoding
- Corrupted PDF

**Solutions**:
1. **Re-save PDF** with Adobe Acrobat or similar
2. **Try different extraction**:
   - PDF → HTML (sometimes better)
   - PDF → Image → OCR
3. **Check PDF repair tools**:
   - [iLovePDF Repair](https://www.ilovepdf.com/repair-pdf)
   - Adobe Acrobat repair

---

#### Problem: Missing images in conversion

**Cause**: Images not embedded properly

**Solutions**:
1. **Extract images separately**:
   ```bash
   python main.py -i document.pdf -o images/ --to png
   ```

2. **Use format that preserves images**:
   - PDF → HTML (embeds images)
   - PDF → DOCX (tries to preserve)

---

### DOCX Issues

#### Problem: "Cannot open DOC files"

**Cause**: Legacy DOC format not supported

**Solutions**:
1. **Convert DOC → DOCX first**:
   - Microsoft Word: Open → Save As → DOCX
   - LibreOffice: Open → Save As → DOCX
   - Online: [cloudconvert.com](https://cloudconvert.com/)

2. **Install compatibility library**:
   ```bash
   pip install doc2docx
   ```

---

#### Problem: Lost formatting in DOCX conversion

**Cause**: Complex styles/layouts

**Solutions**:
1. **Use simpler target format**:
   - DOCX → TXT (preserves content only)
   - DOCX → MD (preserves basic structure)

2. **Manual cleanup** after conversion

---

### Image Issues

#### Problem: "Image too dark/light after conversion"

**Cause**: Color space conversion

**Solutions**:
1. **Preserve original format**:
   - PNG → PNG, JPEG → JPEG

2. **Adjust in image editor** first

3. **Use lossless formats**:
   - PNG, TIFF for quality

---

#### Problem: Transparency lost in JPEG

**Cause**: JPEG doesn't support transparency

**Solutions**:
1. **Use PNG instead**:
   ```bash
   python main.py -i image.png -o image.png --to png
   ```

2. **Accept white background**:
   - Converter automatically fills with white

---

### Data Format Issues

#### Problem: "CSV doesn't match expected format"

**Cause**: JSON/XML structure doesn't fit tabular

**Solutions**:
1. **Check source data structure**:
   - Needs to be array of objects for CSV
   - Nested structures flattened to JSON strings

2. **Use JSON/YAML for complex data**:
   - Better for hierarchical data

---

## Build/Packaging Issues

### Error: "PyInstaller build failed"

**Problem**: Missing dependencies or hooks

**Solutions**:
1. **Update PyInstaller**:
   ```bash
   pip install --upgrade pyinstaller
   ```

2. **Check spec file**:
   - Verify `hiddenimports` list
   - Add missing modules

3. **Manual import test**:
   ```python
   python -c "import fitz; import PIL; import docx"
   ```

---

### Error: ".exe won't run on clean machine"

**Problem**: Missing system dependencies

**Solutions**:
1. **Install Visual C++ Redistributable**:
   - Download from Microsoft
   - Required for many Python packages

2. **Test on clean VM**:
   - VirtualBox or Hyper-V
   - Fresh Windows install

3. **Check error logs**:
   - Run exe from command line to see errors
   ```bash
   PDF-Converter.exe --help
   ```

---

### Error: "Streamlit won't launch in .exe"

**Problem**: Browser not opening

**Solutions**:
1. **Run with explicit GUI flag**:
   ```bash
   PDF-Converter.exe --gui
   ```

2. **Check firewall settings**:
   - Allow Streamlit port (default 8501)

3. **Use CLI mode instead**:
   ```bash
   PDF-Converter.exe -i file.pdf -o file.txt --to txt
   ```

---

## Performance Issues

### Problem: Conversions very slow

**Causes**:
- Large files
- Complex formatting
- System resources

**Solutions**:
1. **Check event logs for slow operations**:
   - Look for operations > 2s
   - Export logs: GUI → "Export Logs"

2. **Reduce file complexity**:
   - Compress images first
   - Simplify formatting

3. **Batch processing**:
   - Use batch mode for multiple files
   - More efficient than multiple single conversions

---

### Problem: High memory usage

**Cause**: Large files loaded into memory

**Solutions**:
1. **Close other applications**

2. **Process files individually**:
   ```bash
   # Instead of batch
   for file in *.pdf; do
     python main.py -i "$file" -o "${file%.pdf}.txt" --to txt
   done
   ```

3. **Upgrade RAM** for consistent large file processing

---

## Logging/Debugging Issues

### Problem: "Cannot find log files"

**Location**: `Log/diagnostics/` folder

**Solutions**:
1. **Check folder exists**:
   - Should auto-create on startup
   - Verify `Log/` is writable

2. **Export from GUI**:
   - Sidebar → "Export Logs (JSON/CSV)"

3. **View recent events**:
   - GUI sidebar shows last 5 events

---

### Problem: "Log files too large"

**Solution**:
1. **Clean old logs**:
   - Delete files in `Log/diagnostics/`
   - Retention set to 7 days by default

2. **Adjust retention**:
   - Edit `src/config/monitor_config.py`:
   ```python
   LOG_RETENTION_DAYS = 3  # Reduce to 3 days
   ```

---

## Getting Help

### Before Reporting Issues

1. ✅ **Check event logs**:
   - Export logs (JSON) for full details
   - Look for ERROR severity events

2. ✅ **Test with sample file**:
   - Rule out file-specific issues
   - Try different format

3. ✅ **Check this guide**:
   - Most common issues covered

4. ✅ **Verify installation**:
   ```bash
   pip list | grep -E "(PyMuPDF|Pillow|docx|openpyxl)"
   ```

---

### Reporting Bugs

Include:
- ✅ **Error message** (exact text)
- ✅ **Command used** or GUI steps
- ✅ **File format** (input and output)
- ✅ **Event log export** (if possible)
- ✅ **System info** (Windows version, Python version)

**GitHub Issues**: [github.com/JulHel-dev/PDF-Converter/issues](https://github.com/JulHel-dev/PDF-Converter/issues)

---

## See Also

- [CONVERSION_MATRIX.md](../implementation/CONVERSION_MATRIX.md) - Supported conversions
- [ARCHITECTURE.md](../development/ARCHITECTURE.md) - System design
- [README.md](../../README.md) - Usage guide
