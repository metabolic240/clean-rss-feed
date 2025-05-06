import feedparser
from datetime import datetime
import html
import random

# Feeds: label => RSS URL
FEEDS = {
    "SeaWolves": "https://www.milb.com/erie/news/rss",
    "Erie Otters": "https://news.google.com/rss/search?q=%22Erie+Otters%22+hockey+-photo+-slideshow+-obituary&hl=en-US&gl=US&ceid=US:en",
    "MLB": "https://www.espn.com/espn/rss/mlb/news",
    "NFL": "https://www.espn.com/espn/rss/nfl/news",
    "NHL": "https://www.espn.com/espn/rss/nhl/news",
    "NBA": "https://www.espn.com/espn/rss/nba/news",
    "Erie News": "https://www.goerie.com/news/rss"
}

# Global headline filter
EXCLUDE_KEYWORDS = [
    "photo", "photos", "click", "slideshow", "gallery", "who", "what",
    "obituary", "see", "top ten", "viral", "sponsored", "buzz", "schedule",
    "ticket", "promo", "advertisement", "sign up", "event", "rankings",
    "preview", "high school", "congratulations", "register", "contest"
]

# Target team filter per ESPN feed
TEAM_KEYWORDS = {
    "NFL": ["steelers", "bills", "browns"],
    "NHL": ["penguins", "sabres", "monsters"],
    "MLB": ["pirates", "guardians"],
    "NBA": ["cavaliers"]
}

def clean_and_write_rss():
    entries = []

    for label, url in FEEDS.items():
        try:
            feed = feedparser.parse(url)
            clean = []

            for entry in feed.entries:
                title = entry.get("title", "").lower()
                if any(bad in title for bad in EXCLUDE_KEYWORDS):
                    continue
                if label in TEAM_KEYWORDS:
                    if not any(team in title for team in TEAM_KEYWORDS[label]):
                        continue  # Skip unrelated national story
                entry.label = label
                clean.append(entry)

            selected = clean[:5]  # Take top 5 valid entries
            entries.extend(selected)
            print(f"[{label}] {len(selected)} items included.")
        except Exception as e:
            print(f"[{label}] Error: {e}")

    if not entries:
        print("⚠️ No entries found after filtering. Check feed sources or filters.")

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
        <title>Filtered Erie + Sports Feed</title>
        <link>https://yourusername.github.io/clean-rss-feed/rss.xml</link>
        <description>Mixed, clean news headlines for signage</description>
        {rss_items}
    </channel>
    </rss>"""

    with open("rss.xml", "w", encoding="utf-8") as f:
        f.write(rss_feed)

if __name__ == "__main__":
    clean_and_write_rss()
