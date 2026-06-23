"""2단계: 주제 전략 — 트렌드를 '클릭 잘 되는 각도'로 응용·조합·점수화·선정.

트렌드를 그대로 쓰지 않는다. 예) "젠슨황" → "젠슨황 방한 수혜주 총정리".
LLM 키가 있으면 더 똑똑한 응용/안전성 점검을 하고, 없으면 휴리스틱으로 동작한다.

핵심 정책:
- 금융/의학 키워드에 가중치(황금 키워드). 단, 의학은 법적 리스크 회피 플래그를 단다.
- 정치/사건사고/혐오·논란 인물은 감점(광고 적합성·브랜드 리스크).
- 한국 독자와 무관한 외국어 전용 트렌드는 제외.
"""
from __future__ import annotations

import dataclasses
import re

from . import config, trends

# ---- 카테고리 추정용 키워드 사전 (휴리스틱) ----
FINANCE_HINTS = ["주가", "주식", "증시", "코스피", "코스닥", "etf", "수혜주", "관련주",
                 "테마주", "배당", "금리", "환율", "비트코인", "코인", "상장", "ipo",
                 "반도체", "전기차", "2차전지", "ai", "엔비디아", "삼성", "현대", "기아",
                 "은행", "보험", "연금", "isa", "청약", "부동산", "달러", "유가", "실적"]
MEDICAL_HINTS = ["건강", "질환", "증상", "치료", "백신", "독감", "당뇨", "혈압", "다이어트",
                 "영양", "수면", "통증", "암", "비만", "콜레스테롤", "단백질", "운동", "면역"]
RISKY_HINTS = ["사망", "극단", "사건", "사고", "성범죄", "마약", "압수수색", "선거", "정청래",
               "대통령", "탄핵", "혐한", "논란", "폭행", "살해", "시신", "재판", "구속",
               # 전쟁·재난·폭력(애드센스 광고 제한 대상)
               "타격", "전쟁", "공습", "미사일", "핵", "테러", "폭격", "교전", "침공",
               "사상자", "총격", "참사", "붕괴", "지진", "납치", "인질", "쿠데타"]

# 단독으로 쓰면 너무 광범위해 글이 막연해지는 키워드(감점 또는 제외)
TOO_BROAD = {"미국", "중국", "일본", "러시아", "이란", "북한", "유럽", "한국", "정부", "세계"}
ENTERTAIN_HINTS = ["배우", "가수", "아이돌", "드라마", "예능", "데뷔", "컴백", "엠카",
                   "나는솔로", "결혼", "열애", "방송",
                   # 스포츠(클릭은 되나 브랜드 안 맞고 단가 낮음 → 비중↓)
                   "월드컵", "축구", "야구", "농구", "골프", "올림픽", "경기", "우승",
                   "결승", "선수", "리그", "감독", "손흥민", "음바페", "메시", "홈런"]

# ---- 각도(앵글) 템플릿 ----
FINANCE_ANGLES = [
    "{kw} 관련주·수혜주 총정리 (지금 주목받는 종목)",
    "{kw} 뜨자 함께 오르는 ETF·테마 정리",
    "{kw} 이슈, 투자자라면 꼭 봐야 할 포인트",
]
MEDICAL_ANGLES = [
    "{kw}, 알아두면 좋은 건강 상식 (전문 정보 정리)",
    "{kw} 관련 흔한 오해와 사실 체크",
]
GENERAL_ANGLES = [
    "{kw}이(가) 화제인 진짜 이유 정리",
    "{kw}, 오늘 꼭 알아야 할 핵심만",
    "{kw} 총정리 — 배경부터 전망까지",
]

HANGUL = re.compile(r"[가-힣]")

# 트렌드 글이 검증에서 탈락했을 때 쓰는 '환각 위험이 거의 없는' 안전 상식 글감(돌아가며 사용)
EVERGREEN: list[tuple[str, str, str]] = [
    # 금융·재테크 (검색량 큼·CPM 높음)
    ("ISA 계좌", "finance", "💰 ISA 계좌, 모르면 세금 더 낸다? 기초부터 활용법까지"),
    ("연말정산", "finance", "🧾 연말정산 '13월의 월급' 만들기, 핵심만 콕!"),
    ("청년도약계좌", "finance", "🌱 청년도약계좌, 진짜 5천만원 모일까? 조건 총정리"),
    ("주택청약 1순위", "finance", "🏠 주택청약 1순위 조건, 헷갈리는 것만 정리"),
    ("연금저축 세액공제", "finance", "💸 연금저축으로 세금 돌려받기, 얼마나 아낄까?"),
    ("신용점수 올리기", "finance", "📈 신용점수 어떻게 올리지? 생활 속 꿀팁 모음"),
    ("해외 ETF 기초", "finance", "🌎 해외 ETF 처음이라면? S&P500부터 차근차근"),
    ("환율 기초", "finance", "💱 환율 오르면 내 돈은? 알아두면 쓸모있는 환율 상식"),
    # 정책·지원금 (검색량 폭발)
    ("정부 지원금 신청", "general", "🎁 놓치면 손해! 받을 수 있는 정부 지원금 정리"),
    ("근로장려금", "general", "💵 근로장려금, 나도 받을 수 있을까? 조건·신청법"),
    ("실업급여 조건", "general", "🧭 실업급여, 얼마·언제까지? 헷갈리는 조건 정리"),
    ("국민연금 수령액", "general", "👵 내 국민연금 얼마 받나? 수령액 늘리는 법"),
    # 건강 상식 (검색량 큼·중장년 타깃)
    ("고혈압 관리", "medical", "🩺 고혈압, 알고 보면 관리되는 병 — 핵심 상식"),
    ("당뇨 초기 증상", "medical", "🍚 당뇨, 이런 신호 놓치지 마세요 — 초기 증상 정리"),
    ("콜레스테롤 낮추기", "medical", "🥗 콜레스테롤, 음식으로 잡는 법 (오해와 사실)"),
    ("잠 잘 자는 법", "medical", "😴 잠이 보약! 숙면을 부르는 생활 습관"),
    ("단백질 섭취", "medical", "💪 단백질 하루 얼마나? 근육·노화에 중요한 이유"),
    ("무릎 관절 건강", "medical", "🦵 무릎 오래 쓰는 법 — 관절 건강 생활 수칙"),
    # 생활 상식·꿀팁 (검색량 큼·에버그린)
    ("전기요금 절약", "general", "⚡ 전기요금 폭탄 피하는 법 — 생활 속 절약 꿀팁"),
    ("냉장고 정리", "general", "🧊 냉장고 정리만 잘해도! 음식 안 버리는 보관법"),
    ("곰팡이 제거", "general", "🧽 욕실 곰팡이, 이렇게 잡으세요 — 제거·예방법"),
    ("자동차 연비 높이기", "general", "🚗 기름값 아끼는 운전 습관 — 연비 높이는 법"),
]


def evergreen_topic(index: int) -> "TopicCandidate":
    kw, cat, angle = EVERGREEN[index % len(EVERGREEN)]
    return TopicCandidate(keyword=kw, category=cat, angle=angle, score=0,
                          needs_medical_disclaimer=(cat == "medical"))


@dataclasses.dataclass
class TopicCandidate:
    keyword: str
    category: str            # finance / medical / entertainment / general / risky
    angle: str               # 최종 제안 제목(각도)
    score: float
    traffic: str = ""
    context: str = ""        # 연관 뉴스 한 줄
    needs_medical_disclaimer: bool = False
    reasons: list[str] = dataclasses.field(default_factory=list)

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "TopicCandidate":
        fields = {f.name for f in dataclasses.fields(cls)}
        return cls(**{k: v for k, v in d.items() if k in fields})


def _has(text: str, hints: list[str]) -> bool:
    low = text.lower()
    return any(h in low for h in hints)


def _categorize(text: str) -> str:
    if _has(text, RISKY_HINTS):
        return "risky"
    if _has(text, FINANCE_HINTS):
        return "finance"
    if _has(text, MEDICAL_HINTS):
        return "medical"
    if _has(text, ENTERTAIN_HINTS):
        return "entertainment"
    return "general"


def _parse_traffic(traffic: str) -> int:
    """'1000+' / '20,000+' → 정수."""
    digits = re.sub(r"[^\d]", "", traffic or "")
    return int(digits) if digits else 0


def _korean_relevant(item: trends.TrendItem) -> bool:
    """한국 독자와 관련된 트렌드인가(제목 또는 연관뉴스에 한글이 있나)."""
    if HANGUL.search(item.title):
        return True
    blob = " ".join(item.news_titles)
    return bool(HANGUL.search(blob))


def _build_candidate(item: trends.TrendItem) -> TopicCandidate | None:
    # 제목 + 연관뉴스로 카테고리 판단 (연예인 이름 등은 뉴스 문맥이 힌트)
    blob = item.title + " " + " ".join(item.news_titles)
    category = _categorize(blob)
    traffic_n = _parse_traffic(item.traffic)
    reasons: list[str] = []

    # 너무 광범위한 단독 키워드는 글이 막연해지므로 강하게 감점
    if item.title.strip() in TOO_BROAD:
        category = "risky" if category != "risky" else category
        reasons.append("광범위 단독 키워드(주제 막연)→제외")

    # 점수: 검색량 기반 베이스 + 카테고리 가중
    score = min(traffic_n, 5000) / 1000.0  # 0~5
    if category == "finance":
        score += 4.0
        reasons.append("금융=황금 키워드(+4)")
        # 실제 투자 신호가 있을 때만 '수혜주' 각도(아니면 무의미 주제 방지: 정보형 각도)
        stock_signals = ["주가", "상장", "증시", "코스피", "코스닥", "수혜", "관련주",
                         "실적", "반도체", "전기차", "2차전지", "배터리", "ipo", "공모",
                         "엔비디아", "테슬라", "삼성전자", "주식", "종목"]
        if _has(blob, stock_signals):
            angle = FINANCE_ANGLES[0].format(kw=item.title)
        else:
            angle = f"{item.title}, 지금 왜 화제일까? 핵심만 콕 정리 📌"
            reasons.append("투자신호 약함→정보형 각도")
    elif category == "medical":
        score += 3.0
        reasons.append("의학=고수익 키워드(+3, 단 법적 고지 필요)")
        angle = MEDICAL_ANGLES[0].format(kw=item.title)
    elif category == "entertainment":
        score += 0.3
        reasons.append("연예·스포츠=브랜드 안맞음·단가 낮음(+0.3)")
        angle = GENERAL_ANGLES[0].format(kw=item.title)
    elif category == "risky":
        score -= 5.0
        reasons.append("정치/사건사고=광고 부적합 리스크(-5)")
        angle = GENERAL_ANGLES[2].format(kw=item.title)
    else:
        angle = GENERAL_ANGLES[1].format(kw=item.title)

    # 금융 키워드와 '간접 연결' 가능한 일반 트렌드는 보너스 (예: 신차/IT 이슈 → 관련주)
    if category in ("general", "entertainment") and _has(blob, ["출시", "신차", "공개", "방한", "투자", "공장", "ai", "신제품"]):
        score += 1.0
        reasons.append("금융 각도로 응용 가능(+1)")

    context = item.news_titles[0] if item.news_titles else ""
    return TopicCandidate(
        keyword=item.title,
        category=category,
        angle=angle,
        score=round(score, 2),
        traffic=item.traffic,
        context=context,
        needs_medical_disclaimer=(category == "medical"),
        reasons=reasons,
    )


def rank(raw: dict, top_n: int = 8) -> list[TopicCandidate]:
    """수집 결과 dict → 점수순 후보 리스트(휴리스틱)."""
    items = [trends.TrendItem(**t) for t in raw.get("trends", [])]
    cands: list[TopicCandidate] = []
    for it in items:
        if not _korean_relevant(it):
            continue
        c = _build_candidate(it)
        if c:
            cands.append(c)
    cands.sort(key=lambda c: c.score, reverse=True)
    return cands[:top_n]


def pick(raw: dict) -> tuple[TopicCandidate | None, list[TopicCandidate]]:
    """최종 1개 + 후보 리스트. risky 는 후보에는 두되 자동선정에선 제외."""
    ranked = rank(raw)
    publishable = [c for c in ranked if c.category != "risky" and c.score > 0]
    chosen = publishable[0] if publishable else None
    return chosen, ranked


def _main() -> None:
    raw = trends.collect()
    chosen, ranked = pick(raw)
    print("\n=== 주제 후보 (점수순) ===")
    for i, c in enumerate(ranked, 1):
        flag = " ⚠의학고지" if c.needs_medical_disclaimer else ""
        print(f"{i:2}. [{c.score:>5}] ({c.category}){flag}  {c.keyword}")
        print(f"     제안 제목: {c.angle}")
        if c.reasons:
            print(f"     근거: {', '.join(c.reasons)}")
    print("\n=== 오늘의 자동 선정 ===")
    if chosen:
        print(f"  ★ {chosen.angle}")
        print(f"     (키워드: {chosen.keyword} / 카테고리: {chosen.category} / 점수: {chosen.score})")
        if chosen.context:
            print(f"     맥락: {chosen.context}")
    else:
        print("  선정할 만한 안전한 주제가 없음 — 다음 수집 주기까지 대기 권장.")


if __name__ == "__main__":
    _main()
