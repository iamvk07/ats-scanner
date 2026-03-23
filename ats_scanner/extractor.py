"""
Text extraction utilities.
Supports: .txt files, .pdf files (basic), raw text strings.
"""

import os
import re
import struct
import zlib


def extract_text(source: str) -> str:
    """
    Extract text from a file path or raw text string.
    Supports .txt and .pdf files, or plain text input.
    """
    if os.path.isfile(source):
        ext = os.path.splitext(source)[1].lower()
        if ext == ".pdf":
            return _extract_pdf(source)
        elif ext == ".txt":
            return _extract_txt(source)
        else:
            raise ValueError(f"Unsupported file type: {ext}. Use .txt or .pdf")
    else:
        # Treat as raw text
        return source.strip()


def _extract_txt(path: str) -> str:
    """Read plain text file."""
    encodings = ["utf-8", "utf-8-sig", "latin-1", "cp1252"]
    for enc in encodings:
        try:
            with open(path, "r", encoding=enc) as f:
                return f.read().strip()
        except (UnicodeDecodeError, LookupError):
            continue
    raise ValueError(f"Could not decode file: {path}")


def _extract_pdf(path: str) -> str:
    """
    Basic PDF text extraction without external libraries.
    Works on most text-based PDFs. For scanned PDFs, use a .txt copy instead.
    """
    try:
        with open(path, "rb") as f:
            data = f.read()

        text_parts = []

        # Extract text from BT...ET blocks
        bt_pattern = re.compile(rb"BT(.*?)ET", re.DOTALL)
        tj_pattern = re.compile(rb"\(([^)]*)\)\s*T[Jj]")
        tj_array = re.compile(rb"\[([^\]]*)\]\s*TJ")
        str_in_array = re.compile(rb"\(([^)]*)\)")

        for bt_match in bt_pattern.finditer(data):
            block = bt_match.group(1)

            # Direct string Tj
            for m in tj_pattern.finditer(block):
                try:
                    text_parts.append(m.group(1).decode("latin-1", errors="ignore"))
                except Exception:
                    pass

            # Array TJ
            for m in tj_array.finditer(block):
                for sm in str_in_array.finditer(m.group(1)):
                    try:
                        text_parts.append(sm.group(1).decode("latin-1", errors="ignore"))
                    except Exception:
                        pass

        raw = " ".join(text_parts)

        # Clean up PDF escape sequences
        raw = raw.replace("\\n", "\n").replace("\\r", "\n").replace("\\t", " ")
        raw = re.sub(r"\\([0-7]{3})", lambda m: chr(int(m.group(1), 8)), raw)
        raw = re.sub(r"\s+", " ", raw).strip()

        if len(raw) < 50:
            raise ValueError("PDF text extraction yielded too little text. Try saving as .txt first.")

        return raw

    except Exception as e:
        raise ValueError(
            f"Could not extract text from PDF: {e}\n"
            "Tip: Copy your resume text into a .txt file for best results."
        )


def clean_text(text: str) -> str:
    """Normalize text for analysis."""
    text = text.lower()
    text = re.sub(r"[^\w\s\+#\./]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()
