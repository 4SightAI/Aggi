import pdfplumber
from langchain_text_splitters import MarkdownHeaderTextSplitter
from pdfminer.pdfinterp import PDFPageInterpreter
import re

PDF_PATH = "./PDF/Harrison_CH_1_12.pdf"

#Start - For invalid color operator warning supression
def _safe_color_op(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError:
            return None
    return wrapper

for op in ("do_rg", "do_g", "do_k", "do_sc", "do_scn"):
    if hasattr(PDFPageInterpreter, op):
        setattr(
            PDFPageInterpreter,
            op,
            _safe_color_op(getattr(PDFPageInterpreter, op))
        )
#End - For invalid color operator warning supression

def extract_pdf_text(pdf_path):
    pages = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text(use_text_flow=True)
            if text:
                pages.append(text)
    return "\n\n".join(pages)

def text_to_markdown(text):
    md_lines = []
    for line in text.splitlines():
        line = line.strip()

        # Heading heuristic (ALL CAPS or numbered sections)
        if line.isupper() and len(line) < 80:
            md_lines.append(f"## {line}")
        elif line[:2].isdigit() and "." in line[:5]:
            md_lines.append(f"### {line}")
        else:
            md_lines.append(line)

    return "\n".join(md_lines)

def markdown_structure_split(markdown_text):
    headers_to_split_on = [
        ("#", "H1"),
        ("##", "H2"),
        ("###", "H3"),
        ("####", "H4"),
    ]

    splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=headers_to_split_on
    )

    return splitter.split_text(markdown_text)

def clean_text(text: str) -> str:
    text = text.replace("\n", " ")
    text = re.sub(r"\s+", " ", text)
    text = text.replace("- ", "")  # fix hyphen line breaks
    return text.strip()

def main(pdf):
    raw_text = extract_pdf_text(PDF_PATH)
    #cleaned = clean_text(raw_text)
    markdown_text = text_to_markdown(raw_text)
    documents = markdown_structure_split(markdown_text)

    chunked_output = [
        {
            "chunk_id": f"MD_{i:05d}",
            "text": doc.page_content,
            "metadata": doc.metadata
        }
        for i, doc in enumerate(documents)
    ]

    print(f"Total markdown chunks: {len(chunked_output)}")

    return chunked_output

if __name__ == "__main__":
    paragraphs = main(PDF_PATH)

    chp_output_file = "Sample_Test_LC_Paragraph_DB.txt"

    with open(chp_output_file, "w", encoding="utf-8") as f:
        for i in paragraphs:
            f.write("{")
            f.write("\n")
            f.write("   'chunk_id': '" + str(i["chunk_id"]) + "', ")
            f.write("\n")
            f.write("   'text': " + str(i["text"]) + ", ")
            f.write("\n")
            f.write("   'metadata': " + str(i["metadata"]) + ", ")
            f.write("\n")
            f.write("},")