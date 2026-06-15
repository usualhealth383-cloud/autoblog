"""5단계: 이미지 수급.

비용·화질을 위해 **무료·저작권 안전 스톡 사진(Pexels→Unsplash)을 먼저** 쓰고,
딱 맞는 게 없을 때만 AI(gpt-image-1)로 생성한다. 이미지는 글 폴더의 images/ 아래
JPEG 로 저장하고 상대경로를 돌려준다(발행 시 GitHub URL 호스팅은 publishers/daily_publish 처리).
"""
from __future__ import annotations

import base64
import re
from pathlib import Path

import requests

from . import config

# DALL·E 가 한국어 텍스트를 이미지에 박지 않도록 프롬프트에 가드 추가
PROMPT_GUARD = ", high quality editorial photograph, no text, no letters, no words"


def _client():
    from openai import OpenAI
    if not config.OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY 가 없습니다.")
    return OpenAI(api_key=config.OPENAI_API_KEY)


def _save_jpeg(data: bytes, dest: Path) -> str:
    import io
    from PIL import Image
    Image.open(io.BytesIO(data)).convert("RGB").save(dest, "JPEG", quality=85, optimize=True)
    return dest.name


# 영어 stock 검색어로 변환(설명형 프롬프트 → 핵심 키워드 몇 개)
_STOP = {"a", "an", "the", "of", "for", "with", "and", "in", "on", "at", "photo",
         "photograph", "high", "quality", "editorial", "no", "text", "image", "shot"}


def _stock_query(prompt: str) -> str:
    words = re.findall(r"[a-zA-Z]+", prompt.lower())
    keep = [w for w in words if w not in _STOP]
    return " ".join(keep[:5]) or "background"


def _fetch_stock(query: str, dest: Path) -> str | None:
    """무료·저작권 안전 스톡 사진(Pexels→Unsplash). 키 없으면 None."""
    pk = config.get("PEXELS_API_KEY")
    if pk:
        try:
            r = requests.get("https://api.pexels.com/v1/search",
                             params={"query": query, "per_page": 1, "orientation": "landscape"},
                             headers={"Authorization": pk}, timeout=20)
            photos = r.json().get("photos", [])
            if photos:
                img = requests.get(photos[0]["src"]["large"], timeout=30).content
                return _save_jpeg(img, dest)
        except Exception as e:
            print(f"    [경고] Pexels 실패: {e}")
    uk = config.get("UNSPLASH_ACCESS_KEY")
    if uk:
        try:
            r = requests.get("https://api.unsplash.com/search/photos",
                             params={"query": query, "per_page": 1, "orientation": "landscape"},
                             headers={"Authorization": f"Client-ID {uk}"}, timeout=20)
            results = r.json().get("results", [])
            if results:
                img = requests.get(results[0]["urls"]["regular"], timeout=30).content
                return _save_jpeg(img, dest)
        except Exception as e:
            print(f"    [경고] Unsplash 실패: {e}")
    return None


def _generate_one(client, prompt: str, dest: Path) -> str | None:
    try:
        resp = client.images.generate(
            model=config.get("IMAGE_MODEL", "gpt-image-1"),
            prompt=prompt + PROMPT_GUARD,
            size="1024x1024",
            quality=config.get("IMAGE_QUALITY", "medium"),
            n=1,
        )
        item = resp.data[0]
        b64 = getattr(item, "b64_json", None)
        if b64:
            data = base64.b64decode(b64)
        else:  # dall-e-3 는 기본적으로 임시 URL 을 돌려줌 → 즉시 다운로드
            import requests
            data = requests.get(item.url, timeout=60).content
        # 용량 절약을 위해 JPEG 로 저장(이미지가 많아져서)
        import io
        from PIL import Image
        Image.open(io.BytesIO(data)).convert("RGB").save(
            dest, "JPEG", quality=85, optimize=True)
        return dest.name
    except Exception as e:
        print(f"    [경고] 이미지 생성 실패: {e}")
        return None


def _target_indices(sections: list[dict]) -> list[int]:
    """모든 섹션에 이미지(섹션=약 2단락 → 2단락당 1개)."""
    return [i for i, s in enumerate(sections) if s.get("image_prompt")]


def generate_for_article(article: dict, out_dir: Path,
                         max_images: int = 4) -> tuple[dict[int, str], str | None]:
    """무료 스톡 먼저, 없으면 AI 생성 → ({섹션인덱스: 상대경로}, 썸네일). 글 전체에 고르게 분산."""
    sections = article.get("sections", [])
    img_dir = out_dir / "images"
    img_dir.mkdir(parents=True, exist_ok=True)

    all_idx = _target_indices(sections)
    if len(all_idx) > max_images:  # 균등 분포로 선택(앞쏠림 방지)
        step = len(all_idx) / max_images
        targets = [all_idx[int(i * step)] for i in range(max_images)]
    else:
        targets = all_idx

    use_stock = bool(config.get("PEXELS_API_KEY") or config.get("UNSPLASH_ACCESS_KEY"))
    images: dict[int, str] = {}
    client = None
    for i in targets:
        prompt = sections[i]["image_prompt"]
        dest = img_dir / f"sec{i}.jpg"
        name = None
        if use_stock:
            name = _fetch_stock(_stock_query(prompt), dest)
            if name:
                print(f"    - 섹션 {i}: 무료 스톡 사진 ✓")
        if not name:  # 스톡 없으면 AI 생성
            if client is None:
                client = _client()
            print(f"    - 섹션 {i}: AI 생성")
            name = _generate_one(client, prompt, dest)
        if name:
            images[i] = f"images/{name}"

    thumbnail = images.get(targets[0]) if targets and targets[0] in images else None
    return images, thumbnail
