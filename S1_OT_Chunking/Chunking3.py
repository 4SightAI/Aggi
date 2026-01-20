import fitz
import re
from collections import Counter
import json

PDF_PATH = "./PDF/Harrison_CH_1_12-1.pdf"
MIN_PARAGRAPH_CHARS = 150  # after cleaning
MIN_BODY_FONT_COUNT = 50   # for estimating body font size per doc

def clean_text(text: str) -> str:
    text = text.replace("\n", " ")
    text = re.sub(r"\s+", " ", text)
    text = text.replace("- ", "")
    return text.strip()

def is_all_caps(text: str) -> bool:
    t = re.sub(r"[^A-Za-z]", "", text)
    return t.isupper() and len(t) > 0

def estimate_body_font(doc):
    font_sizes = []
    for page in doc:
        d = page.get_text("dict")
        for b in d["blocks"]:
            for l in b.get("lines", []):
                for s in l.get("spans", []):
                    size = round(s["size"])
                    font_sizes.append(size)
        if len(font_sizes) > 1000:  # early stop
            break
    if not font_sizes:
        return 10  # fallback
    counter = Counter(font_sizes)
    body_size, _ = counter.most_common(1)[0]
    return body_size

def detect_heading_type(text, max_font, body_font):
    text_stripped = text.strip()
    if len(text_stripped) < 3:
        return None

    # Chapter / Topic-like (big + all caps)
    if is_all_caps(text_stripped) and max_font >= body_font + 2:
        # You can refine here: if it matches r"CHAPTER \d+" mark as 'chapter'
        if re.match(r"^CHAPTER\s+\d+", text_stripped):
            return "chapter"
        return "topic"

    # Subtopic: bigger than body, not all caps, title-ish
    if max_font >= body_font + 1 and not is_all_caps(text_stripped):
        # crude: assume it's a subtopic if line is short
        if len(text_stripped) < 80:
            return "subtopic"

    return None

def extract_structured_paragraphs(pdf_path, book_id="HARRISON_CH_1_12"):
    doc = fitz.open(pdf_path)
    body_font = estimate_body_font(doc)

    paragraphs = []
    para_buffer = []
    para_id = 1

    current_chapter_idx = 0
    current_topic_idx = 0
    current_subtopic_idx = 0
    current_chapter_title = None
    current_topic_title = None
    current_subtopic_title = None

    def flush_paragraph(page_number):
        nonlocal para_buffer, para_id
        if not para_buffer:
            return
        text = clean_text(" ".join(para_buffer))
        para_buffer = []
        if len(text) < MIN_PARAGRAPH_CHARS:
            return
        paragraphs.append({
            "book_id": book_id,
            "paragraph_id": para_id,
            "page": page_number,
            "chapter_index": current_chapter_idx,
            "chapter_title": current_chapter_title,
            "topic_index": current_topic_idx,
            "topic_title": current_topic_title,
            "subtopic_index": current_subtopic_idx,
            "subtopic_title": current_subtopic_title,
            "text": text
        })
        para_id += 1

    for page_number, page in enumerate(doc, start=1):
        d = page.get_text("dict")
        # 'blocks' are already roughly in reading order
        for b in d["blocks"]:
            if "lines" not in b:
                continue
            line_texts = []
            max_font = 0.0
            for l in b["lines"]:
                span_texts = []
                for s in l["spans"]:
                    t = s["text"]
                    if not t.strip():
                        continue
                    span_texts.append(t)
                    max_font = max(max_font, s["size"])
                if span_texts:
                    line_texts.append(" ".join(span_texts))
            if not line_texts:
                # treat as potential paragraph break
                flush_paragraph(page_number)
                continue

            block_text = clean_text(" ".join(line_texts))

            # Decide if heading
            htype = detect_heading_type(block_text, max_font, body_font)

            if htype == "chapter":
                flush_paragraph(page_number)
                current_chapter_idx += 1
                current_topic_idx = 0
                current_subtopic_idx = 0
                current_chapter_title = block_text
                current_topic_title = None
                current_subtopic_title = None
                continue

            if htype == "topic":
                flush_paragraph(page_number)
                current_topic_idx += 1
                current_subtopic_idx = 0
                # if it's also the first big heading after a chapter line,
                # you might want to detect chapter title separately
                current_topic_title = block_text
                current_subtopic_title = None
                continue

            if htype == "subtopic":
                flush_paragraph(page_number)
                current_subtopic_idx += 1
                current_subtopic_title = block_text
                continue

            # Otherwise, treat as body text; accumulate in buffer
            para_buffer.append(block_text)

        # End of page: flush any open paragraph
        flush_paragraph(page_number)

    return paragraphs

def main():
    paragraphs = extract_structured_paragraphs(PDF_PATH)
    print(f"Extracted {len(paragraphs)} structured paragraphs")
    print(paragraphs)

    with open("Sample_Test_Chunk3.txt", "w", encoding="utf-8") as f:
        json.dump(paragraphs, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
