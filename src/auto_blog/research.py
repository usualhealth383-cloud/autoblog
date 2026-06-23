"""딥리서치: 주제에 대해 실제 자료(위키백과 본문 + 최신 뉴스)를 모아 글의 근거로 제공.

헤드라인만 보는 얕은 방식이 아니라, **위키백과 본문(정의·수치·사례·맥락)** 을 읽어
진짜 정보를 확보하고, **최신 뉴스 헤드라인**으로 시의성을 더한다. 둘 다 무료·키 불필요·
안정적이라 매일 무인 실행에도 안전하다. 작성 단계는 이 자료에 근거해 깊이 있게 쓴다.
"""
from __future__ import annotations

import html
import re
import xml.etree.ElementTree as ET
from urllib.parse import quote

import requests

WIKI_API = "https://ko.wikipedia.org/w/api.php"
NEWS_SEARCH = "https://news.google.com/rss/search?q={q}&hl=ko&gl=KR&ceid=KR:ko"
HEADERS = {"User-Agent": "Mozilla/5.0 auto_blog-research/0.2"}
_TAG = re.compile(r"<[^>]+>")


def _strip(s: str) -> str:
    return html.unescape(_TAG.sub(" ", s or "")).strip()


def _wiki(keyword: str, max_chars: int = 3500) -> tuple[str, str]:
    """위키백과에서 키워드와 가장 관련된 문서 본문(평문)을 가져온다 → (본문, 출처제목)."""
    try:
        # 1) 검색으로 가장 맞는 문서 제목 찾기
        s = requests.get(WIKI_API, headers=HEADERS, timeout=15, params={
            "action": "query", "list": "search", "srsearch": keyword,
            "srlimit": 1, "format": "json"}).json()
        hits = s.get("query", {}).get("search", [])
        if not hits:
            return "", ""
        title = hits[0]["title"]
        # 2) 본문 평문 추출
        e = requests.get(WIKI_API, headers=HEADERS, timeout=15, params={
            "action": "query", "prop": "extracts", "explaintext": 1,
            "exsectionformat": "plain", "redirects": 1,
            "titles": title, "format": "json"}).json()
        pages = e.get("query", {}).get("pages", {})
        text = ""
        for p in pages.values():
            text = p.get("extract", "") or ""
        text = re.sub(r"\n{2,}", "\n", text).strip()
        return text[:max_chars], title
    except Exception as ex:
        print(f"  [경고] 위키백과 수집 실패: {ex}")
        return "", ""


def _news(keyword: str, max_items: int = 8) -> list[str]:
    """최신 뉴스 헤드라인(시의성)."""
    try:
        r = requests.get(NEWS_SEARCH.format(q=quote(keyword)), headers=HEADERS, timeout=15)
        root = ET.fromstring(r.text)
        out = []
        for item in root.iter("item"):
            t = _strip(item.findtext("title") or "")
            if t:
                out.append(t)
            if len(out) >= max_items:
                break
        return out
    except Exception as ex:
        print(f"  [경고] 뉴스 수집 실패: {ex}")
        return []


def fetch_grounding(keyword: str, max_items: int = 10) -> tuple[str, list[str]]:
    """딥리서치 자료를 모아 (근거텍스트, 출처리스트) 반환. (이름은 호환 위해 유지)"""
    wiki_text, wiki_title = _wiki(keyword)
    news = _news(keyword)

    parts, sources = [], []
    if wiki_text:
        parts.append(f"[백과사전 자료: '{wiki_title}']\n{wiki_text}")
        sources.append(f"위키백과:{wiki_title}")
    if news:
        parts.append("[최근 뉴스 헤드라인(시의성)]\n" + "\n".join(f"- {t}" for t in news))
        sources += news
    grounding = "\n\n".join(parts)
    n = len(wiki_text)
    print(f"  딥리서치: 위키백과 {n}자 + 뉴스 {len(news)}건 확보")
    return grounding, sources
