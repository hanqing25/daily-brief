#!/usr/bin/env python3
from __future__ import annotations

import datetime as dt
import html
import re
from pathlib import Path

import markdown
import yaml

ROOT = Path(__file__).resolve().parents[1]
BRIEFS_DIR = ROOT / "briefs"
SITE_DIR = ROOT / "site"
CONFIG_PATH = ROOT / "config" / "sources.yaml"
MANUAL_PATH = ROOT / "data" / "manual_sources.txt"

STYLE_CSS = """
:root {
  --bg: #eef7f5;
  --bg-soft: #f7fbfa;
  --paper: #fcfffe;
  --paper-2: #f3fbf9;
  --text: #1d2a28;
  --text-soft: #4d6561;
  --text-faint: #78918c;
  --line: #cfe1dc;
  --accent: #2c7a7b;
  --accent-strong: #1f5e63;
  --accent-soft: #d9efeb;
  --shadow: 0 6px 18px rgba(39, 87, 82, 0.08);
}
* { box-sizing: border-box; }
html {
  scroll-behavior: smooth;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}
body {
  margin: 0;
  color: var(--text);
  background:
    radial-gradient(circle at top right, rgba(164, 214, 207, 0.35), transparent 26%),
    linear-gradient(180deg, #f7fcfb 0%, var(--bg) 100%);
  font-family: "Courier Prime", "IBM Plex Mono", "Courier New", monospace;
  line-height: 1.7;
}
a { color: var(--accent-strong); text-decoration: none; }
a:hover { color: var(--accent); }
.container { width: 100%; padding: 0 22px; }
@media (min-width: 860px) {
  .container { max-width: 760px; margin: 0 auto; }
}
.header {
  position: sticky;
  top: 0;
  z-index: 100;
  background: rgba(247, 252, 251, 0.9);
  backdrop-filter: blur(18px);
  border-bottom: 1px solid var(--line);
}
.header-inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  min-height: 58px;
}
.logo {
  font-size: 18px;
  font-weight: 700;
  letter-spacing: 0.01em;
  color: var(--text);
}
.header-nav {
  display: flex;
  gap: 10px;
  align-items: center;
  flex-wrap: wrap;
}
.nav-link {
  padding: 7px 10px;
  border-radius: 999px;
  font-size: 13px;
  color: var(--text-soft);
  border: 1px solid transparent;
}
.nav-link:hover,
.nav-link.active {
  background: var(--accent-soft);
  border-color: var(--line);
  color: var(--accent-strong);
}
.date-bar {
  border-bottom: 1px solid var(--line);
  background: rgba(247, 252, 251, 0.75);
}
.date-bar-inner {
  display: grid;
  grid-template-columns: 42px 1fr 42px;
  align-items: center;
  gap: 10px;
  min-height: 78px;
}
.date-arrow {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 999px;
  border: 1px solid var(--line);
  background: var(--paper);
  color: var(--text-soft);
}
.date-arrow.disabled { opacity: 0.35; pointer-events: none; }
.date-center { text-align: center; }
.date-main {
  display: block;
  font-size: 22px;
  font-weight: 700;
  letter-spacing: -0.01em;
}
.date-sub {
  display: block;
  margin-top: 4px;
  font-size: 13px;
  color: var(--text-faint);
}
.jump-bar {
  position: sticky;
  top: 58px;
  z-index: 90;
  background: rgba(247, 252, 251, 0.92);
  border-bottom: 1px solid var(--line);
}
.jump-list {
  display: flex;
  gap: 8px;
  overflow-x: auto;
  padding: 10px 0;
  scrollbar-width: none;
}
.jump-list::-webkit-scrollbar { display: none; }
.jump-chip {
  white-space: nowrap;
  padding: 7px 10px;
  border-radius: 999px;
  border: 1px solid var(--line);
  background: var(--paper);
  color: var(--text-soft);
  font-size: 12px;
}
.main-content { padding: 22px 0 52px; }
.hero-card,
.article-card,
.archive-card,
.source-card,
.note-card {
  background: rgba(252, 255, 254, 0.92);
  border: 1px solid var(--line);
  border-radius: 16px;
  box-shadow: var(--shadow);
}
.hero-card {
  padding: 22px 22px 18px;
  margin-bottom: 16px;
}
.eyebrow {
  display: inline-block;
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--text-faint);
}
.hero-head {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-start;
  margin-top: 10px;
}
.hero-copy h1 {
  margin: 0;
  font-size: 32px;
  line-height: 1.08;
}
.hero-copy p {
  margin: 10px 0 0;
  color: var(--text-soft);
  font-size: 15px;
}
.hero-metrics {
  min-width: 190px;
  display: grid;
  gap: 8px;
}
.metric-row {
  padding: 9px 10px;
  border-radius: 12px;
  background: var(--paper-2);
  border: 1px solid var(--line);
}
.metric-label {
  display: block;
  font-size: 11px;
  text-transform: uppercase;
  color: var(--text-faint);
}
.metric-value {
  display: block;
  margin-top: 4px;
  font-size: 14px;
  color: var(--text);
}
.toolbar {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  align-items: center;
  flex-wrap: wrap;
  margin-top: 14px;
  padding-top: 14px;
  border-top: 1px dashed var(--line);
}
.toolbar-note { color: var(--text-faint); font-size: 12px; }
.toolbar-links { display: flex; gap: 8px; flex-wrap: wrap; }
.button-link {
  padding: 8px 11px;
  border-radius: 999px;
  background: var(--accent-soft);
  border: 1px solid var(--line);
  color: var(--accent-strong);
  font-size: 12px;
}
.article-card { padding: 22px; }
.content h1 { display: none; }
.content hr {
  border: 0;
  border-top: 1px dashed var(--line);
  margin: 20px 0;
}
.content h2 {
  margin: 26px 0 12px;
  padding-top: 8px;
  font-size: 22px;
  line-height: 1.25;
  border-top: 1px solid var(--line);
}
.content h2:first-of-type {
  margin-top: 0;
  padding-top: 0;
  border-top: 0;
}
.content h3 {
  margin: 18px 0 8px;
  font-size: 16px;
  line-height: 1.4;
  color: var(--accent-strong);
}
.content p,
.content li { font-size: 15px; color: var(--text); }
.content ul,
.content ol { padding-left: 22px; }
.content li { margin: 7px 0; }
.content strong { color: var(--text); }
.content blockquote {
  margin: 14px 0;
  padding: 12px 14px;
  border-left: 3px solid var(--accent);
  background: var(--paper-2);
  color: var(--text-soft);
}
.content table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 12px;
  font-size: 13px;
}
.content th,
.content td {
  text-align: left;
  vertical-align: top;
  border-bottom: 1px solid var(--line);
  padding: 9px 8px;
}
.content code,
pre,
code {
  font-family: "Courier Prime", "IBM Plex Mono", "Courier New", monospace;
}
.content code {
  background: #eaf5f2;
  padding: 2px 4px;
  border-radius: 4px;
}
.two-col {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}
.source-card,
.note-card,
.archive-card { padding: 18px; }
.source-card h3,
.archive-card h3,
.note-card h3 {
  margin: 0 0 8px;
  font-size: 18px;
}
.source-list,
.note-list {
  margin: 0;
  padding-left: 18px;
}
.source-list li,
.note-list li { margin: 6px 0; font-size: 14px; color: var(--text-soft); }
.pre-box {
  margin-top: 12px;
  padding: 12px;
  border-radius: 12px;
  border: 1px solid var(--line);
  background: #f4fbf9;
  overflow-x: auto;
  font-size: 12px;
  line-height: 1.6;
}
.archive-grid { display: grid; gap: 14px; }
.archive-card p { margin: 0; color: var(--text-soft); font-size: 14px; }
.footer {
  padding: 22px 0 36px;
  color: var(--text-faint);
  font-size: 12px;
}
@media (max-width: 700px) {
  .hero-head,
  .two-col { grid-template-columns: 1fr; display: grid; }
  .hero-metrics { min-width: 0; }
  .container { padding: 0 14px; }
  .date-main { font-size: 18px; }
  .hero-copy h1 { font-size: 26px; }
  .content p,
  .content li { font-size: 14px; }
  .article-card,
  .hero-card,
  .archive-card,
  .source-card,
  .note-card { padding: 16px; }
}
"""


def page_template(title: str, body: str) -> str:
    return f"""<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1, viewport-fit=cover\" />
  <title>{html.escape(title)}</title>
  <meta name=\"description\" content=\"Daily brief archive and selected-source summaries\" />
  <link rel=\"preconnect\" href=\"https://fonts.googleapis.com\" />
  <link rel=\"preconnect\" href=\"https://fonts.gstatic.com\" crossorigin />
  <link href=\"https://fonts.googleapis.com/css2?family=Courier+Prime:wght@400;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap\" rel=\"stylesheet\" />
  <link rel=\"stylesheet\" href=\"style.css\" />
</head>
<body>
{body}
</body>
</html>
"""


def slugify(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text.strip().lower()).strip("-")
    return text or "section"


def section_anchors(md_text: str) -> list[tuple[str, str]]:
    anchors = []
    for line in md_text.splitlines():
        if line.startswith("## "):
            label = line[3:].strip()
            anchors.append((label, slugify(label)))
    return anchors


def add_heading_ids(html_text: str) -> str:
    def repl(match: re.Match[str]) -> str:
        heading = match.group(1)
        return f'<h2 id="{slugify(heading)}">{heading}</h2>'
    return re.sub(r"<h2>(.*?)</h2>", repl, html_text)


def source_count(md_text: str) -> int:
    in_table = False
    count = 0
    for line in md_text.splitlines():
        if line.strip().startswith("| id"):
            in_table = True
            continue
        if in_table:
            if not line.strip().startswith("|"):
                break
            if set(line.replace("|", "").replace("-", "").strip()) == set():
                continue
            count += 1
    return count


def source_names(md_text: str) -> str:
    names = []
    in_table = False
    for line in md_text.splitlines():
        if line.strip().startswith("| id"):
            in_table = True
            continue
        if in_table:
            if not line.strip().startswith("|"):
                break
            if set(line.replace("|", "").replace("-", "").strip()) == set():
                continue
            parts = [p.strip() for p in line.strip().strip("|").split("|")]
            if len(parts) >= 2:
                names.append(parts[1])
    unique = []
    for name in names:
        if name not in unique:
            unique.append(name)
    return ", ".join(unique[:4]) + (" + more" if len(unique) > 4 else "")


def nav_html(active: str) -> str:
    links = [
        ("Latest", "index.html"),
        ("Archive", "archive.html"),
        ("Sources", "sources.html"),
    ]
    return "".join(
        f'<a class="nav-link {"active" if label.lower() == active else ""}" href="{href}">{label}</a>'
        for label, href in links
    )


def page_shell(title: str, main: str, active: str) -> str:
    return f"""
<header class=\"header\">
  <div class=\"container\">
    <div class=\"header-inner\">
      <a class=\"logo\" href=\"index.html\">Daily Brief Ledger</a>
      <nav class=\"header-nav\">{nav_html(active)}</nav>
    </div>
  </div>
</header>
{main}
<footer class=\"container footer\">Built as a public static site from your selected-source research workflow.</footer>
"""


def render_brief_page(md_files: list[Path], index: int) -> None:
    md_file = md_files[index]
    md_text = md_file.read_text(encoding="utf-8")
    html_body = markdown.markdown(md_text, extensions=["tables"])
    html_body = add_heading_ids(html_body)
    date_label = md_file.stem
    human_date = dt.datetime.strptime(date_label, "%Y-%m-%d").strftime("%B %d, %Y")
    anchors = section_anchors(md_text)
    prev_link = f"{md_files[index + 1].stem}.html" if index + 1 < len(md_files) else None
    next_link = f"{md_files[index - 1].stem}.html" if index > 0 else None
    jump_html = "".join(
        f'<a class="jump-chip" href="#{anchor}">{html.escape(label)}</a>' for label, anchor in anchors
    )
    main = f"""
<nav class=\"date-bar\">
  <div class=\"container\">
    <div class=\"date-bar-inner\">
      <a class=\"date-arrow {'disabled' if not prev_link else ''}\" href=\"{prev_link or '#'}\">‹</a>
      <div class=\"date-center\">
        <span class=\"date-main\">{human_date}</span>
        <span class=\"date-sub\">{source_count(md_text)} sources tracked · {html.escape(source_names(md_text) or 'Selected sources')}</span>
      </div>
      <a class=\"date-arrow {'disabled' if not next_link else ''}\" href=\"{next_link or '#'}\">›</a>
    </div>
  </div>
</nav>
<div class=\"jump-bar\">
  <div class=\"container\"><div class=\"jump-list\">{jump_html}</div></div>
</div>
<main class=\"container main-content\">
  <section class=\"hero-card\">
    <span class=\"eyebrow\">Daily Reading Page</span>
    <div class=\"hero-head\">
      <div class=\"hero-copy\">
        <h1>{human_date}</h1>
        <p>A cleaned-up selected-source digest with deeper podcast highlights, line-by-line GPT commentary, and an end-of-day synthesis.</p>
      </div>
      <div class=\"hero-metrics\">
        <div class=\"metric-row\"><span class=\"metric-label\">Generated</span><span class=\"metric-value\">{dt.datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}</span></div>
        <div class=\"metric-row\"><span class=\"metric-label\">Source Count</span><span class=\"metric-value\">{source_count(md_text)}</span></div>
        <div class=\"metric-row\"><span class=\"metric-label\">Tone</span><span class=\"metric-value\">Retro research memo</span></div>
      </div>
    </div>
    <div class=\"toolbar\">
      <span class=\"toolbar-note\">Use the jump bar like the sample site: scan sections, then read only what matters.</span>
      <div class=\"toolbar-links\">
        <a class=\"button-link\" href=\"sources.html\">Manage sources</a>
        <a class=\"button-link\" href=\"archive.html\">Browse archive</a>
      </div>
    </div>
  </section>
  <article class=\"article-card content\">{html_body}</article>
</main>
"""
    out_path = SITE_DIR / f"{date_label}.html"
    out_path.write_text(page_template(f"Daily Brief {date_label}", page_shell(f"Daily Brief {date_label}", main, "latest")), encoding="utf-8")


def build_archive(md_files: list[Path]) -> None:
    cards = []
    for md_file in md_files:
        date_label = md_file.stem
        md_text = md_file.read_text(encoding="utf-8")
        preview = ""
        for line in md_text.splitlines():
            if line.startswith("1.") or line.startswith("1)"):
                preview = line[2:].strip()
                break
        cards.append(
            f"<a class='archive-card' href='{date_label}.html'><h3>{date_label}</h3><p>{html.escape(preview or 'Open daily brief')}</p></a>"
        )
    main = f"""
<main class=\"container main-content\">
  <section class=\"hero-card\">
    <span class=\"eyebrow\">Archive</span>
    <div class=\"hero-head\">
      <div class=\"hero-copy\">
        <h1>All Briefs</h1>
        <p>The same static, light editorial layout as the daily page, but organized as an archive. This keeps the public site simple and cheap to host.</p>
      </div>
    </div>
  </section>
  <section class=\"archive-grid\">{''.join(cards) or '<div class="archive-card"><h3>No briefs yet</h3><p>Run the pipeline first.</p></div>'}</section>
</main>
"""
    (SITE_DIR / "archive.html").write_text(page_template("Daily Brief Archive", page_shell("Daily Brief Archive", main, "archive")), encoding="utf-8")


def build_sources_page() -> None:
    config = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8")) if CONFIG_PATH.exists() else {}
    podcasts = (config.get("podcast_channels") or {}).get("selected_podcasts", [])
    x_accounts = config.get("selected_x_accounts", [])
    manual_text = MANUAL_PATH.read_text(encoding="utf-8") if MANUAL_PATH.exists() else ""
    podcast_items = "".join(f"<li>{html.escape(item['name'])}</li>" for item in podcasts)
    x_items = "".join(f"<li>{html.escape(item['name'])} (@{html.escape(item['handle'])})</li>" for item in x_accounts)
    config_excerpt = html.escape(CONFIG_PATH.read_text(encoding="utf-8"))
    main = f"""
<main class=\"container main-content\">
  <section class=\"hero-card\">
    <span class=\"eyebrow\">Source Manager</span>
    <div class=\"hero-head\">
      <div class=\"hero-copy\">
        <h1>Source Control</h1>
        <p>This public page shows exactly what the brief watches. To add sources, edit the config files in the repo, rerun the pipeline, and push the updated static site.</p>
      </div>
      <div class=\"hero-metrics\">
        <div class=\"metric-row\"><span class=\"metric-label\">Podcast Feeds</span><span class=\"metric-value\">{len(podcasts)}</span></div>
        <div class=\"metric-row\"><span class=\"metric-label\">X Accounts</span><span class=\"metric-value\">{len(x_accounts)}</span></div>
        <div class=\"metric-row\"><span class=\"metric-label\">Edit Files</span><span class=\"metric-value\">`config/sources.yaml` + `data/manual_sources.txt`</span></div>
      </div>
    </div>
  </section>
  <section class=\"two-col\">
    <div class=\"source-card\">
      <h3>Selected Podcasts</h3>
      <ul class=\"source-list\">{podcast_items}</ul>
    </div>
    <div class=\"source-card\">
      <h3>Selected X Accounts</h3>
      <ul class=\"source-list\">{x_items}</ul>
    </div>
    <div class=\"note-card\">
      <h3>How To Add A Podcast</h3>
      <ol class=\"note-list\">
        <li>Find the official RSS feed.</li>
        <li>Add a new item under `podcast_channels.selected_podcasts` in `config/sources.yaml`.</li>
        <li>Run `./run_daily.sh`.</li>
        <li>Push the updated repo so GitHub Pages republishes.</li>
      </ol>
    </div>
    <div class=\"note-card\">
      <h3>How To Add An X Source</h3>
      <ol class=\"note-list\">
        <li>Add the account under `selected_x_accounts` in `config/sources.yaml`.</li>
        <li>Paste specific post URLs into `data/manual_sources.txt` until auto-ingestion is added.</li>
        <li>Run `./run_daily.sh` and push again.</li>
      </ol>
    </div>
  </section>
  <section class=\"note-card\" style=\"margin-top:14px;\">
    <h3>Current Config</h3>
    <div class=\"pre-box\"><pre>{config_excerpt}</pre></div>
  </section>
  <section class=\"note-card\" style=\"margin-top:14px;\">
    <h3>Manual Links File</h3>
    <div class=\"pre-box\"><pre>{html.escape(manual_text)}</pre></div>
  </section>
</main>
"""
    (SITE_DIR / "sources.html").write_text(page_template("Daily Brief Sources", page_shell("Daily Brief Sources", main, "sources")), encoding="utf-8")


def build_index(md_files: list[Path]) -> None:
    if md_files:
        latest = f"{md_files[0].stem}.html"
        body = f"<meta http-equiv=\"refresh\" content=\"0; url={latest}\" /><main class=\"container main-content\"><section class=\"hero-card\"><h1>Redirecting…</h1><p><a href=\"{latest}\">Open latest brief</a></p></section></main>"
    else:
        body = "<main class='container main-content'><section class='hero-card'><h1>No briefs yet</h1></section></main>"
    (SITE_DIR / "index.html").write_text(page_template("Daily Brief", page_shell("Daily Brief", body, "latest")), encoding="utf-8")


def build() -> None:
    SITE_DIR.mkdir(parents=True, exist_ok=True)
    (SITE_DIR / "style.css").write_text(STYLE_CSS.strip() + "\n", encoding="utf-8")
    (SITE_DIR / ".nojekyll").write_text("\n", encoding="utf-8")
    md_files = sorted(BRIEFS_DIR.glob("*.md"), reverse=True)
    for index, _ in enumerate(md_files):
        render_brief_page(md_files, index)
    build_archive(md_files)
    build_sources_page()
    build_index(md_files)
    print(f"Site generated: {SITE_DIR / 'index.html'}")


if __name__ == "__main__":
    build()
