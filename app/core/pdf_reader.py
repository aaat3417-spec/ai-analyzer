import fitz  # PyMuPDF


def read_pdf(file_bytes: bytes) -> str:
    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        text = ""

        for page in doc:
            text += page.get_text()

        return text

    except Exception as e:
        return ""
