"""인스타그램 자동 게시 — Instagram API with Instagram Login(graph.instagram.com).

요즘상식용 인스타 토큰(IG_TOKEN)과 사용자 ID(IG_USER_ID)가 설정돼 있을 때만 동작한다.
인스타는 **이미지 필수**(텍스트 전용 게시 불가)라, image_url 이 없으면 건너뛴다.

흐름: 미디어 컨테이너 생성(POST /{user}/media, image_url+caption) → 게시(POST /{user}/media_publish).
"""
from __future__ import annotations

import requests

from .. import config

BASE = "https://graph.instagram.com/v21.0"


def configured() -> bool:
    return bool(config.get("IG_TOKEN") and config.get("IG_USER_ID"))


def check() -> dict:
    """토큰·계정 연결 확인(게시 없이)."""
    token = config.get("IG_TOKEN")
    uid = config.get("IG_USER_ID")
    if not (token and uid):
        return {"ok": False, "msg": "IG_TOKEN/IG_USER_ID 미설정"}
    r = requests.get(f"{BASE}/me",
                     params={"fields": "user_id,username", "access_token": token}, timeout=20)
    if r.status_code == 200:
        return {"ok": True, "username": r.json().get("username")}
    return {"ok": False, "msg": f"{r.status_code}: {r.text[:120]}"}


def post(caption: str, image_url: str | None = None) -> str:
    """인스타에 이미지+캡션으로 게시하고 결과 메시지를 반환."""
    token = config.get("IG_TOKEN")
    uid = config.get("IG_USER_ID")
    if not (token and uid):
        return "건너뜀: IG 미설정"
    if not image_url:
        return "건너뜀: IG는 이미지 필수(image_url 없음)"
    # 1) 컨테이너 생성
    c = requests.post(f"{BASE}/{uid}/media",
                      data={"access_token": token, "image_url": image_url,
                            "caption": (caption or "")[:2200]}, timeout=90)
    if c.status_code not in (200, 201):
        return f"실패(컨테이너): {c.status_code} {c.text[:150]}"
    cid = c.json().get("id")
    # 2) 게시
    p = requests.post(f"{BASE}/{uid}/media_publish",
                      data={"access_token": token, "creation_id": cid}, timeout=90)
    if p.status_code not in (200, 201):
        return f"실패(게시): {p.status_code} {p.text[:150]}"
    return f"게시됨: ig media {p.json().get('id')}"
