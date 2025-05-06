import feedparser
from datetime import datetime
import html
import random

# Feed sources: label => RSS URL
FEEDS = {
    "SeaWolves": "https://www.milb.com/erie/news/rss",
    "Pittsburgh": "https://www.post-gazette.com/rss/sports",
    "Buffalo": "https://buffalonews.com/search/?f=rss&t=article&c=sports",
    "Cleveland": "https://www.cleveland.com/sports/guardians/rss/index.ssf",
    "Erie": "https://www.goerie.com/news/rss"
}

EXCLUDE_KEYWORDS = [
    "photo", "photos", "click", "slideshow", "gallery", "who", "what",
    "obituary", "see", "top ten", "viral", "sponsored", "buzz"
]

def clean_and_write_rss():
    entries = []
    
    for label, url in FEEDS.items():
        feed = feedparser.parse(url)
        clean = []
        for entry in feed.entries:
            title = entry.get("title", "").lower()
            if any(word in title for word in EXCLUDE_KEYWORDS):
                continue
            # Add label to help with source recognition
            entry.label = label
            clean.append(entry)
        entries.extend(clean[:5])  # Take top 5 clean entries per source

    random.shuffle(entries)

    rss_items = ""
    for e in entries:
        # Add [SOURCE] prefix to title
        label_prefix = f"[{e.label}] " if hasattr(e, "label") else ""
        rss_items += f"""
        <item>
            <title>{label_prefix}{html.escape(e.title)}</title>
            <link>{html.escape(e.link)}</link>
            <pubDate>{e.get("published", datetime.utcnow().isoformat())}</pubDate>
        </item>
        """

    rss_feed = f"""<?xml version="1.0" encoding="UTF-8" ?>
    <rss version="2.0">
        <channel>
            <title>Filtered Local + Sports Feed</title>
            <link>https://yourusername.github.io/clean-rss-feed/rss.xml</link>
            <description>Mixed, clean headlines for signage</description>
            {rss_items}
        </channel>
    </rss>"""

    with open("rss.xml", "w", encoding="utf-8") as f:
        f.write(rss_feed)

if __name__ == "__main__":
    clean_and_write_rss()
