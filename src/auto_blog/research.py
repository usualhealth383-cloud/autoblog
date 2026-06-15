"""사실 그라운딩: 주제 키워드로 실제 뉴스를 모아 글의 근거 자료로 제공.

구글 뉴스 RSS 검색으로 해당 키워드의 최신 기사 제목/요약을 수집한다. 본문 작성 시
이 자료에 근거만 쓰게 하면, 모델이 스펙·가격·수치를 지어내는 환각을 크게 줄일 수 있다.
RSS 라 안정적이고 키도 필요 없다.
"""
from __future__ import annotations

import html
import re
import xml.etree.ElementTree as ET
from urllib.parse import quote

import requests

NEWS_SEARCH = "https://news.google.com/rss/search?q={q}&hl=ko&gl=KR&ceid=KR:ko"
HEADERS = {"User-Agent": "Mozilla/5.0 auto_blog/0.1"}
_TAG = re.compile(r"<[^>]+>")


def _strip(s: str) -> str:
    return html.unescape(_TAG.sub(" ", s or "")).strip()


def fetch_grounding(keyword: str, max_items: int = 10) -> tuple[str, list[str]]:
    """키워드 관련 최신 뉴스 제목 모음 → (근거텍스트, 제목리스트)."""
    url = NEWS_SEARCH.format(q=quote(keyword))
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
        root = ET.fromstring(r.text)
    except (requests.RequestException, ET.ParseError) as e:
        print(f"  [경고] 그라운딩 수집 실패: {e}")
        return "", []

    titles: list[str] = []
    for item in root.iter("item"):
        t = _strip((item.findtext("title") or ""))
        if t:
            titles.append(t)
        if len(titles) >= max_items:
            break

    if not titles:
        return "", []
    grounding = "최근 관련 뉴스 헤드라인(사실 근거):\n" + "\n".join(f"- {t}" for t in titles)
    return grounding, titles
