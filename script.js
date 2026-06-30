const header = document.querySelector("[data-nav]");
const navToggle = document.querySelector(".nav-toggle");
const year = document.querySelector("[data-year]");
const publicationLightboxAssets = {};

const typeLabels = {
  article: "Preprint",
  "article-journal": "Journal Article",
  book: "Book",
  chapter: "Book Chapter",
  inbook: "Book Chapter",
  incollection: "Book Chapter",
  "paper-conference": "Conference Presentation",
  inproceedings: "Conference Paper",
  proceedings: "Conference Paper",
  manuscript: "Working Paper",
  speech: "Talk",
  unpublished: "Working Paper",
  report: "Report",
  techreport: "Report",
  phdthesis: "PhD Thesis",
  mastersthesis: "Master's Thesis",
  thesis: "Thesis",
  misc: "Presentation",
};

function setHeaderState() {
  header?.classList.toggle("is-scrolled", window.scrollY > 24);
}

setHeaderState();
window.addEventListener("scroll", setHeaderState, { passive: true });

navToggle?.addEventListener("click", () => {
  const isOpen = header.classList.toggle("is-open");
  navToggle.setAttribute("aria-expanded", String(isOpen));
});

document.querySelectorAll(".site-nav a").forEach((link) => {
  link.addEventListener("click", () => {
    header?.classList.remove("is-open");
    navToggle?.setAttribute("aria-expanded", "false");
  });
});

if (year) {
  year.textContent = String(new Date().getFullYear());
}

function escapeHtml(value = "") {
  return value.replace(/[&<>"']/g, (char) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
  })[char]);
}

function formatCvDate(date = "") {
  return date.split(";").map((part) => escapeHtml(part.trim())).filter(Boolean).join("<br>");
}

function isFilePreview() {
  return window.location.protocol === "file:";
}

function filePreviewMessage(kind) {
  return `
    <article class="publication-item is-empty">
      <p>
        ${kind} are loaded from local data files when the site is served over HTTP.
        For local preview, run <code>python3 -m http.server 8001</code> in the repo
        and open <code>http://localhost:8001/</code>.
      </p>
    </article>
  `;
}

function cslDateValue(date = {}) {
  if (date.literal) return date.literal;
  const parts = date["date-parts"]?.[0] || [];
  if (!parts.length) return "";
  return parts.map(String).join("-");
}

function normalizeCslItem(item = {}) {
  const fields = {
    title: item.title || "",
    author: item.author || [],
    editor: item.editor || [],
    date: cslDateValue(item.issued),
    year: cslDateValue(item.issued).slice(0, 4),
    journaltitle: item["container-title"] || "",
    journal: item["container-title"] || "",
    booktitle: item["container-title"] || "",
    eventtitle: item["event-title"] || "",
    location: item["event-place"] || item["publisher-place"] || "",
    publisher: item.publisher || "",
    school: item.publisher || "",
    volume: item.volume || "",
    number: item.issue || item.number || "",
    pages: item.page || "",
    doi: item.DOI || "",
    url: item.URL || "",
    abstract: item.abstract || "",
    note: item.note || "",
    annotation: item.note || "",
    type: item.genre || item.type || "",
    keywords: Array.isArray(item.keyword) ? item.keyword.join(", ") : (item.keyword || ""),
    source: item.source || "",
  };

  return {
    key: item["citation-key"] || item.id || "",
    type: item.type || "",
    fields,
    csl: item,
  };
}

function parseReferenceData(source = "") {
  const data = JSON.parse(source.trim());
  const items = Array.isArray(data) ? data : (data.items || []);
  return items.map(normalizeCslItem).sort((a, b) => sortDateValue(b) - sortDateValue(a));
}

function asaAuthorName(name = {}, invert = false) {
  if (name.literal) return name.literal;
  return [name.given, name.family].filter(Boolean).join(" ");
}

function joinNameList(names = []) {
  if (names.length < 2) return names.join("");
  if (names.length === 2) return `${names[0]} and ${names[1]}`;
  return `${names.slice(0, -1).join(", ")}, and ${names[names.length - 1]}`;
}

function citationAuthors(entry) {
  const authorField = entry.fields.author || entry.fields.editor || "";
  return citationNames(authorField);
}

function citationNames(authorField = "") {
  if (Array.isArray(authorField)) {
    return joinNameList(authorField.map((author) => asaAuthorName(author)).filter(Boolean));
  }

  return String(authorField || "").trim() || "Author information forthcoming";
}

function entryYear(entry) {
  const raw = entry.fields.date || entry.fields.year || "";
  const match = String(raw).match(/\d{4}/);
  return match ? match[0] : "Year";
}

function sortDateValue(entry) {
  const raw = entry.fields.date || entry.fields.year || "";
  const match = String(raw).match(/(\d{4})(?:-(\d{2}))?(?:-(\d{2}))?/);
  if (!match) return 0;
  return Number(`${match[1]}${match[2] || "00"}${match[3] || "00"}`);
}

function firstField(fields, names) {
  return names.map((name) => fields[name]).find(Boolean) || "";
}

function presentationVenue(entry) {
  const f = entry.fields;
  const host = firstField(f, [
    "eventtitle",
    "event",
    "booktitle",
    "organization",
    "institution",
    "school",
    "howpublished",
    "publisher",
  ]);
  const location = f.location || f.address || "";
  const type = f.type || "";

  if (host && location) return `${host}, ${location}`;
  if (host) return host;
  if (type && location) return `${type}, ${location}`;
  return location || type;
}

function publicationVenue(entry) {
  const f = entry.fields;
  if (isConferencePresentation(entry) || isInvitedTalk(entry)) {
    return presentationVenue(entry);
  }

  const venue = firstField(f, ["journaltitle", "journal", "booktitle", "publisher", "school"]);
  const location = f.location || f.address || "";

  if (venue && (["book", "inbook", "incollection", "chapter"].includes(entry.type) || isThesis(entry)) && location) {
    return `${venue}, ${location}`;
  }

  return venue || f.note || location || "";
}

function citationFor(entry) {
  const f = entry.fields;
  const authorText = citationAuthors(entry);
  const venue = publicationVenue(entry);
  const rawDoi = f.doi || "";
  const doiUrl = rawDoi ? (rawDoi.startsWith("http") ? rawDoi : `https://doi.org/${rawDoi}`) : "";
  const url = !doiUrl && f.url ? f.url : "";
  const title = f.title || "Untitled publication";
  const isChapter = ["chapter", "inbook", "incollection"].includes(entry.type);
  const quotedTitle = ["article", "article-journal", "paper-conference", "speech"].includes(entry.type) || isWorkingPaper(entry) || isChapter;
  const titleHtml = quotedTitle ? `"${escapeHtml(title)}."` : `<em>${escapeHtml(title)}.</em>`;
  const volumeIssue = f.volume
    ? `${escapeHtml(f.volume)}${f.number ? `(${escapeHtml(f.number)})` : ""}`
    : "";
  const pages = f.pages ? `${volumeIssue ? ":" : ""}${escapeHtml(f.pages)}` : "";
  const editorText = f.editor?.length ? citationNames(f.editor) : "";
  const chapterBook = [
    f.pages && `Pp. ${escapeHtml(f.pages)} in`,
    f.booktitle && `<em>${escapeHtml(f.booktitle)}</em>`,
  ].filter(Boolean).join(" ");
  const chapterParts = isChapter ? [
    chapterBook,
    editorText && `edited by ${escapeHtml(editorText)}`,
    [f.location, f.publisher].filter(Boolean).map(escapeHtml).join(": "),
  ].filter(Boolean) : [];
  const venueAndVolume = !isChapter && venue
    ? `<em>${escapeHtml(venue)}</em>${volumeIssue || pages ? ` ${volumeIssue}${pages}` : ""}`
    : !isChapter ? `${volumeIssue}${pages}` : "";
  const venueParts = [
    ...(isChapter ? [chapterParts.join(", ")] : [venueAndVolume]),
    doiUrl && `<a href="${escapeHtml(doiUrl)}">[Link]</a>`,
    url && `<a href="${escapeHtml(url)}">[Link]</a>`,
  ].filter(Boolean);
  const fullCitation = `${escapeHtml(authorText)}. ${entryYear(entry)}. ${titleHtml}${venueParts.length ? ` ${venueParts.join(", ")}.` : ""}`;

  return {
    authors: authorText,
    title,
    year: entryYear(entry),
    label: isPhdThesis(entry)
      ? "PhD Thesis"
      : isMasterThesis(entry)
        ? "Master's Thesis"
        : isWorkingPaper(entry)
          ? "Working Paper / Preprint"
          : (typeLabels[entry.type] || entry.type),
    detail: venueParts.join(", "),
    fullCitation,
    abstract: f.abstract || "",
    extra: f.note || f.annotation || f.annote || f.extra || "",
    doi: f.doi || "",
    url: f.url || "",
    keywords: (f.keywords || "").toLowerCase(),
    entryType: (f.type || "").toLowerCase(),
    annotation: (f.annotation || "").toLowerCase(),
  };
}

function isInvitedTalk(entry) {
  const f = entry.fields;
  const entryType = (f.type || "").toLowerCase();
  return (
    entry.type === "speech" && !entryType.includes("conference")
  ) || (f.annotation || "").toLowerCase().includes("invited") || entryType.includes("invited");
}

function isWorkingPaper(entry) {
  const f = entry.fields;
  const entryType = (f.type || "").toLowerCase();
  const source = [f.source, f.publisher, f.url].join(" ").toLowerCase();
  return (
    entry.type === "unpublished" ||
    entry.type === "preprint" ||
    entry.type === "manuscript" ||
    entryType.includes("working") ||
    entryType.includes("preprint") ||
    source.includes("preprint") ||
    source.includes("socarxiv") ||
    source.includes("osf")
  );
}

function isConferencePresentation(entry) {
  const entryType = (entry.fields.type || "").toLowerCase();
  return (
    entry.type === "inproceedings" ||
    entry.type === "proceedings" ||
    entry.type === "paper-conference" ||
    entryType.includes("conference") ||
    (entry.type === "misc" && !isInvitedTalk(entry) && !isWorkingPaper(entry))
  );
}

function isThesis(entry) {
  const entryType = (entry.fields.type || "").toLowerCase();
  return (
    ["phdthesis", "mastersthesis", "thesis"].includes(entry.type) ||
    entryType.includes("thesis") ||
    entryType.includes("dissertation")
  );
}

function isMasterThesis(entry) {
  const entryType = (entry.fields.type || "").toLowerCase();
  return isThesis(entry) && !entryType.includes("dissertation") && !entryType.includes("phd");
}

function isPhdThesis(entry) {
  const entryType = (entry.fields.type || "").toLowerCase();
  return isThesis(entry) && (entryType.includes("dissertation") || entryType.includes("phd"));
}

function filterEntries(entries, mode) {
  const filters = {
    selected: (entry) => {
      const selected = citationFor(entry).keywords.includes("selected");
      const publicType = ["article", "article-journal", "book", "inbook", "incollection", "chapter"].includes(entry.type);
      return selected && publicType && !isWorkingPaper(entry);
    },
    "journal-articles": (entry) => (entry.type === "article" || entry.type === "article-journal") && !isWorkingPaper(entry),
    "books-chapters": (entry) => ["book", "inbook", "incollection", "chapter"].includes(entry.type),
    "works-progress": isWorkingPaper,
    "working-papers": isWorkingPaper,
    "conference-presentations": (entry) => isConferencePresentation(entry) && !isInvitedTalk(entry),
    "invited-talks": isInvitedTalk,
    theses: isThesis,
    supervision: isThesis,
    "supervision-doctoral": isPhdThesis,
    "supervision-masters": isMasterThesis,
  };

  const filter = filters[mode];
  return filter ? entries.filter(filter) : entries;
}

function featuredEntries(entries) {
  const selected = filterEntries(entries, "selected")
    .slice(0, 4);

  if (selected.length) return selected;

  return entries
    .filter((entry) => ["article", "article-journal", "book", "inbook", "incollection", "chapter"].includes(entry.type) && !isWorkingPaper(entry))
    .slice(0, 4);
}

function publicationImagesFor(asset = {}) {
  if (Array.isArray(asset.images) && asset.images.length) {
    return asset.images;
  }

  if (asset.image) {
    return [{
      image: asset.image,
      alt: asset.alt || "",
      caption: asset.caption || "",
    }];
  }

  return [];
}

function resolveAssetPath(path = "") {
  if (!path || /^(https?:)?\/\//.test(path) || path.startsWith("/") || path.startsWith("../")) {
    return path;
  }

  return document.querySelector('script[src^="../"]') ? `../${path}` : path;
}

function renderPublicationItem(entry, compact = false, publicationAssets = {}) {
  const citation = citationFor(entry);
  const asset = publicationAssets[entry.key];
  const images = publicationImagesFor(asset);

  if (compact) {
    return `
      <div class="cv-entry">
        <span class="date">${escapeHtml(citation.year)}</span>
        <div>
          <p class="citation-line">${citation.fullCitation}${citation.extra ? ` ${escapeHtml(citation.extra)}` : ""}</p>
        </div>
      </div>
    `;
  }

  return `
    <article class="publication-item${images.length ? " has-image" : ""}">
      <div class="publication-meta">
        <p class="meta">${escapeHtml(citation.label)} · ${escapeHtml(citation.year)}</p>
        ${images.length ? `
          <button class="publication-media" type="button" data-lightbox-key="${escapeHtml(entry.key)}" aria-label="View image for ${escapeHtml(citation.title)}">
            <img src="${escapeHtml(resolveAssetPath(images[0].image))}" alt="${escapeHtml(images[0].alt || "")}">
            ${images.length > 1 ? `<span>${images.length} images</span>` : ""}
          </button>
        ` : ""}
      </div>
      <div>
        <p class="citation-line">${citation.fullCitation}</p>
        ${citation.extra ? `<p>${escapeHtml(citation.extra)}</p>` : ""}
        ${citation.abstract ? `<p>${escapeHtml(citation.abstract)}</p>` : ""}
      </div>
    </article>
  `;
}

async function renderPublications() {
  const targets = document.querySelectorAll("[data-publications]");
  if (!targets.length) return;

  if (isFilePreview()) {
    targets.forEach((target) => {
      target.innerHTML = filePreviewMessage("Publications");
    });
    return;
  }

  try {
    targets.forEach((target) => {
      const source = target.dataset.cslSource || resolveAssetPath("data/publications.json");
      const assetsSource = target.dataset.assetsSource
        || (source.startsWith("../")
          ? "../data/publication-assets.json?v=20260630-publication-data"
          : "data/publication-assets.json?v=20260630-publication-data");

      Promise.all([
        fetch(source).then((response) => response.text()),
        fetch(assetsSource).then((response) => response.ok ? response.json() : {}).catch(() => ({})),
      ])
        .then(([referenceText, publicationAssets]) => {
          Object.assign(publicationLightboxAssets, publicationAssets);
          const entries = parseReferenceData(referenceText);
          const mode = target.dataset.publications;
          const selected = mode === "selected"
            ? featuredEntries(entries)
            : filterEntries(entries, mode);

          if (!selected.length) {
            target.innerHTML = '<article class="publication-item is-empty"><p>No entries found for this section.</p></article>';
            return;
          }

          target.innerHTML = selected
            .map((entry) => renderPublicationItem(entry, target.classList.contains("cv-publications"), publicationAssets, source))
            .join("");
        })
        .catch(() => {
          target.innerHTML = '<article class="publication-item is-empty"><p>Publication list could not be loaded.</p></article>';
        });
    });
  } catch {
    targets.forEach((target) => {
      target.innerHTML = '<article class="publication-item is-empty"><p>Publication list could not be loaded.</p></article>';
    });
  }
}

function ensureLightbox() {
  let lightbox = document.querySelector("[data-publication-lightbox]");
  if (lightbox) return lightbox;

  document.body.insertAdjacentHTML("beforeend", `
    <div class="publication-lightbox" data-publication-lightbox hidden>
      <div class="publication-lightbox-panel" role="dialog" aria-modal="true" aria-label="Publication image viewer">
        <button class="lightbox-close" type="button" data-lightbox-close aria-label="Close image viewer">Close</button>
        <button class="lightbox-nav lightbox-prev" type="button" data-lightbox-prev aria-label="Previous image">Prev</button>
        <figure>
          <img data-lightbox-image alt="">
          <figcaption data-lightbox-caption></figcaption>
        </figure>
        <button class="lightbox-nav lightbox-next" type="button" data-lightbox-next aria-label="Next image">Next</button>
      </div>
    </div>
  `);

  lightbox = document.querySelector("[data-publication-lightbox]");
  lightbox.addEventListener("click", (event) => {
    if (event.target === lightbox || event.target.closest("[data-lightbox-close]")) {
      closePublicationLightbox();
    }
    if (event.target.closest("[data-lightbox-prev]")) {
      stepPublicationLightbox(-1);
    }
    if (event.target.closest("[data-lightbox-next]")) {
      stepPublicationLightbox(1);
    }
  });

  document.addEventListener("keydown", (event) => {
    if (lightbox.hidden) return;
    if (event.key === "Escape") closePublicationLightbox();
    if (event.key === "ArrowLeft") stepPublicationLightbox(-1);
    if (event.key === "ArrowRight") stepPublicationLightbox(1);
  });

  return lightbox;
}

function setLightboxImage(lightbox, images, index) {
  const image = images[index];
  lightbox.dataset.index = String(index);
  lightbox.querySelector("[data-lightbox-image]").src = resolveAssetPath(image.image);
  lightbox.querySelector("[data-lightbox-image]").alt = image.alt || "";
  lightbox.querySelector("[data-lightbox-caption]").textContent = image.caption || "";
  lightbox.querySelector("[data-lightbox-prev]").hidden = images.length < 2;
  lightbox.querySelector("[data-lightbox-next]").hidden = images.length < 2;
}

function openPublicationLightbox(key) {
  const images = publicationImagesFor(publicationLightboxAssets[key]);
  if (!images.length) return;

  const lightbox = ensureLightbox();
  lightbox.dataset.key = key;
  lightbox.hidden = false;
  setLightboxImage(lightbox, images, 0);
  lightbox.querySelector("[data-lightbox-close]")?.focus();
}

function closePublicationLightbox() {
  const lightbox = document.querySelector("[data-publication-lightbox]");
  if (lightbox) {
    lightbox.hidden = true;
  }
}

function stepPublicationLightbox(direction) {
  const lightbox = document.querySelector("[data-publication-lightbox]");
  if (!lightbox || lightbox.hidden) return;

  const images = publicationImagesFor(publicationLightboxAssets[lightbox.dataset.key]);
  if (images.length < 2) return;

  const current = Number(lightbox.dataset.index || 0);
  const next = (current + direction + images.length) % images.length;
  setLightboxImage(lightbox, images, next);
}

document.addEventListener("click", (event) => {
  const trigger = event.target.closest("[data-lightbox-key]");
  if (trigger) {
    openPublicationLightbox(trigger.dataset.lightboxKey);
  }
});

function grantStatusLabel(status = "") {
  return status === "completed" ? "Completed" : "Ongoing";
}

function renderGrantItem(grant, compact = false) {
  const title = escapeHtml(grant.title || "Untitled grant");
  const page = compact ? grant.page : grant.page?.replace(/^grants\//, "");
  const titleHtml = grant.page
    ? `<a href="${escapeHtml(page)}">${title}</a>`
    : title;
  const meta = [grant.dates, grant.funder, grant.role].filter(Boolean).map(escapeHtml).join(" · ");

  if (compact) {
    return `
      <article>
        <span>${escapeHtml(grantStatusLabel(grant.status))} · ${escapeHtml(grant.dates || "")}</span>
        <h3>${titleHtml}</h3>
        <p>${escapeHtml(grant.summary || "")}</p>
      </article>
    `;
  }

  return `
    <article class="grant-card">
      ${grant.image ? `<img src="../${escapeHtml(grant.image)}" alt="">` : ""}
      <div>
        <p class="meta">${escapeHtml(grantStatusLabel(grant.status))}${meta ? ` · ${meta}` : ""}</p>
        <h3>${titleHtml}</h3>
        <p>${escapeHtml(grant.summary || "")}</p>
        ${grant.amount ? `<p><strong>Amount:</strong> ${escapeHtml(grant.amount)}</p>` : ""}
      </div>
    </article>
  `;
}

function cslName(name = {}) {
  if (name.literal) return name.literal;
  return [name.given, name.family].filter(Boolean).join(" ");
}

function noteValue(note = "", label = "") {
  const prefix = `${label}:`;
  const line = note.split(/\r?\n/).find((part) => part.startsWith(prefix));
  return line ? line.slice(prefix.length).trim() : "";
}

function teachingSortValue(term = "") {
  const match = String(term).match(/(Spring|Fall)?\s*((?:19|20)\d{2})/i);
  if (!match) return 0;
  const year = Number(match[2]);
  const termWeight = match[1]?.toLowerCase() === "fall" ? 2 : match[1]?.toLowerCase() === "spring" ? 1 : 0;
  return year * 10 + termWeight;
}

function teachingSummary(text = "") {
  const clean = text.replace(/\s+/g, " ").trim();
  if (clean.length <= 240) return clean;
  return `${clean.slice(0, 237).replace(/\s+\S*$/, "")}...`;
}

function normalizeTeachingRecord(item = {}) {
  const note = item.note || "";
  return {
    id: item["citation-key"] || item.id || slugify(item.title || "teaching"),
    title: item.title || "Untitled course",
    code: item["title-short"] || "",
    program: item["collection-title"] || "",
    institution: item["event-title"] || "",
    term: cslDateValue(item.issued) || "",
    role: noteValue(note, "Role") || item.genre || "Teaching",
    preciseDates: noteValue(note, "Precise date(s)"),
    credits: noteValue(note, "Credits"),
    students: noteValue(note, "Students"),
    hours: noteValue(note, "Teaching hours"),
    organizers: (item.organizer || []).map(cslName).filter(Boolean),
    presenters: (item.presenter || []).map(cslName).filter(Boolean),
    abstract: item.abstract || "",
    url: item.URL || "",
  };
}

function groupTeachingRecords(items = []) {
  const groups = new Map();

  items.map(normalizeTeachingRecord).forEach((record) => {
    const key = record.code || slugify(record.title);
    if (!groups.has(key)) {
      groups.set(key, {
        key,
        title: record.title,
        code: record.code,
        program: record.program,
        institution: record.institution,
        abstract: record.abstract,
        url: record.url,
        roles: [],
      });
    }

    const group = groups.get(key);
    group.program ||= record.program;
    group.institution ||= record.institution;
    group.url ||= record.url;
    if (record.abstract.length > group.abstract.length) group.abstract = record.abstract;
    group.roles.push(record);
  });

  return Array.from(groups.values()).map((group) => {
    group.roles.sort((a, b) => teachingSortValue(b.term) - teachingSortValue(a.term));
    group.latest = group.roles[0]?.term || "";
    group.latestValue = teachingSortValue(group.latest);
    group.kind = group.roles.some((role) => /program|programme/i.test(role.role))
      || (!group.code && /program|programme/i.test(group.title))
      ? "program"
      : "course";
    return group;
  }).sort((a, b) => b.latestValue - a.latestValue || a.title.localeCompare(b.title));
}

function isBenjaminJarvis(name = "") {
  return /benjamin\s+f\.?\s+jarvis/i.test(name) || /benjamin\s+jarvis/i.test(name);
}

function teachingRoleLabel(role) {
  const baseRole = role.role || "Teaching";
  const otherOrganizers = role.organizers.filter((name) => !isBenjaminJarvis(name));
  const userIsOrganizer = role.organizers.some(isBenjaminJarvis);

  if (!otherOrganizers.length) return baseRole;
  if (userIsOrganizer) return `${baseRole} (With ${otherOrganizers.join(", ")})`;
  return `${baseRole} (Coordinator: ${otherOrganizers.join(", ")})`;
}

function renderTeachingRole(role) {
  const label = teachingRoleLabel(role);

  return `
    <li>
      <span class="role-term">${escapeHtml(role.term || "Date forthcoming")}</span>
      <span class="role-title">${escapeHtml(label)}</span>
    </li>
  `;
}

function renderTeachingCourse(course, compact = false) {
  const meta = [course.program, course.institution].filter(Boolean).map(escapeHtml).join(" · ");
  const roleSummary = course.roles
    .map((role) => `${role.term} (${role.role})`)
    .filter(Boolean)
    .join("; ");

  if (compact) {
    return `
      <article class="teaching-card">
        <p class="meta">${escapeHtml(course.latest || "")}</p>
        <h3>${escapeHtml(course.title)}</h3>
        ${course.abstract ? `<p>${escapeHtml(teachingSummary(course.abstract))}</p>` : ""}
        ${roleSummary ? `<p class="teaching-role-summary">${escapeHtml(roleSummary)}</p>` : ""}
      </article>
    `;
  }

  return `
    <article class="teaching-course" id="${escapeHtml(course.key)}">
      <aside class="teaching-course-meta">
        ${meta ? `<p>${meta}</p>` : ""}
      </aside>
      <div class="teaching-course-body">
        <header>
          <h3>${escapeHtml(course.title)}</h3>
          ${course.url ? `<p><a class="text-link" href="${escapeHtml(course.url)}">${escapeHtml(course.url)}</a></p>` : ""}
        </header>
        <p>${escapeHtml(course.abstract || "Course description forthcoming.")}</p>
        <div class="teaching-subsection">
          <h4>Roles</h4>
          <ul class="role-list">
            ${course.roles.map(renderTeachingRole).join("")}
          </ul>
        </div>
      </div>
    </article>
  `;
}

async function renderGrants() {
  const targets = document.querySelectorAll("[data-grants]");
  if (!targets.length) return;

  if (isFilePreview()) {
    targets.forEach((target) => {
      target.innerHTML = target.classList.contains("timeline")
        ? "<article><span>Local preview</span><h3>Project data needs a local server</h3><p>Run <code>python3 -m http.server 8001</code> and open <code>http://localhost:8001/</code> to load projects from <code>data/grants.json</code>.</p></article>"
        : filePreviewMessage("Projects");
    });
    return;
  }

  targets.forEach((target) => {
    fetch(target.dataset.grantsSource || "data/grants.json")
      .then((response) => response.json())
      .then((grants) => {
        const mode = target.dataset.grants;
        const selected = grants.filter((grant) => mode === "all" || grant.status === mode);

        if (!selected.length) {
          target.innerHTML = "<p>No projects found for this section.</p>";
          return;
        }

        target.innerHTML = selected
          .map((grant) => renderGrantItem(grant, target.classList.contains("timeline")))
          .join("");
      })
      .catch(() => {
        target.innerHTML = "<p>Project list could not be loaded.</p>";
      });
  });
}

async function renderTeaching() {
  const targets = document.querySelectorAll("[data-teaching]");
  if (!targets.length) return;

  if (isFilePreview()) {
    targets.forEach((target) => {
      target.innerHTML = '<article class="teaching-card"><h3>Teaching data needs a local server</h3><p>Run <code>python3 -m http.server 8001</code> and open <code>http://localhost:8001/</code> to load teaching from <code>data/teaching-csl.json</code>.</p></article>';
    });
    return;
  }

  targets.forEach((target) => {
    fetch(target.dataset.teachingSource || "data/teaching-csl.json")
      .then((response) => response.json())
      .then((items) => {
        const courses = groupTeachingRecords(items);
        const kind = target.dataset.teachingKind;
        const teachingItems = kind ? courses.filter((course) => course.kind === kind) : courses;
        const selected = target.dataset.teaching === "selected"
          ? teachingItems.slice(0, 3)
          : teachingItems;

        if (!selected.length) {
          target.innerHTML = '<article class="teaching-card"><p>No teaching entries found.</p></article>';
          return;
        }

        target.innerHTML = selected
          .map((course) => renderTeachingCourse(course, target.dataset.teaching === "selected"))
          .join("");
      })
      .catch(() => {
        target.innerHTML = '<article class="teaching-card"><p>Teaching list could not be loaded.</p></article>';
      });
  });
}

function slugify(text) {
  return text.toLowerCase().replace(/&/g, "and").replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
}

function normalizeCvSectionSlug(slug) {
  const aliases = {
    "service-skills-etc": "service-and-skills",
  };
  return aliases[slug] || slug;
}

function parseCvMarkdown(markdown) {
  const sections = {};
  const lines = markdown.split(/\r?\n/);
  let current = null;
  let currentEntry = null;

  for (const rawLine of lines) {
    const line = rawLine.trim();
    if (!line || line.startsWith("# ")) continue;

    if (line.startsWith("## ")) {
      current = normalizeCvSectionSlug(slugify(line.slice(3)));
      sections[current] = [];
      currentEntry = null;
      continue;
    }

    if (line.startsWith("### ") && current) {
      const [date, ...headingParts] = line.slice(4).split("|");
      currentEntry = {
        date: date.trim(),
        heading: headingParts.join("|").trim(),
        detail: [],
      };
      sections[current].push(currentEntry);
      continue;
    }

    if (currentEntry) {
      currentEntry.detail.push(line);
    }
  }

  return sections;
}

async function renderCvMarkdown() {
  const source = document.querySelector("[data-cv-source]");
  if (!source) return;

  try {
    const response = await fetch(source.dataset.cvSource);
    const sections = parseCvMarkdown(await response.text());

    document.querySelectorAll("[data-cv-section]").forEach((section) => {
      const entries = sections[section.dataset.cvSection];
      if (!entries?.length) return;

      const heading = section.querySelector("h2")?.outerHTML || "";
      section.innerHTML = `${heading}${entries.map((entry) => `
        <div class="cv-entry">
          <span class="date">${formatCvDate(entry.date)}</span>
          <div>
            <h3>${escapeHtml(entry.heading)}</h3>
            <p>${escapeHtml(entry.detail.join(" "))}</p>
          </div>
        </div>
      `).join("")}`;
    });
  } catch {
    source.insertAdjacentHTML("afterbegin", '<p>CV source could not be loaded.</p>');
  }
}

renderPublications();
renderCvMarkdown();
renderGrants();
renderTeaching();
