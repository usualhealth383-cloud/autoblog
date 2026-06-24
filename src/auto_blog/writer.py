"""3단계: 본문 생성.

GPT로 약 1500~2000자 한국어 글을 JSON 구조로 받아 글자 수·소제목·이미지 프롬프트·
SEO 메타·의학 고지를 한 번에 통제한다. Gemini/Claude 키가 있으면 교차검수로 한 번
더 다듬고, 없으면 GPT 자기검토 1회로 대체한다.

산출물(Article dict):
  title, meta_description, tags[], sections[{heading, paragraphs[], image_prompt}],
  disclaimer, keyword, category
"""
from __future__ import annotations

import json
import re

from . import config
from .strategist import TopicCandidate

MODEL = config.get("OPENAI_MODEL", "gpt-4o")
MIN_CHARS, MAX_CHARS = 1500, 2100

SYSTEM = """너는 한국 블로그 글을 쓰는 인기 작가다. 정보가 정확하고, 읽기 쉽고,
사람들이 끝까지 읽고 싶게 쓴다. 과장·낚시는 피하되 제목은 클릭하고 싶게 만든다.
반드시 한국어로 쓴다.

[깊이·유용성 — 가장 중요. "AI가 대충 쓴 글"이 절대 되면 안 된다]
- 제공된 [RESEARCH] 자료를 충분히 읽고, 거기 담긴 **구체적 사실·정의·수치·사례·맥락을 적극
  활용**해 깊이 있게 써라. 두루뭉술한 일반론·뻔한 말로 분량만 채우는 글은 실패다.
- 독자가 "오, 이건 몰랐네 / 이거 진짜 유용하다" 싶을 **알맹이(실전 정보, 구체적 방법,
  비교, 예시, 주의점)**를 반드시 담아라. 각 섹션이 새로운 정보를 줘야 한다.
- 같은 말 반복·동어반복 금지. 문단마다 다른 포인트를 다뤄라.
- 단, 자료에 없는 구체 수치는 지어내지 마라(아래 '사실 정확성' 준수).

[저작권 — 반드시 지켜라]
- 자료(위키백과·뉴스 등)의 문장을 **그대로 베끼지 마라.** 사실·수치·개념만 참고하고,
  **반드시 네 표현으로 완전히 새로 써라**(패러프레이즈). 표현은 창작, 사실만 빌린다.
- 특정 자료의 문장·문단을 통째로 옮기면 안 된다.

[말투·스타일 — 재미있고 유쾌하게]
- 친근한 입말체로 독자에게 말 걸듯 쓴다("~인데요", "~거든요", "솔직히 ~죠?").
- 도입부는 강한 후킹으로 시작하고, 위트·공감·호기심 자극으로 끝까지 읽게 만든다.
- 이모지를 적절히(과하지 않게) 쓴다: 제목과 각 소제목에 어울리는 이모지 1개,
  본문에는 가끔. 한 문단에 이모지를 남발하지 않는다.
- 금융·건강처럼 신뢰가 중요한 주제는 가볍고 친근하되 경박하지 않게(정보의 무게는 유지).
- 단, 아래 '사실 정확성·법적 안전'은 말투와 상관없이 언제나 최우선으로 지킨다.

[사실 정확성 — 가장 중요]
- 확실하지 않은 구체 수치(가격, 연비, 배기량, 출시일, 스펙, 통계, 종목명, 주가)는
  지어내지 마라. 모르면 "정확한 사양은 공식 발표를 확인하라"는 식으로 일반적으로 쓰거나 생략하라.
- 근거 자료(SOURCES)가 주어지면, 구체적 사실은 그 자료에 있는 것만 단정하라.
  자료에 없는 숫자·스펙은 절대 단정하지 마라.

[법적 안전 — 반드시 지켜라]
- 실존 인물·기업·브랜드에 대해 부정적·비방적 단정을 쓰지 마라(사실적시 명예훼손 위험).
  논란·의혹은 다루지 말고, 다뤄야 하면 "~라고 보도되었다"처럼 출처를 명시한 전언으로만.
- 단정 대신 신중한 표현을 써라: "~이다" 대신 적절히 "~로 알려져 있다 / ~로 보인다 /
  ~라고 보도되었다". 효능·수익·결과를 보장하는 표현(반드시·100%·확실히 오른다 등)은 금지.
- 의료·금융·법률 조언처럼 들리는 단정(진단·처방·매수 권유)을 하지 마라."""

# 의학 카테고리일 때만 덧붙이는 안전 지침(법적 리스크 회피)
MEDICAL_RULES = """
이 글은 건강/의학 주제다. 반드시 지켜라:
- 진단·처방·단정("~하면 낫는다", "~에 효과가 있다") 금지. "알려져 있다/연구가 있다" 같은 표현 사용.
- 특정 제품·약 추천 금지.
- disclaimer 필드에 "본 글은 일반적인 정보 제공 목적이며 의학적 조언이 아닙니다.
  증상이 있으면 전문의와 상담하세요."를 한국어로 넣어라.
"""

JSON_SHAPE = """
다음 JSON 형식으로만 답하라(설명·마크다운 금지):
{
  "title": "클릭하고 싶은 위트있는 제목(35자 이내, 이모지 1개 포함 가능)",
  "meta_description": "검색결과에 보일 요약 (120~150자)",
  "tags": ["다양하게 10~13개", "핵심키워드+관련어+롱테일(긴 검색어)+사람들이 실제 검색할 표현을 골고루"],
  "sections": [
    {
      "heading": "소제목(앞이나 뒤에 어울리는 이모지 1개)",
      "paragraphs": ["문단", "문단(각 문단 3~6문장)"],
      "image_prompt": "이 단락에 어울리는 이미지를 만들 영어 프롬프트(사진풍, 텍스트 없이)"
    }
  ],
  "disclaimer": "의학 주제면 고지문, 아니면 빈 문자열"
}
규칙:
- 소제목(sections) 4~6개. 도입(강한 후킹) → 핵심 내용 → 다정한 마무리 흐름. 주제에 맞게 유연하게.
- 각 섹션은 문단(paragraph) 1~2개로 **알차게**(실전 정보·구체 팁·맥락). 두루뭉술한 일반론 금지.
- 모든 문단 글자 수 합계가 공백 포함 **약 1500~2000자**가 되게. 주제 분량에 따라 조금 차이나도 괜찮다.
  재밌고 술술 읽히게.
- image_prompt: 그 섹션의 **핵심 소재·상황을 구체적으로** 담은 영어 묘사(추상적·일반적 배경 금지,
  실제 피사체와 장면을 명시). 글 주제와 한눈에 연관되게. 저작권 안전한 생성용 묘사. 텍스트·로고 없이.
"""


def _client():
    from openai import OpenAI
    key = config.OPENAI_API_KEY
    if not key:
        raise RuntimeError("OPENAI_API_KEY 가 .env 에 없습니다.")
    return OpenAI(api_key=key)


def _char_count(article: dict) -> int:
    body = " ".join(
        p for s in article.get("sections", []) for p in s.get("paragraphs", [])
    )
    return len(body)


def _chat_json(client, messages: list[dict]) -> dict:
    resp = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        response_format={"type": "json_object"},
        temperature=0.7,
        max_tokens=8000,
    )
    return json.loads(resp.choices[0].message.content)


def generate_draft(topic: TopicCandidate, grounding: str = "") -> dict:
    """주제 후보 → 본문 JSON. 글자 수가 모자라면 1회 보강."""
    client = _client()
    rules = MEDICAL_RULES if topic.needs_medical_disclaimer else ""
    if grounding:
        sources = (f"\n[RESEARCH — 이 자료를 충분히 읽고, 구체적 사실·수치·사례를 적극 활용해 "
                   f"깊이 있게 써라. 단, 여기 없는 구체 수치는 지어내지 마라]\n{grounding}\n")
    else:
        sources = ("\n[근거 자료 없음 — 일반 상식 글] 변하기 쉬운 구체 수치(금액·세율·수익률·"
                   "한도·연도·통계·순위)는 절대 단정하지 말고 '일정 한도 / 관련 세율 / 수년 전 도입 / "
                   "비과세 혜택' 처럼 일반화하라. 정확한 수치가 필요하면 '최신 공식 정보를 "
                   "확인하세요'라고 안내하라.\n")
    user = f"""주제(제안 제목): {topic.angle}
원본 트렌드 키워드: {topic.keyword}
참고 맥락(뉴스 한 줄): {topic.context or "(없음)"}
카테고리: {topic.category}
{sources}{rules}
{JSON_SHAPE}"""

    article = _chat_json(client, [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": user},
    ])

    # 글자 수 보정: 목표에 도달할 때까지 최대 3회 반복 확장
    for _ in range(3):
        count = _char_count(article)
        if count >= MIN_CHARS:
            break
        need = MIN_CHARS - count
        article = _chat_json(client, [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": user},
            {"role": "assistant", "content": json.dumps(article, ensure_ascii=False)},
            {"role": "user", "content":
                f"지금 본문이 공백 포함 약 {count}자로 목표({MIN_CHARS}~{MAX_CHARS}자)보다 "
                f"약 {need}자 부족하다. 같은 JSON 형식 그대로, 기존 내용을 유지하면서 "
                f"섹션을 추가하거나 각 문단을 더 구체적인 예시·수치·배경 설명으로 늘려 "
                f"전체를 {MIN_CHARS}~{MAX_CHARS}자로 다시 출력하라. 절대 짧아지면 안 된다."},
        ])

    article["keyword"] = topic.keyword
    article["category"] = topic.category
    if topic.needs_medical_disclaimer and not article.get("disclaimer"):
        article["disclaimer"] = ("본 글은 일반적인 정보 제공 목적이며 의학적 조언이 아닙니다. "
                                  "증상이 있으면 전문의와 상담하세요.")
    if topic.category == "finance" and not article.get("disclaimer"):
        article["disclaimer"] = ("본 글은 정보 제공 목적이며 특정 종목의 매수·매도를 권유하지 "
                                  "않습니다. 투자 판단과 책임은 본인에게 있습니다.")
    return article


# ---- 교차검수(옵션): 키가 있을 때만 동작 ----
def cross_review(article: dict, topic: TopicCandidate) -> dict:
    """Gemini/Claude 키가 있으면 비평을 받아 GPT가 반영. 없으면 그대로 반환."""
    critiques = []
    g = _gemini_critique(article)
    if g:
        critiques.append(("Gemini", g))
    c = _claude_critique(article)
    if c:
        critiques.append(("Claude", c))
    if not critiques:
        return article  # 교차검수 비활성 — GPT 단독

    client = _client()
    joined = "\n\n".join(f"[{name} 검수 의견]\n{text}" for name, text in critiques)
    revised = _chat_json(client, [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content":
            f"아래는 네가 쓴 글(JSON)과 다른 AI들의 검수 의견이다. 의견 중 타당한 것을 반영해 "
            f"같은 JSON 형식으로 개선본을 내라. 글자 수 {MIN_CHARS}~{MAX_CHARS} 유지.\n\n"
            f"[원문]\n{json.dumps(article, ensure_ascii=False)}\n\n{joined}"},
    ])
    revised["keyword"] = article.get("keyword")
    revised["category"] = article.get("category")
    revised.setdefault("disclaimer", article.get("disclaimer", ""))
    return revised


def _gemini_critique(article: dict) -> str | None:
    if not config.GEMINI_API_KEY:
        return None
    try:
        from google import genai
        client = genai.Client(api_key=config.GEMINI_API_KEY)
        prompt = ("다음 한국어 블로그 글(JSON)을 검수해 사실오류·어색한 표현·구조 개선점을 "
                  "한국어로 5줄 이내로 지적하라:\n" + json.dumps(article, ensure_ascii=False))
        r = client.models.generate_content(
            model=config.get("GEMINI_MODEL", "gemini-1.5-flash"), contents=prompt)
        return (r.text or "").strip()
    except Exception as e:
        print(f"  [경고] Gemini 검수 건너뜀: {e}")
        return None


def _claude_critique(article: dict) -> str | None:
    if not config.ANTHROPIC_API_KEY:
        return None
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
        msg = client.messages.create(
            model=config.get("ANTHROPIC_MODEL", "claude-sonnet-4-6"),
            max_tokens=1024,
            messages=[{"role": "user", "content":
                "다음 한국어 블로그 글(JSON)을 검수해 사실오류·과장·가독성 개선점을 한국어로 "
                "5줄 이내로 지적하라:\n" + json.dumps(article, ensure_ascii=False)}],
        )
        return "".join(b.text for b in msg.content if hasattr(b, "text")).strip()
    except Exception as e:
        print(f"  [경고] Claude 검수 건너뜀: {e}")
        return None


def verify_and_fix(article: dict, grounding: str) -> tuple[dict, list[str]]:
    """근거 자료에 없는 구체 수치/스펙을 찾아 제거·일반화. (grounding 있을 때만)"""
    if not grounding:
        return article, []
    client = _client()
    check = _chat_json(client, [
        {"role": "system", "content":
            "너는 팩트체커다. 글의 구체적 주장(숫자, 가격, 연비, 배기량, 스펙, 출시일, 통계, "
            "종목명 등)이 주어진 SOURCES 로 뒷받침되는지 검사한다. JSON 으로만 답하라."},
        {"role": "user", "content":
            f"[SOURCES]\n{grounding}\n\n[글(JSON)]\n{json.dumps(article, ensure_ascii=False)}\n\n"
            '다음 형식으로 답하라: {"unsupported": ["근거 없는 구체 주장1", "..."]}. '
            "SOURCES 로 확인 불가한 구체 수치·스펙만 골라라. 일반적 서술은 제외."},
    ])
    issues = [s for s in check.get("unsupported", []) if s]
    if not issues:
        return article, []

    # 문제가 있으면: 해당 주장들을 제거/일반화해 다시 출력
    fixed = _chat_json(client, [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content":
            f"아래 글(JSON)에서 다음 '근거 없는 구체 주장'들을 삭제하거나, 수치를 빼고 "
            f"일반적 서술로 바꿔라(예: '연비 15km/L' → '연비가 우수한 편'). 같은 JSON 형식, "
            f"글자 수 {MIN_CHARS}~{MAX_CHARS} 유지.\n\n근거 없는 주장:\n"
            + "\n".join(f"- {s}" for s in issues)
            + f"\n\n[글]\n{json.dumps(article, ensure_ascii=False)}"}],
    )
    fixed["keyword"] = article.get("keyword")
    fixed["category"] = article.get("category")
    fixed.setdefault("disclaimer", article.get("disclaimer", ""))
    return fixed, issues


def write_article(topic: TopicCandidate, grounding: str = "") -> dict:
    """본문 생성 → 사실검증·자동수정 → 교차검수."""
    article = generate_draft(topic, grounding)
    article, issues = verify_and_fix(article, grounding)
    if issues:
        print(f"  🔍 사실검증: 근거 없는 주장 {len(issues)}건 자동 수정")
        for s in issues[:5]:
            print(f"     - {s}")
    article = cross_review(article, topic)
    article["char_count"] = _char_count(article)
    article["fact_issues_fixed"] = issues
    return article


def _restore_meta(new: dict, old: dict) -> dict:
    new["keyword"] = old.get("keyword")
    new["category"] = old.get("category")
    if not new.get("disclaimer"):
        new["disclaimer"] = old.get("disclaimer", "")
    return new


def final_safety_gate(article: dict, grounding: str) -> tuple[dict, bool, list[str]]:
    """자동발행 직전 엄격 검증. 근거 없는 구체주장/허위가능/명예훼손 소지를 최대 2회
    제거·일반화하고, 그래도 심각한 문제가 남으면 safe=False 를 돌려준다(=발행 보류)."""
    client = _client()
    fixed: list[str] = []
    CHECK_SYS = ("너는 매우 엄격한 팩트체커 겸 법률 리스크 검토자다. 의심스러우면 문제로 "
                 "간주한다. 반드시 JSON 으로만 답한다.")

    def _check(art: dict) -> list[str]:
        res = _chat_json(client, [
            {"role": "system", "content": CHECK_SYS},
            {"role": "user", "content":
                f"[SOURCES(사실 근거)]\n{grounding or '(없음 — 일반 상식 글)'}\n\n"
                f"[검토할 글]\n{json.dumps(art, ensure_ascii=False)}\n\n"
                "아래 4가지만 '문제'로 보고, 나머지는 문제가 아니다:\n"
                "A) 변하기 쉬운 구체 수치를 현재 사실처럼 단정 "
                "(가격·금리·한도·세율·연봉기준·올해 통계·순위 등)\n"
                "B) 시점이 걸린 주장('최근 발표된', '올해부터', '지난달', '신규 출시' 등)인데 "
                "SOURCES 로 확인 불가\n"
                "C) 실존 인물·기업에 대한 부정적·비방·명예훼손 소지 표현\n"
                "D) 효능·수익·결과를 보장하는 표현(반드시·100%·무조건 오른다 등)\n"
                "단, 널리 알려진 '개념 설명'과 정성적·일반적 조언(예: '세금 절약에 도움이 된다', "
                "'분산투자가 중요하다')은 문제가 아니다. SOURCES 가 있으면 그 안의 사실은 문제 아님.\n"
                '형식: {"issues": ["문제되는 주장", ...]}'}])
        return [s for s in res.get("issues", []) if s]

    for _ in range(3):
        issues = _check(article)
        if not issues:
            return article, True, fixed
        fixed += issues
        revised = _chat_json(client, [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content":
                f"아래 글에서 다음 문제들을 고쳐라. 핵심 규칙: **구체적인 숫자(금액·%·세율·"
                f"수익률·한도·연도·통계)를 모두 빼고** '일정 한도 / 관련 세율 / 수년 전 / "
                f"비과세 혜택' 처럼 일반화하라. 시점 주장('최근·올해·지난달')과 보장 표현도 "
                f"없애라. 명예훼손 소지 표현은 삭제하라. 의미·흐름은 살리되 단정하지 마라. "
                f"같은 JSON 형식, 글자 수 {MIN_CHARS}~{MAX_CHARS} 유지.\n\n문제 목록:\n"
                + "\n".join(f"- {s}" for s in issues)
                + f"\n\n[글]\n{json.dumps(article, ensure_ascii=False)}"}])
        article = _restore_meta(revised, article)

    remaining = _check(article)  # 3회 수정 후 최종 점검
    return article, (len(remaining) == 0), fixed


def write_article_safe(topic: TopicCandidate, grounding: str = "") -> tuple[dict, bool, list[str]]:
    """자동발행용 — 본문 생성 + 강한 사실검증 + 엄격 게이트. (article, 발행안전여부, 수정내역)."""
    article = generate_draft(topic, grounding)
    article, issues1 = verify_and_fix(article, grounding)
    article, safe, issues2 = final_safety_gate(article, grounding)
    article["char_count"] = _char_count(article)
    article["fact_issues_fixed"] = issues1 + issues2
    article["safe_to_publish"] = safe
    # 면책 보강
    if topic.category == "finance" and not article.get("disclaimer"):
        article["disclaimer"] = ("본 글은 정보 제공 목적이며 특정 종목의 매수·매도를 권유하지 "
                                  "않습니다. 투자 판단과 책임은 본인에게 있습니다.")
    if topic.needs_medical_disclaimer and not article.get("disclaimer"):
        article["disclaimer"] = ("본 글은 일반적인 정보 제공 목적이며 의학적 조언이 아닙니다. "
                                  "증상이 있으면 전문의와 상담하세요.")
    return article, safe, article["fact_issues_fixed"]
