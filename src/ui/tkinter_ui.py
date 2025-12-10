"""
Native Tkinter GUI for Universal File Converter
Compatible with PyInstaller .exe bundling
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import sys
import threading
from pathlib import Path
from typing import Optional, List, Dict
from datetime import datetime

# Import application modules
from src.config import settings
from src.logging.event_monitor import EventMonitor
from src.utils.format_detector import detect_format, get_supported_conversions
from src.utils.file_utils import get_file_size_mb, get_output_path
from src.detection.ocr_detector import OCRDetector
from src.security.path_security import validate_path, PathSecurityError
from src.security.filename_security import sanitize_filename
from src.security.size_security import FileSizeValidator
from src.ui.themes import THEME_LIGHT, FONTS, ICONS, LOG_COLORS


# Import converter factory from main module to avoid duplication
from src.main import get_converter


class TkinterConverterApp:
    """Main Tkinter application class for Universal File Converter."""
    
    def __init__(self):
        """Initialize the Tkinter application."""
        self.root = tk.Tk()
        self.root.title(f"{settings.WINDOW_TITLE} v{settings.APP_VERSION}")
        self.root.geometry("1200x800")
        self.root.minsize(900, 600)
        
        # Initialize event monitor
        self.monitor = EventMonitor()
        self.monitor.log_event('ui_initialized', {'ui_type': 'tkinter'}, severity='INFO')
        
        # Application state
        self.current_file: Optional[Path] = None
        self.current_format: Optional[str] = None
        self.conversion_history: List[Dict] = []
        self.is_converting: bool = False
        self.pdf_images: List = []
        self.current_page: int = 0
        self.zoom_level: int = 100
        self.theme = THEME_LIGHT
        
        # Size validator
        self.size_validator = FileSizeValidator()
        
        # OCR detector
        self.ocr_detector = OCRDetector()
        
        # Setup UI
        self._set_icon()
        self._configure_styles()
        self._setup_menu()
        self._setup_toolbar()
        self._setup_main_content()
        self._setup_statusbar()
        
        # Bind events
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        
    def _set_icon(self):
        """Set application icon if available."""
        try:
            icon_path = os.path.join(settings.BASE_DIR, 'assets', 'icon.ico')
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
        except Exception:
            pass  # Ignore icon errors
    
    def _configure_styles(self):
        """Configure ttk styles."""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure button styles
        style.configure('TButton', padding=6, relief='flat', background=self.theme['accent'])
        style.map('TButton',
                  background=[('active', self.theme['accent_hover'])])
        
        # Primary button style
        style.configure('Primary.TButton',
                       background=self.theme['accent'],
                       foreground='white',
                       padding=8)
        
        # Configure frame styles
        style.configure('TFrame', background=self.theme['bg_primary'])
        style.configure('TLabelframe', background=self.theme['bg_primary'])
        style.configure('TLabelframe.Label', background=self.theme['bg_primary'])
        
    def _setup_menu(self):
        """Setup menu bar."""
        self.menubar = tk.Menu(self.root)
        self.root.config(menu=self.menubar)
        
        # File menu
        file_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open File...", command=self.open_file, accelerator="Ctrl+O")
        file_menu.add_command(label="Open Folder...", command=self.open_folder, accelerator="Ctrl+Shift+O")
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self._on_closing, accelerator="Alt+F4")
        
        # Convert menu
        convert_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Convert", menu=convert_menu)
        convert_menu.add_command(label="Convert", command=self.start_conversion, accelerator="F5")
        convert_menu.add_command(label="Batch Convert...", command=self.start_batch_conversion)
        convert_menu.add_separator()
        convert_menu.add_command(label="Clear Selection", command=self.clear_selection)
        
        # View menu
        view_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Export Logs (JSON)", command=lambda: self.export_logs('json'))
        view_menu.add_command(label="Export Logs (CSV)", command=lambda: self.export_logs('csv'))
        view_menu.add_separator()
        view_menu.add_command(label="Clear History", command=self.clear_history)
        
        # Help menu
        help_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="Documentation", command=self.show_documentation)
        help_menu.add_separator()
        help_menu.add_command(label="About", command=self.show_about)
        
        # Bind keyboard shortcuts
        self.root.bind('<Control-o>', lambda e: self.open_file())
        self.root.bind('<Control-O>', lambda e: self.open_folder())
        self.root.bind('<F5>', lambda e: self.start_conversion())
    
    def _setup_toolbar(self):
        """Setup toolbar."""
        self.toolbar = ttk.Frame(self.root, padding="5")
        self.toolbar.pack(side=tk.TOP, fill=tk.X)
        
        # Open file button
        self.btn_open_file = ttk.Button(
            self.toolbar,
            text=f"{ICONS['folder_open']} Open File",
            command=self.open_file
        )
        self.btn_open_file.pack(side=tk.LEFT, padx=2)
        
        # Open folder button
        self.btn_open_folder = ttk.Button(
            self.toolbar,
            text=f"{ICONS['folder']} Open Folder",
            command=self.open_folder
        )
        self.btn_open_folder.pack(side=tk.LEFT, padx=2)
        
        # Separator
        ttk.Separator(self.toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=5, fill=tk.Y)
        
        # Format selection
        ttk.Label(self.toolbar, text="Convert to:").pack(side=tk.LEFT, padx=5)
        self.format_var = tk.StringVar()
        self.format_combo = ttk.Combobox(
            self.toolbar,
            textvariable=self.format_var,
            state='readonly',
            width=15
        )
        self.format_combo.pack(side=tk.LEFT, padx=2)
        
        # Separator
        ttk.Separator(self.toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=5, fill=tk.Y)
        
        # Convert button
        self.btn_convert = ttk.Button(
            self.toolbar,
            text=f"{ICONS['rocket']} Convert",
            command=self.start_conversion,
            style='Primary.TButton'
        )
        self.btn_convert.pack(side=tk.LEFT, padx=2)
        
        # Clear button
        self.btn_clear = ttk.Button(
            self.toolbar,
            text=f"{ICONS['clear']} Clear",
            command=self.clear_selection
        )
        self.btn_clear.pack(side=tk.LEFT, padx=2)
    
    def _setup_main_content(self):
        """Setup main content area with paned window."""
        self.main_paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left panel
        self._setup_left_panel()
        
        # Right panel
        self._setup_right_panel()
        
        # Add panels to paned window
        self.main_paned.add(self.left_panel, weight=0)
        self.main_paned.add(self.right_panel, weight=1)
    
    def _setup_left_panel(self):
        """Setup left panel with file info and history."""
        self.left_panel = ttk.Frame(self.main_paned, width=350)
        
        # File Information Frame
        file_info_frame = ttk.LabelFrame(
            self.left_panel,
            text=f"{ICONS['file']} File Information",
            padding="10"
        )
        file_info_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.lbl_filename = ttk.Label(
            file_info_frame,
            text="No file selected",
            wraplength=320,
            font=FONTS['body']
        )
        self.lbl_filename.pack(anchor=tk.W, pady=2)
        
        self.lbl_format = ttk.Label(
            file_info_frame,
            text="Format: -",
            font=FONTS['small']
        )
        self.lbl_format.pack(anchor=tk.W, pady=2)
        
        self.lbl_size = ttk.Label(
            file_info_frame,
            text="Size: -",
            font=FONTS['small']
        )
        self.lbl_size.pack(anchor=tk.W, pady=2)
        
        self.lbl_pages = ttk.Label(
            file_info_frame,
            text="Pages: -",
            font=FONTS['small']
        )
        self.lbl_pages.pack(anchor=tk.W, pady=2)
        
        self.lbl_text_layer = ttk.Label(
            file_info_frame,
            text="Text Layer: -",
            font=FONTS['small']
        )
        self.lbl_text_layer.pack(anchor=tk.W, pady=2)
        
        # Conversion History Frame
        history_frame = ttk.LabelFrame(
            self.left_panel,
            text=f"{ICONS['history']} Conversion History",
            padding="10"
        )
        history_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create Treeview for history
        history_scroll = ttk.Scrollbar(history_frame)
        history_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.history_tree = ttk.Treeview(
            history_frame,
            columns=("Time", "Input", "Output", "Status"),
            show='headings',
            yscrollcommand=history_scroll.set,
            height=15
        )
        history_scroll.config(command=self.history_tree.yview)
        
        self.history_tree.heading("Time", text="Time")
        self.history_tree.heading("Input", text="Input")
        self.history_tree.heading("Output", text="Output")
        self.history_tree.heading("Status", text="Status")
        
        self.history_tree.column("Time", width=80, minwidth=60)
        self.history_tree.column("Input", width=100, minwidth=80)
        self.history_tree.column("Output", width=80, minwidth=60)
        self.history_tree.column("Status", width=60, minwidth=50)
        
        self.history_tree.pack(fill=tk.BOTH, expand=True)
    
    def _setup_right_panel(self):
        """Setup right panel with notebook tabs."""
        self.right_panel = ttk.Frame(self.main_paned)
        
        # Create notebook
        self.notebook = ttk.Notebook(self.right_panel)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Preview tab
        preview_frame = ttk.Frame(self.notebook)
        self.notebook.add(preview_frame, text=f"{ICONS['eye']} Preview")
        self._setup_preview_tab(preview_frame)
        
        # Logs tab
        logs_frame = ttk.Frame(self.notebook)
        self.notebook.add(logs_frame, text=f"{ICONS['log']} Event Logs")
        self._setup_logs_tab(logs_frame)
    
    def _setup_preview_tab(self, parent: ttk.Frame):
        """Setup preview tab with canvas and controls."""
        # Preview canvas
        canvas_frame = ttk.Frame(parent)
        canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbars
        h_scroll = ttk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL)
        h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        
        v_scroll = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL)
        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.preview_canvas = tk.Canvas(
            canvas_frame,
            bg=self.theme['canvas_bg'],
            xscrollcommand=h_scroll.set,
            yscrollcommand=v_scroll.set
        )
        self.preview_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        h_scroll.config(command=self.preview_canvas.xview)
        v_scroll.config(command=self.preview_canvas.yview)
        
        # Preview controls
        self.preview_controls = ttk.Frame(parent)
        self.preview_controls.pack(fill=tk.X, padx=5, pady=5)
        
        self.btn_prev_page = ttk.Button(
            self.preview_controls,
            text=f"{ICONS['prev']} Prev",
            command=self.prev_page,
            state='disabled'
        )
        self.btn_prev_page.pack(side=tk.LEFT, padx=2)
        
        self.page_label = ttk.Label(
            self.preview_controls,
            text="Page 0 of 0",
            font=FONTS['small']
        )
        self.page_label.pack(side=tk.LEFT, padx=10)
        
        self.btn_next_page = ttk.Button(
            self.preview_controls,
            text=f"Next {ICONS['next']}",
            command=self.next_page,
            state='disabled'
        )
        self.btn_next_page.pack(side=tk.LEFT, padx=2)
        
        ttk.Separator(self.preview_controls, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=10, fill=tk.Y)
        
        self.btn_zoom_out = ttk.Button(
            self.preview_controls,
            text=ICONS['zoom_out'],
            command=self.zoom_out,
            state='disabled'
        )
        self.btn_zoom_out.pack(side=tk.LEFT, padx=2)
        
        self.zoom_label = ttk.Label(
            self.preview_controls,
            text="100%",
            font=FONTS['small'],
            width=6
        )
        self.zoom_label.pack(side=tk.LEFT, padx=5)
        
        self.btn_zoom_in = ttk.Button(
            self.preview_controls,
            text=ICONS['zoom_in'],
            command=self.zoom_in,
            state='disabled'
        )
        self.btn_zoom_in.pack(side=tk.LEFT, padx=2)
        
        # Store reference to prevent garbage collection
        self.preview_photo = None
    
    def _setup_logs_tab(self, parent: ttk.Frame):
        """Setup logs tab with text widget."""
        # Log controls
        log_controls = ttk.Frame(parent)
        log_controls.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(
            log_controls,
            text=f"{ICONS['export']} Export JSON",
            command=lambda: self.export_logs('json')
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            log_controls,
            text=f"{ICONS['export']} Export CSV",
            command=lambda: self.export_logs('csv')
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            log_controls,
            text=f"{ICONS['clear']} Clear Logs",
            command=self.clear_log_display
        ).pack(side=tk.RIGHT, padx=2)
        
        # Log text widget
        log_frame = ttk.Frame(parent)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        log_scroll = ttk.Scrollbar(log_frame)
        log_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.log_text = tk.Text(
            log_frame,
            wrap=tk.WORD,
            font=FONTS['monospace'],
            bg=self.theme['log_bg'],
            fg=self.theme['log_fg'],
            yscrollcommand=log_scroll.set,
            state='disabled'
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
        log_scroll.config(command=self.log_text.yview)
        
        # Configure tags for severity colors
        for severity, color in LOG_COLORS.items():
            self.log_text.tag_configure(severity, foreground=color)
    
    def _setup_statusbar(self):
        """Setup status bar."""
        self.statusbar = ttk.Frame(self.root)
        self.statusbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.status_label = ttk.Label(
            self.statusbar,
            text="Ready",
            font=FONTS['small'],
            anchor=tk.W
        )
        self.status_label.pack(side=tk.LEFT, padx=10, pady=2)
        
        self.progress = ttk.Progressbar(
            self.statusbar,
            mode='indeterminate',
            length=200
        )
        # Hidden by default
        
        self.file_count_label = ttk.Label(
            self.statusbar,
            text="",
            font=FONTS['small'],
            anchor=tk.E
        )
        self.file_count_label.pack(side=tk.RIGHT, padx=10, pady=2)
    
    def open_file(self):
        """Open file dialog and load file."""
        file_path = filedialog.askopenfilename(
            title="Select File to Convert",
            initialdir=settings.INPUT_FOLDER,
            filetypes=[
                ("All Supported Files", "*.pdf *.docx *.doc *.xlsx *.xls *.csv *.txt *.md *.html *.json *.yaml *.xml *.png *.jpg *.jpeg *.tiff *.bmp *.gif *.webp"),
                ("PDF Files", "*.pdf"),
                ("Word Documents", "*.docx *.doc"),
                ("Excel Files", "*.xlsx *.xls"),
                ("Images", "*.png *.jpg *.jpeg *.tiff *.bmp *.gif *.webp"),
                ("All Files", "*.*")
            ]
        )
        
        if file_path:
            self._load_file(file_path)
    
    def open_folder(self):
        """Open folder dialog for batch conversion."""
        folder_path = filedialog.askdirectory(
            title="Select Folder for Batch Conversion",
            initialdir=settings.INPUT_FOLDER
        )
        
        if folder_path:
            self._load_folder(folder_path)
    
    def _load_file(self, file_path: str):
        """Load and validate a file."""
        try:
            # Security validation
            safe_path = validate_path(file_path, 'read_input')
            
            # Size validation
            if not self.size_validator.validate_file(safe_path):
                messagebox.showwarning(
                    "File Too Large",
                    f"Maximum file size is {settings.MAX_FILE_SIZE_MB} MB.\n"
                    f"Selected file exceeds this limit."
                )
                self.monitor.log_event('file_size_exceeded', {
                    'file': os.path.basename(file_path),
                    'limit_mb': settings.MAX_FILE_SIZE_MB
                }, severity='WARNING')
                return
            
            # Detect format
            file_format = detect_format(safe_path)
            if not file_format:
                messagebox.showerror(
                    "Unsupported Format",
                    "Could not detect file format or format is not supported."
                )
                self.monitor.log_event('format_detection_failed', {
                    'file': os.path.basename(file_path)
                }, severity='ERROR')
                return
            
            # Update state
            self.current_file = Path(safe_path)
            self.current_format = file_format
            
            # Update UI
            self._update_file_info()
            self._update_format_options()
            self._load_preview()
            self._update_status(f"Loaded: {self.current_file.name}")
            self._add_log_entry(f"File loaded: {self.current_file.name}", 'INFO')
            
            self.monitor.log_event('file_loaded', {
                'filename': self.current_file.name,
                'format': file_format,
                'size_mb': get_file_size_mb(safe_path)
            }, severity='INFO')
            
        except PathSecurityError as e:
            messagebox.showerror("Security Error", f"Invalid path: {e}")
            self.monitor.log_event('path_security_violation', {
                'path': file_path,
                'error': str(e)
            }, severity='CRITICAL')
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load file: {e}")
            self.monitor.log_event('file_load_error', {
                'path': file_path,
                'error': str(e)
            }, severity='ERROR')
    
    def _load_folder(self, folder_path: str):
        """Load folder for batch conversion."""
        try:
            # Security validation
            safe_path = validate_path(folder_path, 'read_input')
            
            # Count supported files
            from src.utils.file_utils import list_files_in_directory
            files = list_files_in_directory(safe_path, settings.SUPPORTED_INPUT_FORMATS)
            
            if not files:
                messagebox.showinfo(
                    "No Files Found",
                    "No supported files found in the selected folder."
                )
                return
            
            # Update status
            self.file_count_label.config(text=f"{len(files)} files")
            self._update_status(f"Folder loaded: {len(files)} files")
            self._add_log_entry(f"Folder loaded: {folder_path} ({len(files)} files)", 'INFO')
            
            self.monitor.log_event('folder_loaded', {
                'path': folder_path,
                'file_count': len(files)
            }, severity='INFO')
            
        except PathSecurityError as e:
            messagebox.showerror("Security Error", f"Invalid path: {e}")
            self.monitor.log_event('path_security_violation', {
                'path': folder_path,
                'error': str(e)
            }, severity='CRITICAL')
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load folder: {e}")
            self.monitor.log_event('folder_load_error', {
                'path': folder_path,
                'error': str(e)
            }, severity='ERROR')
    
    def _validate_file(self, file_path: str) -> bool:
        """Validate file with all security checks."""
        try:
            # Path security
            validate_path(file_path, 'read_input')
            
            # Size validation
            if not self.size_validator.validate_file(file_path):
                return False
            
            return True
        except Exception:
            return False
    
    def clear_selection(self):
        """Clear current file selection and reset UI."""
        self.current_file = None
        self.current_format = None
        self.pdf_images = []
        self.current_page = 0
        self.zoom_level = 100
        
        # Reset file info
        self.lbl_filename.config(text="No file selected")
        self.lbl_format.config(text="Format: -")
        self.lbl_size.config(text="Size: -")
        self.lbl_pages.config(text="Pages: -")
        self.lbl_text_layer.config(text="Text Layer: -")
        
        # Clear preview
        self.preview_canvas.delete("all")
        
        # Reset format combo
        self.format_combo.set('')
        self.format_combo['values'] = []
        
        # Reset controls
        self.btn_prev_page.config(state='disabled')
        self.btn_next_page.config(state='disabled')
        self.btn_zoom_in.config(state='disabled')
        self.btn_zoom_out.config(state='disabled')
        
        # Reset status
        self._update_status("Ready")
        self.file_count_label.config(text="")
        
        self._add_log_entry("Selection cleared", 'INFO')
    
    def _update_file_info(self):
        """Update file information display."""
        if not self.current_file:
            return
        
        try:
            # Filename
            self.lbl_filename.config(text=self.current_file.name)
            
            # Format
            self.lbl_format.config(text=f"Format: {self.current_format.upper()}")
            
            # Size
            size_mb = get_file_size_mb(str(self.current_file))
            self.lbl_size.config(text=f"Size: {size_mb:.2f} MB")
            
            # Pages and text layer (PDF only)
            if self.current_format == 'pdf':
                try:
                    import fitz
                    with fitz.open(str(self.current_file)) as doc:
                        page_count = len(doc)
                        self.lbl_pages.config(text=f"Pages: {page_count}")
                    
                    # Check text layer
                    has_text = self.ocr_detector.check_pdf_text_layer(str(self.current_file))
                    text_status = "Yes ✓" if has_text else "No (Scanned) ⚠️"
                    self.lbl_text_layer.config(text=f"Text Layer: {text_status}")
                    
                    if not has_text:
                        self._add_log_entry(
                            "Warning: PDF appears to be scanned/image-based. OCR recommended for text extraction.",
                            'WARNING'
                        )
                except Exception as e:
                    self.lbl_pages.config(text="Pages: Error")
                    self.lbl_text_layer.config(text="Text Layer: Error")
            else:
                self.lbl_pages.config(text="Pages: N/A")
                self.lbl_text_layer.config(text="Text Layer: N/A")
                
        except Exception as e:
            self.monitor.log_event('file_info_update_error', {
                'error': str(e)
            }, severity='ERROR')
    
    def _update_format_options(self):
        """Update format dropdown with supported output formats."""
        if not self.current_format:
            self.format_combo['values'] = []
            return
        
        # Get supported conversions
        output_formats = get_supported_conversions(self.current_format)
        self.format_combo['values'] = [fmt.upper() for fmt in output_formats]
        
        if output_formats:
            self.format_combo.current(0)
    
    def _update_status(self, message: str):
        """Update status bar message."""
        self.status_label.config(text=message)
        self.root.update_idletasks()
    
    def _add_log_entry(self, message: str, severity: str):
        """Add entry to log display."""
        timestamp = datetime.now().strftime('%H:%M:%S')
        log_line = f"[{timestamp}] [{severity}] {message}\n"
        
        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, log_line, severity)
        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')
    
    def _add_history_entry(self, input_file: str, output_file: str, status: str):
        """Add entry to conversion history."""
        timestamp = datetime.now().strftime('%H:%M')
        input_name = os.path.basename(input_file)
        output_name = os.path.basename(output_file) if output_file else "Error"
        
        self.history_tree.insert(
            '',
            0,
            values=(timestamp, input_name, output_name, status)
        )
        
        # Store in history list
        self.conversion_history.append({
            'timestamp': datetime.now().isoformat(),
            'input': input_file,
            'output': output_file,
            'status': status
        })
    
    def start_conversion(self):
        """Start single file conversion."""
        if not self.current_file:
            messagebox.showwarning("No File", "Please select a file first.")
            return
        
        if not self.format_var.get():
            messagebox.showwarning("No Format", "Please select an output format.")
            return
        
        if self.is_converting:
            messagebox.showinfo("Busy", "Conversion already in progress.")
            return
        
        output_format = self.format_var.get().lower()
        
        # Generate output path
        safe_filename = sanitize_filename(f"{self.current_file.stem}.{output_format}")
        output_path = os.path.join(settings.OUTPUT_FOLDER, safe_filename)
        
        # Start conversion in background thread
        self.is_converting = True
        self._update_status("Converting...")
        self.progress.pack(side=tk.LEFT, padx=10)
        self.progress.start(10)
        self._add_log_entry(f"Starting conversion: {self.current_file.name} -> {output_format.upper()}", 'INFO')
        
        thread = threading.Thread(
            target=self._run_conversion,
            args=(str(self.current_file), output_path, output_format),
            daemon=True
        )
        thread.start()
    
    def _run_conversion(self, input_path: str, output_path: str, output_format: str):
        """Run conversion in background thread."""
        try:
            # Get converter
            converter = get_converter(self.current_format)
            if not converter:
                self.root.after(0, lambda: self._on_conversion_complete(
                    False, f"No converter available for {self.current_format}"
                ))
                return
            
            # Run conversion
            self.monitor.log_event('conversion_started', {
                'input': os.path.basename(input_path),
                'output': os.path.basename(output_path),
                'format': output_format
            }, severity='INFO')
            
            success = converter.convert(input_path, output_path, output_format)
            
            if success:
                self.monitor.log_event('conversion_complete', {
                    'input': os.path.basename(input_path),
                    'output': os.path.basename(output_path)
                }, severity='INFO')
                
                self.root.after(0, lambda: self._on_conversion_complete(
                    True, output_path
                ))
            else:
                self.monitor.log_event('conversion_failed', {
                    'input': os.path.basename(input_path),
                    'output': os.path.basename(output_path)
                }, severity='ERROR')
                
                self.root.after(0, lambda: self._on_conversion_complete(
                    False, "Conversion failed"
                ))
                
        except Exception as e:
            self.monitor.log_event('conversion_error', {
                'error': str(e),
                'error_type': type(e).__name__
            }, severity='ERROR')
            
            self.root.after(0, lambda: self._on_conversion_complete(
                False, str(e)
            ))
    
    def _on_conversion_complete(self, success: bool, result: str):
        """Handle conversion completion (called on main thread)."""
        self.is_converting = False
        self.progress.stop()
        self.progress.pack_forget()
        
        if success:
            self._update_status(f"Conversion complete!")
            self._add_log_entry(f"Conversion successful: {os.path.basename(result)}", 'INFO')
            self._add_history_entry(
                str(self.current_file),
                result,
                f"{ICONS['success']} Success"
            )
            
            # Ask if user wants to open output folder
            response = messagebox.askyesno(
                "Conversion Complete",
                f"File converted successfully!\n\n{os.path.basename(result)}\n\nOpen output folder?"
            )
            
            if response:
                import subprocess
                import platform
                
                if platform.system() == 'Windows':
                    os.startfile(settings.OUTPUT_FOLDER)
                elif platform.system() == 'Darwin':  # macOS
                    subprocess.run(['open', settings.OUTPUT_FOLDER])
                else:  # Linux
                    subprocess.run(['xdg-open', settings.OUTPUT_FOLDER])
        else:
            self._update_status("Conversion failed")
            self._add_log_entry(f"Conversion failed: {result}", 'ERROR')
            self._add_history_entry(
                str(self.current_file),
                "",
                f"{ICONS['error']} Failed"
            )
            messagebox.showerror("Conversion Failed", f"Error: {result}")
    
    def start_batch_conversion(self):
        """Start batch folder conversion."""
        if not self.file_count_label.cget('text'):
            messagebox.showwarning("No Folder", "Please select a folder first using 'Open Folder'.")
            return
        
        if not self.format_var.get():
            messagebox.showwarning("No Format", "Please select an output format.")
            return
        
        # This is a simplified implementation
        messagebox.showinfo("Batch Conversion", "Batch conversion feature coming soon!")
    
    def _load_preview(self):
        """Load preview based on file type."""
        if not self.current_file:
            return
        
        try:
            if self.current_format == 'pdf':
                self._load_pdf_pages()
                self._render_pdf_preview()
            elif self.current_format in ['png', 'jpeg', 'jpg', 'tiff', 'tif', 'bmp', 'gif', 'webp']:
                self._render_image_preview()
            else:
                # Text-based preview
                self.preview_canvas.delete("all")
                self.preview_canvas.create_text(
                    400, 300,
                    text=f"Preview not available for {self.current_format.upper()} files",
                    font=FONTS['body'],
                    fill=self.theme['fg_secondary']
                )
        except Exception as e:
            self.preview_canvas.delete("all")
            self.preview_canvas.create_text(
                400, 300,
                text=f"Preview error: {e}",
                font=FONTS['body'],
                fill=self.theme['error']
            )
            self.monitor.log_event('preview_error', {
                'error': str(e)
            }, severity='ERROR')
    
    def _load_pdf_pages(self):
        """
        Load all PDF pages as images.
        
        Note: For very large PDFs (>50 pages), this loads all pages into memory
        which may cause performance issues. Future enhancement could implement
        lazy loading to only keep current page and adjacent pages in memory.
        """
        try:
            import fitz
            from PIL import Image
            
            self.pdf_images = []
            
            with fitz.open(str(self.current_file)) as doc:
                # For large PDFs, consider limiting preview or implementing lazy loading
                if len(doc) > 100:
                    self._add_log_entry(
                        f"Warning: Large PDF ({len(doc)} pages) may take time to load preview",
                        'WARNING'
                    )
                
                dpi = 100
                zoom = dpi / 72.0
                mat = fitz.Matrix(zoom, zoom)
                
                for page in doc:
                    pix = page.get_pixmap(matrix=mat)
                    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                    self.pdf_images.append(img)
            
            self.current_page = 0
            self.zoom_level = 100
            
            # Enable controls
            if len(self.pdf_images) > 1:
                self.btn_next_page.config(state='normal')
            self.btn_zoom_in.config(state='normal')
            self.btn_zoom_out.config(state='normal')
            
        except Exception as e:
            self.monitor.log_event('pdf_load_error', {
                'error': str(e)
            }, severity='ERROR')
            self.pdf_images = []
    
    def _render_pdf_preview(self):
        """Render current PDF page to preview canvas."""
        if not self.pdf_images:
            return
        
        try:
            from PIL import Image, ImageTk
            
            # Get current page image
            if self.current_page >= len(self.pdf_images):
                self.current_page = 0
            
            img = self.pdf_images[self.current_page]
            
            # Apply zoom
            zoom_factor = self.zoom_level / 100
            new_width = int(img.width * zoom_factor)
            new_height = int(img.height * zoom_factor)
            
            # Resize image
            resized = img.resize((new_width, new_height), Image.LANCZOS)
            
            # Convert to PhotoImage
            self.preview_photo = ImageTk.PhotoImage(resized)
            
            # Display on canvas
            self.preview_canvas.delete("all")
            
            # Center image on canvas
            canvas_width = self.preview_canvas.winfo_width()
            canvas_height = self.preview_canvas.winfo_height()
            x = max(0, (canvas_width - new_width) // 2)
            y = max(0, (canvas_height - new_height) // 2)
            
            self.preview_canvas.create_image(x, y, anchor=tk.NW, image=self.preview_photo)
            
            # Configure scroll region
            self.preview_canvas.config(scrollregion=(0, 0, new_width, new_height))
            
            # Update page label
            self.page_label.config(text=f"Page {self.current_page + 1} of {len(self.pdf_images)}")
            self.zoom_label.config(text=f"{self.zoom_level}%")
            
            # Update navigation buttons
            self.btn_prev_page.config(state='normal' if self.current_page > 0 else 'disabled')
            self.btn_next_page.config(state='normal' if self.current_page < len(self.pdf_images) - 1 else 'disabled')
            
        except Exception as e:
            self.preview_canvas.delete("all")
            self.preview_canvas.create_text(
                400, 300,
                text=f"Preview error: {e}",
                font=FONTS['body'],
                fill=self.theme['error']
            )
    
    def _render_image_preview(self):
        """Render image file to preview canvas."""
        try:
            from PIL import Image, ImageTk
            
            # Use context manager for proper resource cleanup
            with Image.open(str(self.current_file)) as img:
                # Scale to fit canvas
                canvas_width = self.preview_canvas.winfo_width()
                canvas_height = self.preview_canvas.winfo_height()
                
                # Calculate scale factor
                scale_w = canvas_width / img.width
                scale_h = canvas_height / img.height
                scale = min(scale_w, scale_h, 1.0)  # Don't upscale
                
                new_width = int(img.width * scale)
                new_height = int(img.height * scale)
                
                resized = img.resize((new_width, new_height), Image.LANCZOS)
                self.preview_photo = ImageTk.PhotoImage(resized)
            
            # Display on canvas (after image is closed)
            self.preview_canvas.delete("all")
            x = (canvas_width - new_width) // 2
            y = (canvas_height - new_height) // 2
            self.preview_canvas.create_image(x, y, anchor=tk.NW, image=self.preview_photo)
            
        except Exception as e:
            self.preview_canvas.delete("all")
            self.preview_canvas.create_text(
                400, 300,
                text=f"Image preview error: {e}",
                font=FONTS['body'],
                fill=self.theme['error']
            )
    
    def prev_page(self):
        """Go to previous page."""
        if self.current_page > 0:
            self.current_page -= 1
            self._render_pdf_preview()
    
    def next_page(self):
        """Go to next page."""
        if self.current_page < len(self.pdf_images) - 1:
            self.current_page += 1
            self._render_pdf_preview()
    
    def zoom_in(self):
        """Zoom in preview."""
        if self.zoom_level < 200:
            self.zoom_level += 25
            if self.pdf_images:
                self._render_pdf_preview()
    
    def zoom_out(self):
        """Zoom out preview."""
        if self.zoom_level > 50:
            self.zoom_level -= 25
            if self.pdf_images:
                self._render_pdf_preview()
    
    def export_logs(self, format: str):
        """Export logs to file."""
        try:
            export_path = self.monitor.export_log(format=format)
            messagebox.showinfo(
                "Export Complete",
                f"Logs exported successfully!\n\n{export_path}"
            )
            self._add_log_entry(f"Logs exported: {format.upper()}", 'INFO')
        except Exception as e:
            messagebox.showerror("Export Failed", f"Failed to export logs: {e}")
            self._add_log_entry(f"Log export failed: {e}", 'ERROR')
    
    def clear_history(self):
        """Clear conversion history."""
        if messagebox.askyesno("Clear History", "Clear all conversion history?"):
            self.conversion_history.clear()
            for item in self.history_tree.get_children():
                self.history_tree.delete(item)
            self._add_log_entry("Conversion history cleared", 'INFO')
    
    def clear_log_display(self):
        """Clear log display."""
        if messagebox.askyesno("Clear Logs", "Clear log display?"):
            self.log_text.config(state='normal')
            self.log_text.delete('1.0', tk.END)
            self.log_text.config(state='disabled')
    
    def show_about(self):
        """Show about dialog."""
        about_text = f"""Universal File Converter
Version {settings.APP_VERSION}
Build Date: {settings.APP_BUILD_DATE}

AI-Powered Document Converter with OCR Detection
and Black Box Event Logging

Native Tkinter GUI for PyInstaller Compatibility

© 2025 JulHel-dev"""
        
        messagebox.showinfo("About", about_text)
    
    def show_documentation(self):
        """Show documentation."""
        docs_path = os.path.join(settings.BASE_DIR, 'docs')
        if os.path.exists(docs_path):
            messagebox.showinfo(
                "Documentation",
                f"Documentation folder:\n{docs_path}"
            )
        else:
            messagebox.showinfo(
                "Documentation",
                "Documentation not found.\nPlease visit the GitHub repository."
            )
    
    def _on_closing(self):
        """Handle window close event."""
        if self.is_converting:
            if not messagebox.askyesno(
                "Conversion in Progress",
                "A conversion is in progress. Are you sure you want to exit?"
            ):
                return
        
        self.monitor.log_event('ui_closing', {'ui_type': 'tkinter'}, severity='INFO')
        self.root.destroy()
    
    def run(self):
        """Start the application main loop."""
        self._add_log_entry("Tkinter UI initialized", 'INFO')
        self._add_log_entry(f"Version {settings.APP_VERSION}", 'INFO')
        self.root.mainloop()


def main():
    """Entry point for Tkinter UI."""
    app = TkinterConverterApp()
    app.run()


if __name__ == '__main__':
    main()
