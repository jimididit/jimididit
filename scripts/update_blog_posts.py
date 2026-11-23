#!/usr/bin/env python3
"""Rewrite the README blog list between BLOG-POST-LIST markers from the blog RSS feed."""
import re
import urllib.request
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime

FEED = "https://blog.jimididit.com/rss.xml"
README = "README.md"
COUNT = 3
PATTERN = re.compile(r"(<!-- BLOG-POST-LIST:START -->\n).*?(<!-- BLOG-POST-LIST:END -->)", re.S)


def render(root, count=COUNT):
    lines = []
    for item in root.iter("item"):
        d = parsedate_to_datetime(item.findtext("pubDate"))
        lines.append(f"- [**{item.findtext('title')}**]({item.findtext('link')}) - *{d:%b} {d.day}, {d:%Y}*")
        if len(lines) == count:
            break
    return "\n".join(lines) + "\n"


def main():
    req = urllib.request.Request(FEED, headers={"User-Agent": "readme-blog-updater"})
    with urllib.request.urlopen(req, timeout=30) as r:
        body = render(ET.fromstring(r.read()))
    text = open(README, encoding="utf-8").read()
    new, n = PATTERN.subn(lambda m: m.group(1) + body + m.group(2), text)
    assert n == 1, "BLOG-POST-LIST markers not found"
    if new != text:
        open(README, "w", encoding="utf-8").write(new)


if __name__ == "__main__":
    # self-check on a sample feed
    sample = ET.fromstring(
        "<rss><channel>"
        "<item><title>A &amp; B</title><link>http://x/a</link><pubDate>Sun, 22 Nov 2026 00:00:00 GMT</pubDate></item>"
        "<item><title>C</title><link>http://x/c</link><pubDate>Mon, 09 Jun 2025 00:00:00 GMT</pubDate></item>"
        "</channel></rss>")
    assert render(sample, 1) == "- [**A & B**](http://x/a) - *Nov 22, 2026*\n"
    assert render(sample).splitlines()[1].endswith("*Jun 9, 2025*")
    main()
