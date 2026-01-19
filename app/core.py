import os
import subprocess
import tempfile
from PIL import Image

try:
    from PyPDF2 import PdfReader
except ImportError:
    PdfReader = None


class PDFRasterizer:
    """Core PDF rasterization logic"""
    
    @staticmethod
    def get_page_count(pdf):
        """Get the number of pages in a PDF file"""
        try:
            if PdfReader:
                reader = PdfReader(pdf)
                return len(reader.pages)
            else:
                # Fallback to gswin64c if PyPDF2 not available
                result = subprocess.check_output(
                    ["gswin64c", "-q", "-dNODISPLAY", "-c",
                     f"({pdf}) (r) file runpdfbegin pdfpagecount = quit"],
                    stderr=subprocess.DEVNULL,
                    text=True
                )
                return int(result.strip().split()[-1])
        except Exception:
            return "?"

    @staticmethod
    def rasterize_pdf(pdf, output_dir, dpi):
        """
        Rasterize a PDF file to a rasterized PDF
        
        Args:
            pdf (str): Path to input PDF
            output_dir (str): Output directory
            dpi (int): DPI for rasterization
            
        Returns:
            str: Path to output file
        """
        base = os.path.splitext(os.path.basename(pdf))[0]
        out_pdf = os.path.join(output_dir, base + "_RASTERIZED.pdf")

        with tempfile.TemporaryDirectory() as tmp:
            pattern = os.path.join(tmp, "page_%04d.png")

            cmd = [
                "gswin64c",
                "-dSAFER",
                "-dBATCH",
                "-dNOPAUSE",
                "-sDEVICE=png16m",
                f"-r{dpi}",
                f"-sOutputFile={pattern}",
                pdf
            ]

            subprocess.run(cmd, check=True)

            images = []
            for f in sorted(os.listdir(tmp)):
                img = Image.open(os.path.join(tmp, f)).convert("RGB")
                images.append(img)

            images[0].save(out_pdf, save_all=True, append_images=images[1:])
            
        return out_pdf
