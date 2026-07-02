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
TEACHING_SOURCE = ROOT / "data" / "teaching.json"
GRANTS_SOURCE = ROOT / "data" / "grants.json"
PDF_SEPARATOR = " — "


def paragraph(text, style):
    return Paragraph(text, style)


def format_cv_date(text):
    return "<br/>".join(clean_text(part.strip()) for part in text.split(";") if part.strip())


def clean_text(text):
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("--", "-")
    )


def clean_rich_text(text):
    return clean_text(text).replace("&lt;br/&gt;", "<br/>")


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


def csl_date_value(date):
    if (date or {}).get("literal"):
        return str(date["literal"])
    parts = (date or {}).get("date-parts", [[]])[0]
    return "-".join(str(part) for part in parts if part)


def csl_season_label(season):
    if isinstance(season, str):
        normalized = season.lower()
        if "spring" in normalized:
            return "Spring"
        if "summer" in normalized:
            return "Summer"
        if "fall" in normalized or "autumn" in normalized:
            return "Fall"
        if "winter" in normalized:
            return "Winter"
    try:
        season_number = int(season or 0)
    except (TypeError, ValueError):
        return str(season or "")
    return {
        1: "Spring",
        2: "Summer",
        3: "Fall",
        4: "Winter",
    }.get(season_number, "")


def teaching_term_from_month(month):
    try:
        month_number = int(month or 0)
    except (TypeError, ValueError):
        return ""
    if not month_number:
        return ""
    return "Spring" if month_number <= 6 else "Fall"


def teaching_term_from_literal(value):
    year_match = re.search(r"(?:19|20)\d{2}", str(value or ""))
    if not year_match:
        return ""
    year = year_match.group(0)
    month_names = {
        "january": 1,
        "february": 2,
        "march": 3,
        "april": 4,
        "may": 5,
        "june": 6,
        "july": 7,
        "august": 8,
        "september": 9,
        "october": 10,
        "november": 11,
        "december": 12,
    }
    lower = str(value or "").lower()
    month = next((number for name, number in month_names.items() if name in lower), 0)
    term = teaching_term_from_month(month)
    return f"{term} {year}" if term else year


def teaching_date_value(date):
    if (date or {}).get("literal"):
        return teaching_term_from_literal(date["literal"]) or str(date["literal"])
    parts = (date or {}).get("date-parts", [[]])[0]
    if not parts:
        return ""
    season = csl_season_label((date or {}).get("season"))
    if season and len(parts) == 1:
        return f"{season} {parts[0]}"
    if len(parts) > 1:
        term = teaching_term_from_month(parts[1])
        return f"{term} {parts[0]}" if term else str(parts[0])
    return "-".join(str(part) for part in parts if part)


def normalize_csl_item(item):
    issued = csl_date_value(item.get("issued"))
    fields = {
        "title": item.get("title", ""),
        "author": item.get("author", []),
        "editor": item.get("editor", []),
        "contributor": item.get("contributor", []),
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
        "shorttitle": item.get("title-short", ""),
        "collectiontitle": item.get("collection-title", ""),
        "status": item.get("status", ""),
    }
    return {"type": item.get("type", ""), "fields": fields}


def parse_reference_data(path):
    data = json.loads(path.read_text(encoding="utf-8"))
    items = data if isinstance(data, list) else data.get("items", [])
    return sorted((normalize_csl_item(item) for item in items), key=sort_date_value, reverse=True)


def asa_author_text(author_field):
    if isinstance(author_field, list):
        return format_name_list(csl_person_name(author) for author in author_field) or "Author information forthcoming"

    return str(author_field or "").strip() or "Author information forthcoming"


def csl_person_name(person):
    if person.get("literal"):
        return person["literal"]
    return " ".join(part for part in [person.get("given", ""), person.get("family", "")] if part)


def format_name_list(names):
    names = [name for name in names if name]
    if len(names) < 2:
        return "".join(names)
    if len(names) == 2:
        return f"{names[0]} and {names[1]}"
    return f"{', '.join(names[:-1])}, and {names[-1]}"


def is_benjamin_jarvis_name(name):
    return bool(re.search(r"benjamin\s+f\.?\s+jarvis|benjamin\s+jarvis", name, re.I))


def csl_name_list(people, exclude_self=False):
    names = [
        csl_person_name(person)
        for person in people
        if csl_person_name(person) and (not exclude_self or not is_benjamin_jarvis_name(csl_person_name(person)))
    ]
    return format_name_list(names)


def supervision_name_list(entry):
    names = []
    for index, person in enumerate(entry["fields"].get("contributor", [])):
        name = csl_person_name(person)
        if not name:
            continue
        if is_phd_thesis(entry) and index == 0:
            name = f"{name} (Main)"
        names.append(name)
    return format_name_list(names)


def entry_year(entry):
    raw = entry["fields"].get("date") or entry["fields"].get("year") or ""
    match = re.search(r"\d{4}", str(raw))
    return match.group(0) if match else "Year"


def sort_date_value(entry):
    raw = entry["fields"].get("date") or entry["fields"].get("year") or ""
    match = re.search(r"(\d{4})(?:-(\d{1,2}))?(?:-(\d{1,2}))?", str(raw))
    if not match:
        return 0
    return int(f"{match.group(1)}{(match.group(2) or '0').zfill(2)}{(match.group(3) or '0').zfill(2)}")


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


def is_phd_thesis(entry):
    thesis_type = entry["fields"].get("type", "").lower()
    return is_thesis(entry) and ("dissertation" in thesis_type or "phd" in thesis_type)


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
    ]


def csl_name(name):
    if name.get("literal"):
        return name["literal"]
    return " ".join(part for part in [name.get("given", ""), name.get("family", "")] if part)


def note_value(note, label):
    prefix = f"{label}:"
    for line in str(note or "").splitlines():
        if line.startswith(prefix):
            return line[len(prefix):].strip()
    return ""


def teaching_sort_value(term):
    match = re.search(r"(Spring|Fall)?\s*((?:19|20)\d{2})", str(term), re.I)
    if not match:
        return 0
    term_weight = 2 if (match.group(1) or "").lower() == "fall" else 1 if (match.group(1) or "").lower() == "spring" else 0
    return int(match.group(2)) * 10 + term_weight


def is_benjamin_jarvis(name):
    return bool(re.search(r"benjamin\s+f\.?\s+jarvis|benjamin\s+jarvis", name, re.I))


def teaching_role_label(role):
    base_role = role.get("role") or "Teaching"
    other_organizers = [name for name in role.get("organizers", []) if not is_benjamin_jarvis(name)]
    user_is_organizer = any(is_benjamin_jarvis(name) for name in role.get("organizers", []))
    organizer_list = format_name_list(other_organizers)

    if not other_organizers:
        return base_role
    if user_is_organizer:
        return f"{base_role} (With {organizer_list})"
    return f"{base_role} (Coordinator: {organizer_list})"


def normalize_teaching_record(item):
    note = item.get("note", "")
    is_standard_teaching = item.get("type") == "standard"
    organizers = item.get("author", []) if is_standard_teaching else item.get("organizer", []) + item.get("chair", [])
    contributors = (
        item.get("contributor", []) + item.get("presenter", [])
        if is_standard_teaching
        else item.get("author", []) + item.get("presenter", []) + item.get("contributor", [])
    )
    organizer_names = [csl_name(name) for name in organizers if csl_name(name)]
    contributor_names = [csl_name(name) for name in contributors if csl_name(name)]
    teaching_type = item.get("genre") or "Teaching"
    user_is_organizer = any(is_benjamin_jarvis(name) for name in organizer_names)
    user_is_contributor = any(is_benjamin_jarvis(name) for name in contributor_names)
    record_id = item.get("citation-key") or item.get("id") or slugify(item.get("title", "teaching"))
    if user_is_contributor and not user_is_organizer:
        inferred_role = "Guest Lecturer"
    elif user_is_organizer and re.search(r"development-director", record_id, re.I):
        inferred_role = "Program Development Director"
    elif user_is_organizer and re.search(r"program|programme", f"{teaching_type} {item.get('title', '')}", re.I):
        inferred_role = "Program Director"
    elif user_is_organizer:
        inferred_role = "Course Coordinator"
    else:
        inferred_role = teaching_type

    return {
        "id": record_id,
        "title": item.get("title") or "Untitled course",
        "code": item.get("number") or item.get("title-short", ""),
        "program": item.get("authority") or item.get("event-title", ""),
        "institution": item.get("publisher") or item.get("collection-title", ""),
        "location": item.get("publisher-place") or item.get("event-place", ""),
        "term": teaching_date_value(item.get("issued")) or "",
        "role": note_value(note, "Role") or inferred_role,
        "organizers": organizer_names,
        "presenters": contributor_names,
        "abstract": item.get("abstract", ""),
    }


def group_teaching_records(path):
    data = json.loads(path.read_text(encoding="utf-8"))
    items = data if isinstance(data, list) else data.get("items", [])
    groups = {}

    for item in items:
        record = normalize_teaching_record(item)
        key = record["code"] or slugify(record["title"])
        if key not in groups:
            groups[key] = {
                "title": record["title"],
                "code": record["code"],
                "program": record["program"],
                "institution": record["institution"],
                "roles": [],
            }

        group = groups[key]
        group["program"] = group["program"] or record["program"]
        group["institution"] = group["institution"] or record["institution"]
        group["roles"].append(record)

    grouped = []
    for group in groups.values():
        group["roles"].sort(key=lambda role: teaching_sort_value(role["term"]), reverse=True)
        group["latest_value"] = teaching_sort_value(group["roles"][0]["term"] if group["roles"] else "")
        group["kind"] = (
            "program"
            if any(re.search(r"program|programme", role["role"], re.I) for role in group["roles"])
            or (not group["code"] and re.search(r"program|programme", group["title"], re.I))
            else "course"
        )
        grouped.append(group)

    return sorted(grouped, key=lambda group: (-group["latest_value"], group["title"]))


def teaching_date_range(roles):
    years = []
    for role in roles:
        match = re.search(r"(?:19|20)\d{2}", str(role.get("term", "")))
        if match:
            years.append(int(match.group(0)))
    if not years:
        return ""
    if min(years) == max(years):
        return str(max(years))
    return f"{min(years)}-{max(years)}"


def teaching_entries(groups):
    entries = []
    for group in groups:
        meta = PDF_SEPARATOR.join(part for part in [group.get("program", ""), group.get("institution", "")] if part)
        role_history = "<br/>".join(
            PDF_SEPARATOR.join(part for part in [role.get("term", ""), teaching_role_label(role)] if part)
            for role in group["roles"]
            if role.get("term")
        )
        detail = "<br/>".join(clean_rich_text(part) for part in [
            meta,
            f"Teaching History:<br/>{role_history}" if role_history else "",
        ] if part)
        entries.append((teaching_date_range(group["roles"]), clean_text(group["title"]), detail))
    return entries


def grant_decision(entry):
    return note_value(entry["fields"].get("note", ""), "Decision")


def grant_budget(entry):
    return note_value(entry["fields"].get("note", ""), "Budget")


def grant_series_title(entry):
    return entry["fields"].get("collectiontitle", "")


def grant_decision_label(entry):
    decision = grant_decision(entry)
    if not decision:
        return "Pending"
    if re.search(r"granted|needs audit closed", decision, re.I):
        return "Accepted"
    if re.search(r"rejected|not accepted", decision, re.I):
        return "Rejected"
    return decision


def is_accepted_grant(entry):
    return bool(re.search(r"granted|needs audit closed", grant_decision(entry), re.I))


def grant_group_key(entry):
    fields = entry["fields"]
    return fields.get("shorttitle") or fields.get("title") or "Untitled project"


def grant_number_sort_value(entry):
    raw = str(entry["fields"].get("number", ""))
    numbers = re.findall(r"\d+", raw)
    return int("".join(numbers)) if numbers else sort_date_value(entry)


def grant_lifecycle(entries):
    decisions = " | ".join(grant_decision(entry) for entry in entries).lower()
    statuses = " | ".join(str(entry["fields"].get("status", "")) for entry in entries).lower()

    if re.search(r"\bopen\b", statuses):
        return "ongoing"
    if re.search(r"finally registered|submitted|registered|pending|under review", statuses) or any(not grant_decision(entry) for entry in entries):
        return "under-review"
    if re.search(r"granted|needs audit closed", decisions):
        return "completed"
    return "rejected"


def sort_grant_records(entries):
    return sorted(
        entries,
        key=lambda entry: (
            0 if is_accepted_grant(entry) else 1,
            -grant_number_sort_value(entry),
            entry["fields"].get("title", ""),
        ),
    )


def display_grant_record(entries):
    accepted = sorted([entry for entry in entries if is_accepted_grant(entry)], key=sort_date_value, reverse=True)
    if accepted:
        return accepted[0]
    return sorted(entries, key=sort_date_value, reverse=True)[0] if entries else None


def group_grants(path):
    entries = parse_reference_data(path)
    groups = {}
    for entry in entries:
        groups.setdefault(grant_group_key(entry), []).append(entry)

    grouped = []
    for title, records in groups.items():
        records = sort_grant_records(records)
        latest = sorted(records, key=sort_date_value, reverse=True)[0]
        grouped.append({
            "title": title,
            "records": records,
            "display": display_grant_record(records),
            "latest": latest,
            "latest_year": sort_date_value(latest),
            "lifecycle": grant_lifecycle(records),
        })
    return sorted(grouped, key=lambda group: (-group["latest_year"], group["title"]))


def grant_participant_names(entry):
    fields = entry["fields"]
    applicants = fields.get("author", [])
    contributors = fields.get("contributor", [])
    main = csl_person_name(applicants[0]) if applicants else ""
    others = [csl_person_name(person) for person in applicants[1:]] + [csl_person_name(person) for person in contributors]
    names = []
    if main:
        names.append(f"{main} (PI)")
    names.extend(name for name in others if name)
    return format_name_list(names)


def grant_funder_call(entry):
    fields = entry["fields"]
    return PDF_SEPARATOR.join(part for part in [fields.get("publisher", ""), grant_series_title(entry)] if part)


def grant_number_budget(entry):
    fields = entry["fields"]
    parts = []
    if fields.get("number"):
        parts.append(f"Project Number: {fields['number']}")
    if grant_budget(entry):
        parts.append(f"Budget: {grant_budget(entry)}")
    return ", ".join(parts)


def grant_history_text(records):
    rows = []
    for entry in records:
        row = PDF_SEPARATOR.join(part for part in [entry_year(entry), grant_decision_label(entry), grant_funder_call(entry)] if part)
        if row:
            rows.append(row)
    return "<br/>".join(rows)


def grant_display_year(group):
    return entry_year(group.get("display") or group.get("latest") or {"fields": {}})


def grant_cv_entries(groups):
    entries = []
    for group in groups:
        display = group.get("display") or group.get("latest")
        if not display:
            continue
        fields = display["fields"]
        detail_parts = [
            grant_funder_call(display),
            grant_participant_names(display),
            grant_number_budget(display),
            f"Application History:<br/>{grant_history_text(group['records'])}" if group.get("records") else "",
        ]
        entries.append((
            grant_display_year(group),
            clean_text(fields.get("title") or group.get("title") or "Untitled project"),
            "<br/>".join(clean_rich_text(part) for part in detail_parts if part),
        ))
    return entries


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


def supervision_detail(entry):
    fields = entry["fields"]
    parts = [
        fields.get("type") or ("Dissertation" if is_phd_thesis(entry) else "Master's thesis"),
        fields.get("publisher", ""),
        fields.get("location", ""),
    ]
    detail = ". ".join(clean_text(part) for part in parts if part)
    supervisors = supervision_name_list(entry)
    if supervisors:
        supervision_line = f"Supervision: {clean_text(supervisors)}"
        return f"{supervision_line}<br/>{detail}" if detail else supervision_line
    return detail


def supervision_cv_entries(entries):
    rows = []
    for entry in entries:
        fields = entry["fields"]
        student = asa_author_text(fields.get("author", []))
        title = fields.get("title") or "Untitled thesis"
        rows.append((
            entry_year(entry),
            f"{clean_text(student)}. {clean_text(title)}",
            supervision_detail(entry),
        ))
    return rows


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
            story.extend(section("Doctoral Supervision", supervision_cv_entries(doctoral_entries), styles))
        if masters_entries:
            story.extend(section("Master's Supervision", supervision_cv_entries(masters_entries), styles))
    if GRANTS_SOURCE.exists():
        grant_groups = group_grants(GRANTS_SOURCE)
        story.append(paragraph("Grants", styles["Section"]))
        for lifecycle, label in [
            ("ongoing", "Ongoing"),
            ("under-review", "Under Review"),
            ("completed", "Completed"),
            ("rejected", "Rejected"),
        ]:
            lifecycle_groups = [group for group in grant_groups if group["lifecycle"] == lifecycle]
            if lifecycle_groups:
                story.extend(section(label, grant_cv_entries(lifecycle_groups), styles))
    if TEACHING_SOURCE.exists():
        teaching_groups = group_teaching_records(TEACHING_SOURCE)
        course_groups = [group for group in teaching_groups if group["kind"] == "course"]
        program_groups = [group for group in teaching_groups if group["kind"] == "program"]
        if course_groups:
            story.extend(section("Teaching - Courses", teaching_entries(course_groups), styles))
        if program_groups:
            story.extend(section("Teaching - Programs", teaching_entries(program_groups), styles))
    else:
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
