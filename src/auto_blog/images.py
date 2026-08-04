"""5단계: 이미지 수급.

비용·화질을 위해 **무료·저작권 안전 스톡 사진(Pexels→Unsplash)을 먼저** 쓰고,
딱 맞는 게 없을 때만 AI 로 생성한다.
- AI 생성은 **나노바나나(제미나이 이미지, GEMINI_API_KEY)** 를 쓴다. gpt-image-1 대비 대폭 저렴.
- gpt-image-1(OpenAI)은 기본적으로 **쓰지 않는다.** IMAGE_FALLBACK_OPENAI=true 로 명시할 때만
  최후 폴백으로 동작(비용 폭주 방지 — 2026-06 이미지 비용의 원인이 gpt-image-1 이었음).
이미지는 글 폴더의 images/ 아래 JPEG 로 저장하고 상대경로를 돌려준다
(발행 시 GitHub URL 호스팅은 publishers/daily_publish 처리).
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


# 영어 stock 검색어로 변환(설명형 프롬프트 → 핵심 사물 키워드 몇 개)
# 지역어·인물·수식어는 제거해야 스톡 매칭이 정확해진다(예: "korean"으로 검색하면 결과 빈약).
_STOP = {
    "a", "an", "the", "of", "for", "with", "and", "in", "on", "at", "to", "by",
    "photo", "photograph", "high", "quality", "editorial", "no", "text", "image", "shot", "closeup",
    # 지역·국적
    "korean", "korea", "asian", "asia", "western",
    # 인물 일반어
    "person", "people", "man", "woman", "men", "women", "male", "female", "guy", "lady",
    "his", "her", "their", "its", "s", "someone",
    # 연령·수식
    "middle", "aged", "senior", "elderly", "older", "old", "young", "adult",
    "fifties", "sixties", "seventies", "thirties", "forties", "year",
    # 촬영·분위기 형용사
    "close", "up", "wide", "overhead", "portrait", "warm", "cozy", "soft", "natural",
    "bright", "dark", "gentle", "peaceful", "calm", "tired", "happy", "smiling", "relaxed",
    "beautiful", "cute", "fresh", "healthy", "clean", "minimal", "rustic", "backlit",
    "morning", "evening", "night", "day", "light", "lighting", "sunlight", "background",
    "scene", "view", "mood", "atmosphere", "concept", "style", "indoor", "outdoor",
    "sitting", "standing", "looking", "holding", "wearing", "showing", "doing",
}


def _stock_query(prompt: str) -> str:
    words = re.findall(r"[a-zA-Z]+", prompt.lower())
    keep = [w for w in words if w not in _STOP and len(w) > 2]
    return " ".join(keep[:4]) or "background"


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
            quality=config.get("IMAGE_QUALITY", "high"),
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


def _generate_one_gemini(prompt: str, dest: Path) -> str | None:
    """나노바나나(제미나이 이미지)로 1장 생성. GEMINI_API_KEY 필요.

    google-genai SDK 사용(writer.py 교차검수와 동일 패키지). 모델은 GEMINI_IMAGE_MODEL
    (기본 'gemini-2.5-flash-image'). 응답 parts 안의 inline_data(이미지 바이트)를 꺼내 저장."""
    try:
        from google import genai
        client = genai.Client(api_key=config.GEMINI_API_KEY)
        model = config.get("GEMINI_IMAGE_MODEL", "gemini-2.5-flash-image")
        resp = client.models.generate_content(
            model=model, contents=[prompt + PROMPT_GUARD])
        for cand in (getattr(resp, "candidates", None) or []):
            content = getattr(cand, "content", None)
            for part in (getattr(content, "parts", None) or []):
                inline = getattr(part, "inline_data", None)
                data = getattr(inline, "data", None) if inline else None
                if data:
                    if isinstance(data, str):  # 일부 버전은 base64 문자열
                        data = base64.b64decode(data)
                    return _save_jpeg(data, dest)
        print("    [경고] 제미나이 응답에 이미지가 없음")
        return None
    except Exception as e:
        print(f"    [경고] 제미나이(나노바나나) 이미지 생성 실패: {e}")
        return None


def _target_indices(sections: list[dict]) -> list[int]:
    """모든 섹션에 이미지(섹션=약 2단락 → 2단락당 1개)."""
    return [i for i, s in enumerate(sections) if s.get("image_prompt")]


def generate_for_article(article: dict, out_dir: Path,
                         max_images: int = 3) -> tuple[dict[int, str], str | None]:
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
    use_gemini = bool(config.GEMINI_API_KEY)                       # 나노바나나(기본 AI 생성)
    allow_openai = str(config.get("IMAGE_FALLBACK_OPENAI", "")).lower() == "true"  # gpt-image-1은 명시 시만
    images: dict[int, str] = {}
    oai_client = None
    for i in targets:
        prompt = sections[i]["image_prompt"]
        dest = img_dir / f"sec{i}.jpg"
        name = None
        if use_stock:
            name = _fetch_stock(_stock_query(prompt), dest)
            if name:
                print(f"    - 섹션 {i}: 무료 스톡 사진 ✓")
        if not name and use_gemini:  # 스톡 없으면 나노바나나(제미나이)로 생성
            print(f"    - 섹션 {i}: 나노바나나(제미나이) 생성")
            name = _generate_one_gemini(prompt, dest)
        if not name and allow_openai:  # 최후 폴백 — 명시적으로 켰을 때만 gpt-image-1
            if oai_client is None:
                oai_client = _client()
            print(f"    - 섹션 {i}: OpenAI(gpt-image-1) 폴백")
            name = _generate_one(oai_client, prompt, dest)
        if name:
            images[i] = f"images/{name}"

    thumbnail = images.get(targets[0]) if targets and targets[0] in images else None
    return images, thumbnail
