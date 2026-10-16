from io import BytesIO
import pandas as pd
from docx import Document
from pypdf import PdfReader


def extract_text(uploaded_file):
    filename = uploaded_file.name.lower()
    content = uploaded_file.getvalue()

    if not content:
        raise ValueError("The uploaded file is empty.")

    if filename.endswith(".pdf"):
        reader = PdfReader(BytesIO(content))
        text = "\n".join(
            page.extract_text() or ""
            for page in reader.pages
        )

    elif filename.endswith(".docx"):
        document = Document(BytesIO(content))
        text = "\n".join(
            paragraph.text
            for paragraph in document.paragraphs
        )

    elif filename.endswith(".csv"):
        dataframe = pd.read_csv(BytesIO(content))
        text = dataframe.to_string(index=False)

    elif filename.endswith(".txt"):
        text = content.decode("utf-8-sig")

    else:
        raise ValueError("Unsupported file format.")

    if not text.strip():
        raise ValueError(
            "No readable text found. The PDF may be scanned."
        )

    return text