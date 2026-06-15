"""한국어 글 → 영문 번역(같은 구조 유지).

이미 사람이 승인한 글을 번역하는 것이므로 사실관계는 원문을 따른다(추가 환각 없음).
번역본은 영문 독자용으로 자연스럽게 다듬는다.
"""
from __future__ import annotations

import json

from . import config

FIELDS = ("title", "meta_description", "tags", "sections", "disclaimer")


def translate_article(article: dict) -> dict:
    from openai import OpenAI
    client = OpenAI(api_key=config.OPENAI_API_KEY)
    payload = {k: article[k] for k in FIELDS if k in article}
    resp = client.chat.completions.create(
        model=config.get("OPENAI_MODEL", "gpt-4o"),
        response_format={"type": "json_object"},
        temperature=0.3,
        messages=[
            {"role": "system", "content":
                "You are a professional Korean-to-English translator for blog articles. "
                "Translate naturally and fluently for native English readers. Do NOT add "
                "facts; translate faithfully. Keep the exact same JSON structure."},
            {"role": "user", "content":
                "Translate every text field into natural English and return the SAME JSON "
                "shape: {title, meta_description, tags[], sections:[{heading, paragraphs[], "
                "image_prompt}], disclaimer}. Keep image_prompt unchanged. Tags should be "
                "English keywords.\n\n" + json.dumps(payload, ensure_ascii=False)},
        ],
    )
    en = json.loads(resp.choices[0].message.content)
    en["keyword"] = article.get("keyword")
    en["category"] = article.get("category")
    en["lang"] = "en"
    # 글자 수(영문은 단어 기준이라 참고용으로만)
    en["char_count"] = sum(len(p) for s in en.get("sections", [])
                           for p in s.get("paragraphs", []))
    return en
