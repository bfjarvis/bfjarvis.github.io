# bfjarvis.github.io

Personal GitHub Pages site for Benjamin F. Jarvis.

## Structure

- `index.html` - homepage with publications, supervision, grants, teaching, posts, and contact sections.
- `data/grants.json` - structured source for ongoing and completed grants/projects.
- `data/publication-assets.json` - maps Zotero citation keys to representative publication images.
- `data/teaching.json` - structured source for courses, supervision, and selected teaching areas.
- `publications.json` - Better CSL JSON source for publications, presentations, talks, and theses.
- `supervision.json` - Better CSL JSON source for supervised MSc theses.
- `cv/cv.md` - editable Markdown source for the non-publication CV sections.
- `cv/index.html` - HTML curriculum vitae page. It renders `cv/cv.md`, `publications.json`, and `supervision.json` in the browser.
- `grants/` - grant and project index plus project detail pages for ongoing work.
- `teaching/` - teaching index page fed by `data/teaching.json`.
- `cv/Benjamin-F-Jarvis-CV.pdf` - generated PDF CV.
- `posts/statistical-vignettes.html` - starter post for statistical analysis vignettes.
- `vignettes/` - Quarto `.qmd` source files and rendered vignette pages.
- `assets/research-header-painterly.png` - research-derived homepage hero image.
- `assets/research-header-raw.png` - original research-derived header image.
- `assets/research-header-adjusted.png` - adjusted alternate header image.
- `assets/hero-social-statistics.png` - earlier generated hero image, retained as an alternate.
- `scripts/build_cv_pdf.py` - rebuilds the PDF CV from `cv/cv.md`, `publications.json`, and `supervision.json`.
- `scripts/import_vignette.sh` - imports a `.qmd` vignette from this repo or another research repo.
- `scripts/render_vignettes.sh` - renders Quarto vignettes and rebuilds the vignette index.
- `docs/publishing-workflow.md` - recommended workflow for connecting research repos to the website.

GitHub Pages can serve this directly from the repository root with no build step.

## Local Preview

Do not open `index.html` directly with `file://` when previewing the site. Browsers block
the local `fetch()` calls used for `publications.json`, `supervision.json`, `data/grants.json`, and other
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

Export Better CSL JSON from Zotero to `publications.json`. Add the keyword `selected`
to any formal publication that should appear in the homepage Selected Publications section.
Working papers, manuscripts, and preprints are shown separately in Works in Progress.
If no entries are tagged `selected`, the homepage falls back to recent journal articles,
books, and book chapters. All entries appear on the CV page, grouped by output type.

Better CSL JSON is preferred for the website because it is easy to parse in the browser
while preserving Zotero fields such as dates, event titles, locations, URLs, abstracts,
and notes.

To add a representative image for a publication:

1. Put the image in `assets/publications/`.
2. Add an entry to `data/publication-assets.json` using the Zotero citation key from `publications.json`.
3. Use either a single `image` field or an `images` array for a small click-through slideshow.

## Page Hero Images

Pages use `assets/research-header-painterly.png` as the default hero image. To use a
different image on a specific page, add a `--page-hero-image` override to that page's
hero section, for example:

```html
<section class="cv-hero" style="--page-hero-image: url('../assets/my-page-image.png')">
```

## Updating Grants and Projects

Edit `data/grants.json` for ongoing and completed grants/projects. Ongoing grants can
link to project pages in `grants/`, which can gather aims, collaborators, outputs,
publication links, and Quarto vignettes. This is usually cleaner than encoding grants
inside `publications.json`.

## Updating Teaching

Edit `data/teaching.json` for courses and recurring teaching areas.
Entries marked `"selected": true` appear on the homepage. The full list appears on
`teaching/index.html`.

If a course or supervision area needs more space, add a page under `teaching/` and
put its relative URL in that entry's `page` field. Otherwise, leave `page` blank.

## Updating Supervision

Export supervised MSc and PhD theses from Zotero as Better CSL JSON to `supervision.json`.
The CV includes a separate Supervision section, split into doctoral and master's
supervision.

Keep supervisor and co-supervisor details in Zotero's Extra or Notes field. Better CSL
JSON exports those notes as `note`, which the site displays under each supervised thesis.
MSc theses and dissertations can remain together in Zotero; the site uses the CSL
genre to split dissertation or PhD records from master's thesis records.

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
