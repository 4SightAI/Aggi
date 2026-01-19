import pdfplumber
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pdfminer.pdfinterp import PDFPageInterpreter
import re

PDF_PATH = "./PDF/Harrison_CH_1_12.pdf"
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150

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
    pages_text = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text(use_text_flow=True)
            #print(" --------------- ")
            #print(text)
            #print(" --------------- ")
            if text:
                pages_text.append(text)
    return "\n\n".join(pages_text)

def recursive_chunk_text(text):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=[
            "\n\n",   # paragraphs
            "\n",     # lines
            ". ",     # sentences
            " ",      # words
            ""        # characters (fallback)
        ]
    )
    return splitter.split_text(text)

def clean_text(text: str) -> str:
    text = text.replace("\n", " ")
    text = re.sub(r"\s+", " ", text)
    text = text.replace("- ", "")  # fix hyphen line breaks
    return text.strip()

def main(pdf):
    raw_text = extract_pdf_text(pdf)
    #cleaned = clean_text(raw_text)
    chunks = recursive_chunk_text(raw_text)

    chunked_output = [
        {
            "chunk_id": f"CH_{i:05d}",
            "text": chunk,
            "char_count": len(chunk)
        }
        for i, chunk in enumerate(chunks)
    ]

    print(f"Total chunks: {len(chunked_output)}")

    return chunked_output

if __name__ == "__main__":
    paragraphs = main(PDF_PATH)

    chp_output_file = "Sample_Test_LC_Paragraph_TB.txt"

    with open(chp_output_file, "w", encoding="utf-8") as f:
        for i in paragraphs:
            f.write("{")
            f.write("\n")
            f.write("   'chunk_id': '" + str(i["chunk_id"]) + "', ")
            f.write("\n")
            f.write("   'char_count': " + str(i["char_count"]) + ", ")
            f.write("\n")
            f.write("   'text': " + str(i["text"]) + ", ")
            f.write("\n")
            f.write("},")