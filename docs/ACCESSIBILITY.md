# Accessibility (a11y) Guidelines for PDF-Converter UI

## WCAG 2.1 Compliance

This document outlines accessibility features implemented in the PDF-Converter application to ensure WCAG 2.1 Level AA compliance.

### Implemented Features

#### 1. Keyboard Navigation
- All interactive elements accessible via keyboard
- Tab order follows logical reading flow
- Focus indicators visible on all interactive elements
- Escape key closes modals/dialogs

#### 2. Screen Reader Support
- ARIA labels on all form controls
- Alt text for all images and icons
- Semantic HTML structure
- Status messages announced to screen readers

#### 3. Color Contrast
- Text meets WCAG AA minimum contrast ratio (4.5:1 for normal text)
- Interactive elements meet contrast requirements (3:1)
- Color not used as sole means of conveying information

#### 4. Text and Font
- Minimum font size: 12pt
- Resizable text up to 200% without loss of functionality
- Clear, readable fonts used throughout

#### 5. Error Handling
- Clear error messages
- Errors associated with form fields
- Suggestions for fixing errors provided

### Streamlit-Specific Accessibility

```python
# Example accessible form
import streamlit as st

st.title("File Converter")  # Semantic heading

# File upload with clear label
uploaded_file = st.file_uploader(
    "Choose a file to convert",
    help="Supported formats: PDF, DOCX, XLSX, PNG, JPEG"
)

# Output format selection with accessible label
output_format = st.selectbox(
    "Select output format",
    options=["pdf", "docx", "txt"],
    help="Choose the format for conversion"
)

# Clear button labels
if st.button("Convert File", help="Click to start conversion"):
    # Accessible status messages
    st.info("Converting file...")
    # ... conversion logic ...
    st.success("Conversion complete!")
```

### Testing Checklist

- [ ] Test with keyboard only (no mouse)
- [ ] Test with screen reader (NVDA, JAWS, or VoiceOver)
- [ ] Test color contrast with tools like axe DevTools
- [ ] Test text resizing to 200%
- [ ] Verify focus indicators visible
- [ ] Test error messages are clear

### Future Enhancements

- Add skip navigation links
- Implement live regions for dynamic content
- Add high contrast theme option
- Support for reduced motion preferences
