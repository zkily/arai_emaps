"""自動車ニュース RSS 集約サービス（JST 当日フィルタ・キャッシュ）"""
from __future__ import annotations

import asyncio
import hashlib
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

import httpx
from loguru import logger

from app.core.config import settings
from app.core.datetime_utils import JST, now_jst

RSS_FETCH_TIMEOUT = 8.0
TRACKING_PARAMS = frozenset(
    {"utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content", "fbclid", "gclid"}
)

DEFAULT_RSS_FEEDS = (
    "https://news.yahoo.co.jp/rss/media/norimono/all.xml|乗りものニュース,"
    "https://news.yahoo.co.jp/rss/media/bestcar/all.xml|ベストカーWeb,"
    "https://news.yahoo.co.jp/rss/media/autocar/all.xml|AUTOCAR JAPAN,"
    "https://news.yahoo.co.jp/rss/media/motorfan/all.xml|MotorFan,"
    "https://response.jp/rss/index.rdf|レスポンス,"
    "https://news.yahoo.co.jp/rss/media/webcg/all.xml|webCG,"
    "https://news.yahoo.co.jp/rss/media/engine/all.xml|ENGINE WEB"
)


@dataclass
class AutoNewsItem:
    id: str
    title: str
    url: str
    source: str
    published_at: datetime

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "url": self.url,
            "source": self.source,
            "publishedAt": self.published_at.astimezone(JST).isoformat(),
        }


_cache_payload: dict[str, Any] | None = None
_cache_expires_at: datetime | None = None


def get_brand_keywords() -> list[str]:
    """AUTO_NEWS_BRAND_KEYWORDS を解析。空なら絞り込み無効。"""
    raw = (settings.AUTO_NEWS_BRAND_KEYWORDS or "").strip()
    if not raw:
        return []
    return [k.strip() for k in raw.split(",") if k.strip()]


def _text_matches_brand(text: str) -> bool:
    keywords = get_brand_keywords()
    if not keywords:
        return True
    if not text:
        return False
    lowered = text.casefold()
    for kw in keywords:
        if not kw:
            continue
        if kw.isascii():
            if kw.casefold() in lowered:
                return True
        elif kw in text:
            return True
    return False


def _filter_by_brand(items: list[AutoNewsItem]) -> list[AutoNewsItem]:
    keywords = get_brand_keywords()
    if not keywords:
        return items
    return [i for i in items if _text_matches_brand(i.title)]


def get_rss_feed_configs() -> list[tuple[str, str | None]]:
    """AUTO_NEWS_RSS_URLS を `url|表示名` 形式で解析。"""
    raw = (settings.AUTO_NEWS_RSS_URLS or "").strip() or DEFAULT_RSS_FEEDS
    configs: list[tuple[str, str | None]] = []
    for part in raw.split(","):
        chunk = part.strip()
        if not chunk:
            continue
        if "|" in chunk:
            url, name = chunk.split("|", 1)
            configs.append((url.strip(), name.strip() or None))
        else:
            configs.append((chunk, None))
    return configs


def _normalize_url(url: str) -> str:
    parsed = urlparse(url.strip())
    if parsed.scheme.lower() != "https":
        return url.strip()
    query = parse_qs(parsed.query, keep_blank_values=True)
    filtered = {k: v for k, v in query.items() if k.lower() not in TRACKING_PARAMS}
    new_query = urlencode(filtered, doseq=True)
    path = parsed.path.rstrip("/") or "/"
    return urlunparse((parsed.scheme, parsed.netloc.lower(), path, parsed.params, new_query, ""))


def _is_https_url(url: str) -> bool:
    try:
        return urlparse(url.strip()).scheme.lower() == "https"
    except Exception:
        return False


def _clean_title(title: str) -> str:
    text = re.sub(r"\s+", " ", (title or "").strip())
    return text


def _item_id(url: str) -> str:
    return hashlib.sha1(_normalize_url(url).encode("utf-8")).hexdigest()


def _parse_published(entry: dict[str, Any]) -> datetime | None:
    for key in ("published_parsed", "updated_parsed"):
        parsed = entry.get(key)
        if parsed:
            try:
                dt = datetime(*parsed[:6], tzinfo=timezone.utc).astimezone(JST)
                return dt
            except (TypeError, ValueError):
                continue
    for key in ("published", "updated"):
        raw = entry.get(key)
        if not raw:
            continue
        try:
            from email.utils import parsedate_to_datetime

            dt = parsedate_to_datetime(raw)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=JST)
            return dt.astimezone(JST)
        except (TypeError, ValueError, IndexError):
            continue
    return None


def _resolve_source_name(parsed_feed: feedparser.FeedParserDict, default: str | None) -> str:
    if default:
        return default
    title = (parsed_feed.feed.get("title") or "").strip()
    if title:
        return title
    return "自動車ニュース"


def _parse_feed(body: str, feed_url: str, default_source: str | None) -> list[AutoNewsItem]:
    try:
        import feedparser
    except ImportError as e:
        raise RuntimeError(
            "feedparser が未インストールです。pip install feedparser または requirements.txt を再インストールしてください。"
        ) from e

    parsed = feedparser.parse(body)
    source = _resolve_source_name(parsed, default_source)
    items: list[AutoNewsItem] = []
    for entry in parsed.entries or []:
        title = _clean_title(entry.get("title") or "")
        link = (entry.get("link") or "").strip()
        summary = _clean_title(entry.get("summary") or entry.get("description") or "")
        filter_text = f"{title} {summary}".strip()
        if not title or not link or not _is_https_url(link):
            continue
        if not _text_matches_brand(filter_text):
            continue
        published = _parse_published(entry)
        if published is None:
            continue
        norm_url = _normalize_url(link)
        items.append(
            AutoNewsItem(
                id=_item_id(norm_url),
                title=title,
                url=norm_url,
                source=source,
                published_at=published,
            )
        )
    if parsed.bozo and not items:
        logger.warning("auto_news: RSS parse warning for {}: {}", feed_url, parsed.bozo_exception)
    return items


async def _fetch_feed_body(client: httpx.AsyncClient, url: str) -> str | None:
    try:
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.text
    except httpx.HTTPError as e:
        logger.warning("auto_news: failed to fetch RSS {}: {}", url, e)
        return None


async def _fetch_all_feeds() -> list[AutoNewsItem]:
    configs = get_rss_feed_configs()
    if not configs:
        return []

    headers = {
        "User-Agent": "Smart-EMAP/1.0 (+auto-news-ticker)",
        "Accept": "application/rss+xml, application/xml, text/xml, */*",
    }
    async with httpx.AsyncClient(timeout=RSS_FETCH_TIMEOUT, headers=headers, follow_redirects=True) as client:
        bodies = await asyncio.gather(*[_fetch_feed_body(client, url) for url, _ in configs])

    all_items: list[AutoNewsItem] = []
    for (url, default_source), body in zip(configs, bodies):
        if not body:
            continue
        try:
            all_items.extend(_parse_feed(body, url, default_source))
        except Exception as e:
            logger.warning("auto_news: parse error for {}: {}", url, e)
    return all_items


def _dedupe_items(items: list[AutoNewsItem]) -> list[AutoNewsItem]:
    seen_urls: set[str] = set()
    seen_titles: set[str] = set()
    out: list[AutoNewsItem] = []
    for item in sorted(items, key=lambda x: x.published_at, reverse=True):
        url_key = _normalize_url(item.url)
        title_key = item.title.casefold()
        if url_key in seen_urls or title_key in seen_titles:
            continue
        seen_urls.add(url_key)
        seen_titles.add(title_key)
        out.append(item)
    return out


def _filter_today(items: list[AutoNewsItem], today) -> list[AutoNewsItem]:
    return [i for i in items if i.published_at.astimezone(JST).date() == today]


def _filter_last_24h(items: list[AutoNewsItem], now: datetime) -> list[AutoNewsItem]:
    cutoff = now - timedelta(hours=24)
    return [i for i in items if i.published_at.astimezone(JST) >= cutoff]


async def _build_payload(limit: int) -> dict[str, Any]:
    now = now_jst()
    today = now.date()
    raw_items = await _fetch_all_feeds()
    deduped = _dedupe_items(raw_items)
    # 念のためタイトルでも再フィルタ
    deduped = _filter_by_brand(deduped)

    today_items = _filter_today(deduped, today)
    is_fallback = False
    if not today_items:
        today_items = _filter_last_24h(deduped, now)
        is_fallback = bool(today_items)

    limited = today_items[:limit]
    return {
        "date": today.isoformat(),
        "items": [i.to_dict() for i in limited],
        "isFallback": is_fallback,
        "fetchedAt": now.isoformat(),
    }


async def get_auto_news(limit: int | None = None) -> dict[str, Any]:
    """キャッシュ付きで自動車ニュース一覧を返す。"""
    if not settings.AUTO_NEWS_ENABLED:
        now = now_jst()
        return {
            "date": now.date().isoformat(),
            "items": [],
            "isFallback": False,
            "cached": False,
            "fetchedAt": now.isoformat(),
            "enabled": False,
        }

    max_items = limit or settings.AUTO_NEWS_MAX_ITEMS
    max_items = max(1, min(max_items, 50))
    fetch_limit = max(max_items, min(int(settings.AUTO_NEWS_MAX_ITEMS), 50))

    global _cache_payload, _cache_expires_at
    now = now_jst()
    if _cache_payload is not None and _cache_expires_at is not None and now < _cache_expires_at:
        items = _cache_payload.get("items", [])[:max_items]
        return {
            **{k: v for k, v in _cache_payload.items() if k != "items"},
            "items": items,
            "cached": True,
        }

    payload = await _build_payload(fetch_limit)
    ttl = max(60, int(settings.AUTO_NEWS_CACHE_TTL_SECONDS))
    _cache_payload = payload
    _cache_expires_at = now + timedelta(seconds=ttl)
    return {**payload, "items": payload["items"][:max_items], "cached": False}


def clear_auto_news_cache() -> None:
    """テスト・手動リフレッシュ用。"""
    global _cache_payload, _cache_expires_at
    _cache_payload = None
    _cache_expires_at = None
