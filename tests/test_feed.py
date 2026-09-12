from datetime import UTC, datetime

import pytest

from knowledgey.feed import FeedParseError, parse_feed

RSS = """<?xml version="1.0"?>
<rss version="2.0" xmlns:content="http://purl.org/rss/1.0/modules/content/"
     xmlns:dc="http://purl.org/dc/elements/1.1/">
  <channel><title>My Channel</title>
    <item>
      <title>RSS Post</title><link>https://ex.com/a</link>
      <pubDate>Mon, 01 Jan 2025 10:00:00 +0000</pubDate>
      <dc:creator>Ada</dc:creator>
      <description>short summary</description>
      <content:encoded><![CDATA[<p>Full body</p>]]></content:encoded>
    </item>
  </channel>
</rss>"""

ATOM = """<?xml version="1.0"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>Atom Channel</title>
  <entry>
    <title>Atom Post</title><link href="https://ex.com/b"/>
    <published>2025-02-03T08:00:00Z</published>
    <author><name>Grace</name></author>
    <content type="html">&lt;p&gt;Atom body&lt;/p&gt;</content>
  </entry>
</feed>"""


def test_rss_is_parsed() -> None:
    feed = parse_feed(RSS)
    assert feed.title == "My Channel"
    assert [e.title for e in feed.entries] == ["RSS Post"]


def test_atom_is_parsed() -> None:
    feed = parse_feed(ATOM)
    assert feed.title == "Atom Channel"
    assert feed.entries[0].url == "https://ex.com/b"


def test_full_content_is_preferred_over_summary() -> None:
    assert parse_feed(RSS).entries[0].content_html == "<p>Full body</p>"


def test_authors_are_extracted_from_both_formats() -> None:
    assert parse_feed(RSS).entries[0].authors == ["Ada"]
    assert parse_feed(ATOM).entries[0].authors == ["Grace"]


def test_dates_become_aware_datetimes() -> None:
    assert parse_feed(RSS).entries[0].published_at == datetime(2025, 1, 1, 10, 0, tzinfo=UTC)


def test_entry_without_link_is_skipped() -> None:
    xml = RSS.replace("<link>https://ex.com/a</link>", "")
    assert parse_feed(xml).entries == []


def test_entry_without_body_is_skipped() -> None:
    xml = """<?xml version="1.0"?><rss version="2.0"><channel><title>C</title>
    <item><title>T</title><link>https://ex.com/x</link></item></channel></rss>"""
    assert parse_feed(xml).entries == []


def test_garbage_input_raises() -> None:
    with pytest.raises(FeedParseError):
        parse_feed("this is not xml at all")


def test_a_valid_but_empty_feed_is_not_an_error() -> None:
    xml = """<?xml version="1.0"?><rss version="2.0"><channel><title>C</title></channel></rss>"""
    assert parse_feed(xml).entries == []


def test_an_html_page_is_rejected() -> None:
    with pytest.raises(FeedParseError):
        parse_feed("<html><body>not a feed</body></html>")
