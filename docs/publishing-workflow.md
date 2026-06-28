# Publishing Workflow

This site is best treated as the public publishing surface, not necessarily the
only place where analysis happens.

## Recommended Setup

Use separate GitHub repositories for substantial research projects:

- `project-repo/analysis/` for R scripts, Quarto notebooks, model objects, and draft figures.
- `project-repo/data/` for shareable data or data documentation, if allowed.
- `project-repo/vignettes/` for one or more public-facing `.qmd` files.
- `bfjarvis.github.io/vignettes/` for the publishable copies that appear on the website.

When a vignette is ready to publish, import it into this website repo:

```bash
scripts/import_vignette.sh ../project-repo/vignettes/my-note.qmd my-note
scripts/render_vignettes.sh
```

This keeps research repositories free to be messy, private, or computationally
heavy, while the website remains clean and fast.

## Lightweight Local Workflow

For a vignette that only belongs on the site:

1. Copy `vignettes/_template.qmd` to a new file in `vignettes/`.
2. Edit it in RStudio or Positron.
3. Render it with `scripts/render_vignettes.sh`.
4. Commit the `.qmd`, generated `.html`, and updated `vignettes/index.html`.

## Cross-Repository Options

There are three sensible levels of integration:

1. Manual import: use `scripts/import_vignette.sh`. This is simple and reliable.
2. Git submodule or subtree: useful if you want the website to track a public
   vignette folder from another repository.
3. GitHub Actions: useful later if you want one repo to trigger a website rebuild
   automatically after a release.

Start with manual import. Automate only once the repeated workflow becomes clear.
