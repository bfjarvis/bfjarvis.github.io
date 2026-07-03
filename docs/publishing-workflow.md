# Publishing Workflow

This repository is the public publishing surface. Blog source materials live in
the sibling `research-notes` repository.

## Source and Output Repos

- `research-notes/blog/<slug>/index.qmd` - Quarto source note or post.
- `research-notes/blog/_template/index.qmd` - starter template for new posts.
- `research-notes/blog/<slug>/` - post-specific R scripts, data, figures, and references.
- `research-notes/renv.lock` - R dependency lockfile for reproducible rendering.
- `research-notes/scripts/publish_local.py` - local render/copy workflow.
- `research-notes/.github/workflows/publish-blog.yml` - manual-only fallback workflow.
- `bfjarvis.github.io/blog/index.html` - website-owned blog index layout.
- `bfjarvis.github.io/blog/post-template.html` - website-owned post page shell copied into each public post directory.
- `bfjarvis.github.io/blog/posts.json` - metadata generated from post front matter.
- `bfjarvis.github.io/blog/<slug>/content.html` - lean rendered post fragment from Quarto.
- `bfjarvis.github.io/.nojekyll` - tells GitHub Pages to publish the site as plain static files without Jekyll processing.

Keep R code, Quarto source, data, figures, and project-specific dependencies in
`research-notes` where possible. Keep this website repo focused on the static
public site and rendered blog output.

## Publishing a Post

From `research-notes`:

1. Copy `blog/_template/` to a new directory such as `blog/segregation-measurement-note/`.
2. Edit `blog/segregation-measurement-note/index.qmd` in RStudio, Positron, or another Quarto-aware editor.
3. Put post-specific R scripts, figures, data, or references inside the same post directory.
4. Run the local publish script:

   ```bash
   python3 scripts/publish_local.py
   ```

The script runs `quarto render`, rebuilds `posts.json`, copies each rendered
`content.html` fragment into `bfjarvis.github.io/blog/<slug>/`, copies any
post-specific rendered assets, and refreshes each public post's `index.html`
from the website-owned `bfjarvis.github.io/blog/post-template.html` shell.
It preserves `bfjarvis.github.io/blog/index.html` and
`bfjarvis.github.io/blog/post-template.html`.

Then preview the website repo locally and commit the resulting public output in
`bfjarvis.github.io`.

## Manual GitHub Action

The `research-notes` GitHub Action is currently manual-only. It should not be
treated as the default publishing path until the GitHub Pages deployment-layer
failures are understood. The local script is the preferred workflow for now.

## Design Integration

The public website owns blog layout. `blog/index.html` reads `blog/posts.json`
and renders the post list using the site's existing CSS and JavaScript. Each
public post directory contains a copied `post-template.html` shell that fetches the
lean Quarto-rendered `content.html` fragment. This keeps Quarto focused on
analysis output and keeps final page formatting in `bfjarvis.github.io`.
