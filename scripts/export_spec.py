import json
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.units import inch

JSON_INPUT = "generated_spec_doc.json"
TXT_OUTPUT = "generated_spec_doc.txt"
PDF_OUTPUT = "generated_spec_doc.pdf"


def spec_to_string(spec):
    """
    Convert hierarchical spec dictionary into formatted text.
    """
    lines = []
    for section, subsections in spec.items():
        lines.append(f"\n=== {section.upper()} ===\n")
        if isinstance(subsections, dict):
            for sub, content in subsections.items():
                lines.append(f"\n-- {sub} --\n")
                if isinstance(content, dict):
                    for key, val in content.items():
                        lines.append(f"{key}: {val}")
                else:
                    lines.append(str(content))
        else:
            lines.append(str(subsections))
        lines.append("\n")
    return "\n".join(lines)


def create_pdf_from_spec(text, output_file):
    """
    Create a readable PDF version of the specification.
    """
    doc = SimpleDocTemplate(output_file, pagesize=letter,
                            rightMargin=72, leftMargin=72,
                            topMargin=72, bottomMargin=72)
    styles = getSampleStyleSheet()
    style_normal = styles["Normal"]
    style_heading = ParagraphStyle(
        "Heading",
        parent=styles["Heading1"],
        spaceAfter=12,
        fontSize=14,
        leading=16,
        alignment=1
    )

    story = []
    story.append(Paragraph("Generated Specification Document", style_heading))
    story.append(Spacer(1, 0.2 * inch))

    sections = text.split("=== ")
    for section in sections:
        section = section.strip()
        if not section:
            continue
        if " ===" in section:
            section_title, content = section.split(" ===", 1)
            story.append(Paragraph(f"<b>{section_title}</b>", styles["Heading2"]))
            story.append(Spacer(1, 0.1 * inch))
            story.append(Paragraph(content.replace("\n", "<br/>"), style_normal))
        else:
            story.append(Paragraph(section.replace("\n", "<br/>"), style_normal))
        story.append(Spacer(1, 0.2 * inch))

    doc.build(story)
    print(f"📘 PDF specification generated: {output_file}")


if __name__ == "__main__":
    # --- Load JSON ---
    try:
        with open(JSON_INPUT, "r", encoding="utf-8") as f:
            spec_doc = json.load(f)
    except Exception as e:
        print(f"⚠️ Could not read JSON file: {e}")
        exit(1)

    # --- Generate string ---
    spec_doc_str = spec_to_string(spec_doc)
    with open(TXT_OUTPUT, "w", encoding="utf-8") as f:
        f.write(spec_doc_str)
    print(f"📝 Spec string saved to {TXT_OUTPUT}")

    # --- Generate PDF ---
    create_pdf_from_spec(spec_doc_str, PDF_OUTPUT)

    print("\n✅ All outputs generated successfully:")
    print(f"   - JSON: {JSON_INPUT}")
    print(f"   - TXT:  {TXT_OUTPUT}")
    print(f"   - PDF:  {PDF_OUTPUT}")
