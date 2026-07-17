#!/usr/bin/env python3
"""Generate Quarto source pages from local JSON data."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "templates"

TYPE_LABELS = {
    "article": "Preprint",
    "article-journal": "Journal Article",
    "book": "Book",
    "chapter": "Book Chapter",
    "inbook": "Book Chapter",
    "incollection": "Book Chapter",
    "paper-conference": "Conference Presentation",
    "inproceedings": "Conference Paper",
    "proceedings": "Conference Paper",
    "manuscript": "Working Paper",
    "speech": "Talk",
    "unpublished": "Working Paper",
    "report": "Report",
    "techreport": "Report",
    "phdthesis": "PhD Thesis",
    "mastersthesis": "Master's Thesis",
    "thesis": "Thesis",
    "misc": "Presentation",
}


def load_json(path: str):
    with (ROOT / path).open(encoding="utf-8") as handle:
        return json.load(handle)


def write(path: str, text: str) -> None:
    target = ROOT / path
    rendered = text.rstrip() + "\n"
    if target.exists() and target.read_text(encoding="utf-8") == rendered:
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(rendered, encoding="utf-8")


def render_template(name: str, values: dict[str, str]) -> str:
    text = (TEMPLATES / name).read_text(encoding="utf-8")
    for key, value in values.items():
        text = text.replace("{{ " + key + " }}", value)
    return text


def md_escape(value: object) -> str:
    text = str(value or "")
    replacements = {
        "\\": "\\\\",
        "*": "\\*",
        "_": "\\_",
        "[": "\\[",
        "]": "\\]",
        "<": "\\<",
        ">": "\\>",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def md_italic(value: object) -> str:
    return f"*{md_escape(value)}*"


def md_bold(value: object) -> str:
    return f"**{md_escape(value)}**"


def md_link(label: str, url: str) -> str:
    escaped_url = str(url or "").replace(")", "%29").replace(" ", "%20")
    return f"[{md_escape(label)}]({escaped_url})"


def md_paragraphs(value: object) -> str:
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", str(value or "").strip()) if part.strip()]
    return "\n\n".join(md_escape(part) for part in paragraphs)


def md_line_breaks(parts: list[str]) -> str:
    return "  \n".join(md_escape(part.strip()) for part in parts if part.strip())


def md_blocks(parts: list[str]) -> str:
    return "\n\n".join(part.strip() for part in parts if part and part.strip())


def year_from_text(value: object) -> str:
    match = re.search(r"(?:19|20)\d{2}", str(value or ""))
    return match.group(0) if match else ""


def eyebrow_parts(*parts: object) -> str:
    return " • ".join(str(part).strip() for part in parts if str(part or "").strip())


def render_cv_history_row(date: str, text: str) -> str:
    return f"""::: {{.cv-history-row}}
::: {{.cv-history-date}}
{md_escape(date)}
:::

::: {{.cv-history-text}}
{md_escape(text)}
:::
:::"""


def render_content_card(
    classes: list[str],
    eyebrow: str = "",
    title: str = "",
    title_markdown: str = "",
    byline: str = "",
    description: str = "",
    body: str = "",
    media: str = "",
    footer: str = "",
    identifier: str = "",
) -> str:
    all_classes = ["content-card", *classes]
    if media:
        all_classes.append("has-media")
    attributes = "." + " .".join(all_classes)
    if identifier:
        attributes += f" #{identifier}"
    title_line = title_markdown or md_escape(title)
    parts = [
        media,
        "::: {.content-card-body}",
        f"::: {{.content-card-eyebrow}}\n{md_escape(eyebrow)}\n:::" if eyebrow else "",
        f"### {title_line}" if title_line else "",
        f"::: {{.content-card-byline}}\n{md_escape(byline)}\n:::" if byline else "",
        f"::: {{.content-card-description}}\n{description}\n:::" if description else "",
        body,
        footer,
        ":::",
    ]
    return f"::: {{{attributes}}}\n{md_blocks(parts)}\n:::"


def csl_name(name: dict) -> str:
    if name.get("literal"):
        return name["literal"]
    return " ".join(part for part in [name.get("given"), name.get("family")] if part)


def name_list(names: list[str]) -> str:
    names = [name for name in names if name]
    if len(names) < 2:
        return "".join(names)
    if len(names) == 2:
        return f"{names[0]} and {names[1]}"
    return f"{', '.join(names[:-1])}, and {names[-1]}"


def csl_date_value(date: dict | None) -> str:
    if not date:
        return ""
    if date.get("literal"):
        return str(date["literal"])
    parts = date.get("date-parts", [[]])[0]
    return "-".join(str(part).zfill(2) if index else str(part) for index, part in enumerate(parts))


def csl_year(item: dict) -> str:
    value = csl_date_value(item.get("issued"))
    match = re.search(r"(?:19|20)\d{2}", value)
    return match.group(0) if match else ""


def sort_date_value(item: dict) -> int:
    value = csl_date_value(item.get("issued"))
    match = re.search(r"(\d{4})(?:-(\d{1,2}))?(?:-(\d{1,2}))?", value)
    if not match:
        return 0
    year, month, day = match.groups()
    return int(f"{year}{int(month or 0):02d}{int(day or 0):02d}")


def first_field(item: dict, fields: list[str]) -> str:
    for field in fields:
        if item.get(field):
            return str(item[field])
    return ""


def is_benjamin_jarvis(name: str) -> bool:
    return bool(re.search(r"benjamin\s+f\.?\s+jarvis|benjamin\s+jarvis", name, re.I))


def note_value(note: str, label: str) -> str:
    for line in str(note or "").splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        if key.strip().lower() == label.lower():
            return value.strip()
    return ""


def publication_venue(item: dict) -> str:
    if is_conference_presentation(item) or is_invited_talk(item):
        host = first_field(item, ["event-title", "event", "container-title", "publisher"])
        location = item.get("event-place") or item.get("publisher-place") or ""
        if host and location:
            return f"{host}, {location}"
        return host or location
    venue = first_field(item, ["container-title", "publisher"])
    location = item.get("publisher-place") or item.get("event-place") or ""
    if venue and item.get("type") in {"book", "inbook", "incollection", "chapter", "thesis"} and location:
        return f"{venue}, {location}"
    return venue or str(item.get("note") or location or "")


def is_working_paper(item: dict) -> bool:
    entry_type = str(item.get("genre") or item.get("type") or "").lower()
    source = " ".join(str(item.get(field) or "") for field in ["source", "publisher", "URL"]).lower()
    return (
        item.get("type") in {"unpublished", "preprint", "manuscript"}
        or "working" in entry_type
        or "preprint" in entry_type
        or "preprint" in source
        or "socarxiv" in source
        or "osf" in source
    )


def is_invited_talk(item: dict) -> bool:
    entry_type = str(item.get("genre") or "").lower()
    note = str(item.get("note") or "").lower()
    return (item.get("type") == "speech" and "conference" not in entry_type) or "invited" in entry_type or "invited" in note


def is_conference_presentation(item: dict) -> bool:
    entry_type = str(item.get("genre") or "").lower()
    return (
        item.get("type") in {"inproceedings", "proceedings", "paper-conference"}
        or "conference" in entry_type
        or (item.get("type") == "misc" and not is_invited_talk(item) and not is_working_paper(item))
    )


def is_thesis(item: dict) -> bool:
    entry_type = str(item.get("genre") or item.get("type") or "").lower()
    return item.get("type") in {"phdthesis", "mastersthesis", "thesis"} or "thesis" in entry_type or "dissertation" in entry_type


def is_phd_thesis(item: dict) -> bool:
    entry_type = str(item.get("genre") or item.get("type") or "").lower()
    return is_thesis(item) and ("phd" in entry_type or "dissertation" in entry_type or item.get("type") == "phdthesis")


def is_masters_thesis(item: dict) -> bool:
    return is_thesis(item) and not is_phd_thesis(item)


def citation_for(item: dict) -> dict[str, str]:
    authors = name_list([csl_name(name) for name in item.get("author", [])])
    year = csl_year(item)
    title = item.get("title") or "Untitled publication"
    venue = publication_venue(item)
    doi = item.get("DOI") or ""
    url = item.get("URL") or ""
    doi_url = doi if doi.startswith("http") else f"https://doi.org/{doi}" if doi else ""
    link = doi_url or url
    volume = str(item.get("volume") or "")
    issue = str(item.get("issue") or item.get("number") or "")
    pages = str(item.get("page") or "")
    volume_issue = f"{volume}({issue})" if volume and issue else volume
    pages_text = f":{pages}" if volume_issue and pages else pages
    is_chapter = item.get("type") in {"chapter", "inbook", "incollection"}
    quoted = item.get("type") in {"article", "article-journal", "paper-conference", "speech"} or is_working_paper(item) or is_chapter
    title_text = f'"{md_escape(title)}."' if quoted else f"{md_italic(title)}."
    venue_bits = []
    if venue:
        venue_bits.append(md_italic(venue))
    if volume_issue or pages_text:
        venue_bits.append(md_escape(f"{volume_issue}{pages_text}"))
    if link:
        venue_bits.append(md_link("Link", link))
    details = ", ".join(venue_bits)
    full = f"{md_escape(authors)}. {md_escape(year)}. {title_text}"
    if details:
        full += f" {details}."
    label = "Working Paper / Preprint" if is_working_paper(item) else TYPE_LABELS.get(item.get("type"), item.get("type", "Publication"))
    return {
        "authors": authors,
        "year": year,
        "title": title,
        "label": label,
        "full": full,
        "abstract": item.get("abstract") or "",
        "extra": item.get("note") or "",
        "keywords": str(item.get("keyword") or "").lower(),
    }


def publication_images(item: dict, assets: dict) -> list[dict]:
    asset = assets.get(item.get("citation-key") or item.get("id") or "", {})
    if isinstance(asset.get("images"), list):
        return asset["images"]
    if asset.get("image"):
        return [{"image": asset["image"], "alt": asset.get("alt", ""), "caption": asset.get("caption", "")}]
    return []


def publication_asset(item: dict, assets: dict) -> dict:
    return assets.get(item.get("citation-key") or item.get("id") or "", {})


def doi_url(item: dict) -> str:
    doi = str(item.get("DOI") or "").strip()
    if not doi:
        return ""
    return doi if doi.startswith("http") else f"https://doi.org/{doi}"


def publication_primary_link(item: dict) -> tuple[str, str]:
    url = doi_url(item) or str(item.get("URL") or "").strip()
    if not url:
        return "", ""
    venue = publication_context(item)
    label = venue or ("Preprint" if is_working_paper(item) else "Published version")
    return label, url


def publication_preprint_link(item: dict, assets: dict) -> tuple[str, str]:
    asset = publication_asset(item, assets)
    for key in ["preprint", "preprint_url", "preprint-url", "manuscript", "manuscript_url", "osf"]:
        value = asset.get(key)
        if isinstance(value, dict):
            url = value.get("url") or value.get("href")
            label = value.get("label") or value.get("archive") or value.get("source") or "Preprint"
        else:
            url = value
            label = asset.get("preprint_label") or asset.get("preprint-archive") or "Preprint"
        if url:
            return label, str(url)
    return "", ""


def publication_link_bar(item: dict, assets: dict) -> str:
    links = []
    primary_label, primary_url = publication_primary_link(item)
    if primary_url:
        links.append((primary_label, primary_url))
    preprint_label, preprint_url = publication_preprint_link(item, assets)
    if preprint_url and preprint_url not in {url for _, url in links}:
        links.append((preprint_label, preprint_url))
    if not links:
        return ""
    return " · ".join(md_link(label, url) for label, url in links)


def publication_context(item: dict) -> str:
    return item.get("container-title") or item.get("event-title") or item.get("publisher") or item.get("archive") or item.get("source") or ""


def render_publication(item: dict, assets: dict | None = None, compact: bool = False) -> str:
    assets = assets or {}
    citation = citation_for(item)
    if compact:
        return f"""::: {{.cv-entry}}
::: {{.cv-date}}
{md_escape(citation["year"])}
:::

::: {{.cv-detail}}
::: {{.citation-line}}
{citation["full"]}
:::
:::
:::"""
    images = publication_images(item, assets)
    image_markdown = ""
    if images:
        image = images[0]
        image_markdown = f"""::: {{.content-card-media .publication-media}}
![{md_escape(image.get("alt", ""))}]({image.get("image", "")})
:::"""
    abstract = md_paragraphs(citation["abstract"]) if citation["abstract"] else ""
    extra = md_paragraphs(citation["extra"]) if citation["extra"] else ""
    context = publication_context(item)
    links = publication_link_bar(item, assets)
    footer = md_blocks([
        f"::: {{.publication-venue}}\n{md_escape(context)}\n:::" if context and not links else "",
        f"::: {{.publication-links}}\n{links}\n:::" if links else "",
    ])
    body = md_blocks([
        f"::: {{.content-card-detail .publication-footer}}\n{footer}\n:::" if footer else "",
        extra,
    ])
    return render_content_card(
        ["publication-card", "publication-item"],
        eyebrow=eyebrow_parts(citation["year"], citation["label"]),
        title=citation["title"],
        byline=citation["authors"],
        description=abstract,
        body=body,
        media=image_markdown,
    )


def filter_publications(items: list[dict], mode: str) -> list[dict]:
    if mode == "selected":
        selected = [
            item for item in items
            if "selected" in citation_for(item)["keywords"]
            and item.get("type") in {"article", "article-journal", "book", "inbook", "incollection", "chapter"}
            and not is_working_paper(item)
        ]
        if selected:
            return selected
        return [
            item for item in items
            if item.get("type") in {"article", "article-journal", "book", "inbook", "incollection", "chapter"}
            and not is_working_paper(item)
        ]
    if mode == "journal-articles":
        return [item for item in items if item.get("type") in {"article", "article-journal"} and not is_working_paper(item)]
    if mode == "books-chapters":
        return [item for item in items if item.get("type") in {"book", "inbook", "incollection", "chapter"}]
    if mode in {"working-papers", "works-progress"}:
        return [item for item in items if is_working_paper(item)]
    if mode == "conference-presentations":
        return [item for item in items if is_conference_presentation(item) and not is_invited_talk(item)]
    if mode == "invited-talks":
        return [item for item in items if is_invited_talk(item)]
    if mode == "supervision-doctoral":
        return [item for item in items if is_phd_thesis(item)]
    if mode == "supervision-masters":
        return [item for item in items if is_masters_thesis(item)]
    return items


def render_publication_list(items: list[dict], mode: str, assets: dict, limit: int | None = None) -> str:
    selected = filter_publications(items, mode)
    if limit:
        selected = selected[:limit]
    return "\n\n".join(render_publication(item, assets) for item in selected) or "_No entries found._"


def grant_decision(item: dict) -> str:
    return note_value(item.get("note", ""), "Decision")


def is_accepted_grant(item: dict) -> bool:
    return bool(re.search(r"granted|needs audit closed", grant_decision(item), re.I))


def grant_key(item: dict) -> str:
    return item.get("title-short") or item.get("shortTitle") or item.get("title") or "Untitled project"


def grant_lifecycle(records: list[dict]) -> str:
    decisions = " | ".join(grant_decision(item) for item in records).lower()
    statuses = " | ".join(str(item.get("status") or "") for item in records).lower()
    if re.search(r"\bopen\b", statuses):
        return "ongoing"
    if re.search(r"finally registered|submitted|registered|pending|under review", statuses) or any(not grant_decision(item) for item in records):
        return "under-review"
    if re.search(r"granted|needs audit closed", decisions):
        return "completed"
    return "rejected"


def group_grants(items: list[dict]) -> list[dict]:
    groups: dict[str, list[dict]] = {}
    for item in items:
        groups.setdefault(grant_key(item), []).append(item)
    output = []
    for key, records in groups.items():
        records = sorted(records, key=lambda item: (is_accepted_grant(item), sort_date_value(item)), reverse=True)
        display = next((item for item in records if is_accepted_grant(item)), records[0])
        latest = max(records, key=sort_date_value)
        output.append({"key": key, "records": records, "display": display, "latest": latest, "lifecycle": grant_lifecycle(records)})
    return sorted(output, key=lambda group: (sort_date_value(group["latest"]), group["key"]), reverse=True)


def grant_participants(item: dict) -> str:
    authors = item.get("author", [])
    contributors = item.get("contributor", [])
    names = []
    if authors:
        names.append(f"{csl_name(authors[0])} (PI)")
    names.extend(csl_name(name) for name in authors[1:])
    names.extend(csl_name(name) for name in contributors)
    return name_list(names)


def grant_funder(item: dict) -> str:
    return " · ".join(part for part in [item.get("publisher"), item.get("collection-title")] if part)


def render_grant(group: dict) -> str:
    item = group["display"]
    lifecycle = group["lifecycle"].replace("-", " ").title()
    funder = grant_funder(item).replace(" · ", " • ")
    meta = eyebrow_parts(csl_year(item), lifecycle, funder)
    participants = grant_participants(item)
    budget = note_value(item.get("note", ""), "Budget")
    number_budget = ", ".join(part for part in [f"Project Number: {item.get('number')}" if item.get("number") else "", f"Budget: {budget}" if budget else ""] if part)
    abstract = item.get("abstract") or ""
    body = md_blocks([
        f"::: {{.content-card-detail .grant-number-budget}}\n{md_escape(number_budget)}\n:::" if number_budget else "",
    ])
    return render_content_card(
        ["project-card", "grant-card"],
        eyebrow=meta,
        title=item.get("title") or group["key"],
        byline=participants,
        description=md_paragraphs(abstract),
        body=body,
    )


def render_cv_grant(group: dict) -> str:
    item = group["display"]
    year = csl_year(item)
    funder = grant_funder(item)
    participants = grant_participants(item)
    budget = note_value(item.get("note", ""), "Budget")
    number_budget = ", ".join(part for part in [
        f"Project Number: {item.get('number')}" if item.get("number") else "",
        f"Budget: {budget}" if budget else "",
    ] if part)
    history_items = "\n\n".join(
        render_cv_history_row(
            csl_year(record),
            " · ".join(part for part in [
                grant_decision(record) or record.get("status", ""),
                grant_funder(record),
            ] if part),
        )
        for record in group["records"]
    )
    details = [
        f"::: {{.meta}}\n{md_escape(group['lifecycle'].replace('-', ' ').title())} · {md_escape(funder)}\n:::" if funder else "",
        md_escape(participants) if participants else "",
        md_escape(number_budget) if number_budget else "",
        f"#### Application History {{.cv-history-heading}}\n\n::: {{.grant-history .cv-history}}\n{history_items}\n:::" if history_items else "",
    ]
    return f"""::: {{.cv-entry}}
::: {{.cv-date}}
{md_escape(year)}
:::

::: {{.cv-detail}}
### {md_escape(item.get("title") or group["key"])}

{md_blocks(details)}
:::
:::"""


def render_grant_list(groups: list[dict], lifecycle: str, limit: int | None = None) -> str:
    selected = [group for group in groups if group["lifecycle"] == lifecycle]
    if limit:
        selected = selected[:limit]
    return "\n\n".join(render_grant(group) for group in selected) or "_No projects found._"


def teaching_term(date: dict | None) -> str:
    value = csl_date_value(date)
    year_match = re.search(r"(?:19|20)\d{2}", value)
    year = year_match.group(0) if year_match else ""
    if not year:
        return value
    if date and date.get("season") in {1, "1", "spring", "Spring"}:
        return f"Spring {year}"
    if date and date.get("season") in {3, "3", "fall", "Fall", "autumn", "Autumn"}:
        return f"Fall {year}"
    month_match = re.search(r"\d{4}-(\d{1,2})", value)
    if month_match:
        return ("Spring" if int(month_match.group(1)) <= 6 else "Fall") + f" {year}"
    return year


def teaching_sort_value(term: str) -> int:
    match = re.search(r"(Spring|Fall)?\s*((?:19|20)\d{2})", term, re.I)
    if not match:
        return 0
    weight = 2 if (match.group(1) or "").lower() == "fall" else 1 if (match.group(1) or "").lower() == "spring" else 0
    return int(match.group(2)) * 10 + weight


def slugify(text: str) -> str:
    return re.sub(r"(^-|-$)", "", re.sub(r"[^a-z0-9]+", "-", text.lower().replace("&", "and")))


def normalize_teaching(item: dict) -> dict:
    organizers = item.get("author", []) if item.get("type") == "standard" else item.get("organizer", []) + item.get("chair", [])
    contributors = item.get("contributor", []) + item.get("presenter", [])
    organizer_names = [csl_name(name) for name in organizers]
    contributor_names = [csl_name(name) for name in contributors]
    record_id = item.get("citation-key") or item.get("id") or slugify(item.get("title", "teaching"))
    user_organizer = any(is_benjamin_jarvis(name) for name in organizer_names)
    user_contributor = any(is_benjamin_jarvis(name) for name in contributor_names)
    teaching_type = item.get("genre") or "Teaching"
    if user_contributor and not user_organizer:
        role = "Guest Lecturer"
    elif user_organizer and re.search(r"program|programme", f"{teaching_type} {item.get('title', '')}", re.I):
        role = "Program Director"
    elif user_organizer:
        role = "Course Coordinator"
    else:
        role = teaching_type
    role = note_value(item.get("note", ""), "Role") or role
    return {
        "key": item.get("number") or slugify(item.get("title", "")),
        "title": item.get("title") or "Untitled course",
        "code": item.get("number") or item.get("title-short") or "",
        "program": item.get("authority") or item.get("event-title") or "",
        "institution": item.get("publisher") or item.get("collection-title") or "",
        "term": teaching_term(item.get("issued")),
        "role": role,
        "organizers": organizer_names,
        "abstract": item.get("abstract") or "",
        "url": item.get("URL") or "",
    }


def group_teaching(items: list[dict]) -> list[dict]:
    groups: dict[str, dict] = {}
    for item in map(normalize_teaching, items):
        group = groups.setdefault(item["key"], {"key": item["key"], "title": item["title"], "code": item["code"], "program": item["program"], "institution": item["institution"], "abstract": item["abstract"], "url": item["url"], "roles": []})
        if len(item["abstract"]) > len(group["abstract"]):
            group["abstract"] = item["abstract"]
        group["roles"].append(item)
    output = []
    for group in groups.values():
        group["roles"].sort(key=lambda role: teaching_sort_value(role["term"]), reverse=True)
        group["kind"] = "program" if re.search(r"program|programme", f"{group['title']} {group['roles'][0]['role']}", re.I) else "course"
        output.append(group)
    return sorted(output, key=lambda group: teaching_sort_value(group["roles"][0]["term"]), reverse=True)


def render_teaching(course: dict) -> str:
    latest = course["roles"][0]
    year = year_from_text(latest["term"])
    meta = eyebrow_parts(latest["role"], course["institution"])
    link = md_link(course["url"], course["url"]) if course["url"] else ""
    body = md_blocks([
        f"::: {{.content-card-detail .teaching-link}}\n{link}\n:::" if link else "",
    ])
    return render_content_card(
        ["teaching-card", "teaching-course"],
        identifier=slugify(course["key"] or course["title"]),
        eyebrow=eyebrow_parts(year or latest["term"], course["program"]),
        title=course["title"],
        byline=meta,
        description=md_paragraphs(course["abstract"] or "Course description forthcoming."),
        body=body,
    )


def teaching_date_range(roles: list[dict]) -> str:
    years = []
    for role in roles:
        match = re.search(r"(?:19|20)\d{2}", role.get("term", ""))
        if match:
            years.append(int(match.group(0)))
    if not years:
        return ""
    first = min(years)
    last = max(years)
    return str(last) if first == last else f"{first}-{last}"


def render_cv_teaching(course: dict) -> str:
    meta = " | ".join(part for part in [course["program"], course["institution"]] if part)
    roles = "\n\n".join(render_cv_history_row(role["term"], role["role"]) for role in course["roles"])
    return f"""::: {{.cv-entry}}
::: {{.cv-date}}
{md_escape(teaching_date_range(course["roles"]))}
:::

::: {{.cv-detail}}
### {md_escape(course["title"])}

{md_escape(meta) if meta else ""}

#### Teaching History {{.cv-history-heading}}

::: {{.cv-history .teaching-history}}
{roles}
:::
:::
:::"""


def render_teaching_list(courses: list[dict], kind: str | None = None, limit: int | None = None) -> str:
    selected = [course for course in courses if kind is None or course["kind"] == kind]
    if limit:
        selected = selected[:limit]
    return "\n\n".join(render_teaching(course) for course in selected) or "_No teaching entries found._"


def render_post_card(post: dict) -> str:
    categories = ", ".join(post.get("categories", []))
    eyebrow = eyebrow_parts(year_from_text(post.get("date", "")) or post.get("date", ""), categories)
    return render_content_card(
        ["post-card", "compact-card"],
        eyebrow=eyebrow,
        title_markdown=md_link(post.get("title", "Untitled post"), "blog/" + post.get("url", "")),
        byline=post.get("author", ""),
        description=md_paragraphs(post.get("description", "")),
    )


def parse_front_matter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n", text, flags=re.S)
    if not match:
        return {}
    meta: dict[str, object] = {}
    current_list: str | None = None
    for raw_line in match.group(1).splitlines():
        line = raw_line.rstrip()
        if not line.strip():
            continue
        list_item = re.match(r"^\s*-\s+(.+?)\s*$", line)
        if list_item and current_list:
            meta.setdefault(current_list, []).append(unquote_yaml_value(list_item.group(1)))
            continue
        key_value = re.match(r"^([A-Za-z0-9_-]+):\s*(.*?)\s*$", line)
        if not key_value:
            continue
        key, value = key_value.groups()
        if value:
            meta[key] = unquote_yaml_value(value)
            current_list = None
        else:
            meta[key] = []
            current_list = key
    return meta


def unquote_yaml_value(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        try:
            return json.loads(value) if value[0] == '"' else value[1:-1]
        except json.JSONDecodeError:
            return value[1:-1]
    return value


def discover_blog_posts() -> list[dict]:
    posts = []
    for path in sorted((ROOT / "blog").glob("*/index.qmd")):
        metadata = parse_front_matter(path)
        if not metadata:
            continue
        slug = path.parent.name
        metadata.setdefault("title", slug.replace("-", " ").title())
        metadata.setdefault("description", "")
        metadata.setdefault("date", "")
        metadata.setdefault("categories", [])
        metadata["slug"] = slug
        metadata["url"] = f"{slug}/"
        posts.append(metadata)
    return sorted(posts, key=lambda post: str(post.get("date", "")), reverse=True)


def split_cv_sections(cv_body: str) -> dict[str, str]:
    sections: dict[str, list[str]] = {}
    current: str | None = None
    for line in cv_body.splitlines():
        match = re.match(r"^##\s+(.+?)\s*$", line)
        if match:
            current = match.group(1).strip().lower()
            sections[current] = []
            continue
        if current:
            sections[current].append(line)
    return {key: "\n".join(value).strip() for key, value in sections.items()}


def render_cv_markdown_entries(markdown: str) -> str:
    entries = re.split(r"(?m)^###\s+", markdown.strip())
    rendered = []
    for entry in entries:
        entry = entry.strip()
        if not entry:
            continue
        lines = entry.splitlines()
        heading = lines[0].strip()
        body = "\n".join(lines[1:]).strip()
        if "|" in heading:
            date, title = [part.strip() for part in heading.split("|", 1)]
        else:
            date, title = "", heading
        date_markdown = md_line_breaks(date.split(";"))
        paragraphs = md_paragraphs(body)
        rendered.append(f"""::: {{.cv-entry}}
::: {{.cv-date}}
{date_markdown}
:::

::: {{.cv-detail}}
### {md_escape(title)}

{paragraphs}
:::
:::""")
    return "\n\n".join(rendered) or "_No entries found._"


def render_supervision(item: dict) -> str:
    student = name_list([csl_name(name) for name in item.get("author", [])])
    title = item.get("title") or "Untitled thesis"
    supervisors = name_list([csl_name(name) for name in item.get("contributor", [])])
    detail = ". ".join(part for part in [item.get("genre") or item.get("type"), item.get("publisher"), item.get("publisher-place")] if part)
    return f"""::: {{.cv-entry .supervision-entry}}
::: {{.cv-date}}
{md_escape(csl_year(item))}
:::

::: {{.cv-detail}}
::: {{.citation-line}}
{md_bold(student + ".")} {md_escape(title)}
:::

{f"Supervision: {md_escape(supervisors)}." if supervisors else ""}

{f"{md_escape(detail)}." if detail else ""}
:::
:::"""


def main() -> None:
    publications = sorted(load_json("data/publications.json"), key=sort_date_value, reverse=True)
    publication_assets = load_json("data/publication-assets.json")
    grants = group_grants(load_json("data/grants.json"))
    teaching = group_teaching(load_json("data/teaching.json"))
    supervision = sorted(load_json("data/supervision.json"), key=sort_date_value, reverse=True)
    posts = discover_blog_posts()
    cv_body = (ROOT / "cv" / "cv.md").read_text(encoding="utf-8")
    cv_sections = split_cv_sections(cv_body)

    write("index.qmd", render_template("index.qmd.j2", {
        "works_progress": render_publication_list(publications, "works-progress", publication_assets, limit=3),
        "selected_publications": render_publication_list(publications, "selected", publication_assets, limit=4),
        "ongoing_projects": render_grant_list(grants, "ongoing", limit=4),
        "selected_teaching": render_teaching_list(teaching, limit=3),
        "recent_posts": "\n\n".join(render_post_card(post) for post in posts[:3]) or "_No posts found._",
    }))
    write("publications.qmd", render_template("publications.qmd.j2", {
        "journal_articles": render_publication_list(publications, "journal-articles", publication_assets),
        "books_chapters": render_publication_list(publications, "books-chapters", publication_assets),
        "working_papers": render_publication_list(publications, "working-papers", publication_assets),
        "conference_presentations": render_publication_list(publications, "conference-presentations", publication_assets),
        "invited_talks": render_publication_list(publications, "invited-talks", publication_assets),
    }))
    write("projects.qmd", render_template("projects.qmd.j2", {
        "ongoing_projects": render_grant_list(grants, "ongoing"),
        "under_review_projects": render_grant_list(grants, "under-review"),
        "completed_projects": render_grant_list(grants, "completed"),
        "rejected_projects": render_grant_list(grants, "rejected"),
    }))
    write("teaching.qmd", render_template("teaching.qmd.j2", {
        "courses": render_teaching_list(teaching, kind="course"),
        "programs": render_teaching_list(teaching, kind="program"),
    }))
    write("cv.qmd", render_template("cv.qmd.j2", {
        "appointments": render_cv_markdown_entries(cv_sections.get("appointments", "")),
        "education": render_cv_markdown_entries(cv_sections.get("education", "")),
        "journal_articles": "\n\n".join(render_publication(item, compact=True) for item in filter_publications(publications, "journal-articles")),
        "books_chapters": "\n\n".join(render_publication(item, compact=True) for item in filter_publications(publications, "books-chapters")),
        "working_papers": "\n\n".join(render_publication(item, compact=True) for item in filter_publications(publications, "working-papers")),
        "conference_presentations": "\n\n".join(render_publication(item, compact=True) for item in filter_publications(publications, "conference-presentations")),
        "invited_talks": "\n\n".join(render_publication(item, compact=True) for item in filter_publications(publications, "invited-talks")),
        "cv_grants": "\n\n".join(render_cv_grant(group) for group in grants),
        "cv_teaching": "\n\n".join(render_cv_teaching(course) for course in teaching),
        "doctoral_supervision": "\n\n".join(render_supervision(item) for item in filter_publications(supervision, "supervision-doctoral")) or "_No entries found._",
        "masters_supervision": "\n\n".join(render_supervision(item) for item in filter_publications(supervision, "supervision-masters")) or "_No entries found._",
        "service": render_cv_markdown_entries(cv_sections.get("service", "")),
        "skills": render_cv_markdown_entries(cv_sections.get("skills", "")),
        "miscellaneous": render_cv_markdown_entries(cv_sections.get("miscellaneous", "")),
    }))
    write("blog/index.qmd", render_template("blog-index.qmd.j2", {}))


if __name__ == "__main__":
    main()
