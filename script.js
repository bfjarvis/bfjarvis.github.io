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

function cslSeasonLabel(season) {
  if (typeof season === "string") {
    const normalized = season.toLowerCase();
    if (normalized.includes("spring")) return "Spring";
    if (normalized.includes("summer")) return "Summer";
    if (normalized.includes("fall") || normalized.includes("autumn")) return "Fall";
    if (normalized.includes("winter")) return "Winter";
  }
  return {
    1: "Spring",
    2: "Summer",
    3: "Fall",
    4: "Winter",
  }[Number(season)] || "";
}

function teachingTermFromMonth(month) {
  const value = Number(month);
  if (!value) return "";
  return value <= 6 ? "Spring" : "Fall";
}

function teachingTermFromLiteral(value = "") {
  const year = String(value).match(/(?:19|20)\d{2}/)?.[0] || "";
  if (!year) return "";
  const monthNames = {
    january: 1,
    february: 2,
    march: 3,
    april: 4,
    may: 5,
    june: 6,
    july: 7,
    august: 8,
    september: 9,
    october: 10,
    november: 11,
    december: 12,
  };
  const lower = String(value).toLowerCase();
  const monthName = Object.keys(monthNames).find((name) => lower.includes(name));
  const term = monthName ? teachingTermFromMonth(monthNames[monthName]) : "";
  return term ? `${term} ${year}` : year;
}

function teachingDateValue(date = {}) {
  if (date.literal) return teachingTermFromLiteral(date.literal) || date.literal;
  const parts = date["date-parts"]?.[0] || [];
  if (!parts.length) return "";
  const season = cslSeasonLabel(date.season);
  if (season && parts.length === 1) return `${season} ${parts[0]}`;
  if (parts.length > 1) {
    const term = teachingTermFromMonth(parts[1]);
    return term ? `${term} ${parts[0]}` : String(parts[0]);
  }
  return parts.map(String).join("-");
}

function normalizeCslItem(item = {}) {
  const fields = {
    title: item.title || "",
    author: item.author || [],
    editor: item.editor || [],
    contributor: item.contributor || [],
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

function formatNameList(names = []) {
  if (names.length < 2) return names.join("");
  if (names.length === 2) return `${names[0]} and ${names[1]}`;
  return `${names.slice(0, -1).join(", ")}, and ${names[names.length - 1]}`;
}

function isBenjaminJarvisName(name = "") {
  return /benjamin\s+f\.?\s+jarvis/i.test(name) || /benjamin\s+jarvis/i.test(name);
}

function cslNameList(people = [], { excludeSelf = false } = {}) {
  const names = people
    .map((person) => asaAuthorName(person))
    .filter(Boolean)
    .filter((name) => !excludeSelf || !isBenjaminJarvisName(name));
  return formatNameList(names);
}

function supervisionNameList(entry) {
  const contributors = entry.fields.contributor || [];
  const names = contributors
    .map((person, index) => {
      const name = asaAuthorName(person);
      if (!name) return "";
      return isPhdThesis(entry) && index === 0 ? `${name} (Main)` : name;
    })
    .filter(Boolean);
  return formatNameList(names);
}

function citationAuthors(entry) {
  const authorField = entry.fields.author || entry.fields.editor || "";
  return citationNames(authorField);
}

function citationNames(authorField = "") {
  if (Array.isArray(authorField)) {
    return cslNameList(authorField);
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

function supervisionRoleDetail(entry) {
  const f = entry.fields;
  return [
    f.type || (isPhdThesis(entry) ? "Dissertation" : "Master's thesis"),
    f.publisher,
    f.location,
  ].filter(Boolean).map(escapeHtml).join(". ");
}

function renderSupervisionItem(entry) {
  const f = entry.fields;
  const student = citationNames(f.author);
  const title = f.title || "Untitled thesis";
  const detail = supervisionRoleDetail(entry);
  const supervisors = supervisionNameList(entry);

  return `
    <div class="cv-entry">
      <span class="date">${escapeHtml(entryYear(entry))}</span>
      <div>
        <h3>${escapeHtml(student)}. ${escapeHtml(title)}</h3>
        ${supervisors ? `<p class="supervision-line">Supervision: ${escapeHtml(supervisors)}.</p>` : ""}
        ${detail ? `<p>${detail}.</p>` : ""}
      </div>
    </div>
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
            .map((entry) => mode?.startsWith("supervision")
              ? renderSupervisionItem(entry)
              : renderPublicationItem(entry, target.classList.contains("cv-publications"), publicationAssets, source))
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

function cslName(name = {}) {
  if (name.literal) return name.literal;
  return [name.given, name.family].filter(Boolean).join(" ");
}

function noteValue(note = "", label = "") {
  const prefix = `${label}:`;
  const line = note.split(/\r?\n/).find((part) => part.startsWith(prefix));
  return line ? line.slice(prefix.length).trim() : "";
}

function cslDateYear(item = {}) {
  return cslDateValue(item.issued).slice(0, 4) || "Year";
}

function grantDecision(item = {}) {
  return noteValue(item.note || "", "Decision");
}

function grantBudget(item = {}) {
  return noteValue(item.note || "", "Budget");
}

function grantSeriesTitle(item = {}) {
  return item["collection-title"] || item["series-title"] || item.series || item.seriesTitle || "";
}

function grantDecisionLabel(item = {}) {
  const decision = grantDecision(item);
  if (!decision) return "Pending";
  if (/granted|needs audit closed/i.test(decision)) return "Accepted";
  if (/rejected|not accepted/i.test(decision)) return "Rejected";
  return decision;
}

function isAcceptedGrant(item = {}) {
  return /granted|needs audit closed/i.test(grantDecision(item));
}

function grantGroupKey(item = {}) {
  return item["title-short"] || item.shortTitle || item.title || "Untitled project";
}

function grantLifecycle(items = []) {
  const decisions = items.map(grantDecision).join(" | ").toLowerCase();
  const statuses = items.map((item) => String(item.status || "")).join(" | ").toLowerCase();

  if (/\bopen\b/.test(statuses)) {
    return "ongoing";
  }
  if (/finally registered|submitted|registered|pending|under review/.test(statuses) || items.some((item) => !grantDecision(item))) {
    return "under-review";
  }
  if (/granted|needs audit closed/.test(decisions)) {
    return "completed";
  }
  return "rejected";
}

function grantLifecycleLabel(lifecycle = "") {
  return {
    ongoing: "Ongoing",
    "under-review": "Under Review",
    completed: "Completed",
    rejected: "Rejected",
  }[lifecycle] || "Project";
}

function grantSortValue(item = {}) {
  const parts = item.issued?.["date-parts"]?.[0] || [];
  if (parts.length) {
    const [year = 0, month = 0, day = 0] = parts.map((part) => Number(part) || 0);
    return year * 10000 + month * 100 + day;
  }
  return (Number(cslDateYear(item).replace(/\D/g, "")) || 0) * 10000;
}

function grantNumberSortValue(item = {}) {
  const raw = String(item.number || "");
  const numbers = raw.match(/\d+/g);
  return numbers ? Number(numbers.join("")) : grantSortValue(item);
}

function sortGrantRecords(records = []) {
  return [...records].sort((a, b) => {
    if (isAcceptedGrant(a) !== isAcceptedGrant(b)) return isAcceptedGrant(a) ? -1 : 1;
    return grantNumberSortValue(b) - grantNumberSortValue(a) || String(a.title || "").localeCompare(b.title || "");
  });
}

function displayGrantRecord(records = []) {
  const accepted = records.filter(isAcceptedGrant).sort((a, b) => grantSortValue(b) - grantSortValue(a));
  return accepted[0] || [...records].sort((a, b) => grantSortValue(b) - grantSortValue(a))[0] || {};
}

function groupGrants(grants = []) {
  const groups = new Map();
  grants.forEach((grant) => {
    const key = grantGroupKey(grant);
    if (!groups.has(key)) {
      groups.set(key, {
        key,
        title: key,
        records: [],
      });
    }
    groups.get(key).records.push(grant);
  });

  return Array.from(groups.values()).map((group) => {
    group.records = sortGrantRecords(group.records);
    group.lifecycle = grantLifecycle(group.records);
    group.display = displayGrantRecord(group.records);
    group.latest = [...group.records].sort((a, b) => grantSortValue(b) - grantSortValue(a))[0];
    group.latestYear = grantSortValue(group.latest);
    return group;
  }).sort((a, b) => b.latestYear - a.latestYear || a.title.localeCompare(b.title));
}

function grantParticipantNames(item = {}, mainLabel = "PI") {
  const applicants = item.author || [];
  const contributors = item.contributor || [];
  const mainApplicant = cslName(applicants[0]);
  const otherParticipants = [
    ...applicants.slice(1).map(cslName),
    ...contributors.map(cslName),
  ].filter(Boolean);
  const names = [];

  if (mainApplicant) names.push(`${mainApplicant} (${mainLabel})`);
  names.push(...otherParticipants);
  return formatNameList(names);
}

function renderGrantApplicants(item = {}, mainLabel = "PI") {
  const names = grantParticipantNames(item, mainLabel);
  return names ? escapeHtml(names) : "";
}

function renderGrantNumberBudget(item = {}) {
  const parts = [];
  const budget = grantBudget(item);

  if (item.number) parts.push(`Project Number: ${item.number}`);
  if (budget) parts.push(`Budget: ${budget}`);
  return parts.map(escapeHtml).join(", ");
}

function grantFunderCall(item = {}) {
  const parts = [];

  if (item.publisher) parts.push(item.publisher);
  if (grantSeriesTitle(item)) parts.push(grantSeriesTitle(item));
  return parts.map(escapeHtml).join(" · ");
}

function renderGrantHistoryItem(item = {}) {
  return `
    <li class="grant-history-item">
      <span class="grant-history-year">${escapeHtml(cslDateYear(item))}</span>
      <span class="grant-history-decision">${escapeHtml(grantDecisionLabel(item))}</span>
      <span class="grant-history-funder">${grantFunderCall(item)}</span>
    </li>
  `;
}

function renderGrantGroup(group, compact = false) {
  const display = group.display || group.latest || {};
  const latestMeta = [grantLifecycleLabel(group.lifecycle), cslDateYear(display), display.publisher].filter(Boolean).map(escapeHtml).join(" · ");
  const funderCall = grantFunderCall(display);
  const numberBudget = renderGrantNumberBudget(display);
  const participants = renderGrantApplicants(display);
  const abstract = display.abstract || "";

  if (compact) {
    return `
      <article>
        <span>${latestMeta}</span>
        <h3>${escapeHtml(display.title || group.title)}</h3>
        ${abstract ? `<p>${escapeHtml(abstract)}</p>` : participants ? `<p>${participants}</p>` : ""}
      </article>
    `;
  }

  return `
    <article class="grant-card">
      <div>
        ${funderCall ? `<p class="meta grant-eyebrow">${funderCall}</p>` : ""}
        <h3>${escapeHtml(display.title || group.title)}</h3>
        ${participants ? `<p class="grant-participants">${participants}</p>` : ""}
        ${numberBudget ? `<p class="grant-number-budget">${numberBudget}</p>` : ""}
        ${abstract ? `<p class="grant-description">${escapeHtml(abstract)}</p>` : ""}
        <h4 class="grant-history-title">Application History</h4>
        <ol class="grant-history">
          ${group.records.map(renderGrantHistoryItem).join("")}
        </ol>
      </div>
    </article>
  `;
}

function grantDisplayYear(group = {}) {
  return cslDateYear(group.display || group.latest || {});
}

function renderCvGrantHistoryItem(item = {}) {
  return `
    <li class="grant-history-item">
      <span class="grant-history-year">${escapeHtml(cslDateYear(item))}</span>
      <span class="grant-history-decision">${escapeHtml(grantDecisionLabel(item))}</span>
      <span class="grant-history-funder">${grantFunderCall(item)}</span>
    </li>
  `;
}

function renderCvGrantEntry(group = {}) {
  const display = group.display || group.latest || {};
  const funderCall = grantFunderCall(display);
  const participants = renderGrantApplicants(display, "PI");
  const numberBudget = renderGrantNumberBudget(display);

  return `
    <div class="cv-entry cv-grant-entry">
      <span class="date">${escapeHtml(grantDisplayYear(group))}</span>
      <div>
        ${funderCall ? `<p class="meta grant-eyebrow">${funderCall}</p>` : ""}
        <h3>${escapeHtml(display.title || group.title)}</h3>
        ${participants ? `<p class="grant-participants">${participants}</p>` : ""}
        ${numberBudget ? `<p class="grant-number-budget">${numberBudget}</p>` : ""}
        <h4 class="grant-history-title">Application History</h4>
        <ol class="grant-history cv-grant-history">
          ${group.records.map(renderCvGrantHistoryItem).join("")}
        </ol>
      </div>
    </div>
  `;
}

function teachingSortValue(term = "") {
  const match = String(term).match(/(Spring|Fall)?\s*((?:19|20)\d{2})/i);
  if (!match) return 0;
  const year = Number(match[2]);
  const termWeight = match[1]?.toLowerCase() === "fall" ? 2 : match[1]?.toLowerCase() === "spring" ? 1 : 0;
  return year * 10 + termWeight;
}

function normalizeTeachingRecord(item = {}) {
  const note = item.note || "";
  const isStandardTeaching = item.type === "standard";
  const organizers = isStandardTeaching
    ? (item.author || [])
    : [...(item.organizer || []), ...(item.chair || [])];
  const contributors = isStandardTeaching
    ? [...(item.contributor || []), ...(item.presenter || [])]
    : [...(item.author || []), ...(item.presenter || []), ...(item.contributor || [])];
  const organizerNames = organizers.map(cslName).filter(Boolean);
  const contributorNames = contributors.map(cslName).filter(Boolean);
  const teachingType = item.genre || "Teaching";
  const userIsOrganizer = organizerNames.some(isBenjaminJarvisName);
  const userIsContributor = contributorNames.some(isBenjaminJarvisName);
  const recordId = item["citation-key"] || item.id || slugify(item.title || "teaching");
  const inferredRole = userIsContributor && !userIsOrganizer
    ? "Guest Lecturer"
    : userIsOrganizer && /development-director/i.test(recordId)
      ? "Program Development Director"
    : userIsOrganizer && /program|programme/i.test(`${teachingType} ${item.title || ""}`)
      ? "Program Director"
      : userIsOrganizer
        ? "Course Coordinator"
        : teachingType;

  return {
    id: recordId,
    title: item.title || "Untitled course",
    code: item.number || item["title-short"] || "",
    program: item.authority || item["event-title"] || "",
    institution: item.publisher || item["collection-title"] || "",
    location: item["publisher-place"] || item["event-place"] || "",
    term: teachingDateValue(item.issued) || "",
    role: noteValue(note, "Role") || inferredRole,
    preciseDates: noteValue(note, "Precise date(s)"),
    credits: noteValue(note, "Credits"),
    students: noteValue(note, "Students"),
    hours: noteValue(note, "Hours") || noteValue(note, "Teaching hours"),
    organizers: organizerNames,
    presenters: contributorNames,
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

function teachingRoleLabel(role) {
  const baseRole = role.role || "Teaching";
  const otherOrganizers = role.organizers.filter((name) => !isBenjaminJarvisName(name));
  const userIsOrganizer = role.organizers.some(isBenjaminJarvisName);
  const organizerList = formatNameList(otherOrganizers);

  if (!otherOrganizers.length) return baseRole;
  if (userIsOrganizer) return `${baseRole} (With ${organizerList})`;
  return `${baseRole} (Coordinator: ${organizerList})`;
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

function teachingCompactMeta(course = {}) {
  const latestRole = course.roles?.[0] || {};
  const term = latestRole.term || course.latest || "";
  const role = latestRole.role || "";
  return [term, role].filter(Boolean).map(escapeHtml).join("<br>");
}

function renderTeachingCourse(course, compact = false) {
  const meta = [course.program, course.institution].filter(Boolean).map(escapeHtml).join(" · ");

  if (compact) {
    return `
      <article class="teaching-card">
        <p class="meta">${teachingCompactMeta(course)}</p>
        <h3>${escapeHtml(course.title)}</h3>
        ${course.abstract ? `<p>${escapeHtml(course.abstract)}</p>` : ""}
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
          <h4>Teaching History</h4>
          <ul class="role-list teaching-history">
            ${course.roles.map(renderTeachingRole).join("")}
          </ul>
        </div>
      </div>
    </article>
  `;
}

function teachingDateRange(roles = []) {
  const years = roles
    .map((role) => String(role.term || "").match(/(?:19|20)\d{2}/)?.[0])
    .filter(Boolean)
    .map(Number);

  if (!years.length) return "";
  const first = Math.min(...years);
  const last = Math.max(...years);
  return first === last ? String(last) : `${first}-${last}`;
}

function renderCvTeachingEntry(course) {
  const meta = [course.program, course.institution].filter(Boolean).map(escapeHtml).join(" | ");

  return `
    <div class="cv-entry">
      <span class="date">${escapeHtml(teachingDateRange(course.roles))}</span>
      <div>
        <h3>${escapeHtml(course.title)}</h3>
        ${meta ? `<p>${meta}</p>` : ""}
        <h4 class="grant-history-title">Teaching History</h4>
        <ul class="role-list teaching-history cv-teaching-history">
          ${course.roles.map(renderTeachingRole).join("")}
        </ul>
      </div>
    </div>
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
        const grouped = groupGrants(grants);
        const selected = grouped.filter((group) => mode === "all" || group.lifecycle === mode);

        if (!selected.length) {
          target.innerHTML = "<p>No projects found for this section.</p>";
          return;
        }

        const visible = target.classList.contains("timeline") ? selected.slice(0, 4) : selected;

        target.innerHTML = visible
          .map((group) => renderGrantGroup(group, target.classList.contains("timeline")))
          .join("");
      })
      .catch(() => {
        target.innerHTML = "<p>Project list could not be loaded.</p>";
      });
  });
}

async function renderCvTeaching() {
  const target = document.querySelector("[data-cv-teaching-source]");
  if (!target) return;

  if (isFilePreview()) {
    target.innerHTML = '<h2>Teaching</h2><p>Teaching data needs a local server.</p>';
    return;
  }

  try {
    const response = await fetch(target.dataset.cvTeachingSource);
    const courses = groupTeachingRecords(await response.json());
    const courseGroups = courses.filter((course) => course.kind === "course");
    const programGroups = courses.filter((course) => course.kind === "program");
    const sections = [
      courseGroups.length && `<h3 class="cv-subheading">Courses</h3>${courseGroups.map(renderCvTeachingEntry).join("")}`,
      programGroups.length && `<h3 class="cv-subheading">Programs</h3>${programGroups.map(renderCvTeachingEntry).join("")}`,
    ].filter(Boolean);

    target.innerHTML = `<h2>Teaching</h2>${sections.join("") || "<p>No teaching entries found.</p>"}`;
  } catch {
    target.innerHTML = "<h2>Teaching</h2><p>Teaching list could not be loaded.</p>";
  }
}

async function renderCvGrants() {
  const target = document.querySelector("[data-cv-grants-source]");
  if (!target) return;

  if (isFilePreview()) {
    target.innerHTML = '<h2>Grants</h2><p>Grant data needs a local server.</p>';
    return;
  }

  try {
    const response = await fetch(target.dataset.cvGrantsSource);
    const groups = groupGrants(await response.json());
    const sections = [
      ["ongoing", "Ongoing"],
      ["under-review", "Under Review"],
      ["completed", "Completed"],
      ["rejected", "Rejected"],
    ].map(([lifecycle, label]) => {
      const entries = groups.filter((group) => group.lifecycle === lifecycle);
      return entries.length
        ? `<h3 class="cv-subheading">${label}</h3>${entries.map(renderCvGrantEntry).join("")}`
        : "";
    }).filter(Boolean);

    target.innerHTML = `<h2>Grants</h2>${sections.join("") || "<p>No grant entries found.</p>"}`;
  } catch {
    target.innerHTML = "<h2>Grants</h2><p>Grant list could not be loaded.</p>";
  }
}

async function renderTeaching() {
  const targets = document.querySelectorAll("[data-teaching]");
  if (!targets.length) return;

  if (isFilePreview()) {
    targets.forEach((target) => {
      target.innerHTML = '<article class="teaching-card"><h3>Teaching data needs a local server</h3><p>Run <code>python3 -m http.server 8001</code> and open <code>http://localhost:8001/</code> to load teaching from <code>data/teaching.json</code>.</p></article>';
    });
    return;
  }

  targets.forEach((target) => {
    fetch(target.dataset.teachingSource || "data/teaching.json")
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
renderCvTeaching();
renderCvGrants();
