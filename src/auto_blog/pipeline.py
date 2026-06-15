"""전체 파이프라인 오케스트레이터.

트렌드 수집 → 주제 선정 → 본문 생성 → (이미지) → 서식화 → 산출물 저장.
산출물은 data/posts/<slug>/ 아래에 article.json, preview.html 로 저장된다.
승인 대시보드가 이 폴더를 읽어 미리보기를 띄우고, 승인 시 발행 모듈이 발행한다.
"""
from __future__ import annotations

import json
import re
from datetime import datetime

from . import config, formatter, strategist, trends, writer


def _slug(text: str) -> str:
    s = re.sub(r"[^\w가-힣]+", "-", text).strip("-")
    return s[:40] or "post"


def propose() -> dict:
    """트렌드 수집 + 주제 후보 리스트(본문 생성 전, 저렴). 대시보드가 이걸 띄운다."""
    raw = trends.collect()
    ranked = strategist.rank(raw)
    return {
        "collected_at": raw.get("collected_at"),
        "candidates": [c.to_dict() for c in ranked],
    }


def generate_for_topic(topic: strategist.TopicCandidate, *,
                       generate_images: bool = True, max_images: int = 4,
                       ground: bool = True) -> dict:
    """선택된 주제 → 본문 + 이미지 + 서식화 → data/posts/ 에 저장하고 record 반환.

    ground=True(트렌드 주제)면 실제 뉴스를 근거로 쓰고 사실검증한다.
    ground=False(개념·상식 글)면 모델의 안정적 지식을 쓴다.
    """
    grounding = ""
    if ground:
        from . import research
        print("②.5 사실 근거(뉴스) 수집 중…")
        grounding, titles = research.fetch_grounding(topic.keyword)
        print(f"  근거 헤드라인 {len(titles)}건 확보")

    print(f"③ 본문 생성 중… (GPT)  주제: {topic.angle}")
    article = writer.write_article(topic, grounding)
    print(f"  완성: '{article.get('title')}'  ({article.get('char_count')}자)")

    stamp = datetime.now().strftime("%Y%m%d-%H%M")
    out_dir = config.DATA_DIR / "posts" / f"{stamp}-{_slug(topic.keyword)}"
    out_dir.mkdir(parents=True, exist_ok=True)

    images: dict[int, str] = {}
    thumbnail = None
    if generate_images:
        try:
            from . import images as imgmod
            print("④ 이미지 생성 중…")
            images, thumbnail = imgmod.generate_for_article(article, out_dir, max_images)
        except Exception as e:
            print(f"  [경고] 이미지 생성 건너뜀: {e}")

    print("⑤ 서식화 + 저장 중…")
    record = {
        "created_at": datetime.now().isoformat(),
        "topic": topic.to_dict(),
        "article": article,
        "images": images,
        "thumbnail": thumbnail,
        "status": "pending_approval",
        "dir": out_dir.name,
    }
    (out_dir / "article.json").write_text(
        json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    preview = formatter.render_preview(article, images, thumbnail)
    (out_dir / "preview.html").write_text(preview, encoding="utf-8")
    print(f"\n완료 ✅  미리보기: {out_dir / 'preview.html'}")
    return record


def run(generate_images: bool = True) -> dict | None:
    """자동 모드: 후보 중 1순위(안전)를 골라 바로 생성."""
    print("① 트렌드 수집 + ② 주제 선정 중…")
    raw = trends.collect()
    chosen, ranked = strategist.pick(raw)
    if not chosen:
        print("  발행할 안전한 주제가 없습니다. 종료.")
        return None
    print(f"  ★ 선정: {chosen.angle}")
    return generate_for_topic(chosen, generate_images=generate_images)


def _finalize(topic: strategist.TopicCandidate, article: dict,
              max_images: int = 4) -> dict:
    """본문(article) → 이미지 + 서식화 + 저장 → record 반환."""
    stamp = datetime.now().strftime("%Y%m%d-%H%M")
    out_dir = config.DATA_DIR / "posts" / f"{stamp}-{_slug(topic.keyword)}"
    out_dir.mkdir(parents=True, exist_ok=True)
    images: dict[int, str] = {}
    thumbnail = None
    try:
        from . import images as imgmod
        print("④ 이미지 생성 중…")
        images, thumbnail = imgmod.generate_for_article(article, out_dir, max_images)
    except Exception as e:
        print(f"  [경고] 이미지 생성 건너뜀: {e}")
    record = {
        "created_at": datetime.now().isoformat(),
        "topic": topic.to_dict(),
        "article": article,
        "images": images,
        "thumbnail": thumbnail,
        "status": "pending_approval",
        "dir": out_dir.name,
        "used_fallback": getattr(topic, "_fallback", False),
    }
    (out_dir / "article.json").write_text(
        json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    (out_dir / "preview.html").write_text(
        formatter.render_preview(article, images, thumbnail), encoding="utf-8")
    return record


def run_auto() -> dict:
    """자동발행용 — 트렌드 글을 엄격검증, 통과 못 하면 안전 상식글로 교체해 생성.
    항상 발행 가능한 record 를 돌려준다(안전성 최우선)."""
    from . import research
    print("① 트렌드 수집 + ② 주제 선정…")
    raw = trends.collect()
    chosen, _ = strategist.pick(raw)

    article = None
    topic = None
    if chosen:
        print(f"  후보: {chosen.angle}")
        grounding, _t = research.fetch_grounding(chosen.keyword)
        print("③ 본문 생성 + 엄격 사실검증…")
        art, safe, issues = writer.write_article_safe(chosen, grounding)
        if safe:
            topic, article = chosen, art
            print(f"  ✅ 엄격검증 통과 (자동수정 {len(issues)}건)")
        else:
            print(f"  ⚠️ 엄격검증 미통과 → 안전 상식글로 교체 (수정 시도 {len(issues)}건)")

    if article is None:
        idx = datetime.now().timetuple().tm_yday
        topic = strategist.evergreen_topic(idx)
        topic._fallback = True
        print(f"③(대체) 안전 상식글 생성: {topic.angle}")
        article, safe, issues = writer.write_article_safe(topic, "")

    print(f"  완성: '{article.get('title')}'  ({article.get('char_count')}자)")
    record = _finalize(topic, article)
    return record


if __name__ == "__main__":
    import sys
    no_img = "--no-images" in sys.argv
    run(generate_images=not no_img)
