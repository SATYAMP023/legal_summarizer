<<<<<<< HEAD
import PyPDF2
from transformers import AutoTokenizer
from tkinter import Tk
from tkinter.filedialog import askopenfilename


def extract_text_from_pdf(pdf_path):
    text = ""
    with open(pdf_path, "rb") as file:
        reader = PyPDF2.PdfReader(file)
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + " "
    return text


def count_tokens_with_tokenizer(text, model_name="allenai/led-base-16384"):
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    tokens = tokenizer.encode(text)
    return len(tokens)


if __name__ == "__main__":
    # Hide main Tkinter window
    Tk().withdraw()

    # Open file dialog to select PDF
    pdf_path = askopenfilename(
        title="Select Legal Document PDF",
        filetypes=[("PDF Files", "*.pdf")]
    )

    if not pdf_path:
        print("No file selected!")
        exit()

    print("Extracting text from PDF...")
    document_text = extract_text_from_pdf(pdf_path)

    print("Counting tokens using LED tokenizer...")
    token_count = count_tokens_with_tokenizer(document_text)

    print(f"\nTotal Tokens (Model-based): {token_count}")
=======
import PyPDF2
from transformers import AutoTokenizer
from tkinter import Tk
from tkinter.filedialog import askopenfilename


def extract_text_from_pdf(pdf_path):
    text = ""
    with open(pdf_path, "rb") as file:
        reader = PyPDF2.PdfReader(file)
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + " "
    return text


def count_tokens_with_tokenizer(text, model_name="allenai/led-base-16384"):
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    tokens = tokenizer.encode(text)
    return len(tokens)


if __name__ == "__main__":
    # Hide main Tkinter window
    Tk().withdraw()

    # Open file dialog to select PDF
    pdf_path = askopenfilename(
        title="Select Legal Document PDF",
        filetypes=[("PDF Files", "*.pdf")]
    )

    if not pdf_path:
        print("No file selected!")
        exit()

    print("Extracting text from PDF...")
    document_text = extract_text_from_pdf(pdf_path)

    print("Counting tokens using LED tokenizer...")
    token_count = count_tokens_with_tokenizer(document_text)

    print(f"\nTotal Tokens (Model-based): {token_count}")
>>>>>>> 273dcd41279759bf77f4e5d4c52464f035c48e21
