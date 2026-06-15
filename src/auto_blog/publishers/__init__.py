"""6단계: 발행.

승인된 글을 각 플랫폼에 내보낸다.
- Blogger: 공식 API 로 자동 발행(설정돼 있을 때).
- 네이버: 자동발행 안 함 → 복붙용 HTML 초안 파일 생성.
- 워드프레스: 나중에 연결(설정 시 자동 발행).
"""
from __future__ import annotations

from pathlib import Path

from .. import config
from . import naver_draft


def _int_keys(images: dict) -> dict:
    """JSON 저장 시 문자열이 된 이미지 키를 int 로 되돌린다."""
    out = {}
    for k, v in (images or {}).items():
        try:
            out[int(k)] = v
        except (ValueError, TypeError):
            out[k] = v
    return out


def publish(record: dict, post_dir: Path) -> dict:
    """승인된 record 를 발행. 결과를 플랫폼별 dict 로 반환."""
    results: dict[str, str] = {}

    # 1) 네이버 복붙 초안은 항상 생성
    try:
        path = naver_draft.generate(record, post_dir)
        results["naver"] = f"초안 생성됨: {path.name} (네이버에 복붙)"
    except Exception as e:
        results["naver"] = f"실패: {e}"

    # 2) Blogger 자동 발행 (설정돼 있을 때만)
    if config.get("BLOGGER_BLOG_ID"):
        try:
            from . import blogger
            url = blogger.publish(record, post_dir)
            results["blogger"] = f"발행됨: {url}"
            # 영문 번역본 자동 발행 (TRANSLATE_TO_ENGLISH=true 일 때)
            if config.TRANSLATE_TO_ENGLISH:
                try:
                    from .. import translate
                    en = translate.translate_article(record["article"])
                    en_url = blogger.publish_article(en, record, post_dir)
                    record["article_en"] = en
                    results["blogger_en"] = f"발행됨(EN): {en_url}"
                except Exception as e:
                    results["blogger_en"] = f"영문 실패: {e}"
        except Exception as e:
            results["blogger"] = f"실패: {e}"
    else:
        results["blogger"] = "건너뜀: BLOGGER_BLOG_ID 미설정"

    # 3) 워드프레스 (설정 시)
    if config.get("WORDPRESS_URL") and config.get("WORDPRESS_APP_PASSWORD"):
        try:
            from . import wordpress
            url = wordpress.publish(record, post_dir)
            results["wordpress"] = f"발행됨: {url}"
        except Exception as e:
            results["wordpress"] = f"실패: {e}"
    else:
        results["wordpress"] = "건너뜀: 워드프레스 미설정"

    return results
