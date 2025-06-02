import feedparser
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
import html
import random

# ── Define UTC thresholds ───────────────────────────────────────────────────────
NOW_UTC = datetime.now(timezone.utc)
LOCAL_CUTOFF_UTC = NOW_UTC - timedelta(days=2)      # last 48 hours for LOCAL
NATIONAL_CUTOFF_UTC = NOW_UTC - timedelta(days=2)   # last 48 hours for NATIONAL and sports

# ── RSS source feeds ───────────────────────────────────────────────────────────
FEEDS = {
    "LOCAL": [
        "https://www.goerie.com/rss/top-stories",
        "https://rss.eriereader.com/all",
        "https://talkerie.com/category/erie/feed",
        "https://www.goerie.com/rss/politics",
        "https://www.erienewsnow.com/rss?path=/news/weather"
    ],
    "NATIONAL": [
        "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en",
        "https://apnews.com/hub/ap-top-news?format=rss",
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
    "pet", "wall of honor", "tips", "review"
]

STORY_LIMITS = {
    "LOCAL": 15,
    "NATIONAL": 10,
    "NFL": 2,
    "NHL": 2,
    "MLB": 2,
    "NBA": 2
}


def parse_entry_datetime(entry):
    """
    Attempt to parse an entry's publication datetime in UTC.
    Check entry.published_parsed, then entry.published string,
    then entry.updated_parsed, then entry.updated string.
    Return a timezone-aware datetime in UTC, or None if parsing fails.
    """
    if getattr(entry, "published_parsed", None):
        return datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
    pub_str = entry.get("published")
    if pub_str:
        try:
            dt = parsedate_to_datetime(pub_str)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except Exception:
            pass
    if getattr(entry, "updated_parsed", None):
        return datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)
    upd_str = entry.get("updated")
    if upd_str:
        try:
            dt = parsedate_to_datetime(upd_str)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except Exception:
            pass
    return None


def clean_and_write_rss():
    entries = []
    seen_titles = set()

    for label, sources in FEEDS.items():
        urls = sources if isinstance(sources, list) else [sources]
        clean = []

        for url in urls:
            print(f"\n[DEBUG] Fetching {label} feed: {url}")
            try:
                feed = feedparser.parse(url)
                if feed.bozo:
                    print(f"[DEBUG]  → parse error: {feed.bozo_exception}")
                for entry in feed.entries:
                    entry_dt_utc = parse_entry_datetime(entry)
                    title = entry.get("title", "").strip()
                    # Print debug info for LOCAL before filtering:
                    if label == "LOCAL":
                        if entry_dt_utc:
                            print(f"[DEBUG-LOCAL] Title={title!r}, ParsedUTC={entry_dt_utc.isoformat()}")
                        else:
                            print(f"[DEBUG-LOCAL] Title={title!r}, ParsedUTC=NONE")

                    if not entry_dt_utc:
                        continue  # skip if no parseable date

                    # ── 2) Date‐filter by category ──────────────────────────────────────
                    if label == "LOCAL":
                        if entry_dt_utc < LOCAL_CUTOFF_UTC:
                            continue  # older than 48 hours → skip
                    else:
                        if entry_dt_utc < NATIONAL_CUTOFF_UTC:
                            continue  # older than 48 hours → skip

                    # ── 3) Title filter & deduplication ─────────────────────────────────
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
