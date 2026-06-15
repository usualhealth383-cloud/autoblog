"""1단계: 트렌드 수집.

오늘 한국에서 급상승 중인 검색어와 연관 뉴스를 모은다. API 키가 필요 없는
무료 공개 소스(구글 트렌드 RSS, 구글 뉴스 RSS)만 사용한다.

소스:
- 구글 트렌드 급상승 검색어 RSS  (실시간 인기 검색어 + 대략적 검색량 + 연관 뉴스)
- 구글 뉴스 RSS                   (맥락 보강용 헤드라인)
- (선택) 네이버 데이터랩 — 키가 있으면 strategist 단계에서 보강
"""
from __future__ import annotations

import dataclasses
import html
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

import requests

from . import config

GEO = config.TARGET_GEO

# 구글 트렌드 급상승 검색어 RSS (현행/구버전 둘 다 시도)
TREND_RSS_URLS = [
    f"https://trends.google.com/trending/rss?geo={GEO}",
    f"https://trends.google.co.kr/trends/trendingsearches/daily/rss?geo={GEO}",
]
# 구글 뉴스 RSS (한국어/한국)
NEWS_RSS_URL = "https://news.google.com/rss?hl=ko&gl=KR&ceid=KR:ko"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) auto_blog/0.1",
    "Accept": "application/rss+xml, application/xml, text/xml, */*",
}
NS = {"ht": "https://trends.google.com/trending/rss"}


@dataclasses.dataclass
class TrendItem:
    title: str
    traffic: str = ""           # 예: "20,000+"
    news_titles: list[str] = dataclasses.field(default_factory=list)
    news_links: list[str] = dataclasses.field(default_factory=list)
    source: str = "google_trends"

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)


def _fetch(url: str, timeout: int = 15) -> str | None:
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout)
        r.raise_for_status()
        return r.text
    except requests.RequestException as e:
        print(f"  [경고] 수집 실패: {url}\n         {e}")
        return None


def _text(el) -> str:
    return html.unescape((el.text or "").strip()) if el is not None else ""


def fetch_google_trends(max_items: int = 20) -> list[TrendItem]:
    """구글 트렌드 급상승 검색어를 가져온다."""
    xml_text = None
    for url in TREND_RSS_URLS:
        xml_text = _fetch(url)
        if xml_text:
            break
    if not xml_text:
        return []

    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as e:
        print(f"  [경고] 트렌드 RSS 파싱 실패: {e}")
        return []

    items: list[TrendItem] = []
    for item in root.iter("item"):
        title = _text(item.find("title"))
        if not title:
            continue
        traffic = _text(item.find("ht:approx_traffic", NS))
        news_titles, news_links = [], []
        for ni in item.findall("ht:news_item", NS):
            nt = _text(ni.find("ht:news_item_title", NS))
            nl = _text(ni.find("ht:news_item_url", NS))
            if nt:
                news_titles.append(nt)
            if nl:
                news_links.append(nl)
        items.append(TrendItem(title=title, traffic=traffic,
                               news_titles=news_titles, news_links=news_links))
        if len(items) >= max_items:
            break
    return items


def fetch_google_news(max_items: int = 15) -> list[TrendItem]:
    """구글 뉴스 헤드라인(맥락 보강용)."""
    xml_text = _fetch(NEWS_RSS_URL)
    if not xml_text:
        return []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return []
    items: list[TrendItem] = []
    for item in root.iter("item"):
        title = _text(item.find("title"))
        link = _text(item.find("link"))
        if not title:
            continue
        items.append(TrendItem(title=title, news_links=[link] if link else [],
                               source="google_news"))
        if len(items) >= max_items:
            break
    return items


def collect() -> dict:
    """모든 소스를 모아 dict 로 반환."""
    trends = fetch_google_trends()
    news = fetch_google_news()
    return {
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "geo": GEO,
        "trends": [t.to_dict() for t in trends],
        "news": [n.to_dict() for n in news],
    }


def _main() -> None:
    data = collect()
    print(f"\n=== 구글 트렌드 급상승 ({data['geo']}) — {len(data['trends'])}건 ===")
    for i, t in enumerate(data["trends"], 1):
        traffic = f"  (검색량 {t['traffic']})" if t["traffic"] else ""
        print(f"{i:2}. {t['title']}{traffic}")
        if t["news_titles"]:
            print(f"     ↳ {t['news_titles'][0]}")
    print(f"\n=== 구글 뉴스 헤드라인 — {len(data['news'])}건 ===")
    for i, n in enumerate(data["news"][:10], 1):
        print(f"{i:2}. {n['title']}")


if __name__ == "__main__":
    _main()
