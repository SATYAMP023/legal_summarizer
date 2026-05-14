<<<<<<< HEAD
# src/utils/pdf_loader.py

import pdfplumber
import io

def extract_text_from_pdf(uploaded_file) -> str:
    """
    Extract text from a PDF file uploaded via Streamlit.
    uploaded_file is a BytesIO-like Streamlit UploadedFile object.
    """
    text = ""
    try:
        with pdfplumber.open(io.BytesIO(uploaded_file.read())) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        raise RuntimeError(f"Failed to extract PDF text: {e}")

    return text.strip()
=======
import PyPDF2

def extract_text_from_pdf(file):

    reader = PyPDF2.PdfReader(file)
    text = ""

    for page in reader.pages:
        text += page.extract_text() + "\n"

    return text
>>>>>>> 273dcd41279759bf77f4e5d4c52464f035c48e21
