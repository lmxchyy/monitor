
import feedparser
import datetime as dt

url = "https://36kr.com/feed"
parsed = feedparser.parse(url)
if parsed.entries:
    entry = parsed.entries[0]
    print(f"Title: {entry.title}")
    print(f"Published (raw): {getattr(entry, 'published', 'N/A')}")
    if hasattr(entry, 'published_parsed'):
        pp = entry.published_parsed
        date_obj = dt.date(pp.tm_year, pp.tm_mon, pp.tm_mday)
        print(f"Parsed into date: {date_obj}")
