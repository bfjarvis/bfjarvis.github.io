# bfjarvis.github.io

Quarto source for Benjamin F. Jarvis's personal academic website.

## Structure

- `_quarto.yml` - Quarto website configuration. The site renders locally to `docs/`.
- `index.qmd`, `publications.qmd`, `projects.qmd`, `teaching.qmd`, and `cv.qmd` - generated Quarto source pages.
- `templates/*.qmd.j2` - editable page templates used by `scripts/generate_site.py`.
- `data/grants.json` - structured source for ongoing and completed grants/projects.
- `data/publication-assets.json` - maps Zotero citation keys to representative publication images.
- `data/teaching.json` - CSL JSON source for courses and programme teaching records.
- `data/publications.json` - Better CSL JSON source for publications, presentations, talks, and theses.
- `data/supervision.json` - Better CSL JSON source for supervised MSc and PhD theses.
- `cv/cv.md` - editable Markdown source for the non-publication CV sections.
- `cv/Benjamin-F-Jarvis-CV.pdf` - generated PDF CV.
- `blog/index.qmd` - Quarto blog listing.
- `blog/<slug>/index.qmd` - native Quarto blog posts with their own front matter, prose, code, data, and figures.
- `assets/research-header-painterly.png` - research-derived homepage hero image.
- `scripts/generate_site.py` - reads the JSON data and templates, then writes the generated `.qmd` pages.
- `scripts/build_cv_pdf.py` - rebuilds the PDF CV from `cv/cv.md`, `data/publications.json`, and `data/supervision.json`.

For publication, use Quarto's `gh-pages` workflow. Source files live on `main`; rendered
site output is published to the `gh-pages` branch by `quarto publish gh-pages`.

## Local Preview

Generate the Quarto pages from the JSON data, then render the site:

```bash
python3 scripts/generate_site.py
quarto render
```

For a local development server, run:

```bash
quarto preview
```

```text
http://localhost:4321/
```

## Updating Publications

Export Better CSL JSON from Zotero to `data/publications.json`. Add the keyword `selected`
to any formal publication that should appear in the homepage Selected Publications section.
Working papers, manuscripts, and preprints are shown separately in Works in Progress.
If no entries are tagged `selected`, the homepage falls back to recent journal articles,
books, and book chapters. All entries appear on the CV page, grouped by output type.

Better CSL JSON is preferred because it is easy for the generator to parse while
preserving Zotero fields such as dates, event titles, locations, URLs, abstracts,
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
list appears on `teaching.qmd`.

Suggested Zotero conventions for teaching:

- Use Zotero item type `Standard` so teaching records can be excluded from publication searches.
- Use `Type` / CSL `genre` for `University Course` or `University Program`.
- Use `Title` for the course or programme name.
- Use `Short Title` / CSL `number` for the course code when one exists.
- Use `Meeting` / CSL `authority` for the programme, department, or teaching unit.
- Use `Series` / CSL `publisher` for the university or educational institution.
- Use `Location` / CSL `publisher-place` for the geographic location of teaching.
- Use `Chair/Organizer` / CSL `author` for course directors or coordinators.
- Use `Presenter` / CSL `contributor` for guest lecturers, including Benjamin F. Jarvis when relevant.
- Put teaching metadata in `Extra` or `Notes` using stable labels such as `Hours: 14`, `Credits: 7.5`, and `Students: 27`.

If a course or supervision area needs more space, add a Quarto page and put its
relative URL in that entry's `page` field. Otherwise, leave `page` blank.

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
Quarto CV and the PDF CV both render a separate supervision line, for example:

```text
Supervision: Maria Branden (Main), Benjamin F. Jarvis, and Sarah Valdez.
```

## Updating the CV

Edit `cv/cv.md` for appointments, education, teaching, service, and skills.
Then rebuild the PDF with:

```bash
python3 scripts/build_cv_pdf.py
```

## Publishing Blog Posts

Blog posts live directly in this repository as Quarto documents. Add or edit
posts under `blog/<slug>/index.qmd`, with any post-specific data, scripts, and
figures colocated in that same directory.

```bash
quarto render
```

Quarto builds the blog listing from `blog/index.qmd` and the post front matter.

## Publishing

Commit the Quarto source files on `main`, then publish the rendered site with:

```bash
quarto publish gh-pages
```

The local `docs/` render directory and `.quarto/` cache are ignored. They are useful
for previewing, but they are not the deployment source for this repository.
