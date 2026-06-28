from pathlib import Path
import re

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "cv" / "Benjamin-F-Jarvis-CV.pdf"
CV_SOURCE = ROOT / "cv" / "cv.md"
BIB_SOURCE = ROOT / "publications.bib"


def paragraph(text, style):
    return Paragraph(text, style)


def clean_text(text):
    return decode_latex(
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("--", "-")
    )


def decode_latex(text):
    replacements = {
        r"\"a": "ä",
        r"\"A": "Ä",
        r"\"o": "ö",
        r"\"O": "Ö",
        r"\"u": "ü",
        r"\"U": "Ü",
        r"\"e": "ë",
        r"\"E": "Ë",
        r"\"i": "ï",
        r"\"I": "Ï",
        r"\'e": "é",
        r"\'E": "É",
        r"\`e": "è",
        r"\`E": "È",
        r"\aa": "å",
        r"\AA": "Å",
        r"\&": "&",
        r"\,": " ",
    }

    decoded = text
    for latex, plain in replacements.items():
        decoded = decoded.replace(latex, plain)
    decoded = re.sub(r"[{}]", "", decoded)
    decoded = re.sub(r"\\[a-zA-Z]+\s?", "", decoded)
    return decoded


def slugify(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower().replace("&", "and")).strip("-")


def parse_cv_markdown(path):
    sections = {}
    current = None
    current_entry = None

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("# "):
            continue

        if line.startswith("## "):
            current = slugify(line[3:])
            sections[current] = []
            current_entry = None
            continue

        if line.startswith("### ") and current:
            date, _, heading = line[4:].partition("|")
            current_entry = {
                "date": date.strip(),
                "heading": heading.strip(),
                "detail": [],
            }
            sections[current].append(current_entry)
            continue

        if current_entry:
            current_entry["detail"].append(line)

    return sections


def parse_bibtex(path):
    source = path.read_text(encoding="utf-8")
    entries = []
    index = 0

    while index < len(source):
        start = source.find("@", index)
        if start == -1:
            break

        open_brace = source.find("{", start)
        if open_brace == -1:
            break

        entry_type = source[start + 1 : open_brace].strip().lower()
        depth = 1
        close = open_brace + 1

        while close < len(source) and depth:
            if source[close] == "{":
                depth += 1
            elif source[close] == "}":
                depth -= 1
            close += 1

        body = source[open_brace + 1 : close - 1]
        _, _, field_text = body.partition(",")
        fields = parse_bib_fields(field_text)
        fields = {key: re.sub(r"\s+", " ", value) for key, value in fields.items()}
        entries.append({"type": entry_type, "fields": fields})
        index = close

    return sorted(entries, key=lambda entry: int(entry["fields"].get("year", 0)), reverse=True)


def parse_bib_fields(field_text):
    fields = {}
    cursor = 0

    while cursor < len(field_text):
        match = re.search(r"([A-Za-z][\w-]*)\s*=", field_text[cursor:])
        if not match:
            break

        key = match.group(1).lower()
        cursor += match.end()

        while cursor < len(field_text) and field_text[cursor].isspace():
            cursor += 1

        if cursor >= len(field_text):
            break

        delimiter = field_text[cursor]
        cursor += 1

        if delimiter == "{":
            depth = 1
            start = cursor
            while cursor < len(field_text) and depth:
                if field_text[cursor] == "{":
                    depth += 1
                elif field_text[cursor] == "}":
                    depth -= 1
                cursor += 1
            value = field_text[start : cursor - 1]
        elif delimiter == '"':
            start = cursor
            while cursor < len(field_text) and field_text[cursor] != '"':
                cursor += 1
            value = field_text[start:cursor]
            cursor += 1
        else:
            start = cursor - 1
            while cursor < len(field_text) and field_text[cursor] != ",":
                cursor += 1
            value = field_text[start:cursor]

        fields[key] = value.strip().strip(",")

        while cursor < len(field_text) and field_text[cursor] != ",":
            cursor += 1
        if cursor < len(field_text) and field_text[cursor] == ",":
            cursor += 1

    return fields


def author_text(author_field):
    authors = []
    for author in re.split(r"\s+and\s+", author_field or ""):
        parts = [part.strip() for part in author.split(",")]
        authors.append(f"{parts[1]} {parts[0]}" if len(parts) > 1 else author.strip())
    return ", ".join(filter(None, authors)) or "Author information forthcoming"


def is_invited_talk(entry):
    fields = entry["fields"]
    return "invited" in fields.get("annotation", "").lower() or "invited" in fields.get("type", "").lower()


def is_working_paper(entry):
    fields = entry["fields"]
    entry_type = entry["type"]
    zotero_type = fields.get("type", "").lower()
    return (
        entry_type in {"unpublished", "preprint"}
        or "working" in zotero_type
        or bool(fields.get("eprint") or fields.get("archiveprefix"))
    )


def is_conference_presentation(entry):
    fields = entry["fields"]
    zotero_type = fields.get("type", "").lower()
    return (
        entry["type"] in {"inproceedings", "proceedings"}
        or "conference" in zotero_type
        or (entry["type"] == "misc" and not is_invited_talk(entry) and not is_working_paper(entry))
    )


def publication_groups(path):
    entries = parse_bibtex(path)
    return [
        ("Journal Articles", [entry for entry in entries if entry["type"] == "article"]),
        ("Books and Book Chapters", [entry for entry in entries if entry["type"] in {"book", "inbook", "incollection"}]),
        ("Working Papers and Preprints", [entry for entry in entries if is_working_paper(entry)]),
        (
            "Conference Presentations",
            [entry for entry in entries if is_conference_presentation(entry) and not is_invited_talk(entry)],
        ),
        ("Invited Talks", [entry for entry in entries if is_invited_talk(entry)]),
        ("Theses", [entry for entry in entries if entry["type"] in {"phdthesis", "mastersthesis"}]),
    ]


def publication_entries(entries):
    publications = []
    for entry in entries:
        fields = entry["fields"]
        venue = (
            fields.get("journaltitle")
            or fields.get("journal")
            or fields.get("booktitle")
            or fields.get("publisher")
            or fields.get("note")
            or fields.get("address")
            or entry["type"]
        )
        details = [
            f"<i>{clean_text(venue)}</i>",
            clean_text(fields.get("volume", "")),
            f"({clean_text(fields['number'])})" if fields.get("number") else "",
            clean_text(fields.get("pages", "")),
            f"DOI: {clean_text(fields['doi'])}" if fields.get("doi") else "",
        ]
        publications.append(
            (
                fields.get("year", "Year"),
                f"{clean_text(author_text(fields.get('author', '')))}. {clean_text(fields.get('title', 'Untitled publication'))}.",
                ", ".join(part for part in details if part),
            )
        )
    return publications


def section(title, entries, styles):
    story = [paragraph(title, styles["Section"]), Spacer(1, 0.06 * inch)]
    for date, heading, detail in entries:
        table = Table(
            [
                [
                    paragraph(date, styles["Date"]),
                    [
                        paragraph(heading, styles["EntryHeading"]),
                        paragraph(detail, styles["Body"]),
                    ],
                ]
            ],
            colWidths=[1.1 * inch, 5.35 * inch],
        )
        table.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ]
            )
        )
        story.append(table)
    story.append(Spacer(1, 0.16 * inch))
    return story


def build():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    cv_sections = parse_cv_markdown(CV_SOURCE)

    doc = SimpleDocTemplate(
        str(OUTPUT),
        pagesize=letter,
        rightMargin=0.7 * inch,
        leftMargin=0.7 * inch,
        topMargin=0.62 * inch,
        bottomMargin=0.62 * inch,
        title="Benjamin F. Jarvis CV",
        author="Benjamin F. Jarvis",
    )

    base = getSampleStyleSheet()
    styles = {
        "Name": ParagraphStyle(
            "Name",
            parent=base["Title"],
            fontName="Times-Bold",
            fontSize=25,
            leading=28,
            textColor=colors.HexColor("#1d2224"),
            alignment=0,
            spaceAfter=4,
        ),
        "Contact": ParagraphStyle(
            "Contact",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=13,
            textColor=colors.HexColor("#475054"),
            spaceAfter=16,
        ),
        "Section": ParagraphStyle(
            "Section",
            parent=base["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=10.5,
            leading=13,
            textColor=colors.HexColor("#1d6f6e"),
            uppercase=True,
            spaceBefore=8,
            spaceAfter=4,
        ),
        "Date": ParagraphStyle(
            "Date",
            parent=base["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=8.5,
            leading=11,
            textColor=colors.HexColor("#9a4d39"),
        ),
        "EntryHeading": ParagraphStyle(
            "EntryHeading",
            parent=base["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=9.6,
            leading=12,
            textColor=colors.HexColor("#1d2224"),
            spaceAfter=2,
        ),
        "Body": ParagraphStyle(
            "Body",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=9.1,
            leading=12,
            textColor=colors.HexColor("#475054"),
        ),
    }

    story = [
        paragraph("Benjamin F. Jarvis", styles["Name"]),
        paragraph(
            "Academic CV | Quantitative social science, social stratification, segregation, and statistical analysis<br/>"
            "Email: benjamin.jarvis@liu.se | Website: bfjarvis.github.io | ORCID: 0000-0001-8127-4051",
            styles["Contact"],
        ),
    ]

    story.extend(
        section(
            "Appointments",
            [(entry["date"], entry["heading"], " ".join(entry["detail"])) for entry in cv_sections.get("appointments", [])],
            styles,
        )
    )
    story.extend(
        section(
            "Education",
            [(entry["date"], entry["heading"], " ".join(entry["detail"])) for entry in cv_sections.get("education", [])],
            styles,
        )
    )
    story.extend(
        []
    )
    for title, entries in publication_groups(BIB_SOURCE):
        if entries:
            story.extend(section(title, publication_entries(entries), styles))
    story.extend(
        section(
            "Grants",
            [(entry["date"], entry["heading"], " ".join(entry["detail"])) for entry in cv_sections.get("grants", [])],
            styles,
        )
    )
    story.extend(
        section(
            "Teaching",
            [(entry["date"], entry["heading"], " ".join(entry["detail"])) for entry in cv_sections.get("teaching", [])],
            styles,
        )
    )
    story.extend(
        section(
            "Service and Skills",
            [
                (entry["date"], entry["heading"], " ".join(entry["detail"]))
                for entry in cv_sections.get("service-and-skills", [])
            ],
            styles,
        )
    )

    doc.build(story)


if __name__ == "__main__":
    build()
