import sys
import os
from typing import List
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Preformatted
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.lib import colors


def build_styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="TitleZiran", fontName="Helvetica-Bold", fontSize=18, leading=22, spaceAfter=12, textColor=colors.HexColor('#2D3748')))
    styles.add(ParagraphStyle(name="H1Ziran", parent=styles["Heading1"], fontSize=16, leading=20, spaceBefore=12, spaceAfter=8, textColor=colors.HexColor('#2D3748')))
    styles.add(ParagraphStyle(name="H2Ziran", parent=styles["Heading2"], fontSize=14, leading=18, spaceBefore=10, spaceAfter=6, textColor=colors.HexColor('#4A5568')))
    styles.add(ParagraphStyle(name="H3Ziran", parent=styles["Heading3"], fontSize=12, leading=16, spaceBefore=8, spaceAfter=6, textColor=colors.HexColor('#4A5568')))
    styles.add(ParagraphStyle(name="BodyZiran", parent=styles["BodyText"], fontSize=10, leading=14, alignment=TA_LEFT, spaceAfter=6))
    styles.add(ParagraphStyle(name="BulletZiran", parent=styles["BodyText"], fontSize=10, leading=14, leftIndent=14, bulletIndent=8, spaceAfter=4))
    styles.add(ParagraphStyle(name="CodeZiran", fontName="Courier", fontSize=9, leading=12, backColor=colors.whitesmoke, leftIndent=6, rightIndent=6, spaceBefore=4, spaceAfter=6, borderPadding=(4,4,4,4)))
    return styles


def parse_markdown_to_story(md_lines: List[str]):
    styles = build_styles()
    story = []

    # Title (first non-empty line starting with # ) used as cover title
    title_added = False
    in_code = False
    code_buffer: List[str] = []
    para_buffer: List[str] = []

    def flush_paragraph():
        nonlocal para_buffer
        if para_buffer:
            text = " ".join([line.strip() for line in para_buffer if line.strip()])
            if text:
                story.append(Paragraph(text, styles["BodyZiran"]))
            para_buffer = []

    def flush_code():
        nonlocal code_buffer
        if code_buffer:
            code_text = "\n".join(code_buffer)
            story.append(Preformatted(code_text, styles["CodeZiran"]))
            code_buffer = []

    for raw in md_lines:
        line = raw.rstrip("\n")

        # Code fences
        if line.strip().startswith("```"):
            if in_code:
                # closing fence
                flush_code()
                in_code = False
            else:
                # opening fence
                flush_paragraph()
                in_code = True
            continue

        if in_code:
            code_buffer.append(line)
            continue

        # Headings
        if line.startswith("# "):
            flush_paragraph()
            if not title_added:
                story.append(Paragraph(line[2:].strip(), styles["TitleZiran"]))
                story.append(Spacer(1, 12))
                title_added = True
            else:
                story.append(Paragraph(line[2:].strip(), styles["H1Ziran"]))
            continue
        if line.startswith("## "):
            flush_paragraph()
            story.append(Paragraph(line[3:].strip(), styles["H2Ziran"]))
            continue
        if line.startswith("### "):
            flush_paragraph()
            story.append(Paragraph(line[4:].strip(), styles["H3Ziran"]))
            continue

        # Bullets (simple)
        stripped = line.lstrip()
        if stripped.startswith("- ") or stripped.startswith("* "):
            flush_paragraph()
            text = stripped[2:].strip()
            story.append(Paragraph(f"• {text}", styles["BulletZiran"]))
            continue

        # Blank line => flush current paragraph
        if not line.strip():
            flush_paragraph()
            continue

        # Accumulate normal paragraph
        para_buffer.append(line)

    # Flush any remaining
    flush_paragraph()
    flush_code()

    return story


def convert_md_to_pdf(input_md: str, output_pdf: str):
    if not os.path.isfile(input_md):
        raise FileNotFoundError(f"Markdown file not found: {input_md}")

    with open(input_md, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    story = parse_markdown_to_story(lines)

    doc = SimpleDocTemplate(
        output_pdf,
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
        title=os.path.splitext(os.path.basename(output_pdf))[0],
        author="Sistema de Gestão de Compras"
    )
    doc.build(story)


if __name__ == "__main__":
    # Usage: python scripts/generate_pdf_from_md.py <input_md> [output_pdf]
    if len(sys.argv) < 2:
        print("Usage: python scripts/generate_pdf_from_md.py <input_md> [output_pdf]")
        sys.exit(1)

    input_md = sys.argv[1]
    if len(sys.argv) >= 3:
        output_pdf = sys.argv[2]
    else:
        base, _ = os.path.splitext(input_md)
        output_pdf = base + ".pdf"

    # Ensure output directory exists
    out_dir = os.path.dirname(os.path.abspath(output_pdf))
    if out_dir and not os.path.isdir(out_dir):
        os.makedirs(out_dir, exist_ok=True)

    convert_md_to_pdf(input_md, output_pdf)
    print(f"PDF gerado em: {output_pdf}")
