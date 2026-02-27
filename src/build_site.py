#!/usr/bin/env python3
from __future__ import annotations

import datetime as dt
import html
import re
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parents[1]
BRIEFS_DIR = ROOT / "briefs"
SITE_DIR = ROOT / "site"

STYLE_CSS = """
:root {
  --bg: #f6f1e8;
  --paper: #fffdf8;
  --paper-strong: #fffaf1;
  --text: #1d1b18;
  --muted: #6b645c;
  --line: #ddd2c0;
  --accent: #0e5c4d;
  --accent-soft: #dfeee9;
  --shadow: 0 10px 30px rgba(52, 42, 24, 0.08);
}
* { box-sizing: border-box; }
html { scroll-behavior: smooth; }
body {
  margin: 0;
  color: var(--text);
  background:
    radial-gradient(circle at 10% 0%, rgba(199, 229, 218, 0.6), transparent 28%),
    radial-gradient(circle at 100% 0%, rgba(245, 218, 183, 0.45), transparent 24%),
    var(--bg);
  font-family: Georgia, "Times New Roman", serif;
}
a { color: var(--accent); text-decoration: none; }
a:hover { text-decoration: underline; }
.container { max-width: 1040px; margin: 0 auto; padding: 0 18px; }
.header {
  position: sticky;
  top: 0;
  z-index: 20;
  backdrop-filter: blur(14px);
  background: rgba(246, 241, 232, 0.88);
  border-bottom: 1px solid rgba(221, 210, 192, 0.8);
}
.header-inner {
  min-height: 64px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}
.logo {
  font-size: 20px;
  font-weight: 700;
  letter-spacing: 0.02em;
  color: var(--text);
}
.header-nav { display: flex; gap: 14px; font-size: 14px; color: var(--muted); }
.date-bar { border-bottom: 1px solid rgba(221, 210, 192, 0.9); }
.date-bar-inner {
  min-height: 74px;
  display: grid;
  grid-template-columns: 56px 1fr 56px;
  align-items: center;
  gap: 10px;
}
.date-arrow {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 42px;
  height: 42px;
  border-radius: 999px;
  border: 1px solid var(--line);
  background: rgba(255,255,255,0.6);
  color: var(--text);
}
.date-arrow.disabled { opacity: 0.35; pointer-events: none; }
.date-center { text-align: center; }
.date-main { display: block; font-size: 22px; font-weight: 700; }
.date-sub { display: block; margin-top: 4px; color: var(--muted); font-size: 14px; }
.jump-bar {
  position: sticky;
  top: 64px;
  z-index: 15;
  background: rgba(246, 241, 232, 0.93);
  border-bottom: 1px solid rgba(221, 210, 192, 0.9);
}
.jump-list {
  display: flex;
  gap: 10px;
  overflow-x: auto;
  padding: 12px 0;
  scrollbar-width: none;
}
.jump-list::-webkit-scrollbar { display: none; }
.jump-chip {
  white-space: nowrap;
  padding: 7px 12px;
  border-radius: 999px;
  background: var(--paper);
  border: 1px solid var(--line);
  color: var(--muted);
  font-size: 13px;
}
.main-content { padding: 26px 0 56px; }
.hero {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 260px;
  gap: 18px;
  margin-bottom: 18px;
}
.panel {
  background: var(--paper);
  border: 1px solid var(--line);
  border-radius: 18px;
  box-shadow: var(--shadow);
}
.hero-main { padding: 22px 24px; }
.eyebrow {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--muted);
}
.hero h1 { margin: 12px 0 8px; font-size: 34px; line-height: 1.05; }
.hero p { margin: 0; color: var(--muted); font-size: 16px; line-height: 1.65; }
.hero-side { padding: 20px; }
.metric { padding: 10px 0; border-bottom: 1px solid var(--line); }
.metric:last-child { border-bottom: 0; }
.metric-label { display: block; font-size: 12px; text-transform: uppercase; color: var(--muted); letter-spacing: 0.08em; }
.metric-value { display: block; margin-top: 4px; font-size: 18px; font-weight: 700; }
.article { padding: 18px 24px 26px; }
.content h1 { display: none; }
.content h2 {
  margin: 28px 0 12px;
  padding-top: 8px;
  font-size: 22px;
  border-top: 1px solid var(--line);
}
.content h2:first-of-type { margin-top: 0; border-top: 0; padding-top: 0; }
.content h3 {
  margin: 18px 0 8px;
  font-size: 17px;
  color: var(--accent);
}
.content p, .content li { font-size: 17px; line-height: 1.72; }
.content ul, .content ol { padding-left: 22px; }
.content li { margin: 8px 0; }
.content blockquote {
  margin: 14px 0;
  padding: 10px 14px;
  border-left: 3px solid var(--accent);
  background: var(--paper-strong);
  color: var(--muted);
}
.content table { width: 100%; border-collapse: collapse; margin-top: 12px; font-size: 14px; }
.content th, .content td { padding: 10px 8px; border-bottom: 1px solid var(--line); text-align: left; vertical-align: top; }
.content code {
  background: #f2ece2;
  border-radius: 5px;
  padding: 2px 5px;
  font-size: 0.95em;
}
.archive-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 16px;
}
.archive-card { padding: 18px; }
.archive-card h3 { margin: 0 0 6px; font-size: 22px; }
.archive-card p { margin: 0; color: var(--muted); line-height: 1.6; }
.footer {
  padding: 24px 0 40px;
  color: var(--muted);
  font-size: 13px;
}
@media (max-width: 860px) {
  .hero { grid-template-columns: 1fr; }
}
@media (max-width: 640px) {
  .container { padding: 0 14px; }
  .date-bar-inner { grid-template-columns: 44px 1fr 44px; }
  .date-main { font-size: 18px; }
  .hero h1 { font-size: 28px; }
  .content p, .content li { font-size: 16px; }
  .article, .hero-main, .hero-side { padding-left: 18px; padding-right: 18px; }
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


def render_brief_page(md_files: list[Path], index: int) -> None:
    md_file = md_files[index]
    md_text = md_file.read_text(encoding="utf-8")
    html_body = markdown.markdown(md_text, extensions=["tables"])
    html_body = add_heading_ids(html_body)
    date_label = md_file.stem
    human_date = dt.datetime.strptime(date_label, "%Y-%m-%d").strftime("%B %d, %Y")
    anchors = section_anchors(md_text)
    prev_link = f'{md_files[index + 1].stem}.html' if index + 1 < len(md_files) else None
    next_link = f'{md_files[index - 1].stem}.html' if index > 0 else None
    jump_html = "".join(
        f'<a class="jump-chip" href="#{anchor}">{html.escape(label)}</a>' for label, anchor in anchors
    )
    body = f"""
<header class=\"header\">
  <div class=\"container\">
    <div class=\"header-inner\">
      <a class=\"logo\" href=\"index.html\">Daily Brief</a>
      <nav class=\"header-nav\">
        <a href=\"archive.html\">Archive</a>
        <a href=\"index.html\">Latest</a>
      </nav>
    </div>
  </div>
</header>
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
  <div class=\"container\">
    <div class=\"jump-list\">{jump_html}</div>
  </div>
</div>
<main class=\"container main-content\">
  <section class=\"hero\">
    <div class=\"panel hero-main\">
      <span class=\"eyebrow\">Selected Source Brief</span>
      <h1>{human_date}</h1>
      <p>A daily reading page built from your chosen accounts and latest podcast episodes, with transcript-based summaries and an explicit GPT investment commentary section.</p>
    </div>
    <aside class=\"panel hero-side\">
      <div class=\"metric\"><span class=\"metric-label\">Generated</span><span class=\"metric-value\">{dt.datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}</span></div>
      <div class=\"metric\"><span class=\"metric-label\">Source Count</span><span class=\"metric-value\">{source_count(md_text)}</span></div>
      <div class=\"metric\"><span class=\"metric-label\">Format</span><span class=\"metric-value\">Podcast + X Digest</span></div>
    </aside>
  </section>
  <article class=\"panel article content\">{html_body}</article>
</main>
<footer class=\"container footer\">Static site generated from markdown briefs.</footer>
"""
    out_path = SITE_DIR / f"{date_label}.html"
    out_path.write_text(page_template(f"Daily Brief {date_label}", body), encoding="utf-8")


def build_archive(md_files: list[Path]) -> None:
    cards = []
    for md_file in md_files:
        date_label = md_file.stem
        md_text = md_file.read_text(encoding="utf-8")
        preview = ""
        for line in md_text.splitlines():
            if line.startswith("1."):
                preview = line[2:].strip()
                break
        cards.append(
            f"<a class='panel archive-card' href='{date_label}.html'><h3>{date_label}</h3><p>{html.escape(preview or 'Open daily brief')}</p></a>"
        )
    body = f"""
<header class=\"header\">
  <div class=\"container\">
    <div class=\"header-inner\">
      <a class=\"logo\" href=\"index.html\">Daily Brief</a>
      <nav class=\"header-nav\"><a href=\"archive.html\">Archive</a></nav>
    </div>
  </div>
</header>
<main class=\"container main-content\">
  <section class=\"hero\">
    <div class=\"panel hero-main\">
      <span class=\"eyebrow\">Archive</span>
      <h1>All Briefs</h1>
      <p>Browse each day’s digest as a permanent static page. This is the page you can publish on GitHub Pages.</p>
    </div>
  </section>
  <section class=\"archive-grid\">{''.join(cards) or '<div class="panel archive-card"><h3>No briefs yet</h3><p>Run the pipeline first.</p></div>'}</section>
</main>
<footer class=\"container footer\">Generated {dt.datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}</footer>
"""
    (SITE_DIR / "archive.html").write_text(page_template("Daily Brief Archive", body), encoding="utf-8")


def build_index(md_files: list[Path]) -> None:
    if md_files:
        latest = f"{md_files[0].stem}.html"
        body = f"""
<meta http-equiv=\"refresh\" content=\"0; url={latest}\" />
<header class=\"header\"><div class=\"container\"><div class=\"header-inner\"><a class=\"logo\" href=\"{latest}\">Daily Brief</a></div></div></header>
<main class=\"container main-content\"><section class=\"panel hero-main\"><h1>Redirecting to latest brief…</h1><p><a href=\"{latest}\">Open the latest brief</a> or <a href=\"archive.html\">browse the archive</a>.</p></section></main>
"""
    else:
        body = "<main class='container main-content'><section class='panel hero-main'><h1>No briefs yet</h1></section></main>"
    (SITE_DIR / "index.html").write_text(page_template("Daily Brief", body), encoding="utf-8")


def build() -> None:
    SITE_DIR.mkdir(parents=True, exist_ok=True)
    (SITE_DIR / "style.css").write_text(STYLE_CSS.strip() + "\n", encoding="utf-8")
    (SITE_DIR / ".nojekyll").write_text("\n", encoding="utf-8")
    md_files = sorted(BRIEFS_DIR.glob("*.md"), reverse=True)
    for index, _ in enumerate(md_files):
        render_brief_page(md_files, index)
    build_archive(md_files)
    build_index(md_files)
    print(f"Site generated: {SITE_DIR / 'index.html'}")


if __name__ == "__main__":
    build()
