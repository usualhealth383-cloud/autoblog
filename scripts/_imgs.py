"""한국 vs 남아공 글에 어울리는 이미지를 AI로 새로 생성(저작권 안전) →
저장 폴더의 sec0/2/5.jpg 덮어쓰기 + GitHub 호스팅 파일 갱신 + 텔레그램 전송.
"""
import base64
import sys
from pathlib import Path

sys.path.insert(0, "src")
sys.stdout.reconfigure(encoding="utf-8")
import requests  # noqa: E402
from auto_blog import config, images as imgmod  # noqa: E402
from auto_blog import telegram_bot as tb  # noqa: E402

DIR = "20260624-1926-korea-southafrica"
out_dir = config.DATA_DIR / "posts" / DIR
img_dir = out_dir / "images"
REPO = "usualhealth383-cloud/autoblog"

# 관련성 높은 + 저작권 안전 프롬프트(실제 선수/로고 없음)
PROMPTS = {
    0: ("Passionate South Korean football supporters wearing red shirts, cheering and "
        "celebrating in a packed stadium during a night match, waving red scarves, "
        "hopeful energetic atmosphere"),
    2: ("Two football players competing for the ball on green pitch under bright stadium "
        "floodlights at night, dynamic action, plain kits without any logos or text"),
    5: ("A packed modern football stadium at night under floodlights, huge cheering crowd, "
        "world cup match atmosphere, viewed from the upper stands"),
}

client = imgmod._client()
made = {}
for idx, prompt in PROMPTS.items():
    dest = img_dir / f"sec{idx}.jpg"
    print(f"생성 sec{idx} …")
    name = imgmod._generate_one(client, prompt, dest)
    if name:
        made[idx] = dest
        print(f"   ✓ {dest.name}")
    else:
        print("   ✗ 실패")

# GitHub 파일 덮어쓰기(sha 필요)
token = None
try:
    import subprocess
    token = subprocess.check_output(["gh", "auth", "token"], shell=True).decode().strip()
except Exception as e:
    print("gh 토큰 실패:", e)

if token:
    h = {"Authorization": f"token {token}", "Accept": "application/vnd.github+json"}
    for idx, dest in made.items():
        path = f"public/{DIR}/sec{idx}.jpg"
        url = f"https://api.github.com/repos/{REPO}/contents/{path}"
        sha = None
        g = requests.get(url, headers=h, timeout=30)
        if g.status_code == 200:
            sha = g.json().get("sha")
        body = {"message": f"img {path}", "branch": "main",
                "content": base64.b64encode(dest.read_bytes()).decode()}
        if sha:
            body["sha"] = sha
        r = requests.put(url, headers=h, json=body, timeout=60)
        print(f"   GitHub sec{idx}: {r.status_code}")

# 텔레그램 전송
for cid in tb._load_chats():
    for idx in sorted(made):
        with open(made[idx], "rb") as f:
            requests.post(f"{tb.API}/sendPhoto",
                          data={"chat_id": cid,
                                "caption": "⚽ 한국 vs 남아공 — 응원 분위기 이미지(저작권 안전, 새로 생성)"
                                if idx == min(made) else None},
                          files={"photo": f}, timeout=60)
print("전송 완료:", len(made), "장")
