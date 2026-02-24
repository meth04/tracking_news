from __future__ import annotations

import hashlib
import unicodedata
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any


def _normalize_text(value: str) -> str:
    return " ".join(value.strip().lower().split())


def stable_event_id(source: str, title: str, link: str, published: str | None) -> str:
    published_part = published or ""
    raw = (
        f"{_normalize_text(source)}|{_normalize_text(title)}|"
        f"{link.strip()}|{published_part.strip()}"
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def parse_datetime(value: str | None) -> datetime:
    if not value:
        return datetime.now(tz=timezone.utc)

    value = value.strip()
    if value.endswith("Z"):
        value = value.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(value)
    except ValueError:
        dt = parsedate_to_datetime(value)

    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def strip_diacritics(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    return "".join(ch for ch in normalized if not unicodedata.combining(ch))


def parse_feed(raw: str) -> list[dict[str, Any]]:
    root = ET.fromstring(raw)
    if root.tag.lower().endswith("rss"):
        return _parse_rss(root)
    return _parse_atom(root)


def _parse_rss(root: ET.Element) -> list[dict[str, Any]]:
    channel = root.find("channel")
    source = (
        channel.findtext("title", default="unknown-source")
        if channel is not None
        else "unknown-source"
    )
    items: list[dict[str, Any]] = []
    if channel is None:
        return items
    for entry in channel.findall("item"):
        title = entry.findtext("title", default="")
        summary = entry.findtext("description", default="")
        link = entry.findtext("link", default="")
        published = entry.findtext("pubDate", default=None)
        items.append(
            {
                "event_id": stable_event_id(source, title, link, published),
                "source": source,
                "title": title,
                "summary": summary,
                "link": link,
                "published_at": parse_datetime(published),
            }
        )
    return items


def _parse_atom(root: ET.Element) -> list[dict[str, Any]]:
    ns = {"a": "http://www.w3.org/2005/Atom"}
    source = root.findtext("a:title", default="unknown-source", namespaces=ns)
    items: list[dict[str, Any]] = []
    for entry in root.findall("a:entry", ns):
        title = entry.findtext("a:title", default="", namespaces=ns)
        summary = entry.findtext("a:summary", default="", namespaces=ns)
        link_el = entry.find("a:link", ns)
        link = ""
        if link_el is not None:
            link = link_el.attrib.get("href", "")
        published = entry.findtext("a:updated", default=None, namespaces=ns)
        items.append(
            {
                "event_id": stable_event_id(source, title, link, published),
                "source": source,
                "title": title,
                "summary": summary,
                "link": link,
                "published_at": parse_datetime(published),
            }
        )
    return items
