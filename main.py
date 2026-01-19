#!/usr/bin/env python3
"""
PDF Rasterizer - Main entry point
"""

from app import RasterizerApp


def main():
    """Launch the PDF Rasterizer application"""
    app = RasterizerApp()
    app.mainloop()


if __name__ == "__main__":
    main()
