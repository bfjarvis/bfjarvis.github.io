from pathlib import Path
import json
import re

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "cv" / "Benjamin-F-Jarvis-CV.pdf"
CV_SOURCE = ROOT / "cv" / "cv.md"
PUBLICATIONS_SOURCE = ROOT / "data" / "publications.json"
SUPERVISION_SOURCE = ROOT / "data" / "supervision.json"


def paragraph(text, style):
    return Paragraph(text, style)


def format_cv_date(text):
    return "<br/>".join(clean_text(part.strip()) for part in text.split(";") if part.strip())


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


def normalize_cv_section_slug(slug):
    aliases = {
        "service-skills-etc": "service-and-skills",
    }
    return aliases.get(slug, slug)


def parse_cv_markdown(path):
    sections = {}
    current = None
    current_entry = None

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("# "):
            continue

        if line.startswith("## "):
            current = normalize_cv_section_slug(slugify(line[3:]))
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

    return sorted(entries, key=sort_date_value, reverse=True)


def csl_date_value(date):
    parts = (date or {}).get("date-parts", [[]])[0]
    return "-".join(str(part) for part in parts if part)


def normalize_csl_item(item):
    issued = csl_date_value(item.get("issued"))
    fields = {
        "title": item.get("title", ""),
        "author": item.get("author", []),
        "editor": item.get("editor", []),
        "date": issued,
        "year": issued[:4],
        "journaltitle": item.get("container-title", ""),
        "journal": item.get("container-title", ""),
        "booktitle": item.get("container-title", ""),
        "eventtitle": item.get("event-title", ""),
        "location": item.get("event-place") or item.get("publisher-place", ""),
        "publisher": item.get("publisher", ""),
        "school": item.get("publisher", ""),
        "volume": item.get("volume", ""),
        "number": item.get("issue") or item.get("number", ""),
        "pages": item.get("page", ""),
        "doi": item.get("DOI", ""),
        "url": item.get("URL", ""),
        "abstract": item.get("abstract", ""),
        "note": item.get("note", ""),
        "annotation": item.get("note", ""),
        "type": item.get("genre") or item.get("type", ""),
        "source": item.get("source", ""),
    }
    return {"type": item.get("type", ""), "fields": fields}


def parse_reference_data(path):
    if path.suffix.lower() == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        items = data if isinstance(data, list) else data.get("items", [])
        return sorted((normalize_csl_item(item) for item in items), key=sort_date_value, reverse=True)

    return parse_bibtex(path)


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
    if isinstance(author_field, list):
        authors = []
        for author in author_field:
            if author.get("literal"):
                authors.append(author["literal"])
            else:
                authors.append(" ".join(part for part in [author.get("given"), author.get("family")] if part))
        return ", ".join(filter(None, authors)) or "Author information forthcoming"

    authors = []
    for author in re.split(r"\s+and\s+", author_field or ""):
        parts = [part.strip() for part in author.split(",")]
        authors.append(f"{parts[1]} {parts[0]}" if len(parts) > 1 else author.strip())
    return ", ".join(filter(None, authors)) or "Author information forthcoming"


def asa_author_text(author_field):
    def join_names(names):
        names = [name for name in names if name]
        if len(names) < 2:
            return "".join(names) or "Author information forthcoming"
        if len(names) == 2:
            return f"{names[0]} and {names[1]}"
        return f"{', '.join(names[:-1])}, and {names[-1]}"

    if isinstance(author_field, list):
        authors = []
        for author in author_field:
            if author.get("literal"):
                authors.append(author["literal"])
                continue
            given = author.get("given", "")
            family = author.get("family", "")
            authors.append(" ".join(part for part in [given, family] if part))
        return join_names(authors)

    return join_names(author_text(author_field).split(", "))


def entry_year(entry):
    raw = entry["fields"].get("date") or entry["fields"].get("year") or ""
    match = re.search(r"\d{4}", str(raw))
    return match.group(0) if match else "Year"


def sort_date_value(entry):
    raw = entry["fields"].get("date") or entry["fields"].get("year") or ""
    match = re.search(r"(\d{4})(?:-(\d{2}))?(?:-(\d{2}))?", str(raw))
    if not match:
        return 0
    return int(f"{match.group(1)}{match.group(2) or '00'}{match.group(3) or '00'}")


def first_field(fields, names):
    for name in names:
        if fields.get(name):
            return fields[name]
    return ""


def is_invited_talk(entry):
    fields = entry["fields"]
    zotero_type = fields.get("type", "").lower()
    return (
        entry["type"] == "speech" and "conference" not in zotero_type
    ) or "invited" in fields.get("annotation", "").lower() or "invited" in zotero_type


def is_working_paper(entry):
    fields = entry["fields"]
    entry_type = entry["type"]
    zotero_type = fields.get("type", "").lower()
    source = " ".join([fields.get("source", ""), fields.get("publisher", ""), fields.get("url", "")]).lower()
    return (
        entry_type in {"unpublished", "preprint", "manuscript"}
        or "working" in zotero_type
        or "preprint" in zotero_type
        or "preprint" in source
        or "socarxiv" in source
        or "osf" in source
        or bool(fields.get("eprint") or fields.get("archiveprefix"))
    )


def is_conference_presentation(entry):
    fields = entry["fields"]
    zotero_type = fields.get("type", "").lower()
    return (
        entry["type"] in {"inproceedings", "proceedings", "paper-conference"}
        or "conference" in zotero_type
        or (entry["type"] == "misc" and not is_invited_talk(entry) and not is_working_paper(entry))
    )


def is_thesis(entry):
    thesis_type = entry["fields"].get("type", "").lower()
    return entry["type"] in {"phdthesis", "mastersthesis", "thesis"} or "thesis" in thesis_type or "dissertation" in thesis_type


def is_master_thesis(entry):
    thesis_type = entry["fields"].get("type", "").lower()
    return is_thesis(entry) and "dissertation" not in thesis_type and "phd" not in thesis_type


def publication_groups(path):
    entries = parse_reference_data(path)
    return [
        ("Journal Articles", [entry for entry in entries if entry["type"] in {"article", "article-journal"} and not is_working_paper(entry)]),
        ("Books and Book Chapters", [entry for entry in entries if entry["type"] in {"book", "inbook", "incollection", "chapter"}]),
        ("Works in Progress", [entry for entry in entries if is_working_paper(entry)]),
        (
            "Conference Presentations",
            [entry for entry in entries if is_conference_presentation(entry) and not is_invited_talk(entry)],
        ),
        ("Invited and Other Talks", [entry for entry in entries if is_invited_talk(entry)]),
        ("Theses", [entry for entry in entries if is_thesis(entry)]),
    ]


def presentation_venue(entry):
    fields = entry["fields"]
    host = first_field(
        fields,
        [
            "eventtitle",
            "event",
            "booktitle",
            "organization",
            "institution",
            "school",
            "howpublished",
            "publisher",
        ],
    )
    location = fields.get("location") or fields.get("address") or ""
    talk_type = fields.get("type", "")

    if host and location:
        return f"{host}, {location}"
    if host:
        return host
    if talk_type and location:
        return f"{talk_type}, {location}"
    return location or talk_type


def publication_venue(entry):
    fields = entry["fields"]
    if is_conference_presentation(entry) or is_invited_talk(entry):
        return presentation_venue(entry)

    venue = first_field(fields, ["journaltitle", "journal", "booktitle", "publisher", "school"])
    location = fields.get("location") or fields.get("address") or ""

    if venue and (entry["type"] in {"book", "inbook", "incollection"} or is_thesis(entry)) and location:
        return f"{venue}, {location}"

    return venue or fields.get("note") or location or entry["type"]


def publication_entries(entries):
    publications = []
    for entry in entries:
        fields = entry["fields"]
        venue = publication_venue(entry)
        doi = fields.get("doi", "")
        doi_url = doi if doi.startswith("http") else f"https://doi.org/{doi}" if doi else ""
        url = "" if doi_url else fields.get("url", "")
        volume_issue = fields.get("volume", "")
        if volume_issue and fields.get("number"):
            volume_issue = f"{volume_issue}({fields['number']})"
        pages = fields.get("pages", "")
        if volume_issue and pages:
            volume_issue = f"{volume_issue}:{pages}"
        elif pages:
            volume_issue = pages
        venue_and_volume = f"<i>{clean_text(venue)}</i>{f' {clean_text(volume_issue)}' if volume_issue else ''}" if venue else clean_text(volume_issue)
        details = [
            venue_and_volume,
            clean_text(doi_url),
            clean_text(url) if url and url != doi_url else "",
        ]
        title = clean_text(fields.get("title", "Untitled publication"))
        is_chapter = entry["type"] in {"chapter", "inbook", "incollection"}
        if is_chapter:
            chapter_details = []
            chapter_book = []
            if fields.get("pages"):
                chapter_book.append(f"Pp. {clean_text(fields['pages'])} in")
            if fields.get("booktitle"):
                chapter_book.append(f"<i>{clean_text(fields['booktitle'])}</i>")
            if chapter_book:
                chapter_details.append(" ".join(chapter_book))
            if fields.get("editor"):
                chapter_details.append(f"edited by {clean_text(asa_author_text(fields['editor']))}")
            publication_place = " ".join(part for part in [fields.get("location", ""), fields.get("publisher", "")] if part)
            if fields.get("location") and fields.get("publisher"):
                publication_place = f"{fields['location']}: {fields['publisher']}"
            if publication_place:
                chapter_details.append(clean_text(publication_place))
            details = [
                ", ".join(part for part in chapter_details if part),
                clean_text(doi_url),
                clean_text(url) if url and url != doi_url else "",
            ]
        if entry["type"] in {"article", "article-journal", "paper-conference", "speech"} or is_working_paper(entry) or is_chapter:
            title = f'"{title}."'
        else:
            title = f"<i>{title}.</i>"
        detail = ". ".join(
            part
            for part in [
                ", ".join(part for part in details if part),
                clean_text(fields.get("note") or fields.get("annotation") or fields.get("annote") or fields.get("extra") or ""),
            ]
            if part
        )
        citation = f"{clean_text(asa_author_text(fields.get('author', '')))}. {entry_year(entry)}. {title}"
        if detail:
            citation = f"{citation} {detail}."
        publications.append(
            (
                entry_year(entry),
                citation,
                "",
            )
        )
    return publications


def section(title, entries, styles):
    story = [paragraph(title, styles["Section"])]
    for date, heading, detail in entries:
        table = Table(
            [
                [
                    paragraph(format_cv_date(date), styles["Date"]),
                    [
                        paragraph(heading, styles["EntryHeading"] if detail else styles["Body"]),
                        paragraph(detail, styles["Body"]) if detail else Spacer(1, 0),
                    ],
                ]
            ],
            colWidths=[0.82 * inch, 6.04 * inch],
        )
        table.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("TOPPADDING", (0, 0), (-1, -1), 1.4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3.8),
                ]
            )
        )
        story.append(table)
    story.append(Spacer(1, 0.05 * inch))
    return story


def build():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    cv_sections = parse_cv_markdown(CV_SOURCE)

    doc = SimpleDocTemplate(
        str(OUTPUT),
        pagesize=letter,
        rightMargin=0.5 * inch,
        leftMargin=0.5 * inch,
        topMargin=0.45 * inch,
        bottomMargin=0.48 * inch,
        title="Benjamin F. Jarvis CV",
        author="Benjamin F. Jarvis",
    )

    base = getSampleStyleSheet()
    styles = {
        "Name": ParagraphStyle(
            "Name",
            parent=base["Title"],
            fontName="Times-Bold",
            fontSize=21,
            leading=23,
            textColor=colors.HexColor("#1d2224"),
            alignment=0,
            spaceAfter=2,
        ),
        "Contact": ParagraphStyle(
            "Contact",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=8.2,
            leading=10,
            textColor=colors.HexColor("#475054"),
            spaceAfter=7,
        ),
        "Section": ParagraphStyle(
            "Section",
            parent=base["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=9.2,
            leading=10.5,
            textColor=colors.HexColor("#1d6f6e"),
            uppercase=True,
            spaceBefore=4,
            spaceAfter=2,
        ),
        "Date": ParagraphStyle(
            "Date",
            parent=base["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=7.5,
            leading=9,
            textColor=colors.HexColor("#9a4d39"),
        ),
        "EntryHeading": ParagraphStyle(
            "EntryHeading",
            parent=base["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=8.2,
            leading=9.7,
            textColor=colors.HexColor("#1d2224"),
            spaceAfter=0.5,
        ),
        "Body": ParagraphStyle(
            "Body",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=7.8,
            leading=9.3,
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
    for title, entries in publication_groups(PUBLICATIONS_SOURCE):
        if entries:
            story.extend(section(title, publication_entries(entries), styles))
    if SUPERVISION_SOURCE.exists():
        supervision_entries = [entry for entry in parse_reference_data(SUPERVISION_SOURCE) if is_thesis(entry)]
        doctoral_entries = [entry for entry in supervision_entries if not is_master_thesis(entry)]
        masters_entries = [entry for entry in supervision_entries if is_master_thesis(entry)]
        if doctoral_entries or masters_entries:
            story.append(paragraph("Supervision", styles["Section"]))
        if doctoral_entries:
            story.extend(section("Doctoral Supervision", publication_entries(doctoral_entries), styles))
        if masters_entries:
            story.extend(section("Master's Supervision", publication_entries(masters_entries), styles))
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
            "Service",
            [(entry["date"], entry["heading"], " ".join(entry["detail"])) for entry in cv_sections.get("service", [])],
            styles,
        )
    )
    story.extend(
        section(
            "Skills",
            [(entry["date"], entry["heading"], " ".join(entry["detail"])) for entry in cv_sections.get("skills", [])],
            styles,
        )
    )
    story.extend(
        section(
            "Miscellaneous",
            [(entry["date"], entry["heading"], " ".join(entry["detail"])) for entry in cv_sections.get("miscellaneous", [])],
            styles,
        )
    )

    doc.build(story)


if __name__ == "__main__":
    build()
