import fitz
import re
from langchain_text_splitters import MarkdownHeaderTextSplitter

PDF_PATH = "./PDF/Harrison_CH_1_12.pdf"

def extract_pdf_blocks(pdf_path):
    doc = fitz.open(pdf_path)
    blocks = []

    for page in doc:
        page_blocks = page.get_text("blocks")
        for b in page_blocks:
            x0, y0, x1, y1, text, block_no, block_type = b
            if block_type == 0 and text.strip():  # text blocks only
                blocks.append(text.strip())

    doc.close()
    return blocks

def blocks_to_markdown(blocks):
    md_lines = []

    for block in blocks:
        lines = block.splitlines()
        first_line = lines[0].strip()

        # Heuristic heading detection
        if first_line.isupper() and len(first_line) < 80:
            md_lines.append(f"## {first_line}")
            md_lines.extend(lines[1:])
        elif first_line[:1].isdigit() and "." in first_line[:5]:
            md_lines.append(f"### {first_line}")
            md_lines.extend(lines[1:])
        else:
            md_lines.extend(lines)

        md_lines.append("")  # paragraph break

    return "\n".join(md_lines)

def split_markdown_by_structure(markdown_text):
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

def main(pdf):
    blocks = extract_pdf_blocks(pdf)
    markdown_text = blocks_to_markdown(blocks)
    documents = split_markdown_by_structure(markdown_text)

    chunked_output = [
        {
            "chunk_id": f"BLK_{i:05d}",
            "text": doc.page_content,
            "metadata": doc.metadata
        }
        for i, doc in enumerate(documents)
    ]

    print(f"Total markdown chunks: {len(chunked_output)}")

    return chunked_output

if __name__ == "__main__":
    paragraphs = main(PDF_PATH)

    chp_output_file = "Sample_Test_LC_Paragraph_DB_PyMuPDF.txt"

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
            f.write("\n")