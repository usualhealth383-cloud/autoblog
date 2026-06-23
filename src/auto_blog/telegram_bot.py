"""텔레그램 알림 + 원격 승인 봇.

- 매일 글이 생성되면 봇이 썸네일 + 본문 전체 + [✅승인][✕반려] 버튼을 보낸다.
- 한 텔레그램 계정을 폰·PC에 로그인해두면 두 기기에 동시 알림이 오고,
  어느 기기에서 버튼을 눌러도 게시된다(인터넷 기반이라 외부에서도 작동).
- 승인 누르면 publishers.publish 로 Blogger 게시 + 네이버 초안 생성.

추가 라이브러리 없이 requests 로 Telegram HTTP API 를 직접 호출한다.

실행:
  python -m auto_blog.telegram_bot          # 봇 상시 실행(승인 버튼 수신)
  python -m auto_blog.telegram_bot --whoami # 내 chat_id 확인(먼저 봇에 /start 전송)
"""
from __future__ import annotations

import json
from pathlib import Path

import requests

from . import config

TOKEN = config.get("TELEGRAM_BOT_TOKEN")
API = f"https://api.telegram.org/bot{TOKEN}"
POSTS = config.DATA_DIR / "posts"
CHATS_FILE = config.ROOT / "config" / "telegram_chats.json"


# ---------- chat_id 저장/로드 ----------
def _load_chats() -> list[int]:
    if CHATS_FILE.exists():
        try:
            return json.loads(CHATS_FILE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return []
    return []


def _save_chats(chats: list[int]) -> None:
    CHATS_FILE.parent.mkdir(exist_ok=True)
    CHATS_FILE.write_text(json.dumps(chats), encoding="utf-8")


def _remember_chat(chat_id: int) -> None:
    chats = _load_chats()
    if chat_id not in chats:
        chats.append(chat_id)
        _save_chats(chats)
        print(f"  새 수신자 등록: {chat_id}")


# ---------- 보내기 ----------
def _body_text(article: dict, max_len: int = 3800) -> str:
    lines = [f"📌 {article.get('title','')}", ""]
    for s in article.get("sections", []):
        lines.append(f"■ {s.get('heading','')}")
        lines.extend(s.get("paragraphs", []))
        lines.append("")
    if article.get("disclaimer"):
        lines.append(f"※ {article['disclaimer']}")
    text = "\n".join(lines)
    return text[:max_len] + ("…(이하 생략)" if len(text) > max_len else "")


def send_for_approval(record: dict, post_dir: Path,
                      chat_ids: list[int] | None = None) -> None:
    """글 하나를 승인 요청으로 전송."""
    if not TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN 미설정")
    chat_ids = chat_ids or _load_chats()
    if not chat_ids:
        raise RuntimeError("등록된 chat_id 가 없습니다. 먼저 봇에 /start 를 보내세요.")

    article = record["article"]
    dir_name = post_dir.name
    thumb_rel = record.get("thumbnail")
    cat = (record.get("topic") or {}).get("category", "")
    cap = f"📰 새 글 검토 요청\n\n📌 {article.get('title','')}\n🏷 {cat} · {article.get('char_count','?')}자"
    keyboard = {"inline_keyboard": [[
        {"text": "✅ 승인·게시", "callback_data": f"ap|{dir_name}"},
        {"text": "✕ 반려", "callback_data": f"rj|{dir_name}"},
    ]]}

    for cid in chat_ids:
        # 1) 썸네일 + 제목
        if thumb_rel and (post_dir / thumb_rel).exists():
            with open(post_dir / thumb_rel, "rb") as f:
                requests.post(f"{API}/sendPhoto", data={"chat_id": cid, "caption": cap},
                              files={"photo": f}, timeout=30)
        else:
            requests.post(f"{API}/sendMessage", data={"chat_id": cid, "text": cap}, timeout=30)
        # 2) 본문 전체(폰에서 읽기)
        requests.post(f"{API}/sendMessage",
                      data={"chat_id": cid, "text": _body_text(article),
                            "disable_web_page_preview": "true"}, timeout=30)
        # 3) 승인 버튼
        requests.post(f"{API}/sendMessage",
                      data={"chat_id": cid, "text": "이 글을 블로그에 게시할까요?",
                            "reply_markup": json.dumps(keyboard)}, timeout=30)


def send_report(record: dict, results: dict, chat_ids: list[int] | None = None,
                threads_text: str = "") -> None:
    """자동발행 후 결과 보고(승인 버튼 없음). 게시 링크 + 자동수정 내역 + 삭제 안내."""
    if not TOKEN:
        return
    chat_ids = chat_ids or _load_chats()
    if not chat_ids:
        return
    article = record["article"]
    links = []
    for k, v in results.items():
        if "blogspot.com" in str(v):
            label = "🇺🇸 영문" if k.endswith("_en") else "🇰🇷 한글"
            links.append(f"{label}: {str(v).split('발행됨')[-1].lstrip('(EN): ').lstrip(': ')}")
    fixed = record["article"].get("fact_issues_fixed", [])
    fb = "  (안전 상식글로 교체됨)" if record.get("used_fallback") else ""
    naver_url = "https://usualhealth383-cloud.github.io/autoblog/naver.html"
    text = (f"✅ 오늘의 글 자동 발행 완료!{fb}\n\n"
            f"📌 {article.get('title','')}  ({article.get('char_count','?')}자)\n\n"
            + "\n".join(links)
            + f"\n\n📋 네이버 복붙용: {naver_url}"
            + (f"\n\n🧵 스레드용 (복사해서 올리세요):\n{threads_text}" if threads_text else "")
            + f"\n\n🛡 자동 사실검증으로 근거 없는 주장 {len(fixed)}건 제거함."
            + "\n혹시 내용이 이상하면 위 링크에서 바로 삭제/수정하세요.")
    thumb_rel = record.get("thumbnail")
    post_dir = config.DATA_DIR / "posts" / record.get("dir", "")
    for cid in chat_ids:
        if thumb_rel and (post_dir / thumb_rel).exists():
            with open(post_dir / thumb_rel, "rb") as f:
                requests.post(f"{API}/sendPhoto",
                              data={"chat_id": cid, "caption": text},
                              files={"photo": f}, timeout=30)
        else:
            requests.post(f"{API}/sendMessage",
                          data={"chat_id": cid, "text": text}, timeout=30)


def _edit_done(chat_id: int, message_id: int, text: str) -> None:
    requests.post(f"{API}/editMessageText",
                  data={"chat_id": chat_id, "message_id": message_id, "text": text},
                  timeout=30)


def _answer(callback_id: str, text: str = "") -> None:
    requests.post(f"{API}/answerCallbackQuery",
                  data={"callback_query_id": callback_id, "text": text}, timeout=30)


# ---------- 콜백 처리(승인/반려) ----------
def _handle_callback(cb: dict) -> None:
    from . import publishers
    data = cb.get("data", "")
    msg = cb.get("message", {})
    chat_id = msg.get("chat", {}).get("id")
    msg_id = msg.get("message_id")
    cb_id = cb.get("id")

    action, _, dir_name = data.partition("|")
    if dir_name == "__test__":  # 작동 확인용 안전 테스트(실제 게시 안 함)
        _answer(cb_id, "✅ 버튼 작동 성공!")
        _edit_done(chat_id, msg_id, "✅ 테스트 성공 — 알림·승인 버튼이 정상 작동합니다!")
        return
    post_dir = POSTS / dir_name
    af = post_dir / "article.json"
    if not af.exists():
        _answer(cb_id, "글을 찾을 수 없습니다.")
        return
    rec = json.loads(af.read_text(encoding="utf-8"))

    if rec.get("status") == "published":
        _answer(cb_id, "이미 게시된 글입니다.")
        return

    if action == "ap":
        _answer(cb_id, "게시 중…")
        results = publishers.publish(rec, post_dir)
        rec["status"] = "published"
        rec["publish_results"] = results
        af.write_text(json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8")
        url = ""
        for v in results.values():
            if "blogspot.com" in str(v):
                url = str(v).split("발행됨: ")[-1]
        _edit_done(chat_id, msg_id, f"✅ 게시 완료!\n{url or results.get('blogger','')}")
    elif action == "rj":
        rec["status"] = "rejected"
        af.write_text(json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8")
        _answer(cb_id, "반려했습니다.")
        _edit_done(chat_id, msg_id, "✕ 반려됨 — 게시하지 않았습니다.")


_LAST_RUN_FILE = config.ROOT / "config" / "last_run.txt"


def _already_ran_today(today: str) -> bool:
    return _LAST_RUN_FILE.exists() and _LAST_RUN_FILE.read_text(encoding="utf-8").strip() == today


def _mark_ran(today: str) -> None:
    _LAST_RUN_FILE.parent.mkdir(exist_ok=True)
    _LAST_RUN_FILE.write_text(today, encoding="utf-8")


def run_bot(daily_job=None, daily_hour: int | None = None) -> None:
    """롱폴링으로 메시지·버튼 수신(상시). daily_job 이 주어지면 매일 daily_hour 시에 1회 실행."""
    if not TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN 미설정")
    from datetime import datetime

    def _now():
        # 서버 시간대(UTC 등)와 무관하게 한국시간 기준으로 6시를 판단
        try:
            from zoneinfo import ZoneInfo
            return datetime.now(ZoneInfo(config.get("TIMEZONE", "Asia/Seoul")))
        except Exception:
            return datetime.now()

    print(f"텔레그램 봇 실행 중… (매일 KST {daily_hour}시 생성)" if daily_job else "텔레그램 봇 실행 중…")
    offset = None
    while True:
        try:
            r = requests.get(f"{API}/getUpdates",
                             params={"timeout": 50, "offset": offset}, timeout=60)
            for upd in r.json().get("result", []):
                offset = upd["update_id"] + 1
                if "message" in upd:
                    chat = upd["message"]["chat"]
                    _remember_chat(chat["id"])
                    txt = upd["message"].get("text", "")
                    if txt.startswith("/start"):
                        requests.post(f"{API}/sendMessage", data={
                            "chat_id": chat["id"],
                            "text": "✅ 등록됐습니다! 매일 새 글이 만들어지면 여기로 알림이 옵니다."},
                            timeout=30)
                elif "callback_query" in upd:
                    _handle_callback(upd["callback_query"])

            # 매일 정해진 시각에 1회 글 생성 + 알림 (한국시간 기준)
            if daily_job and daily_hour is not None:
                now = _now()
                today = now.strftime("%Y-%m-%d")
                if now.hour == daily_hour and not _already_ran_today(today):
                    _mark_ran(today)
                    print(f"[{now:%H:%M}] 일일 글 생성 시작…")
                    try:
                        daily_job()
                    except Exception as e:
                        print(f"  [오류] 일일 생성 실패: {e}")
        except requests.RequestException as e:
            print(f"  [경고] 폴링 오류(재시도): {e}")


def _whoami() -> None:
    r = requests.get(f"{API}/getUpdates", timeout=30)
    seen = set()
    for upd in r.json().get("result", []):
        m = upd.get("message") or {}
        chat = m.get("chat")
        if chat:
            seen.add(chat["id"])
            _remember_chat(chat["id"])
    print("감지된 chat_id:", sorted(seen) or "없음 (봇에 먼저 /start 를 보내세요)")


if __name__ == "__main__":
    import sys
    if "--whoami" in sys.argv:
        _whoami()
    else:
        run_bot()
