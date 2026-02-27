#!/usr/bin/env python3
from __future__ import annotations
import argparse
import datetime as dt
import json
import os
import re
import tempfile
from hashlib import sha256
from pathlib import Path
from typing import Any

import feedparser
import requests
import yaml
from bs4 import BeautifulSoup
from dateutil import parser as date_parser
from dotenv import load_dotenv
from openai import OpenAI
from youtube_transcript_api import YouTubeTranscriptApi


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "config" / "sources.yaml"
RAW_DIR = ROOT / "data" / "raw"
BRIEFS_DIR = ROOT / "briefs"
TRANSCRIPTS_DIR = ROOT / "data" / "transcripts"


def load_config(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def parse_datetime(value: str | None) -> dt.datetime | None:
    if not value:
        return None
    try:
        parsed = date_parser.parse(value)
        if not parsed.tzinfo:
            parsed = parsed.replace(tzinfo=dt.timezone.utc)
        return parsed.astimezone(dt.timezone.utc)
    except Exception:
        return None


def normalize_date_window(target_date: dt.date) -> tuple[dt.datetime, dt.datetime]:
    """
    Use rolling freshness window for today's run, fixed day window for historical runs.
    """
    now = dt.datetime.now(dt.timezone.utc)
    today = now.date()

    if target_date >= today:
        end = now
        start = now - dt.timedelta(hours=36)
        return start, end

    start = dt.datetime.combine(target_date, dt.time.min, tzinfo=dt.timezone.utc)
    end = start + dt.timedelta(days=1)
    return start, end


def fetch_rss_items(sources: list[dict[str, str]], section: str, start: dt.datetime, end: dt.datetime) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for src in sources:
        feed = feedparser.parse(src["url"])
        for entry in feed.entries:
            published = parse_datetime(entry.get("published") or entry.get("updated"))
            if published is None:
                continue
            if not (start <= published < end):
                continue
            items.append(
                {
                    "section": section,
                    "source_type": "rss",
                    "source_name": src["name"],
                    "title": entry.get("title", ""),
                    "summary": re.sub("<[^>]+>", "", entry.get("summary", "")).strip(),
                    "url": entry.get("link", ""),
                    "published_utc": published.isoformat(),
                }
            )
    return items


def load_manual_sources(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "|" in line:
            url, note = [x.strip() for x in line.split("|", 1)]
        else:
            url, note = line, ""
        rows.append({"url": url, "note": note})
    return rows


def fetch_manual_items(rows: list[dict[str, str]], target_date: dt.date) -> list[dict[str, Any]]:
    date_str = dt.datetime.combine(target_date, dt.time.min, tzinfo=dt.timezone.utc).isoformat()
    return [
        {
            "section": "manual",
            "source_type": "manual",
            "source_name": "Manual Source",
            "title": row["note"] or row["url"],
            "summary": row["note"],
            "url": row["url"],
            "published_utc": date_str,
        }
        for row in rows
    ]


def fetch_podcast_items(channels: list[dict[str, str]], start: dt.datetime, end: dt.datetime) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for channel in channels:
        feed_url = channel.get("youtube_channel_feed") or channel.get("rss_feed")
        if not feed_url:
            continue
        feed = feedparser.parse(feed_url)
        if not feed.entries:
            continue
        entry = feed.entries[0]
        published = parse_datetime(entry.get("published") or entry.get("updated"))
        if published is None:
            published = end
        items.append(
            {
                "section": "podcast",
                "source_type": "youtube_podcast" if channel.get("youtube_channel_feed") else "podcast_rss",
                "source_name": channel["name"],
                "title": entry.get("title", ""),
                "summary": re.sub("<[^>]+>", "", entry.get("summary", "")).strip(),
                "url": entry.get("link", ""),
                "audio_url": next((l.get("href", "") for l in entry.get("links", []) if l.get("rel") == "enclosure"), ""),
                "published_utc": published.isoformat(),
            }
        )
    return items


def extract_video_id(url: str) -> str | None:
    patterns = [
        r"v=([a-zA-Z0-9_-]{11})",
        r"youtu\.be/([a-zA-Z0-9_-]{11})",
        r"youtube\.com/shorts/([a-zA-Z0-9_-]{11})",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def fetch_youtube_transcript(url: str, max_chars: int = 6000) -> str:
    video_id = extract_video_id(url)
    if not video_id:
        return ""
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        text = " ".join(chunk.get("text", "") for chunk in transcript)
        text = re.sub(r"\s+", " ", text).strip()
        return text[:max_chars]
    except Exception:
        return ""


def fetch_article_text(url: str, max_chars: int = 5000) -> str:
    if "x.com/" in url or "twitter.com/" in url:
        url = f"https://r.jina.ai/http://{url.replace('https://', '').replace('http://', '')}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    }
    try:
        resp = requests.get(url, timeout=10, headers=headers)
        if resp.status_code >= 400:
            return ""
        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "noscript"]):
            tag.extract()
        text = " ".join(soup.get_text(" ").split())
        return text[:max_chars]
    except Exception:
        return ""


def transcribe_podcast_excerpt(client: OpenAI, audio_url: str, cache_key: str, max_chars: int = 6000) -> str:
    TRANSCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = TRANSCRIPTS_DIR / f"{cache_key}.txt"
    if cache_file.exists():
        return cache_file.read_text(encoding="utf-8")[:max_chars]

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
        "Range": "bytes=0-12000000",
    }
    try:
        resp = requests.get(audio_url, timeout=25, headers=headers)
        if resp.status_code >= 400 or not resp.content:
            return ""

        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
            tmp.write(resp.content)
            tmp_path = tmp.name

        try:
            with open(tmp_path, "rb") as f:
                transcript = client.audio.transcriptions.create(
                    model="gpt-4o-mini-transcribe",
                    file=f,
                )
            text = (getattr(transcript, "text", "") or "").strip()
            if text:
                cache_file.write_text(text, encoding="utf-8")
            return text[:max_chars]
        finally:
            try:
                os.remove(tmp_path)
            except Exception:
                pass
    except Exception:
        return ""


def collect_day(config_path: Path, target_date: dt.date) -> Path:
    config = load_config(config_path)
    start, end = normalize_date_window(target_date)
    podcast_start = start if target_date < dt.datetime.now(dt.timezone.utc).date() else end - dt.timedelta(days=7)

    rss_items: list[dict[str, Any]] = []
    for section_name, sources in (config.get("rss_sources") or {}).items():
        rss_items.extend(fetch_rss_items(sources, section_name, start, end))

    podcast_items: list[dict[str, Any]] = []
    for section_name, channels in (config.get("podcast_channels") or {}).items():
        podcast_items.extend(fetch_podcast_items(channels, podcast_start, end))

    manual_file = ROOT / config.get("manual_sources_file", "data/manual_sources.txt")
    manual_items = fetch_manual_items(load_manual_sources(manual_file), target_date)

    all_items = sorted(
        rss_items + podcast_items + manual_items,
        key=lambda x: x.get("published_utc", ""),
        reverse=True,
    )

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    out = RAW_DIR / f"{target_date.isoformat()}.json"
    out.write_text(json.dumps(all_items, indent=2), encoding="utf-8")
    return out


def build_prompt(client: OpenAI, items: list[dict[str, Any]], target_date: dt.date) -> tuple[str, str]:
    enriched = []
    for idx, item in enumerate(items[:30], start=1):
        url = item.get("url", "")
        content = ""
        if item.get("source_type") == "youtube_podcast":
            content = fetch_youtube_transcript(url)
        elif item.get("source_type") == "podcast_rss":
            audio_url = item.get("audio_url", "")
            cache_key = sha256((audio_url or url).encode("utf-8")).hexdigest()[:16]
            if audio_url:
                content = transcribe_podcast_excerpt(client, audio_url, cache_key)
            if not content and url:
                content = fetch_article_text(url)
        elif url:
            content = fetch_article_text(url)

        enriched.append(
            {
                "id": idx,
                "section": item.get("section"),
                "source_name": item.get("source_name"),
                "title": item.get("title"),
                "summary": item.get("summary"),
                "url": url or item.get("audio_url", ""),
                "audio_url": item.get("audio_url", ""),
                "published_utc": item.get("published_utc"),
                "content_excerpt": content,
            }
        )

    system = (
        "You are a sharp research editor. "
        "Write a concise daily brief in markdown based only on the selected X posts and latest podcast episodes provided. "
        "Prioritize signal over noise, identify why each item matters, and separate facts from opinion. "
        "Use citation markers like [1], [2] linked to source ids. "
        "Every substantive claim must be supported by at least one source id."
    )

    user = (
        f"Date: {target_date.isoformat()}\n"
        "Produce sections in this exact order:\n"
        "1) Top 10 Signals (one-line each)\n"
        "2) X Account Updates\n"
        "3) Podcast Highlights\n"
        "4) Cross-Cutting Themes\n"
        "5) GPT Commentary\n"
        "6) Open Questions / Uncertainties\n"
        "7) Source List (id -> source, title, url)\n\n"
        "Rules:\n"
        "- Be precise and critical; no generic wording.\n"
        "- Do not invent facts. If unclear, say uncertainty explicitly.\n"
        "- If a section has no strong evidence, write: No high-confidence updates.\n"
        "- Do not add external assumptions, market chatter, or unnamed analyst views.\n"
        "- Do not force everything into AI or investing themes if the source is about something else.\n"
        "- In Podcast Highlights, cover each available podcast separately.\n"
        "- For each podcast, include: a 2-4 sentence episode summary, 3-5 specific highlights, and 1-2 insight bullets.\n"
        "- In GPT Commentary, use this exact sub-structure:\n"
        "  a) On Top Signals: 5-10 bullets commenting on the most important items and what they imply.\n"
        "  b) On Each Podcast: one short paragraph for each podcast with your interpretation and implications.\n"
        "  c) Final Take: a concluding paragraph titled 'What I Think After Seeing All This'.\n"
        "- In GPT Commentary, write your own synthesis with explicit investment implications where relevant: business model shifts, moats, platform risk, distribution, market structure, or health/wellness consumer trends.\n"
        "- Label interpretation clearly and keep it grounded in the sources.\n"
        "- Keep total length under 3000 words.\n"
        "- Mention major disagreements among sources when present.\n\n"
        f"Items:\n{json.dumps(enriched, ensure_ascii=False)}"
    )
    return system, user


def summarize_day(target_date: dt.date, model: str, input_json: Path | None = None) -> Path:
    if input_json is None:
        input_json = RAW_DIR / f"{target_date.isoformat()}.json"
    if not input_json.exists():
        raise FileNotFoundError(f"Missing input file: {input_json}")

    items = json.loads(input_json.read_text(encoding="utf-8"))
    if not items:
        raise RuntimeError("No source items found for target date. Add sources or manual links.")

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is not set. Run: export OPENAI_API_KEY='YOUR_KEY_HERE'"
        )
    client = OpenAI(api_key=api_key)
    system, user = build_prompt(client, items, target_date)

    response = client.responses.create(
        model=model,
        input=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0.2,
    )

    text = response.output_text.strip()
    text = text.replace("**Highlights:**\n-", "**Highlights:**\n\n-")
    text = text.replace("**Insights:**\n-", "**Insights:**\n\n-")
    BRIEFS_DIR.mkdir(parents=True, exist_ok=True)
    out = BRIEFS_DIR / f"{target_date.isoformat()}.md"
    out.write_text(text + "\n", encoding="utf-8")
    return out


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Daily brief pipeline")
    parser.add_argument("action", choices=["collect", "summarize", "run"], help="Pipeline step")
    parser.add_argument("--date", default=dt.date.today().isoformat(), help="Target date (YYYY-MM-DD, UTC)")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG), help="Path to source config")
    parser.add_argument("--model", default="gpt-4.1", help="OpenAI model for summarization")
    return parser.parse_args()


def main() -> None:
    load_dotenv(ROOT / ".env")
    args = parse_args()
    target_date = dt.date.fromisoformat(args.date)
    config_path = Path(args.config)

    if args.action == "collect":
        out = collect_day(config_path, target_date)
        print(f"Collected sources: {out}")
    elif args.action == "summarize":
        out = summarize_day(target_date, args.model)
        print(f"Brief generated: {out}")
    else:
        raw_file = collect_day(config_path, target_date)
        print(f"Collected sources: {raw_file}")
        out = summarize_day(target_date, args.model, raw_file)
        print(f"Brief generated: {out}")


if __name__ == "__main__":
    main()
