"""스레드(Threads) 자동 게시 — 공식 Threads API.

요즘상식용 스레드 계정 토큰(THREADS_TOKEN)과 사용자 ID(THREADS_USER_ID)가 설정돼 있을 때만
동작한다. 없으면 호출측에서 건너뛴다(안전).

흐름: 컨테이너 생성(POST /{user}/threads) → 게시(POST /{user}/threads_publish).
이미지가 있으면 IMAGE, 없으면 TEXT 로 올린다. 본문(text)에 링크·해시태그를 포함한다.
"""
from __future__ import annotations

import requests

from .. import config

BASE = "https://graph.threads.net/v1.0"


def configured() -> bool:
    return bool(config.get("THREADS_TOKEN") and config.get("THREADS_USER_ID"))


def check() -> dict:
    """토큰·계정 연결 확인(게시 없이)."""
    token = config.get("THREADS_TOKEN")
    uid = config.get("THREADS_USER_ID")
    if not (token and uid):
        return {"ok": False, "msg": "THREADS_TOKEN/THREADS_USER_ID 미설정"}
    r = requests.get(f"{BASE}/{uid}",
                     params={"fields": "username", "access_token": token}, timeout=20)
    if r.status_code == 200:
        return {"ok": True, "username": r.json().get("username")}
    return {"ok": False, "msg": f"{r.status_code}: {r.text[:120]}"}


def post(text: str, image_url: str | None = None) -> str:
    """스레드에 게시하고 결과 메시지를 반환."""
    token = config.get("THREADS_TOKEN")
    uid = config.get("THREADS_USER_ID")
    if not (token and uid):
        return "건너뜀: THREADS 미설정"
    # 1) 컨테이너 생성
    data = {"access_token": token, "text": text[:480]}
    if image_url:
        data["media_type"] = "IMAGE"
        data["image_url"] = image_url
    else:
        data["media_type"] = "TEXT"
    c = requests.post(f"{BASE}/{uid}/threads", data=data, timeout=60)
    if c.status_code not in (200, 201):
        return f"실패(컨테이너): {c.status_code} {c.text[:120]}"
    cid = c.json().get("id")
    # 2) 게시
    p = requests.post(f"{BASE}/{uid}/threads_publish",
                      data={"access_token": token, "creation_id": cid}, timeout=60)
    if p.status_code not in (200, 201):
        return f"실패(게시): {p.status_code} {p.text[:120]}"
    return f"게시됨: thread id {p.json().get('id')}"
