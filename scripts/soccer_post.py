"""한국 vs 남아공 월드컵 조별리그 최종전 — 딥리서치 근거 기반 글.
Blogger 4000자(상세) 발행 + 네이버 1000자(+사진) 텔레그램 전송.
"""
import json
import sys
from datetime import datetime
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import requests  # noqa: E402

from auto_blog import config, formatter, images as imgmod, writer  # noqa: E402
from auto_blog import telegram_bot as tb  # noqa: E402
from auto_blog import publishers  # noqa: E402
from openai import OpenAI  # noqa: E402

# ── 딥리서치 결과(실제 사실) — 표현은 새로, 사실만 근거 ──
GROUNDING = """[딥리서치 사실 — 이 정보에 근거하되 문장은 네 표현으로 새로 써라]
- 경기: 2026 북중미(캐나다·멕시코·미국) 월드컵 조별리그 최종전(3차전), 대한민국 vs 남아프리카공화국.
- 일시: 2026년 6월 25일(목), 한국시간 오전 10시 시작.
- 장소: 멕시코 몬테레이 스타디움.
- TV 중계: KBS, JTBC 생중계(KBS 캐스터로 전현무 아나운서 투입 예정).
- 무료 스트리밍: 네이버 '치지직'(앱·모바일)에서 무료 시청 가능. (출근길·직장·학교에서 보기 좋음)
- 한국 현황: 1차전 체코 2-1 승, 2차전 멕시코 0-1 패 → 현재 1승 1패.
- 의미: 이 남아공전 결과에 16강 진출이 걸려 있는 '운명의 최종전'.
"""

client = OpenAI(api_key=config.OPENAI_API_KEY)
MODEL = config.get("OPENAI_MODEL", "gpt-4o")

TASK = ("주제: 2026 월드컵 '대한민국 vs 남아프리카공화국' 조별리그 최종전 프리뷰.\n"
        "반드시 포함: ①경기 일시·장소 ②중계 보는 법(KBS·JTBC·치지직 무료) ③16강이 걸린 "
        "의미와 한국 현황(1승1패) ④관전 포인트·전망 ⑤따뜻한 응원 마무리.\n")


def _count(a: dict) -> int:
    return sum(len(p) for s in a.get("sections", []) for p in s.get("paragraphs", []))


def gen(target: str, shape: str) -> dict:
    r = client.chat.completions.create(
        model=MODEL, response_format={"type": "json_object"}, temperature=0.7, max_tokens=8000,
        messages=[
            {"role": "system", "content": writer.SYSTEM},
            {"role": "user", "content": TASK + f"분량/구성: {target}\n" + GROUNDING + "\n" + shape}])
    return json.loads(r.choices[0].message.content)


def gen_long(shape: str, lo: int = 3600, hi: int = 4500, tries: int = 4) -> dict:
    """한 번에 길게 안 나오므로, 목표 글자수에 닿을 때까지 확장 반복."""
    a = gen(f"공백 포함 {lo}~{hi}자, 소제목 8~10개로 아주 자세하고 알차게. 재밌고 유익하게.", shape)
    for _ in range(tries):
        c = _count(a)
        print(f"   현재 {c}자")
        if c >= lo:
            break
        r = client.chat.completions.create(
            model=MODEL, response_format={"type": "json_object"}, temperature=0.6, max_tokens=8000,
            messages=[
                {"role": "system", "content": writer.SYSTEM},
                {"role": "user", "content":
                    f"아래 JSON 글을 더 깊고 풍성하게 확장하라. 같은 JSON 형식 유지. "
                    f"기존 사실·내용은 그대로 두고, 문단을 늘리거나 소제목을 추가해 전체 문단 "
                    f"글자수 합계를 공백 포함 {lo}~{hi}자로 만들어라. 절대 짧아지면 안 된다. "
                    f"근거에 없는 거짓 사실은 추가 금지.\n" + GROUNDING + "\n" + shape
                    + "\n\n[현재 글]\n" + json.dumps(a, ensure_ascii=False)}])
        a = json.loads(r.choices[0].message.content)
    return a


BLOG_SHAPE = """JSON 형식: {"title":"위트있는 제목(이모지 1개)","meta_description":"120~150자",
"tags":["10~13개 다양하게(핵심+관련+롱테일)"],
"sections":[{"heading":"소제목(이모지)","paragraphs":["문단","문단"],"image_prompt":"영어 사진 묘사(축구/경기장/응원 등, 텍스트 없이)"}],
"disclaimer":""}"""

NAVER_SHAPE = """JSON 형식: {"title":"위트있는 제목(이모지)","tags":["8~12개 다양하게"],
"sections":[{"heading":"소제목(이모지)","paragraphs":["문단"]}]}"""

RESUME = sys.argv[1] if len(sys.argv) > 1 else None
if RESUME:
    out_dir = config.DATA_DIR / "posts" / RESUME
    blog = json.loads((out_dir / "blog.json").read_text(encoding="utf-8"))
    imgs = {int(p.stem[3:]): f"images/{p.name}" for p in sorted((out_dir / "images").glob("sec*.jpg"))}
    thumb = imgs.get(min(imgs)) if imgs else None
    print(f"♻ 재개: {out_dir.name} | 글 {_count(blog)}자 | 이미지 {len(imgs)}장")
else:
    print("① 블로거 4000자 생성(확장 루프)…")
    blog = gen_long(BLOG_SHAPE)
    blog["keyword"] = "한국 남아공"
    blog["category"] = "general"
    blog["char_count"] = _count(blog)
    print("   제목:", blog["title"], "| ", blog["char_count"], "자")

    print("② 사진 3장(스톡/생성)…")
    stamp = datetime.now().strftime("%Y%m%d-%H%M")
    out_dir = config.DATA_DIR / "posts" / f"{stamp}-korea-southafrica"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "blog.json").write_text(json.dumps(blog, ensure_ascii=False, indent=2), encoding="utf-8")
    imgs, thumb = imgmod.generate_for_article(blog, out_dir, max_images=3)
    print("   이미지:", len(imgs), "장")

print("③ 이미지 GitHub URL 호스팅 + 블로거 발행(KR+EN)…")
record = {"article": blog, "images": imgs, "thumbnail": thumb,
          "status": "published", "dir": out_dir.name}
sys.path.insert(0, str(ROOT / "scripts"))
import daily_publish as dp  # noqa: E402
record["image_urls"] = dp._host_images_on_github(record, out_dir)
print("   호스팅된 이미지:", len(record["image_urls"]), "장")
results = publishers.publish(record, out_dir)
for k, v in results.items():
    print("   ", k, ":", str(v))
blog_url = ""
b = str(results.get("blogger", ""))
if "발행됨:" in b:
    blog_url = b.split("발행됨:")[-1].strip()

print("④ 네이버 1000자 생성…")
nav = gen("공백 포함 900~1300자, 소제목 4개로 핵심만 짧고 임팩트 있게. 시간·중계는 꼭.", NAVER_SHAPE)
nav_text = "📌 " + nav["title"] + "\n"
for s in nav["sections"]:
    nav_text += f"\n■ {s['heading']}\n" + "\n".join(s.get("paragraphs", []))
nav_tags = " ".join("#" + str(t).replace(" ", "") for t in nav.get("tags", []))

print("⑤ 텔레그램 전송(네이버용 글 + 사진)…")
for cid in tb._load_chats():
    # 사진 먼저(파일 업로드)
    files_sent = 0
    for i in sorted(imgs):
        p = out_dir / imgs[i]
        if p.exists():
            with open(p, "rb") as f:
                requests.post(f"{tb.API}/sendPhoto", data={"chat_id": cid}, files={"photo": f}, timeout=30)
            files_sent += 1
    # 네이버용 글
    msg = ("⚽ 한국 vs 남아공 — 네이버용 (1000자)\n\n" + nav_text
           + f"\n\n🏷 태그: {nav_tags}"
           + (f"\n\n📷 위 사진 {files_sent}장 저장해서 네이버에 넣으세요."
              f"\n🔗 블로거(4000자): {blog_url}"))
    requests.post(f"{tb.API}/sendMessage",
                  data={"chat_id": cid, "text": msg[:4096], "disable_web_page_preview": "true"}, timeout=30)
print("완료 ✅  블로거:", blog_url)
