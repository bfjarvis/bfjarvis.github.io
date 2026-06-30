from html import escape
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
VIGNETTES = ROOT / "vignettes"
OUTPUT = VIGNETTES / "index.html"


def parse_front_matter(path):
    text = path.read_text(encoding="utf-8")
    match = re.match(r"---\n(.*?)\n---", text, re.S)
    data = {}
    if not match:
        return data

    for line in match.group(1).splitlines():
        if ":" not in line or line.startswith(" "):
            continue
        key, value = line.split(":", 1)
        value = value.strip().strip('"')
        data[key.strip()] = value
    return data


def vignette_rows():
    rows = []
    for qmd in sorted(VIGNETTES.glob("*.qmd")):
        if qmd.name.startswith("_"):
            continue
        meta = parse_front_matter(qmd)
        html_name = qmd.with_suffix(".html").name
        html_exists = (VIGNETTES / html_name).exists()
        rows.append(
            {
                "title": meta.get("title", qmd.stem.replace("-", " ").title()),
                "description": meta.get("description", ""),
                "date": meta.get("date", ""),
                "categories": meta.get("categories", ""),
                "html": html_name,
                "html_exists": html_exists,
                "source": qmd.name,
            }
        )
    return sorted(rows, key=lambda row: row["date"], reverse=True)


def build():
    rows = vignette_rows()
    items = "\n".join(
        f"""
          <article class="vignette-item">
            <p class="meta">{escape(row["date"])} · {escape(row["categories"].strip("[]"))}</p>
            <h2><a href="{escape(row["html"] if row["html_exists"] else row["source"])}">{escape(row["title"])}</a></h2>
            <p>{escape(row["description"])}</p>
            <div class="vignette-actions">
              {f'<a href="{escape(row["html"])}">Read HTML</a>' if row["html_exists"] else ""}
              <a href="{escape(row["source"])}">Source .qmd</a>
            </div>
          </article>
        """
        for row in rows
    )

    OUTPUT.write_text(
        f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="description" content="Quarto data vignettes and reproducible analysis notes by Benjamin F. Jarvis.">
    <title>Vignettes | Benjamin F. Jarvis</title>
    <link rel="stylesheet" href="../styles.css?v=20260630-fold-cue">
  </head>
  <body>
    <header class="site-header is-scrolled" data-nav>
      <a class="site-mark" href="../" aria-label="Benjamin F. Jarvis home"><span>Benjamin F. Jarvis</span></a>
      <button class="nav-toggle" type="button" aria-label="Open navigation" aria-expanded="false">
        <span></span>
        <span></span>
      </button>
      <nav class="site-nav" aria-label="Primary navigation">
        <a href="../publications/">Publications</a>
        <a href="../grants/">Projects</a>
        <a href="../teaching/">Teaching</a>
        <a href="../vignettes/">Vignettes</a>
        <a href="../cv/">CV</a>
      </nav>
    </header>

    <main>
      <section class="cv-hero">
        <h1>Data vignettes & reproducible notes</h1>
      </section>

      <section class="cv-page">
        <div class="vignette-index">
          {items or "<p>No vignettes found yet.</p>"}
        </div>
      </section>
    </main>

    <footer class="site-footer" aria-labelledby="footer-contact-title">
      <div>
        <h2 id="footer-contact-title">Contact, connect, collaborate.</h2>
      </div>
      <div class="contact-links">
        <a href="mailto:benjamin.jarvis@liu.se">benjamin.jarvis@liu.se</a>
        <a href="https://liu.se/en/organisation/liu/iei/ias">Institute for Analytical Sociology</a>
        <a href="https://scholar.google.com/citations?user=AZvfKd8AAAAJ&amp;hl=en&amp;oi=ao">Google Scholar</a>
        <a href="https://orcid.org/0000-0001-8127-4051">ORCID</a>
        <a href="https://github.com/bfjarvis">GitHub</a>
      </div>
      <p class="footer-copyright">&copy; <span data-year></span> Benjamin F. Jarvis</p>
    </footer>

    <script src="../script.js?v=20260630-teaching-projects"></script>
  </body>
</html>
""",
        encoding="utf-8",
    )


if __name__ == "__main__":
    build()
