"""제휴마케팅 모듈 — 글에 어울리는 쿠팡 파트너스 추천 상품/증권사 제휴 링크를 붙인다.

설계 의도(메모리 [[autoblog-project]] 수익화 결정):
- 애드센스만으로는 RPM 이 낮다. 같은 트래픽에서 **구매의도(commercial intent)가 있는 글**에만
  제휴 링크를 넣어 수익을 끌어올린다. 정보형 글은 건드리지 않는다.
- 한계비용이 거의 0: 상품 추출 LLM 호출 1회 + 쿠팡 딥링크 API(무료)뿐.

흐름:
  enrich(article, topic)
    ├─ (의학 제외, 키 있으면) LLM 으로 상품 검색어 2~3개 추출 → 쿠팡 딥링크 생성
    ├─ (금융 글) 증권사 계좌개설 제휴 고정 링크
    └─ 결과를 article["affiliate"] 에 저장 → formatter.render_body 가 본문에 렌더

법적 안전(공정위 표시광고법): 제휴 링크가 하나라도 있으면 '대가성 문구'를 링크 근처에 명확히
삽입한다(disclosure). 허위·과장 후기는 쓰지 않는다(상품은 '검색 결과'로만 연결).
"""
from __future__ import annotations

import hashlib
import hmac
import json
import urllib.parse
import urllib.request
from datetime import datetime, timezone

from . import config

# ---- 공정위 필수 대가성 고지 ----
DISCLOSURE_KO = ("이 글에는 제휴(쿠팡 파트너스 등) 링크가 포함되어 있으며, 이를 통해 구매가 "
                 "발생하면 작성자가 일정액의 수수료를 제공받을 수 있습니다.")

COUPANG_DOMAIN = "https://api-gateway.coupang.com"
COUPANG_DEEPLINK_PATH = (
    "/v2/providers/affiliate_open_api/apis/openapi/v1/deeplink")


# ---------------------------------------------------------------- 설정
def _coupang_keys() -> tuple[str, str]:
    return config.get("COUPANG_ACCESS_KEY"), config.get("COUPANG_SECRET_KEY")


def coupang_enabled() -> bool:
    a, s = _coupang_keys()
    return bool(a and s)


# ---------------------------------------------------------------- 쿠팡 딥링크
def _coupang_search_url(keyword: str) -> str:
    q = urllib.parse.quote(keyword)
    return f"https://www.coupang.com/np/search?component=&q={q}&channel=user"


def _coupang_auth(method: str, path: str, access: str, secret: str) -> str:
    """쿠팡 파트너스 HMAC 서명(CEA) 헤더를 만든다."""
    signed_date = datetime.now(timezone.utc).strftime("%y%m%dT%H%M%SZ")
    message = signed_date + method + path
    signature = hmac.new(secret.encode("utf-8"), message.encode("utf-8"),
                         hashlib.sha256).hexdigest()
    return (f"CEA algorithm=HmacSHA256, access-key={access}, "
            f"signed-date={signed_date}, signature={signature}")


def coupang_deeplinks(keywords: list[str]) -> list[dict]:
    """검색어 목록 → [{"name": 검색어, "url": 단축 제휴링크}]. 실패 시 빈 리스트."""
    access, secret = _coupang_keys()
    if not (access and secret) or not keywords:
        return []
    urls = [_coupang_search_url(k) for k in keywords]
    body = json.dumps({"coupangUrls": urls}).encode("utf-8")
    auth = _coupang_auth("POST", COUPANG_DEEPLINK_PATH, access, secret)
    req = urllib.request.Request(
        COUPANG_DOMAIN + COUPANG_DEEPLINK_PATH, data=body, method="POST",
        headers={"Authorization": auth, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    out: list[dict] = []
    for kw, item in zip(keywords, data.get("data", []) or []):
        link = item.get("shortenUrl") or item.get("landingUrl") or item.get("originalUrl")
        if link:
            out.append({"name": kw, "url": link})
    return out


# ---------------------------------------------------------------- 상품 추출(LLM)
def extract_products(article: dict) -> list[str]:
    """글을 읽고 자연스럽게 어울리는 '실물 상품 검색어' 2~3개. 없으면 빈 리스트."""
    from . import writer
    client = writer._client()
    title = article.get("title", "")
    body = " ".join(
        p for s in article.get("sections", []) for p in s.get("paragraphs", [])
    )[:3000]
    res = writer._chat_json(client, [
        {"role": "system", "content":
            "너는 블로그 글에 어울리는 쿠팡 추천 상품을 고르는 도우미다. JSON 으로만 답한다."},
        {"role": "user", "content":
            "다음 글을 읽고, 독자가 실제로 구매할 만한 **쿠팡 상품 검색어** 2~3개를 고르라.\n"
            "규칙:\n"
            "- 글 주제와 자연스럽게 이어지는 실물 상품만(예: 수면 글→베개·수면안대, 캠핑 글→캠핑용품).\n"
            "- 정치·시술·금융상품·논란 주제처럼 쿠팡에서 팔지 않거나 부적절한 건 제외.\n"
            "- 너무 비싸거나 글과 동떨어진 상품은 넣지 마라. 애매하면 적게(또는 0개).\n"
            "- 적절한 상품이 없으면 반드시 빈 배열로 답하라.\n"
            '형식: {"products": ["검색어1", "검색어2"]}\n\n'
            f"[제목] {title}\n[본문] {body}"},
    ])
    return [p.strip() for p in res.get("products", []) if p and p.strip()][:3]


# ---------------------------------------------------------------- 오케스트레이터
def enrich(article: dict, topic=None) -> dict:
    """article 에 제휴 정보를 채운다(article["affiliate"]). 실패해도 발행은 막지 않는다.

    - 의학 카테고리: 상품 추천 제외(시술·치료 오인 방지, 법적 안전).
    - 금융 카테고리: 증권사 계좌개설 제휴 고정 링크(SECURITIES_AFFILIATE_URL).
    - 그 외: 쿠팡 추천 상품.
    """
    category = (getattr(topic, "category", None)
                or article.get("category") or "general")
    aff: dict = {
        "heading": "🛒 함께 보면 좋은 추천",
        "products": [],
        "securities": None,
        "disclosure": DISCLOSURE_KO,
    }

    # 1) 쿠팡 추천 상품 (의학 제외)
    if category != "medical" and coupang_enabled():
        try:
            keywords = extract_products(article)
            if keywords:
                aff["products"] = coupang_deeplinks(keywords)
        except Exception as e:  # 네트워크/LLM 실패는 조용히 무시(발행 우선)
            print(f"  [경고] 쿠팡 제휴 건너뜀: {e}")

    # 2) 금융 글 → 증권사 제휴 고정 링크
    if category == "finance":
        url = config.get("SECURITIES_AFFILIATE_URL")
        if url:
            aff["securities"] = {
                "text": config.get("SECURITIES_AFFILIATE_TEXT",
                                   "📈 주식 투자가 처음이라면? 증권 계좌 개설하고 시작하기"),
                "url": url,
            }

    has_any = bool(aff["products"] or aff["securities"])
    article["affiliate"] = aff if has_any else None
    if has_any:
        n = len(aff["products"]) + (1 if aff["securities"] else 0)
        print(f"  -> 제휴 링크 {n}개 삽입 (카테고리: {category})")
    return article
