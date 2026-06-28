# bfjarvis.github.io

Personal GitHub Pages site for Benjamin F. Jarvis.

## Structure

- `index.html` - homepage with publications, grants, teaching, posts, and contact sections.
- `data/grants.json` - structured source for ongoing and completed grants/projects.
- `data/publication-assets.json` - maps BibTeX keys to representative publication images.
- `data/teaching.json` - structured source for courses, supervision, and selected teaching areas.
- `publications.bib` - BibTeX/BibLaTeX source for publications. Export this from Zotero and replace/update the file.
- `cv/cv.md` - editable Markdown source for the non-publication CV sections.
- `cv/index.html` - HTML curriculum vitae page. It renders `cv/cv.md` and `publications.bib` in the browser.
- `grants/` - grant and project index plus project detail pages for ongoing work.
- `teaching/` - teaching index page fed by `data/teaching.json`.
- `cv/Benjamin-F-Jarvis-CV.pdf` - generated PDF CV.
- `posts/statistical-vignettes.html` - starter post for statistical analysis vignettes.
- `vignettes/` - Quarto `.qmd` source files and rendered vignette pages.
- `assets/research-header.png` - research-derived homepage hero image.
- `assets/hero-social-statistics.png` - earlier generated hero image, retained as an alternate.
- `scripts/build_cv_pdf.py` - rebuilds the PDF CV from `cv/cv.md` and `publications.bib`.
- `scripts/import_vignette.sh` - imports a `.qmd` vignette from this repo or another research repo.
- `scripts/render_vignettes.sh` - renders Quarto vignettes and rebuilds the vignette index.
- `docs/publishing-workflow.md` - recommended workflow for connecting research repos to the website.

GitHub Pages can serve this directly from the repository root with no build step.

## Local Preview

Do not open `index.html` directly with `file://` when previewing the site. Browsers block
the local `fetch()` calls used for `publications.bib`, `data/grants.json`, and other
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

Export BibTeX or BibLaTeX from Zotero to `publications.bib`. Add the keyword `selected`
to any entry that should appear on the homepage. If no entries are tagged `selected`,
the homepage falls back to recent journal articles, books, book chapters, and working papers/preprints.
All entries appear on the CV page, grouped by publication type.

To add a representative image for a publication:

1. Put the image in `assets/publications/`.
2. Add an entry to `data/publication-assets.json` using the BibTeX key from `publications.bib`.
3. Use either a single `image` field or an `images` array for a small click-through slideshow.

## Updating Grants and Projects

Edit `data/grants.json` for ongoing and completed grants/projects. Ongoing grants can
link to project pages in `grants/`, which can gather aims, collaborators, outputs,
publication links, and Quarto vignettes. This is usually cleaner than encoding grants
inside `publications.bib`.

## Updating Teaching

Edit `data/teaching.json` for courses, supervision, and recurring teaching areas.
Entries marked `"selected": true` appear on the homepage. The full list appears on
`teaching/index.html`.

If a course or supervision area needs more space, add a page under `teaching/` and
put its relative URL in that entry's `page` field. Otherwise, leave `page` blank.

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
