"""4단계: 서식화 — Article JSON → 깔끔한 HTML.

- 발행용 본문 HTML(render_body): Blogger/워드프레스 본문에 그대로 넣는 조각.
- 미리보기 페이지(render_preview): 승인 대시보드에서 보여줄 완전한 HTML 문서.
제목 크게, 소제목 강조, 문단 띄우기, 이미지 자리, 의학 고지 박스, 태그, SEO 메타 포함.
"""
from __future__ import annotations

import html


def _esc(s: str) -> str:
    return html.escape(s or "", quote=True)


def _image_block(url: str | None, prompt: str) -> str:
    """이미지가 있으면 <img>, 없으면 프롬프트가 보이는 회색 자리표시."""
    if url:
        return (f'<figure style="margin:24px 0;text-align:center">'
                f'<img src="{_esc(url)}" alt="{_esc(prompt)}" '
                f'style="max-width:100%;height:auto;border-radius:12px"/></figure>')
    return (f'<div style="margin:24px 0;padding:40px;background:#f1f3f5;border-radius:12px;'
            f'text-align:center;color:#868e96;font-size:14px">🖼️ 이미지 생성 예정<br>'
            f'<span style="font-size:12px">{_esc(prompt)}</span></div>')


def render_body(article: dict, images: dict[int, str] | None = None) -> str:
    """발행용 본문 HTML 조각(제목 제외 본문 + 고지 + 태그)."""
    images = images or {}
    parts: list[str] = []

    for i, sec in enumerate(article.get("sections", [])):
        parts.append(
            f'<h2 style="font-size:24px;font-weight:800;color:#212529;'
            f'margin:36px 0 14px;line-height:1.4">{_esc(sec.get("heading",""))}</h2>'
        )
        # 실제 생성된 이미지가 있는 섹션에만 표시(빈 자리표시 안 띄움)
        url = images.get(i)
        if url:
            parts.append(_image_block(url, sec.get("image_prompt", "")))
        for para in sec.get("paragraphs", []):
            parts.append(
                f'<p style="font-size:17px;line-height:1.9;color:#343a40;'
                f'margin:0 0 18px">{_esc(para)}</p>'
            )

    if article.get("disclaimer"):
        parts.append(
            f'<div style="margin:32px 0;padding:16px 20px;background:#fff3bf;'
            f'border-left:4px solid #f59f00;border-radius:8px;font-size:14px;color:#664d03">'
            f'⚠️ {_esc(article["disclaimer"])}</div>'
        )

    tags = article.get("tags", [])
    if tags:
        chips = " ".join(
            f'<span style="display:inline-block;background:#e7f5ff;color:#1971c2;'
            f'padding:4px 12px;border-radius:16px;font-size:13px;margin:4px 4px 0 0">'
            f'#{_esc(t)}</span>' for t in tags
        )
        parts.append(f'<div style="margin-top:28px">{chips}</div>')

    # 모든 글에 면책 고지 자동 삽입 (법적 위험 완화)
    parts.append(
        '<p style="margin-top:28px;padding-top:14px;border-top:1px solid #e9ecef;'
        'color:#adb5bd;font-size:12px;line-height:1.7">'
        '※ 본 글은 일반적인 정보 제공을 목적으로 작성되었으며, 내용의 정확성·완전성을 '
        '보장하지 않습니다. 가격·사양·통계 등 구체적인 정보는 공식 출처를 통해 확인하시기 '
        '바라며, 중요한 결정에 앞서 전문가와 상담하세요.</p>'
    )
    return "\n".join(parts)


def render_preview(article: dict, images: dict[int, str] | None = None,
                   thumbnail: str | None = None) -> str:
    """대시보드 미리보기용 완전한 HTML 문서."""
    title = _esc(article.get("title", "(제목 없음)"))
    desc = _esc(article.get("meta_description", ""))
    count = article.get("char_count", "")
    thumb = (f'<img src="{_esc(thumbnail)}" alt="{title}" '
             f'style="width:100%;max-height:380px;object-fit:cover;border-radius:16px;'
             f'margin-bottom:8px"/>') if thumbnail else ""
    body = render_body(article, images)
    return f"""<!doctype html>
<html lang="ko"><head><meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>{title}</title>
<meta name="description" content="{desc}"/>
<meta property="og:title" content="{title}"/>
<meta property="og:description" content="{desc}"/>
</head>
<body style="margin:0;background:#f8f9fa">
<article style="max-width:720px;margin:0 auto;padding:32px 20px 80px;
background:#fff;font-family:-apple-system,'Segoe UI','Malgun Gothic',sans-serif">
{thumb}
<h1 style="font-size:34px;font-weight:900;color:#212529;line-height:1.35;margin:12px 0 8px">{title}</h1>
<p style="color:#868e96;font-size:14px;margin:0 0 8px">{desc}</p>
<p style="color:#adb5bd;font-size:12px;margin:0 0 24px">본문 {count}자</p>
<hr style="border:none;border-top:1px solid #e9ecef;margin:0 0 8px"/>
{body}
</article></body></html>"""


def seo_meta(article: dict) -> dict:
    """발행 시 함께 넘길 SEO 메타."""
    return {
        "title": article.get("title", ""),
        "description": article.get("meta_description", ""),
        "labels": article.get("tags", []),
    }


def _demo() -> None:
    """키 없이 서식화만 시각 확인용 가짜 글."""
    from . import config
    article = {
        "title": "기아 PV5 수혜주 총정리 — 지금 주목받는 종목",
        "meta_description": "기아 PV5 출시로 함께 주목받는 관련주와 투자 포인트를 한눈에 정리했습니다.",
        "tags": ["기아PV5", "수혜주", "전기차", "관련주", "투자"],
        "sections": [
            {"heading": "왜 지금 기아 PV5인가",
             "paragraphs": ["기아 PV5가 캠핑·소상공인 시장에서 화제입니다. " * 6,
                            "2500만원대 가격과 공간 활용성이 핵심 포인트입니다. " * 6],
             "image_prompt": "a modern electric van for camping, sunny day, photo"},
            {"heading": "함께 주목받는 관련주",
             "paragraphs": ["배터리·부품 협력사들이 대표적입니다. " * 6],
             "image_prompt": "stock chart going up on a screen, photo"},
        ],
        "disclaimer": "",
        "char_count": 1234,
    }
    out = config.DATA_DIR / "preview_demo.html"
    out.write_text(render_preview(article), encoding="utf-8")
    print(f"미리보기 데모 저장: {out}")


if __name__ == "__main__":
    _demo()
