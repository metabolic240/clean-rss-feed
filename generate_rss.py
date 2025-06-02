import feedparser
from datetime import datetime, timezone, timedelta
import html
import random

# ── Define UTC thresholds ───────────────────────────────────────────────────────
NOW_UTC = datetime.now(timezone.utc)
LOCAL_CUTOFF_UTC = NOW_UTC - timedelta(days=1)      # last 24 hours for LOCAL
NATIONAL_CUTOFF_UTC = NOW_UTC - timedelta(days=2)   # last 48 hours for NATIONAL and sports

# ── RSS source feeds ───────────────────────────────────────────────────────────
FEEDS = {
    "LOCAL": [
        "https://www.yourerie.com/feed/",
        "https://www.erienewsnow.com/rss?path=%2Fnews%2Flocal",
        "https://www.milb.com/erie/news/rss",
        "https://news.google.com/rss/search?q=%22Erie+Otters%22+hockey+-photo+-slideshow+-obituary&hl=en-US&gl=US&ceid=US:en"
    ],
    "NATIONAL": [
        "http://rss.cnn.com/rss/cnn_topstories.rss",
        "https://www.usatoday.com/rss/topstories/",
        "http://feeds.reuters.com/reuters/topNews"
    ],
    "NFL": "https://www.espn.com/espn/rss/nfl/news",
    "NHL": "https://www.espn.com/espn/rss/nhl/news",
    "MLB": "https://www.espn.com/espn/rss/mlb/news",
    "NBA": "https://www.espn.com/espn/rss/nba/news"
}

EXCLUDE_KEYWORDS = [
    "photo", "photos", "click", "slideshow", "gallery", "who", "what", "where", "here's how",
    "obituary", "see", "top ten", "viral", "sponsored", "buzz", "schedule",
    "ticket", "promo", "advertisement", "sign up", "event", "rankings",
    "preview", "high school", "congratulations", "register", "contest", "birthday", "why", "?",
    "pet", "wall of honor", "tips"
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
                    # ── 1) Extract publication time from entry.published_parsed or entry.updated_parsed ──
                    entry_time = None
                    if getattr(entry, "published_parsed", None):
                        entry_time = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                    elif getattr(entry, "updated_parsed", None):
                        entry_time = datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)
                    else:
                        continue  # no parseable date → skip

                    # ── 2) Date‐filter by category ──────────────────────────────────────
                    if label == "LOCAL":
                        if entry_time < LOCAL_CUTOFF_UTC:
                            continue  # older than 24 hours → skip
                    else:
                        # NATIONAL and sports: require within last 48 hours
                        if entry_time < NATIONAL_CUTOFF_UTC:
                            continue  # older than 48 hours → skip

                    # ── 3) Title filter & deduplication ─────────────────────────────────
                    title = entry.get("title", "").strip()
                    lower_title = title.lower()
                    if not title or lower_title in seen_titles:
                        continue
                    if any(bad in lower_title for bad in EXCLUDE_KEYWORDS):
                        continue
                    seen_titles.add(lower_title)

                    # ── 4) Tag and collect ───────────────────────────────────────────────
                    entry.label = label
                    clean.append(entry)

            except Exception as e:
                print(f"[{label}] Error parsing feed {url}: {e}")

        # ── 5) Apply story limits ───────────────────────────────────────────────
        if label == "LOCAL":
            otters_added = False
            seawolves_added = False
            filtered = []
            for entry in clean:
                t_lower = entry.get("title", "").lower()
                if "erie otters" in t_lower and not otters_added:
                    filtered.append(entry)
                    otters_added = True
                elif ("seawolves" in t_lower or "sea wolves" in t_lower) and not seawolves_added:
                    filtered.append(entry)
                    seawolves_added = True
                else:
                    filtered.append(entry)
                if len(filtered) >= STORY_LIMITS[label]:
                    break
            selected = filtered
        else:
            selected = clean[:STORY_LIMITS[label]]

        entries.extend(selected)
        print(f"[{label}] {len(selected)} entries included.")

    if not entries:
        print("⚠️ No entries found. Check filters or feed URLs.")

    random.shuffle(entries)

    # ── 6) Build RSS items block ──────────────────────────────────────────────
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
