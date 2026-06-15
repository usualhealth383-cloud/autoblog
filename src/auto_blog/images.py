"""5단계: 이미지 생성/수급.

DALL·E 3 로 섹션별 이미지를 만든다(저작권 안전 — 새로 생성). 비용 통제를 위해
formatter 가 실제로 노출하는 위치(첫 섹션 + 홀수 섹션)만, 최대 N장 생성한다.
이미지는 글 폴더의 images/ 아래 PNG 로 저장하고, preview.html 에서 보이도록
상대경로를 돌려준다. (발행 시 외부 URL 호스팅은 publishers 단계에서 처리.)

스톡 검색(Unsplash/Pexels)도 키가 있으면 대체 수단으로 쓸 수 있게 자리만 마련.
"""
from __future__ import annotations

import base64
from pathlib import Path

from . import config

# DALL·E 가 한국어 텍스트를 이미지에 박지 않도록 프롬프트에 가드 추가
PROMPT_GUARD = ", high quality editorial photograph, no text, no letters, no words"


def _client():
    from openai import OpenAI
    if not config.OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY 가 없습니다.")
    return OpenAI(api_key=config.OPENAI_API_KEY)


def _generate_one(client, prompt: str, dest: Path) -> str | None:
    try:
        resp = client.images.generate(
            model=config.get("IMAGE_MODEL", "gpt-image-1"),
            prompt=prompt + PROMPT_GUARD,
            size="1024x1024",
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
    """이미지 생성 → ({섹션인덱스: 상대경로}, 썸네일 상대경로). 글 전체에 고르게 분산."""
    client = _client()
    sections = article.get("sections", [])
    img_dir = out_dir / "images"
    img_dir.mkdir(parents=True, exist_ok=True)

    images: dict[int, str] = {}
    all_idx = _target_indices(sections)
    if len(all_idx) > max_images:  # 균등 분포로 선택(앞쏠림 방지)
        step = len(all_idx) / max_images
        targets = [all_idx[int(i * step)] for i in range(max_images)]
    else:
        targets = all_idx
    for i in targets:
        prompt = sections[i]["image_prompt"]
        print(f"    - 섹션 {i} 이미지 생성…")
        name = _generate_one(client, prompt, img_dir / f"sec{i}.jpg")
        if name:
            images[i] = f"images/{name}"

    thumbnail = images.get(targets[0]) if targets and targets[0] in images else None
    return images, thumbnail
