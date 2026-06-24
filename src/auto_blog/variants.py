"""채널별 변형본 생성 — 같은 블로그 글을 스레드/네이버에 맞게 재가공.

- 스레드: 스크롤 멈추는 후킹 + 핵심 1~2개 + 블로그 링크. 500자 제한, 유쾌·임팩트.
- 네이버: 제목·도입을 새로 써서 중복(저품질) 회피. 유쾌한 말투 유지.
둘 다 블로그 본문(딥리서치 기반)을 출처로 하므로 내용은 정확하다.
"""
from __future__ import annotations

import json

from . import config

MODEL = config.get("OPENAI_MODEL", "gpt-4o")


def _client():
    from openai import OpenAI
    return OpenAI(api_key=config.OPENAI_API_KEY)


def _src(article: dict, n_sections: int = 3, limit: int = 1600) -> str:
    body = " ".join(p for s in article.get("sections", [])[:n_sections]
                    for p in s.get("paragraphs", []))
    return (article.get("title", "") + "\n" + body)[:limit]


def _full_text(article: dict, limit: int = 6000) -> str:
    """제목 + 모든 소제목/문단을 합친 전체 본문(네이버 압축본 생성용)."""
    parts = [article.get("title", "")]
    for s in article.get("sections", []):
        parts.append(s.get("heading", ""))
        parts.extend(s.get("paragraphs", []))
    return "\n".join(p for p in parts if p)[:limit]


def make_threads(article: dict) -> dict:
    """블로그 글 → 스레드용 짧고 후킹 있는 글. {text, hashtags}. (링크는 호출측에서 덧붙임)"""
    client = _client()
    r = client.chat.completions.create(
        model=MODEL, response_format={"type": "json_object"}, temperature=0.9,
        messages=[
            {"role": "system", "content":
                "너는 스레드(Threads)에서 잘 터지는 한국어 카피라이터다. JSON 으로만 답한다."},
            {"role": "user", "content":
                "다음 블로그 글을 스레드용으로 재가공하라. 규칙:\n"
                "- 첫 줄이 전부다. 피드에서 첫 줄만 보이므로 스크롤을 멈추게 하는 강한 후킹 "
                "한 문장(의외의 사실/공감 빵 터지는 상황/숫자/긴장감).\n"
                "- 짧게! 본문 200자 이내. 2~4줄 덩어리로 줄바꿈해 한눈에 읽히게. 핵심 정보만 추려라.\n"
                "- 유쾌·친근한 입말체 + 이모지로 생동감. 마지막은 공감 한마디나 가벼운 CTA/질문.\n"
                "- 해시태그 3~5개(주제 관련). 군더더기·뻔한 말 금지.\n"
                '형식: {"text": "후킹+핵심+CTA(줄바꿈 포함)", "hashtags": ["#태그", ...]}\n\n'
                f"[블로그 글]\n{_src(article)}"}])
    d = json.loads(r.choices[0].message.content)
    return {"text": d.get("text", ""), "hashtags": d.get("hashtags", [])}


def make_summary(article: dict) -> str:
    """다정하고 따뜻하고 재밌게, 1000자 내외 요약. 텔레그램 보고용."""
    client = _client()
    r = client.chat.completions.create(
        model=MODEL, temperature=0.85,
        messages=[
            {"role": "system", "content":
                "너는 다정하고 따뜻한 친구처럼 글을 소개하는 한국어 에디터다."},
            {"role": "user", "content":
                "다음 블로그 글을 친한 친구에게 다정하게 알려주듯 정리하라. 규칙:\n"
                "- 분량은 공백 포함 900~1000자 정도(너무 길지 않게). 6~8문장.\n"
                "- 핵심을 빠짐없이 담되, 따뜻하고 재밌게. 이모지 약간. 어려운 말 없이.\n"
                "- 마지막에 살짝 더 읽고 싶게 만들기.\n"
                "- 문장은 반드시 자연스럽게 끝맺어라(중간에 끊지 말 것).\n\n"
                f"[블로그 글]\n{_src(article, n_sections=5, limit=2600)}"}])
    return (r.choices[0].message.content or "").strip()


def make_naver(article: dict) -> dict:
    """네이버용 변형 — 블로거 원문을 ~2000자로 새로 압축·재서술한다.

    원문과 문장 표현을 충분히 다르게 써서 '중복(저품질) 콘텐츠' 페널티를 피한다.
    {title, lead, sections} 를 돌려준다(sections 는 재서술된 압축 본문)."""
    client = _client()
    r = client.chat.completions.create(
        model=MODEL, response_format={"type": "json_object"}, temperature=0.8,
        max_tokens=6000,
        messages=[
            {"role": "system", "content":
                "너는 네이버 블로그 작가다. 한국어. JSON 으로만 답한다."},
            {"role": "user", "content":
                "다음 블로그 원문을 네이버 블로그용으로 **새로 써라**(원문과 표현을 충분히 다르게 "
                "→ 중복 콘텐츠 회피). 규칙:\n"
                "- 원문과 다른 '새 제목' 1개(어울리는 이모지 1개 가능).\n"
                "- 새로 쓴 '도입 문단' 1개(4~6문장, 강한 후킹).\n"
                "- 본문 섹션 3~4개. 각 섹션 heading(이모지 1개 가능) + paragraphs(1~2문단, "
                "각 문단 3~5문장).\n"
                "- 전체 본문(섹션 문단 합계) 글자 수가 공백 포함 **약 2000자(1700~2300자)**.\n"
                "- 사실·수치는 원문과 동일하게 유지하되 **문장은 새로 써라(통째로 베끼지 말 것)**.\n"
                "- 유쾌·친근한 입말체 + 이모지 약간.\n"
                '형식: {"title": "새 제목", "lead": "새 도입 문단", '
                '"sections": [{"heading": "소제목", "paragraphs": ["문단", "문단"]}]}\n\n'
                f"[원문]\n{_full_text(article)}"}])
    d = json.loads(r.choices[0].message.content)
    return {"title": d.get("title", article.get("title", "")),
            "lead": d.get("lead", ""),
            "sections": d.get("sections", [])}
