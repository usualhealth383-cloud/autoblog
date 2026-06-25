"""한국 0-1 남아공 패배 → 32강 경우의 수. 딥리서치 근거 기반.
Blogger(1500~2000자) + 네이버 복붙페이지 갱신 + 스레드 자동게시 + 텔레그램 보고.
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
sys.path.insert(0, str(ROOT / "scripts"))

import requests  # noqa: E402
from openai import OpenAI  # noqa: E402

from auto_blog import config, images as imgmod, writer, variants  # noqa: E402
from auto_blog import telegram_bot as tb  # noqa: E402
from auto_blog.publishers import blogger, threads_upload  # noqa: E402
import daily_publish as dp  # noqa: E402

GROUNDING = """[딥리서치 사실 — 출처 기반, 문장은 네 표현으로 새로 써라. 확정 아닌 건 '가능성/유력'으로]
- 2026 북중미 월드컵 A조 최종 3차전(6월 25일, 멕시코 몬테레이 스타디움): 대한민국 0-1 남아프리카공화국 패배.
- 결과: 한국 1승 2패, 승점 3, 골득실 -1, 2득점 → A조 3위. (무승부만 했어도 32강 직행이었는데 아쉽게 패).
- A조 상황: 멕시코가 1위 유력, 남아프리카공화국이 2위로 32강 직행 확정, 한국은 3위, 체코와 함께 직행권 밖.
- 진출 방식: 48개국·12개 조. 각 조 1·2위(총 24팀) 직행 + 조 3위 12팀 중 성적 좋은 8팀이 와일드카드 → 총 32팀이 32강.
- 한국 경우의 수: 자력 불가, '타력'. 조 3위 12팀 중 상위 8위 안에 들어야 함. 승점3 팀 수·골득실·다득점으로 결정.
- 3위 경쟁 구도(확정 아님, 진행 중): 한국 승점3·골득실 -1. 위에 보스니아헤르체고비나(B조, 승점4). 아래에 스코틀랜드(C조, 승점3·골득실 -3). 나머지 9개 조의 3위는 6월 26~28일 최종전으로 단계적 확정 → 그때 한국 운명 결정.
- 32강 대진: FIFA가 수학적으로 미리 고정(추첨 없음). 12개 조 중 어느 8개 조의 3위가 오르느냐에 따라 495가지 조합.
- 한국이 3위로 진출 시 상대: 대진표상 6월 30일 경기로 거론되며, 조합에 따라 E조 1위(현재 독일이 선두) 또는 다른 조 1위(캐나다 등)와 만날 수 있음. **상대는 아직 미확정**, 조별리그 종료 후 확정.
- OPTA 통계: 한국의 32강 진출 확률 87.6%로 비교적 유리(승점3에 골득실 0 이상이면 96%+인데, 한국은 -1이라 약간 불안).
- 톤: 패배는 아쉽지만 비난보다 희망·응원. 선수 비하 금지. 진출·상대 모두 단정 금지(가능성/유력으로).
"""

SHAPE = """JSON 형식: {"title":"클릭하고 싶은 제목(이모지 1개, 35자내)","meta_description":"120~150자",
"tags":["다양하게 10~13개(핵심+관련+롱테일)"],
"sections":[{"heading":"소제목(이모지)","paragraphs":["문단","문단"],"image_prompt":"섹션 핵심 소재의 구체적 영어 사진묘사(축구/응원/경기장 등, 실제선수·로고·텍스트 없이)"}],
"disclaimer":""}"""

client = OpenAI(api_key=config.OPENAI_API_KEY)
MODEL = config.get("OPENAI_MODEL", "gpt-4o")
TASK = ("주제: 2026 월드컵 '대한민국 0-1 남아공' 패배 이후, 한국의 32강 진출 경우의 수 + 대진 전망.\n"
        "반드시 포함: ①경기 결과와 A조 최종 상황(멕시코·남아공 1·2위 진출, 한국 3위) ②32강 진출 방식"
        "(조3위 와일드카드 8팀) ③한국의 경우의 수와 3위 경쟁 구도(누가 위/아래, 6/26~28 확정) ④한국이 "
        "진출하면 만날 상대 전망(아직 미확정이나 거론되는 시나리오: E조 1위 독일 유력·캐나다 등, 6/30) "
        "⑤진출 가능성(OPTA 87.6%) ⑥따뜻한 응원 마무리. 진출·상대 단정 금지(가능성/유력으로).\n")


def _count(a):
    return sum(len(p) for s in a.get("sections", []) for p in s.get("paragraphs", []))


def gen():
    r = client.chat.completions.create(
        model=MODEL, response_format={"type": "json_object"}, temperature=0.7, max_tokens=6000,
        messages=[{"role": "system", "content": writer.SYSTEM},
                  {"role": "user", "content": TASK + GROUNDING + "\n" + SHAPE}])
    return json.loads(r.choices[0].message.content)


def gen_target(lo=1500, hi=2100, tries=3):
    a = gen()
    for _ in range(tries):
        c = _count(a)
        print(f"   현재 {c}자")
        if c >= lo:
            break
        r = client.chat.completions.create(
            model=MODEL, response_format={"type": "json_object"}, temperature=0.6, max_tokens=6000,
            messages=[{"role": "system", "content": writer.SYSTEM},
                      {"role": "user", "content":
                       f"아래 JSON 글을 더 알차게 확장하라. 같은 JSON 형식 유지. 기존 사실 유지하며 "
                       f"문단/소제목을 보강해 전체 문단 글자수 합계를 공백 포함 {lo}~{hi}자로. 근거에 없는 "
                       f"거짓 추가 금지.\n" + GROUNDING + "\n" + SHAPE
                       + "\n\n[현재 글]\n" + json.dumps(a, ensure_ascii=False)}])
        a = json.loads(r.choices[0].message.content)
    return a


print("① 글 생성(1500~2000자)…")
blog = gen_target()
blog["keyword"] = "한국 32강 경우의 수"
blog["category"] = "general"
blog["char_count"] = _count(blog)
print("   제목:", blog["title"], "|", blog["char_count"], "자")

print("② 사진(스톡/생성)…")
stamp = datetime.now().strftime("%Y%m%d-%H%M")
out_dir = config.DATA_DIR / "posts" / f"{stamp}-korea-round32"
out_dir.mkdir(parents=True, exist_ok=True)
(out_dir / "blog.json").write_text(json.dumps(blog, ensure_ascii=False, indent=2), encoding="utf-8")
imgs, thumb = imgmod.generate_for_article(blog, out_dir, max_images=3)
print("   이미지:", len(imgs), "장")

print("③ 이미지 GitHub 호스팅…")
rec = {"article": blog, "images": imgs, "thumbnail": thumb, "status": "published", "dir": out_dir.name}
rec["image_urls"] = dp._host_images_on_github(rec, out_dir)
print("   호스팅:", len(rec["image_urls"]), "장")

results = {}
print("④ Blogger 발행(KR)…")
try:
    url = blogger.publish(rec, out_dir)
    results["blogger"] = f"발행됨: {url}"
    print("   ✅", url)
except Exception as e:
    results["blogger"] = f"실패: {e}"
    print("   ❌", str(e)[:150])

print("⑤ 네이버 복붙페이지 갱신…")
try:
    nv = variants.make_naver(blog)
except Exception:
    nv = {"title": blog["title"], "lead": ""}
dp._update_naver_page(rec, results, nv)

print("⑥ 스레드 게시…")
threads_text = ""
try:
    tv = variants.make_threads(blog)
    blog_url = results.get("blogger", "").split("발행됨: ")[-1] if "발행됨" in results.get("blogger", "") else ""
    threads_text = (tv["text"] + ("\n\n" + blog_url if blog_url else "")
                    + "\n" + " ".join(tv.get("hashtags", []))).strip()
    thumb_url = rec["image_urls"].get("0") or (next(iter(rec["image_urls"].values())) if rec["image_urls"] else None)
    if "--no-threads" in sys.argv:
        print("   건너뜀(--no-threads, 중복 방지)")
        results["threads"] = "건너뜀(이미 게시됨)"
    elif threads_text and threads_upload.configured():
        msg = threads_upload.post(threads_text, thumb_url)
        results["threads"] = msg
        print("   스레드:", msg)
except Exception as e:
    print("   스레드 실패:", str(e)[:120])

print("⑦ 텔레그램 보고…")
naver_url = "https://usualhealth383-cloud.github.io/autoblog/naver.html"
photo_urls = [rec["image_urls"][k] for k in sorted(rec["image_urls"], key=lambda x: int(x))]
for cid in tb._load_chats():
    if photo_urls:
        media = [{"type": "photo", "media": u} for u in photo_urls]
        media[0]["caption"] = "⚽ 한국 32강 경우의 수 — 사진 3장"
        requests.post(f"{tb.API}/sendMediaGroup", data={"chat_id": cid, "media": json.dumps(media)}, timeout=60)
    msg = (f"⚽ 한국 32강 경우의 수 글 완료\n\n"
           f"📝 블로거: {results.get('blogger','-')}\n"
           f"🟢 네이버 복붙: {naver_url}\n"
           f"🧵 스레드: {results.get('threads','-')}")
    requests.post(f"{tb.API}/sendMessage",
                  data={"chat_id": cid, "text": msg[:4096], "disable_web_page_preview": "true"}, timeout=30)
print("완료 ✅")
