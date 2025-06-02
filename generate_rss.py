import feedparser
from datetime import datetime, timezone, timedelta
import html
import random

# ── Define “today” in UTC and allowable date range ─────────────────────────────
TODAY_UTC = datetime.now(timezone.utc).date()
YESTERDAY_UTC = TODAY_UTC - timedelta(days=1)
TOMORROW_UTC = TODAY_UTC + timedelta(days=1)

# ── RSS source feeds ───────────────────────────────────────────────────────────
FEEDS = {
    "LOCAL": [
        "https://www.yourerie.com/feed/",
        "https://www.erienewsnow.com/rss?path=%2Fnews%2Flocal",
        "https://www.milb.com/erie/news/rss",
        "https://news.google.com/rss/search?q=%22Erie+Otters%22+hockey+-photo+-slideshow+-obituary&hl=en-US&gl=US&ceid=US:en"
    ],
    "NATIONAL": "https://feeds.a.dj.com/rss/RSSWorldNews.xml",  # WSJ World
    "NFL": "https://www.espn.com/espn/rss/nfl/news",
    "NHL": "https://www.espn.com/espn/rss/nhl/news",
    "MLB": "https://www.espn.com/espn/rss/mlb/news",
    "NBA": "https://www.espn.com/espn/rss/nba/news"
}

EXCLUDE_KEYWORDS = [
    "photo", "photos", "click", "slideshow", "gallery", "who", "what", "where", "here's how",
    "obituary", "see", "top ten", "viral", "sponsored", "buzz", "schedule",
    "ticket", "promo", "advertisement", "sign up", "event", "rankings",
    "preview", "high school", "congratulations", "register", "contest", "birthday", "why", "?"
]

STORY_LIMITS = {
    "LOCAL": 15,
    "NATIONAL": 10,
    "NFL": 2,
    "NHL": 2,
    "MLB": 2,
    "NBA": 2
}


def clean_and_write_rss():
    entries = []
    seen_titles = set()

    for label, sources in FEEDS.items():
        urls = sources if isinstance(sources, list) else [sources]
        clean = []

        for url in urls:
            try:
                feed = feedparser.parse(url)
                for entry in feed.entries:

                    # ── 1) DATE FILTER: allow entries from yesterday, today, or tomorrow (UTC) ─
                    if hasattr(entry, "published_parsed") and entry.published_parsed:
                        entry_dt = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc).date()
                    elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
                        entry_dt = datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc).date()
                    else:
                        continue  # no valid timestamp → skip

                    # Keep if entry_dt is YESTERDAY_UTC, TODAY_UTC, or TOMORROW_UTC
                    if entry_dt not in {YESTERDAY_UTC, TODAY_UTC, TOMORROW_UTC}:
                        continue  # skip if outside the desired date range

                    # ── 2) TITLE FILTER & DEDUPLICATION ──────────────────────────────────
                    title = entry.get("title", "").strip()
                    if not title or title.lower() in seen_titles:
                        continue
                    if any(bad in title.lower() for bad in EXCLUDE_KEYWORDS):
                        continue
                    seen_titles.add(title.lower())

                    # ── 3) TAG THE ENTRY WITH ITS LABEL AND COLLECT ──────────────────────
                    entry.label = label
                    clean.append(entry)

            except Exception as e:
                print(f"[{label}] Error reading feed {url}: {e}")

        # ── 4) APPLY STORY LIMITS PER LABEL ───────────────────────────────────────
        if label == "LOCAL":
            otters_added = False
            seawolves_added = False
            filtered = []

            for entry in clean:
                t = entry.get("title", "").lower()
                if "erie otters" in t:
                    if not otters_added:
                        filtered.append(entry)
                        otters_added = True
                elif "seawolves" in t or "sea wolves" in t:
                    if not seawolves_added:
                        filtered.append(entry)
                        seawolves_added = True
                else:
                    filtered.append(entry)

                if len(filtered) >= STORY_LIMITS.get(label, 10):
                    break

            selected = filtered
        else:
            selected = clean[:STORY_LIMITS.get(label, 3)]

        entries.extend(selected)
        print(f"[{label}] {len(selected)} entries included.")

    if not entries:
        print("⚠️ No entries found. Check filters or feed URLs.")

    random.shuffle(entries)

    # ── 5) BUILD RSS ITEMS BLOCK ───────────────────────────────────────────────
    rss_items = ""
    for e in entries:
        label_prefix = f"[{e.label}] " if hasattr(e, "label") else ""
        pub_date = e.get("published", datetime.utcnow().isoformat())
        rss_items += f"""
        <item>
            <title>{label_prefix}{html.escape(e.title)}</title>
            <link>{html.escape(e.link)}</link>
            <pubDate>{pub_date}</pubDate>
        </item>
        """

    rss_feed = f"""<?xml version="1.0" encoding="UTF-8" ?>
    <rss version="2.0">
    <channel>
        <title>Metabolic Signage Feed</title>
        <link>https://metabolic240.github.io/clean-rss-feed/rss.xml</link>
        <description>Filtered national sports and local Erie headlines</description>
        {rss_items}
    </channel>
    </rss>"""

    with open("rss.xml", "w", encoding="utf-8") as f:
        f.write(rss_feed)


if __name__ == "__main__":
    clean_and_write_rss()
