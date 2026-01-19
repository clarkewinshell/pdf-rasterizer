import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from .core import PDFRasterizer

APP_TITLE = "Redacted PDF Rasterizer v1.0"
DEFAULT_DPI = 300

# Color scheme
BG_COLOR = "#f0f0f0"
TEXT_COLOR = "#000000"
BUTTON_BG = "#e1e1e1"
BUTTON_BORDER = "#b0b0b0"
TABLE_BG = "#ffffff"
CONSOLE_BG = "#ffffff"
CONSOLE_TEXT = "#000000"


class RasterizerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("600x500")
        self.resizable(False, False)
        self.configure(bg=BG_COLOR)
        
        # Theme
        self._setup_theme()

        self.pdfs = []
        self.output_dir = tk.StringVar()
        self.strip_metadata = tk.BooleanVar()
        self.dpi = tk.IntVar(value=DEFAULT_DPI)
        
        # Set icon path relative to app package
        icon_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 
            "assets/icon.ico"
        )
        self.iconbitmap(icon_path)

        self._build_ui()

    # ---------------- UI Setup ----------------

    def _setup_theme(self):
        style = ttk.Style()
        style.theme_use('winnative')
        
        # Color configurations
        style.configure("TFrame", background=BG_COLOR)
        style.configure("TLabel", background=BG_COLOR, foreground=TEXT_COLOR)
        style.configure("TCheckbutton", background=BG_COLOR, foreground=TEXT_COLOR)
        style.configure("TSpinbox", fieldbackground=TABLE_BG, foreground=TEXT_COLOR)
        style.configure("TEntry", fieldbackground=TABLE_BG, foreground=TEXT_COLOR)
        style.configure("Treeview", background=TABLE_BG, foreground=TEXT_COLOR, 
                       fieldbackground=TABLE_BG)
        style.configure("Treeview.Heading", background=BUTTON_BG, foreground=TEXT_COLOR)
        style.map("Treeview", background=[('selected', "#0078d7")], 
                 foreground=[('selected', "#ffffff")])

    # ---------------- UI ----------------

    def _build_ui(self):
        self._build_toolbar()
        self._build_table()
        self._build_controls()
        self._build_console()

    def _build_toolbar(self):
        """Build simple toolbar with buttons"""
        bar = tk.Frame(self, bg=BG_COLOR)
        bar.pack(fill="x", padx=10, pady=8)

        ttk.Button(bar, text="Select PDF(s)", command=self.add_pdfs).pack(side="left", padx=3)
        ttk.Button(bar, text="Add", command=self.add_pdfs).pack(side="right", padx=3)
        ttk.Button(bar, text="Remove", command=self.remove_selected).pack(side="right", padx=3)
        ttk.Button(bar, text="Clear", command=self.clear_list).pack(side="right", padx=3)

    def _build_table(self):
        frame = ttk.Frame(self)
        frame.pack(fill="both", expand=True, padx=10, pady=5)

        cols = ("#", "Title", "Pages", "Size", "Path")
        self.tree = ttk.Treeview(frame, columns=cols, show="headings", height=8)

        self.tree.heading("#", text="#")
        self.tree.heading("Title", text="Title")
        self.tree.heading("Pages", text="Pages")
        self.tree.heading("Size", text="Size")
        self.tree.heading("Path", text="Path")

        self.tree.column("#", width=35, anchor="center")
        self.tree.column("Title", width=300, anchor="w")
        self.tree.column("Pages", width=60, anchor="center")
        self.tree.column("Size", width=70, anchor="center")
        self.tree.column("Path", width=400, anchor="w")

        # Scroll
        vsb = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscroll=vsb.set, xscroll=hsb.set)
        
        # Grid layout for tree and scrollbars
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)
        
        # Open PDF on double-click
        self.tree.bind("<Double-1>", self.open_pdf_on_double_click)

    def _build_controls(self):
        frame = ttk.Frame(self)
        frame.pack(fill="x", padx=10, pady=8)

        # First row: metadata checkbox and DPI
        row1 = ttk.Frame(frame)
        row1.pack(fill="x", pady=5)
        
        ttk.Checkbutton(
            row1,
            text="Strip metadata",
            variable=self.strip_metadata
        ).pack(side="left", padx=5)

        ttk.Label(row1, text="DPI").pack(side="left", padx=(15, 5))
        ttk.Spinbox(
            row1,
            from_=72,
            to=1200,
            width=6,
            textvariable=self.dpi
        ).pack(side="left")

        # Second row: output folder selection and rasterize button
        row2 = ttk.Frame(frame)
        row2.pack(fill="x", pady=5)
        
        ttk.Label(row2, text="Output:").pack(side="left", padx=5)
        ttk.Entry(
            row2,
            textvariable=self.output_dir,
            width=45
        ).pack(side="left", padx=5, fill="x", expand=True)

        ttk.Button(
            row2,
            text="Output folder",
            command=self.select_output
        ).pack(side="left", padx=5)

        ttk.Button(
            row2,
            text="Rasterize",
            command=self.start_rasterize
        ).pack(side="left", padx=5)


    def _build_console(self):
        frame = ttk.Frame(self)
        frame.pack(fill="both", padx=10, pady=10)

        self.console = tk.Text(
            frame,
            height=7,
            bg=CONSOLE_BG,
            fg="#00aa00",
            insertbackground="#000000",
            relief="sunken",
            bd=1,
            font=("Courier New", 9),
            state="disabled"
        )
        self.console.pack(fill="both", expand=True)

    # ---------------- Logic ----------------

    def log(self, msg):
        self.console.config(state="normal")
        self.console.insert("end", f"Console$ : {msg}\n")
        self.console.see("end")
        self.console.config(state="disabled")

    def add_pdfs(self):
        files = filedialog.askopenfilenames(
            filetypes=[("PDF files", "*.pdf")]
        )
        for f in files:
            if f not in self.pdfs:
                self.pdfs.append(f)
        self.refresh_table()

    def remove_selected(self):
        for sel in self.tree.selection():
            index = int(self.tree.item(sel)["values"][0]) - 1
            self.pdfs.pop(index)
        self.refresh_table()

    def clear_list(self):
        self.pdfs.clear()
        self.refresh_table()

    def select_output(self):
        d = filedialog.askdirectory()
        if d:
            self.output_dir.set(d)

    def refresh_table(self):
        self.tree.delete(*self.tree.get_children())
        for i, pdf in enumerate(self.pdfs, 1):
            size = os.path.getsize(pdf) // 1024
            pages = PDFRasterizer.get_page_count(pdf)
            self.tree.insert("", "end", values=(
                i,
                os.path.basename(pdf),
                pages,
                f"{size} KB",
                pdf
            ))

    def open_pdf_on_double_click(self, event):
        """Open PDF file when double-clicked"""
        import subprocess
        selection = self.tree.selection()
        if selection:
            item = selection[0]
            pdf_path = self.tree.item(item)["values"][4]  # Get path
            try:
                if os.name == 'nt':  # Windows
                    os.startfile(pdf_path)
                else:  # macOS and Linux
                    subprocess.Popen(['open', pdf_path])
                self.log(f"Opened: {os.path.basename(pdf_path)}")
            except Exception as e:
                self.log(f"Error opening PDF: {str(e)}")

    def start_rasterize(self):
        if not self.pdfs or not self.output_dir.get():
            messagebox.showerror("Error", "Missing input files or output folder.")
            return

        threading.Thread(target=self.rasterize_all, daemon=True).start()

    def rasterize_all(self):
        for pdf in self.pdfs:
            self.log(f"Rasterizing: {os.path.basename(pdf)}")
            try:
                PDFRasterizer.rasterize_pdf(pdf, self.output_dir.get(), self.dpi.get())
                self.log("  -> Done")
            except Exception as e:
                self.log(f"  -> ERROR: {e}")

        self.log("Job(s) completed.")
