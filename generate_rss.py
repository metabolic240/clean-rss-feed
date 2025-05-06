import feedparser
from datetime import datetime
import html
import random

FEEDS = {
    "LOCAL": [
        "https://rssfeeds.goerie.com/goerie/home",
        "https://www.erienewsnow.com/category/208145/local-news?clienttype=rss",
        "https://www.milb.com/erie/news/rss",
        "https://news.google.com/rss/search?q=%22Erie+Otters%22+hockey+-photo+-slideshow+-obituary&hl=en-US&gl=US&ceid=US:en",
        "https://www.yourerie.com/feed/"
    ],
    "NATIONAL": [
        "https://www.yourerie.com/feed/"
    ],
    "NFL": "https://www.espn.com/espn/rss/nfl/news",
    "NHL": "https://www.espn.com/espn/rss/nhl/news",
    "MLB": "https://www.espn.com/espn/rss/mlb/news",
    "NBA": "https://www.espn.com/espn/rss/nba/news"
}

# Apply filtering only to LOCAL and NATIONAL feeds
EXCLUDE_KEYWORDS = [
    "photo", "photos", "click", "slideshow", "gallery", "who", "what",
    "obituary", "see", "top ten", "viral", "sponsored", "buzz", "schedule",
    "ticket", "promo", "advertisement", "sign up", "event", "rankings",
    "preview", "high school", "congratulations", "register", "contest",
    "birthday", "cooking", "recipe", "this", "that", "why", "how",
    "here's", "what's", "live at", "celebration", "review", "gig",
    "super suppers", "on our air", "community", "local love", "segment",
    "chef", "dish", "video", "clip"
]

# Tag-based filtering for YourErie.com
ALLOWED_CATEGORIES = {
    "LOCAL": ["local news", "crime"],
    "NATIONAL": ["national news", "politics"]
}

def clean_and_write_rss():
    entries = []

    for label, sources in FEEDS.items():
        urls = sources if isinstance(sources, list) else [sources]
        clean = []

        for url in urls:
            try:
                feed = feedparser.parse(url)

                for entry in feed.entries:
                    title = entry.get("title", "").lower()

                    # Restrict YourErie feed to specific tags
                    if "yourerie.com" in url and label in ALLOWED_CATEGORIES:
                        categories = [tag.term.lower() for tag in entry.get("tags", []) if hasattr(tag, 'term')]
                        if not any(cat in categories for cat in ALLOWED_CATEGORIES[label]):
                            continue

                    if label in ["LOCAL", "NATIONAL"] and any(bad in title for bad in EXCLUDE_KEYWORDS):
                        continue

                    entry.label = label
                    clean.append(entry)

            except Exception as e:
                print(f"[{label}] Error reading feed {url}: {e}")

        selected = clean[:3]
        entries.extend(selected)
        print(f"[{label}] {len(selected)} entries included.")

    if not entries:
        print("⚠️ No entries found. Check filters or feed URLs.")

    random.shuffle(entries)

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
        <link>https://yourusername.github.io/clean-rss-feed/rss.xml</link>
        <description>Filtered national sports and local Erie headlines</description>
        {rss_items}
    </channel>
    </rss>"""

    with open("rss.xml", "w", encoding="utf-8") as f:
        f.write(rss_feed)

if __name__ == "__main__":
    clean_and_write_rss()
