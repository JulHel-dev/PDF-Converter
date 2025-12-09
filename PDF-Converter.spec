# -*- mode: python ; coding: utf-8 -*-

"""
PyInstaller spec file for PDF-Converter
Builds standalone Windows executable with all dependencies bundled
"""
import os

block_cipher = None

a = Analysis(
    ['src/main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('src/config', 'src/config'),
        ('docs', 'docs'),
        ('assets', 'assets'),
    ],
    hiddenimports=[
        # PDF processing
        'fitz',
        'fitz.fitz',
        'fitz.utils',
        
        # Image processing
        'PIL',
        'PIL.Image',
        'PIL.ImageFile',
        'PIL.ImageDraw',
        'PIL.ImageFont',
        'PIL.ExifTags',
        
        # Document processing
        'openpyxl',
        'openpyxl.styles',
        'docx',
        'docx.shared',
        
        # Data formats
        'markdown',
        'markdown.extensions',
        'markdown.extensions.extra',
        'markdown.extensions.codehilite',
        'markdown.extensions.tables',
        'yaml',
        
        # UI
        'streamlit',
        'streamlit.web.cli',
        
        # Utilities
        'magic',
        
        # Standard library imports that might be missed
        'xml.etree.ElementTree',
        'csv',
        'json',
        'tempfile',
        'pathlib',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'pytest',
        'unittest',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='PDF-Converter',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Set to True for CLI mode (shows console window)
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.ico' if os.path.exists('assets/icon.ico') else None,
)
