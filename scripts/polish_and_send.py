"""오늘 블로그 글을 '첫 글'답게 더 짧고 잘 다듬어 텔레그램으로 보낸다(검토용)."""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import requests  # noqa: E402

from auto_blog import config  # noqa: E402
from auto_blog import telegram_bot as tb  # noqa: E402
from auto_blog.publishers import blogger  # noqa: E402

svc = blogger._service()
bid = config.get("BLOGGER_BLOG_ID")
posts = svc.posts().list(blogId=bid, maxResults=4, fetchBodies=True).execute().get("items", [])
ko = [p for p in posts if any("가" <= c <= "힣" for c in p["title"])][0]
src_title = ko["title"]
src_text = re.sub(r"<[^>]+>", " ", ko.get("content", ""))[:3500]

from openai import OpenAI  # noqa: E402
client = OpenAI(api_key=config.OPENAI_API_KEY)


def _gen(extra=""):
    r = client.chat.completions.create(
        model=config.get("OPENAI_MODEL", "gpt-4o"),
        response_format={"type": "json_object"}, temperature=0.7,
        messages=[
            {"role": "system", "content":
                "너는 한국 블로그 베스트 에디터다. 첫 글답게 알차고 따뜻하게 쓴다. JSON 으로만 답."},
            {"role": "user", "content":
                "다음 글을 '블로그 첫 글'답게 더 잘 다듬어라. 규칙:\n"
                "- 소제목 5개. **각 소제목마다 본문 2문단(한 문단 4~5문장)**으로 충분히 알차게.\n"
                "- 전체 공백 포함 **2300~2800자**(절대 2000자 미만 금지). 반복·뻔한 일반론은 빼되 "
                "실전 정보·구체 팁은 풍부하게 살려라.\n"
                "- 강한 후킹 도입 + 따뜻하고 유쾌한 입말체 + 이모지 적당히. 표현은 새로(저작권). "
                "마무리는 다정하게.\n"
                '형식: {"title":"제목(이모지 가능)", "sections":[{"heading":"소제목","body":"2문단"}]}'
                + extra + f"\n\n[원본 제목]\n{src_title}\n[원본 본문]\n{src_text}"}])
    return json.loads(r.choices[0].message.content)


art = _gen()
_len = sum(len(s.get("body", "")) for s in art.get("sections", []))
if _len < 2000:  # 너무 짧으면 한 번 더(길이 보강)
    art = _gen(f"\n\n앞서 약 {_len}자로 너무 짧았다. 각 문단을 더 구체적인 예시·팁으로 "
               f"늘려 반드시 2300~2800자로 다시 써라.")

# 텔레그램용 메시지 구성
lines = [f"✨ 첫 글 다듬은 버전이에요 (좀 더 알차게! 검토해보세요)\n", f"📌 {art['title']}\n"]
total = 0
for s in art.get("sections", []):
    lines.append(f"\n■ {s.get('heading','')}")
    lines.append(s.get("body", ""))
    total += len(s.get("body", ""))
msg = "\n".join(lines)
lines.append(f"\n\n(약 {total}자로 압축 — 원본보다 짧고 깔끔해요)")
msg = "\n".join(lines)[:4096]

for cid in tb._load_chats():
    requests.post(f"{tb.API}/sendMessage",
                  data={"chat_id": cid, "text": msg, "disable_web_page_preview": "true"},
                  timeout=30)
print("전송 완료. 제목:", art["title"], "| 약", total, "자")
