"""Blogger 한도가 풀리면 대기 중인 수동 글(경우의수 + 건강 3편)을 자동 발행.
- 각 주제의 '최신 폴더' blog.json + 이미 호스팅된 이미지 URL 로 Blogger 발행.
- 성공하면 폴더에 PUBLISHED 마커(=재발행 방지). 새로 발행된 게 있거나 전부 끝나면 텔레그램 알림.
- 모두 끝나면 마지막 줄에 'ALL_DONE' 출력(예약작업이 이걸 보고 스스로 중단).
- 아직 403(한도)면 아무 것도 안 올리고 조용히 종료 → 다음 기회에 재시도.
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
from auto_blog import config  # noqa: E402
from auto_blog import telegram_bot as tb  # noqa: E402
from auto_blog.publishers import blogger  # noqa: E402

REPO = "usualhealth383-cloud/autoblog"
RAW = f"https://raw.githubusercontent.com/{REPO}/main/public"
TOPICS = ["korea-round32", "health-water", "health-sleep", "health-egg"]
posts = config.DATA_DIR / "posts"


def latest_dir(key):
    dirs = sorted(posts.glob(f"*-{key}"))
    return dirs[-1] if dirs else None


done, new_pub, pending, blocked = [], [], [], False
for key in TOPICS:
    d = latest_dir(key)
    if not d or not (d / "blog.json").exists():
        continue
    marker = d / "PUBLISHED"
    if marker.exists():
        done.append((key, marker.read_text(encoding="utf-8").strip()))
        continue
    blog = json.loads((d / "blog.json").read_text(encoding="utf-8"))
    imgs, image_urls = {}, {}
    for p in sorted((d / "images").glob("sec*.jpg")):
        idx = int(p.stem[3:])
        imgs[idx] = f"images/{p.name}"
        image_urls[str(idx)] = f"{RAW}/{d.name}/sec{idx}.jpg"
    rec = {"article": blog, "images": imgs, "image_urls": image_urls, "dir": d.name}
    try:
        url = blogger.publish(rec, d)
        marker.write_text(url, encoding="utf-8")
        new_pub.append((blog.get("title", key), url))
        done.append((key, url))
        print(f"[발행] {key} -> {url}")
    except Exception as e:
        msg = str(e)
        if "403" in msg or "permission" in msg.lower() or "429" in msg:
            blocked = True
            pending.append(key)
            print(f"[대기] {key}: 아직 한도(403/429)")
        else:
            pending.append(key)
            print(f"[오류] {key}: {msg[:120]}")

# 텔레그램: 새로 발행됐거나, 전부 끝났을 때만 알림(스팸 방지)
if new_pub or (not pending and done):
    lines = ["📝 Blogger 대기글 자동 발행 결과\n"]
    for title, url in new_pub:
        lines.append(f"✅ {title}\n{url}")
    if not pending:
        lines.append("\n🎉 대기 중이던 글 전부 발행 완료!")
    body = "\n".join(lines)
    for cid in tb._load_chats():
        requests.post(f"{tb.API}/sendMessage",
                      data={"chat_id": cid, "text": body[:4096], "disable_web_page_preview": "true"},
                      timeout=30)

print(f"\n요약: 발행완료 {len(done)} / 대기 {len(pending)} (blocked={blocked})")
if not pending:
    print("ALL_DONE")
