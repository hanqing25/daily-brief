# Daily Brief App (Phase 1: Text Output)

This project generates a daily markdown brief focused on:
- X posts from selected KOLs (manual links you paste)
- Selected podcasts (audio transcription + deeper summary)

Output is saved to:
- `briefs/YYYY-MM-DD.md`

## 1) Setup

```bash
cd "/Users/hqyu/Desktop/agents/codex/daily brief app"
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Set your OpenAI API key:

```bash
cp .env.example .env
# edit .env and set your real key
```

## 2) Configure sources

Edit `config/sources.yaml` to keep only your highest-value sources.

For X/Twitter posts from your selected accounts, paste links into:
- `data/manual_sources.txt`

## 3) Run daily pipeline

Run both collection + summarization:

```bash
./run_daily.sh
```

This also rebuilds the simple website view at:
- `site/index.html`

Or run steps separately:

```bash
python src/daily_brief.py collect --date 2026-02-27
python src/daily_brief.py summarize --date 2026-02-27
```

## 4) What this version does

- Pulls fresh items from configured RSS/YouTube feeds.
  - If `--date` is today (or future), it uses a rolling last 36-hour window.
  - If `--date` is in the past, it uses that UTC calendar day.
- Reads manual high-value links from `data/manual_sources.txt`.
- Extracts article text or transcript when possible.
- For podcast RSS episodes, it attempts audio transcription (first audio chunk) and caches transcript files in `data/transcripts/`.
- Produces one investor-grade markdown brief.

## 5) Limits in this first version

- X/Twitter full auto-fetch is not integrated (manual post links are used for reliability).
- Some sites block scraping; in those cases the model uses metadata + what is available.
- Paywalled pages may have incomplete text.

## 6) Next phase

After you validate output quality for 3-5 days, we build a clean web view for historical briefs and filtering.

## 7) Open website locally

```bash
cd "/Users/hqyu/Desktop/agents/codex/daily brief app"
python3 -m http.server 8000
```

Then open:
- `http://localhost:8000/site/index.html`

## 8) Publish publicly with GitHub Pages

Cheapest default: GitHub Pages.

Why:
- free for public repositories
- static HTML works well for this project
- good fit for `github.io` links

This repo already includes:
- GitHub Pages deploy workflow: `.github/workflows/deploy-pages.yml`
- static output marker: `site/.nojekyll`

Steps:

```bash
cd "/Users/hqyu/Desktop/agents/codex/daily brief app"
git init
git add .
git commit -m "Initial daily brief site"
git branch -M main
git remote add origin YOUR_GITHUB_REPO_URL
git push -u origin main
```

Then in GitHub:
- open `Settings` -> `Pages`
- set `Build and deployment` to `GitHub Actions`

After the workflow runs, your public URL will be:
- `https://YOUR_GITHUB_USERNAME.github.io/YOUR_REPO_NAME/`

Notes:
- `index.html` redirects to the latest brief page
- `archive.html` lists all brief pages
- do not commit `.env`
