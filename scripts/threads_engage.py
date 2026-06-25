"""스레드 댓글 자동 답글 — 우리(@usual_sense) 글에 달린 댓글에 다정하게 답한다.

- 최근 우리 글의 댓글을 읽어, 아직 답 안 한 '남의 댓글'에만 짧고 따뜻하게 답글(되묻기로 대화 유도).
- 자기 댓글·이미 답한 댓글·빈 댓글은 건너뜀. 한 번에 최대 N개(스팸 방지).
- 답한 댓글 id는 data/threads_replied.json 에 기록(중복 방지). 새로 답하면 텔레그램 보고.
※ '우리 글 댓글에 답하기'는 정상적 소통이라 ToS 안전(대량 팔로우/낯선글 도배와 다름).
"""
import json
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import requests  # noqa: E402
from openai import OpenAI  # noqa: E402
from auto_blog import config  # noqa: E402
from auto_blog import telegram_bot as tb  # noqa: E402

B = "https://graph.threads.net/v1.0"
TOK = config.get("THREADS_TOKEN")
UID = config.get("THREADS_USER_ID")
ME = "usual_sense"
MAX_REPLIES = 8
STATE = config.DATA_DIR / "threads_replied.json"

if not (TOK and UID):
    print("THREADS 미설정 — 종료")
    sys.exit(0)

replied = set()
if STATE.exists():
    try:
        replied = set(json.loads(STATE.read_text(encoding="utf-8")))
    except Exception:
        replied = set()

client = OpenAI(api_key=config.OPENAI_API_KEY)


def gen_reply(post_text: str, comment_text: str) -> str:
    r = client.chat.completions.create(
        model=config.get("OPENAI_MODEL", "gpt-4o"), temperature=0.8, max_tokens=200,
        messages=[
            {"role": "system", "content":
                "너는 '요즘상식' 건강·생활 스레드 운영자다. 댓글에 다정하고 짧게, 사람처럼 답한다."},
            {"role": "user", "content":
                f"[우리 글]\n{post_text[:200]}\n\n[달린 댓글]\n{comment_text}\n\n"
                "이 댓글에 다정하고 자연스럽게 답글을 1~2문장으로 써라. 친근한 입말체 + 이모지 1개. "
                "홍보·판매·링크 금지. 가능하면 가벼운 되묻기로 대화를 이어가라. 댓글 내용에 진짜 반응할 것."}])
    return (r.choices[0].message.content or "").strip()


def post_reply(text: str, reply_to_id: str) -> bool:
    c = requests.post(f"{B}/{UID}/threads",
                      data={"access_token": TOK, "media_type": "TEXT",
                            "text": text[:480], "reply_to_id": reply_to_id}, timeout=60)
    if c.status_code not in (200, 201):
        print("  답글 컨테이너 실패:", c.status_code, c.text[:100])
        return False
    cid = c.json().get("id")
    p = requests.post(f"{B}/{UID}/threads_publish",
                      data={"access_token": TOK, "creation_id": cid}, timeout=60)
    if p.status_code not in (200, 201):
        print("  답글 게시 실패:", p.status_code, p.text[:100])
        return False
    return True


posts = requests.get(f"{B}/{UID}/threads",
                     params={"fields": "id,text", "limit": 20, "access_token": TOK},
                     timeout=20).json().get("data", [])
print("최근 글", len(posts), "개 점검")

new = []
for p in posts:
    if len(new) >= MAX_REPLIES:
        break
    reps = requests.get(f"{B}/{p['id']}/replies",
                        params={"fields": "id,text,username", "access_token": TOK},
                        timeout=20).json().get("data", [])
    for c in reps:
        if len(new) >= MAX_REPLIES:
            break
        if c.get("username") == ME or c["id"] in replied:
            continue
        text = (c.get("text") or "").strip()
        if len(text) < 2:
            continue
        reply = gen_reply(p.get("text", ""), text)
        if reply and post_reply(reply, c["id"]):
            replied.add(c["id"])
            new.append((c.get("username", "?"), text[:40], reply[:60]))
            print(f"  답글: @{c.get('username')} <- {reply[:40]}")

STATE.write_text(json.dumps(list(replied), ensure_ascii=False), encoding="utf-8")

if new:
    msg = "💬 스레드 댓글 자동 답글\n\n" + "\n\n".join(
        f"@{u} \"{ct}\"\n↳ {rt}" for u, ct, rt in new)
    for cid in tb._load_chats():
        requests.post(f"{tb.API}/sendMessage",
                      data={"chat_id": cid, "text": msg[:4096], "disable_web_page_preview": "true"},
                      timeout=30)

print(f"완료 ✅ 새 답글 {len(new)}개")
