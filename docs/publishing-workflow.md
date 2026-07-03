# Publishing Workflow

This repository is the public publishing surface. Blog source materials live in
the sibling `research-notes` repository.

## Source and Output Repos

- `research-notes/blog/<slug>/index.qmd` - Quarto source note or post.
- `research-notes/blog/_template/index.qmd` - starter template for new posts.
- `research-notes/blog/<slug>/` - post-specific R scripts, data, figures, and references.
- `research-notes/renv.lock` - R dependency lockfile for reproducible rendering.
- `research-notes/.github/workflows/publish-blog.yml` - render and publish workflow.
- `bfjarvis.github.io/blog/index.html` - website-owned blog index layout.
- `bfjarvis.github.io/blog/post-template.html` - website-owned post page shell copied into each public post directory.
- `bfjarvis.github.io/blog/posts.json` - metadata generated from post front matter.
- `bfjarvis.github.io/blog/<slug>/content.html` - lean rendered post fragment from Quarto.

Keep R code, Quarto source, data, figures, and project-specific dependencies in
`research-notes` where possible. Keep this website repo focused on the static
public site and rendered blog output.

## Publishing a Post

From `research-notes`:

1. Copy `blog/_template/` to a new directory such as `blog/segregation-measurement-note/`.
2. Edit `blog/segregation-measurement-note/index.qmd` in RStudio, Positron, or another Quarto-aware editor.
3. Put post-specific R scripts, figures, data, or references inside the same post directory.
4. Render locally with `quarto render` and run `python3 scripts/build_posts_json.py` if you want to preview the payload.
5. Commit and push to `main`.

GitHub Actions in `research-notes` will:

1. Check out `research-notes`.
2. Install Quarto and R.
3. Restore R packages from `renv.lock`.
4. Render the Quarto project.
5. Check out `bfjarvis/bfjarvis.github.io`.
6. Update `bfjarvis.github.io/blog/posts.json`.
7. Copy each rendered `content.html` fragment into `bfjarvis.github.io/blog/<slug>/`.
8. Copy the website-owned `bfjarvis.github.io/blog/post-template.html` shell to `bfjarvis.github.io/blog/<slug>/index.html`.
9. Commit and push the website update.

## Authentication

Add a `research-notes` repository secret named `WEBSITE_REPO_TOKEN`. For the
initial setup, a fine-grained personal access token with contents read/write
permission for `bfjarvis.github.io` is simplest. A write-enabled deploy key
scoped to the website repo is a narrower option for later.

## Design Integration

The public website owns blog layout. `blog/index.html` reads `blog/posts.json`
and renders the post list using the site's existing CSS and JavaScript. Each
public post directory contains a copied `post-template.html` shell that fetches the
lean Quarto-rendered `content.html` fragment. This keeps Quarto focused on
analysis output and keeps final page formatting in `bfjarvis.github.io`.
