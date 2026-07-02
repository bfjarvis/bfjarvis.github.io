# bfjarvis.github.io

Personal GitHub Pages site for Benjamin F. Jarvis.

## Structure

- `index.html` - homepage with publications, supervision, grants, teaching, posts, and contact sections.
- `data/grants.json` - structured source for ongoing and completed grants/projects.
- `data/grants-zotero-import.json` - temporary CSL JSON seed made from the historical grants spreadsheet for importing into Zotero.
- `data/publication-assets.json` - maps Zotero citation keys to representative publication images.
- `data/teaching.json` - CSL JSON source for courses and programme teaching records.
- `data/publications.json` - Better CSL JSON source for publications, presentations, talks, and theses.
- `data/supervision.json` - Better CSL JSON source for supervised MSc and PhD theses.
- `cv/cv.md` - editable Markdown source for the non-publication CV sections.
- `cv/index.html` - HTML curriculum vitae page. It renders `cv/cv.md`, `data/publications.json`, and `data/supervision.json` in the browser.
- `grants/` - grant and project index plus project detail pages for ongoing work.
- `teaching/` - teaching index page fed by `data/teaching.json`.
- `cv/Benjamin-F-Jarvis-CV.pdf` - generated PDF CV.
- `posts/statistical-vignettes.html` - starter post for statistical analysis vignettes.
- `vignettes/` - Quarto `.qmd` source files and rendered vignette pages.
- `assets/research-header-painterly.png` - research-derived homepage hero image.
- `assets/research-header-raw.png` - original research-derived header image.
- `assets/research-header-adjusted.png` - adjusted alternate header image.
- `assets/hero-social-statistics.png` - earlier generated hero image, retained as an alternate.
- `scripts/build_cv_pdf.py` - rebuilds the PDF CV from `cv/cv.md`, `data/publications.json`, and `data/supervision.json`.
- `scripts/import_vignette.sh` - imports a `.qmd` vignette from this repo or another research repo.
- `scripts/render_vignettes.sh` - renders Quarto vignettes and rebuilds the vignette index.
- `docs/publishing-workflow.md` - recommended workflow for connecting research repos to the website.

GitHub Pages can serve this directly from the repository root with no build step.

## Local Preview

Do not open `index.html` directly with `file://` when previewing the site. Browsers block
the local `fetch()` calls used for `data/publications.json`, `data/supervision.json`, `data/grants.json`, and other
structured content.

Run a local static server from the repository root instead:

```bash
python3 -m http.server 8001
```

Then open:

```text
http://localhost:8001/
```

## Updating Publications

Export Better CSL JSON from Zotero to `data/publications.json`. Add the keyword `selected`
to any formal publication that should appear in the homepage Selected Publications section.
Working papers, manuscripts, and preprints are shown separately in Works in Progress.
If no entries are tagged `selected`, the homepage falls back to recent journal articles,
books, and book chapters. All entries appear on the CV page, grouped by output type.

Better CSL JSON is preferred for the website because it is easy to parse in the browser
while preserving Zotero fields such as dates, event titles, locations, URLs, abstracts,
and notes.

To add a representative image for a publication:

1. Put the image in `assets/publications/`.
2. Add an entry to `data/publication-assets.json` using the Zotero citation key from `data/publications.json`.
3. Use either a single `image` field or an `images` array for a small click-through slideshow.

## Page Hero Images

Pages use `assets/research-header-painterly.png` as the default hero image. To use a
different image on a specific page, add a `--page-hero-image` override to that page's
hero section, for example:

```html
<section class="cv-hero" style="--page-hero-image: url('../assets/my-page-image.png')">
```

## Updating Grants and Projects

Export cleaned grant/project records from Zotero as CSL JSON to `data/grants.json`.
The Projects page groups records by Zotero's `Short Title` / CSL `title-short` field.
Use the same short title for repeated submissions that share a common project thread,
even when the full submitted title changes across applications.

The site splits grouped project threads into Ongoing, Under Review, Completed, and Rejected sections.
Within each thread, it lists the submission history, including date, decision, funder,
registration number, full submitted title, main applicant, co-applicants, and other
contributors. Ongoing groups are those with an `Open` status. Under Review groups are
submitted or registered records without a decision. Completed groups are those with a
granted or administratively closed record. Remaining groups are treated as rejected
applications.

For each grouped project thread, the displayed project title and participant list come
from the accepted version when one exists. If no version has been accepted, the site uses
the most recent version by report/project number. The history table then provides a
compact year/status/funder-call trail for the related submissions.

The `data/grants-zotero-import.json` file is only a seed file for Zotero import,
created from `Grants.xlsx`; it is not used by the website.

Suggested Zotero conventions for grants/projects:

- Use Zotero item type `Report`.
- Set `Report Type` / CSL `genre` to `Grant`.
- Use the project title as `Title`.
- Use the project leader or principal investigator as `Author`.
- Use the funder as `Institution` or `Publisher`, depending on the Zotero UI/export.
- Use `Series Title` for the specific funder call when the agency has multiple calls.
- Use the registration or decision number as `Report Number`.
- Use the application or award year as `Date`.
- Put decision state, project status, and budget in `Extra` or `Notes` using stable labels such as `Decision: Granted`, `Status: Open`, and `Budget: 4,000,000 SEK`.
- Put a public project page, funder page, or repository in `URL` when one exists.

The homepage shows a compact preview of the most recent ongoing project threads only.
The full Projects page shows ongoing, under review, completed, and rejected groups.

## Updating Teaching

Export course records from Zotero as CSL JSON and save them to
`data/teaching.json`.
The most recent grouped course records appear on the homepage. The full grouped
list appears on `teaching/index.html`.

If a course or supervision area needs more space, add a page under `teaching/` and
put its relative URL in that entry's `page` field. Otherwise, leave `page` blank.

## Updating Supervision

Export supervised MSc and PhD theses from Zotero as Better CSL JSON to `data/supervision.json`.
The CV includes a separate Supervision section, split into doctoral and master's
supervision.

Suggested Zotero conventions for supervision:

- Use one Zotero item per thesis.
- Use the student as `Author`.
- Use the thesis title as `Title`.
- Use `Thesis` as the item type when possible.
- Use `Type` / CSL `genre` to distinguish `PhD dissertation`, `Doctoral dissertation`, or `Master's thesis`.
- Use Linkoping University as the university/institution and Norrkoping as the place when appropriate.
- Put all supervisors in Zotero's `Contributor` field, including Benjamin F. Jarvis.
- For doctoral dissertations, list the main supervisor first. The website and PDF CV label the first doctoral contributor with `(Main)`.
- For master's theses, contributor order is used as given, but no `(Main)` label is added.

MSc theses and dissertations can remain together in Zotero; the site uses the CSL
genre/type to split dissertation or PhD records from master's thesis records. The
browser CV and the PDF CV both render a separate supervision line, for example:

```text
Supervision: Maria Branden (Main), Benjamin F. Jarvis, and Sarah Valdez.
```

## Updating the CV

Edit `cv/cv.md` for appointments, education, teaching, service, and skills.
Then rebuild the PDF with:

```bash
python3 scripts/build_cv_pdf.py
```

## Publishing Quarto Vignettes

1. Copy `vignettes/_template.qmd` to a new filename such as
   `vignettes/segregation-measurement-note.qmd`.
2. Edit the `.qmd` in RStudio, Positron, or another Quarto-aware editor.
3. Render and rebuild the vignette index:

```bash
scripts/render_vignettes.sh
```

The script renders every non-template `.qmd` file in `vignettes/` and then updates
`vignettes/index.html`. If a vignette has not been rendered yet, the index links to
the source `.qmd` file instead of a missing HTML page.

To import a vignette from another research repository:

```bash
scripts/import_vignette.sh ../project-repo/vignettes/my-note.qmd my-note
```
