"""
Text extraction utilities.
Supports: .txt files, .pdf files (basic), .tex files (LaTeX), .docx files (Word), raw text strings.
"""

import os
import re
import struct
import zipfile
import zlib
from xml.etree import ElementTree


def extract_text(source: str) -> str:
    """
    Extract text from a file path or raw text string.
    Supports .txt, .pdf, .tex, and .docx files, or plain text input.
    """
    if os.path.isfile(source):
        ext = os.path.splitext(source)[1].lower()
        if ext == ".pdf":
            return _extract_pdf(source)
        elif ext == ".txt":
            return _extract_txt(source)
        elif ext == ".tex":
            return _extract_tex(source)
        elif ext == ".docx":
            return _extract_docx(source)
        else:
            raise ValueError(
                f"Unsupported file type: {ext}. Use .txt, .pdf, .tex, or .docx"
            )
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
                        text_parts.append(
                            sm.group(1).decode("latin-1", errors="ignore")
                        )
                    except Exception:
                        pass

        raw = " ".join(text_parts)

        # Clean up PDF escape sequences
        raw = raw.replace("\\n", "\n").replace("\\r", "\n").replace("\\t", " ")
        raw = re.sub(r"\\([0-7]{3})", lambda m: chr(int(m.group(1), 8)), raw)
        raw = re.sub(r"\s+", " ", raw).strip()

        if len(raw) < 50:
            raise ValueError(
                "PDF text extraction yielded too little text. Try saving as .txt first."
            )

        return raw

    except Exception as e:
        raise ValueError(
            f"Could not extract text from PDF: {e}\n"
            "Tip: Copy your resume text into a .txt file for best results."
        )


def _extract_tex(path: str) -> str:
    raw = _extract_txt(path)
    return strip_latex(raw)


def strip_latex(text: str) -> str:
    # Remove comments (% to end of line, but not escaped \%)
    text = re.sub(r"(?<!\\)%.*", "", text)

    # Remove \begin{...} and \end{...}
    text = re.sub(r"\\(?:begin|end)\{[^}]*\}", "", text)

    # Remove preamble commands and their arguments
    text = re.sub(
        r"\\(?:documentclass|usepackage|input|include|bibliography|bibliographystyle)"
        r"(?:\[[^\]]*\])?\{[^}]*\}",
        "",
        text,
    )

    # Convert \item to newline (before generic command removal)
    text = re.sub(r"\\item\s*", "\n", text)

    # Multi-pass: peel nested formatting commands layer by layer
    _fmt_re = re.compile(
        r"\\(?:textbf|textit|emph|underline|texttt|textrm|textsf|textsc"
        r"|section|subsection|subsubsection|paragraph|subparagraph"
        r"|title|author|date)\*?\{([^}]*)\}"
    )
    for _ in range(3):
        text, n = _fmt_re.subn(r"\1", text)
        if n == 0:
            break

    # Handle \href{url}{text} -> text
    text = re.sub(r"\\href\{[^}]*\}\{([^}]*)\}", r"\1", text)

    # Strip moderncv / resume-class command names but KEEP their {arg} content.
    # e.g. \cvitem{Key}{Value} -> {Key}{Value} (braces cleaned later)
    #      \cventry{yr}{title}{co}{loc}{grade}{details} -> keeps all args
    #      \name{First}{Last} -> {First}{Last}
    text = re.sub(
        r"\\(?:cvitem|cventry|cvlistitem|cvdoubleitem|cvcolumn"
        r"|cvskill|cvitemwithcomment"
        r"|name|address|email|phone|social|extrainfo)"
        r"(?:\[[^\]]*\])?",
        " ",
        text,
    )

    # Remove remaining \command with optional [] and {} args
    text = re.sub(r"\\[a-zA-Z]+\*?(?:\[[^\]]*\])?(?:\{[^}]*\})*", "", text)

    # Replace escaped special characters with space
    text = re.sub(r"\\[\\&%$#_{}~^]", " ", text)

    # Clean up leftover braces, multiple spaces, blank lines
    text = re.sub(r"[{}]", " ", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n", text)

    return text.strip()


def _extract_docx(path: str) -> str:
    """
    Extract text from a .docx file without external libraries.
    .docx is a ZIP archive; text content is in word/document.xml.
    """
    try:
        with zipfile.ZipFile(path, "r") as z:
            if "word/document.xml" not in z.namelist():
                raise ValueError("Invalid .docx file: word/document.xml not found")
            xml_content = z.read("word/document.xml")

        tree = ElementTree.fromstring(xml_content)

        # Word XML namespace
        W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"

        paragraphs = []
        for para in tree.iter(f"{{{W_NS}}}p"):
            texts = []
            for node in para.iter(f"{{{W_NS}}}t"):
                if node.text:
                    texts.append(node.text)
            if texts:
                paragraphs.append("".join(texts))

        result = "\n".join(paragraphs).strip()

        if len(result) < 10:
            raise ValueError(
                "DOCX text extraction yielded too little text. "
                "Try saving as .txt first."
            )

        return result

    except zipfile.BadZipFile:
        raise ValueError(
            f"Could not read .docx file: {path}\n"
            "The file may be corrupted. Try re-saving from Word or use .txt."
        )
    except ValueError:
        raise
    except Exception as e:
        raise ValueError(
            f"Could not extract text from DOCX: {e}\n"
            "Tip: Copy your resume text into a .txt file for best results."
        )


def clean_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^\w\s\+#\./]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()
