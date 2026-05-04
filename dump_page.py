
from sources.http import fetch_html
import os

url = "https://www.iguopin.com/search?keyword=北京锐凌科技有限公司"
try:
    fr = fetch_html(url)
    with open("sample_page.html", "w", encoding="utf-8") as f:
        f.write(fr.text)
    print(f"Saved {len(fr.text)} chars to sample_page.html")
except Exception as e:
    print(f"Error: {e}")
