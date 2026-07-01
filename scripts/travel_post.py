"""태국 방콕+파타야 3박4일 플래닝 가이드 — 딥리서치 정보 정리형(경험담 사칭 X).
사진 적극 수급(랜드마크 6장) + 홈판 스타일. 스레드 게시 + 복붙페이지 + 텔레그램.
"""
import html
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
from auto_blog.publishers import threads_upload  # noqa: E402
import daily_publish as dp  # noqa: E402

client = OpenAI(api_key=config.OPENAI_API_KEY)
MODEL = config.get("OPENAI_MODEL", "gpt-4o")
SLUG = "thailand-3n4d"
MAX_IMAGES = 6

GROUNDING = """[딥리서치 사실 — 출처기반, 네 표현으로. '정보 정리형'이며 '가본 것처럼' 경험담 사칭 금지. 가격은 대략 범위로, 변동 안내]
- 콘셉트: 방콕(도시)+파타야(바다) 조합이 3박4일에 가장 무난. 파타야는 방콕에서 차로 약 2시간.
- 무비자: 한국인은 관광 목적 무비자 90일 체류(여권만 있으면 됨).
- 추천 동선(예시): 1일차 파타야 도착·터미널21(피어21 푸드코트 가성비) → 2일차 코란섬(산호섬) 반나절 투어(제트스키·바나나보트·패러세일링)+진리의 성전 → 3일차 방콕 이동, 왕궁·왓프라깨우·왓포, 짜오프라야강 왓아룬(새벽사원) 야경 → 4일차 담넌사두억 수상시장·매끌렁 기찻길시장.
- 예산(대략, 1인·여행스타일 따라 편차 큼): 3박4~5일 80~150만원선. 항공 평수기 30~40만·성수기 50~60만, 숙박 4성 1박 7~10만·5성 15~25만, 식비 하루 5만원이면 넉넉(길거리 팟타이/쌀국수 2,000~3,000원).
- 환전: 5만원권 현금→현지 환전소(슈퍼리치 등)가 유리. 트래블카드·GLN QR 결제 대중화 → 현금은 예산 30%만 추천.
- 팁 문화: 객실청소·벨보이 20~50바트, 마사지 만족 시 50~100바트 정도.
- 7월은 우기지만 하루 종일 X → 오후·저녁 1~2시간 스콜(쏟아지다 금방 갬). 한국 장마와 다름. 기온 26~33도.
- 우기 팁: 오전엔 야외(사원·해변), 오후엔 실내(쇼핑몰·마사지·카페)로 짜면 비 영향 적음. 남부 섬(푸켓·피피)은 파도↑·배편 취소 가능 → 우기엔 방콕·파타야가 안전.
- 준비물: 젖어도 잘 마르는 신발(크록스·샌들), 얇은 겉옷(실내 냉방 강함), 접이식 우비/방수재킷, 방수팩, 모기퇴치제.
- 우기 장점: 항공·호텔이 성수기 대비 30~50% 저렴.
"""

TASK = ("주제: 7월(우기) 태국 방콕+파타야 3박4일 자유여행 '플래닝 가이드'. 처음 가는 사람이 일정·예산·"
        "준비를 한 번에 파악하게.\n반드시 포함: ①무비자 등 기본정보 ②3박4일 추천 동선 ③예산 총정리"
        "(항공·숙소·식비, 대략 범위) ④7월 우기 여행 꿀팁(일정 짜는 법) ⑤준비물 체크 ⑥환전·팁 문화 "
        "⑦설레는 마무리.\n**정보 정리형**으로 쓰고, 직접 다녀온 척(경험담) 금지. 가격은 '대략/변동 가능'.\n")

SHAPE = """JSON 형식: {"title":"클릭하고 싶은 제목(이모지 1개,35자내)","meta_description":"120~150자",
"tags":["다양하게 10~13개(태국·방콕·파타야·여행경비·무비자·우기 등)"],
"sections":[{"heading":"소제목(이모지)","paragraphs":["문단","문단"],"image_prompt":"그 섹션에 맞는 태국 랜드마크/장면의 구체적 영어 사진묘사(예: Bangkok Grand Palace golden temple, Wat Arun riverside sunset, Pattaya beach aerial, Thai street food pad thai, floating market boats, tuk tuk street) — 텍스트·로고 없이"}],
"disclaimer":"가격·영업정보·교통은 변동될 수 있으니 예약 전 최신 정보를 확인하세요."}"""


def _count(a):
    return sum(len(p) for s in a.get("sections", []) for p in s.get("paragraphs", []))


def gen_target(lo=2000, hi=2800, tries=4):
    base = TASK + GROUNDING + "\n" + SHAPE
    r = client.chat.completions.create(
        model=MODEL, response_format={"type": "json_object"}, temperature=0.75, max_tokens=7000,
        messages=[{"role": "system", "content": writer.SYSTEM}, {"role": "user", "content": base}])
    a = json.loads(r.choices[0].message.content)
    for _ in range(tries):
        c = _count(a)
        print(f"   현재 {c}자")
        if c >= lo:
            break
        r = client.chat.completions.create(
            model=MODEL, response_format={"type": "json_object"}, temperature=0.6, max_tokens=7000,
            messages=[{"role": "system", "content": writer.SYSTEM}, {"role": "user", "content":
                      f"아래 JSON 글을 더 알차게 확장(같은 형식, 사실 유지, 경험담 사칭·거짓 금지). 전체 문단 "
                      f"글자수 합계 공백포함 {lo}~{hi}자. 소제목도 더 늘려도 됨.\n" + GROUNDING + "\n" + SHAPE
                      + "\n\n[현재 글]\n" + json.dumps(a, ensure_ascii=False)}])
        a = json.loads(r.choices[0].message.content)
    return a


PAGE = """<!doctype html><html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>{title} — 복붙</title>
<style>:root{{--navy:#13294b}}*{{box-sizing:border-box}}body{{margin:0;font-family:-apple-system,'Malgun Gothic',sans-serif;background:#f4f5f7;color:#1f2430;line-height:1.8;padding:16px}}.wrap{{max-width:720px;margin:0 auto}}.bar{{position:sticky;top:0;background:#f4f5f7;padding:10px 0;display:flex;gap:8px;flex-wrap:wrap;border-bottom:1px solid #e3e6ea;z-index:5}}button{{border:0;border-radius:10px;padding:11px 14px;font-size:15px;font-weight:700;cursor:pointer}}.main{{background:var(--navy);color:#fff;flex:1;min-width:170px}}.sub{{background:#fff;color:var(--navy);border:1.5px solid var(--navy)}}.card{{background:#fff;border-radius:14px;padding:22px;margin-top:14px;box-shadow:0 2px 10px rgba(0,0,0,.05)}}h1{{font-size:21px;line-height:1.4;color:var(--navy)}}h2{{font-size:18px;margin:1.4em 0 .4em;color:var(--navy)}}img{{width:100%;border-radius:12px;margin:14px 0;display:block}}.tags{{margin-top:10px;color:#2c6;font-weight:600}}.disc{{font-size:13px;color:#8a909c;margin-top:14px}}.hint{{font-size:13px;color:#7a8190}}#toast{{position:fixed;left:50%;bottom:26px;transform:translateX(-50%);background:#1f2430;color:#fff;padding:11px 18px;border-radius:22px;opacity:0;transition:.25s;font-weight:600}}#toast.on{{opacity:1}}</style></head>
<body><div class="wrap"><div class="bar">
<button class="main" onclick="copyBody()">📋 본문 전체 복사 (글+사진+태그)</button>
<button class="sub" onclick="copyTitle()">제목 복사</button>
<button class="sub" onclick="copyTags()">🏷 태그 복사</button></div>
<p class="hint">제목 복사 → 제목칸 · 본문 전체 복사 → 본문(사진·태그 같이) · 네이버/블로거에 붙여넣기</p>
<div class="card"><div id="body">{body}</div></div></div>
<div id="toast"></div><script>
const TITLE=document.getElementById('title').textContent;
const tagsEl=document.getElementById('tags');
const TAGS=tagsEl?tagsEl.textContent.replace(/#/g,' ').replace(/\\s+/g,' ').trim():'';
function toast(m){{const t=document.getElementById('toast');t.textContent=m;t.classList.add('on');setTimeout(()=>t.classList.remove('on'),1600)}}
function copyTitle(){{navigator.clipboard.writeText(TITLE).then(()=>toast('제목 복사됨!')).catch(()=>toast('실패'))}}
function copyTags(){{navigator.clipboard.writeText(TAGS).then(()=>toast('태그 복사됨!(# 없이)')).catch(()=>toast('실패'))}}
function copyBody(){{const b=document.getElementById('body');const s=window.getSelection();const r=document.createRange();r.selectNodeContents(b);s.removeAllRanges();s.addRange(r);let ok=false;try{{ok=document.execCommand('copy')}}catch(e){{}}s.removeAllRanges();toast(ok?'글+사진 복사됨! 붙여넣기':'실패 — 직접 드래그')}}
</script></body></html>"""


def esc(t):
    return html.escape(str(t))


def render_page(article, image_urls):
    parts = [f'<h1 id="title">{esc(article["title"])}</h1>']
    for i, s in enumerate(article.get("sections", [])):
        parts.append(f'<h2>{esc(s["heading"])}</h2>')
        for p in s.get("paragraphs", []):
            parts.append(f'<p>{esc(p)}</p>')
        url = image_urls.get(str(i)) or image_urls.get(i)
        if url:
            parts.append(f'<img src="{url}" alt="">')
    if article.get("disclaimer"):
        parts.append(f'<p class="disc">※ {esc(article["disclaimer"])}</p>')
    tagline = " ".join("#" + str(t).replace(" ", "") for t in article.get("tags", []))
    parts.append(f'<p class="tags" id="tags">{esc(tagline)}</p>')
    return PAGE.format(title=esc(article["title"]), body="\n".join(parts))


RESUME = [a for a in sys.argv[1:] if not a.startswith("--")]
if RESUME:
    out_dir = config.DATA_DIR / "posts" / RESUME[0]
    art = json.loads((out_dir / "blog.json").read_text(encoding="utf-8"))
    imgs = {int(p.stem[3:]): f"images/{p.name}" for p in sorted((out_dir / "images").glob("sec*.jpg"))}
    print(f"♻ 재개: {out_dir.name} | {_count(art)}자 | 이미지 {len(imgs)}장")
else:
    print("① 태국 가이드 생성(2000~2800자)…")
    art = gen_target()
    art["keyword"] = "태국 3박4일"
    art["category"] = "general"
    print("   제목:", art["title"], "|", _count(art), "자 | 섹션", len(art["sections"]))
    print(f"② 사진 적극 수급(최대 {MAX_IMAGES}장)…")
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    out_dir = config.DATA_DIR / "posts" / f"{stamp}-{SLUG}"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "blog.json").write_text(json.dumps(art, ensure_ascii=False, indent=2), encoding="utf-8")
    imgs, _ = imgmod.generate_for_article(art, out_dir, max_images=MAX_IMAGES)

import base64 as _b64  # noqa: E402
import os as _os  # noqa: E402


def _host_upsert(images, dirname, folder):
    """sha 조회 후 PUT(덮어쓰기) — 기존 파일 422·신규 모두 처리."""
    repo = _os.environ.get("GITHUB_REPOSITORY")
    token = _os.environ.get("GITHUB_TOKEN")
    if not (repo and token):
        return {}
    h = {"Authorization": f"token {token}", "Accept": "application/vnd.github+json"}
    urls = {}
    for idx, rel in images.items():
        src = folder / rel
        if not src.exists():
            continue
        path = f"public/{dirname}/{_os.path.basename(rel)}"
        api = f"https://api.github.com/repos/{repo}/contents/{path}"
        sha = None
        try:
            g = requests.get(api, headers=h, timeout=30)
            if g.status_code == 200:
                sha = g.json().get("sha")
        except requests.RequestException:
            pass
        body = {"message": f"img {path}", "branch": "main",
                "content": _b64.b64encode(src.read_bytes()).decode()}
        if sha:
            body["sha"] = sha
        try:
            r = requests.put(api, headers=h, json=body, timeout=60)
            if r.status_code in (200, 201):
                urls[str(idx)] = f"https://raw.githubusercontent.com/{repo}/main/{path}"
            else:
                print("  업로드 실패", idx, r.status_code, r.text[:80])
        except requests.RequestException as e:
            print("  업로드 오류", idx, e)
    return urls


rec = {"article": art, "images": imgs, "dir": out_dir.name}
rec["image_urls"] = _host_upsert(imgs, out_dir.name, out_dir)
print("   사진:", len(rec["image_urls"]), "장")

print("③ 복붙 페이지…")
(ROOT / "docs" / f"travel-{SLUG}.html").write_text(render_page(art, rec["image_urls"]), encoding="utf-8")

print("④ 스레드 게시…")
th_msg = "건너뜀"
try:
    tv = variants.make_threads(art)
    text = (tv["text"] + "\n" + " ".join(tv.get("hashtags", []))).strip()
    thumb_url = rec["image_urls"].get("0") or (next(iter(rec["image_urls"].values())) if rec["image_urls"] else None)
    if text and threads_upload.configured() and "--no-threads" not in sys.argv:
        th_msg = threads_upload.post(text, thumb_url)
except Exception as e:
    th_msg = f"실패: {e}"
print("   스레드:", th_msg)

print("⑤ 텔레그램…")
page = f"https://usualhealth383-cloud.github.io/autoblog/travel-{SLUG}.html"
msg = (f"🇹🇭 태국 3박4일 가이드 완료 ({_count(art)}자, 사진 {len(rec['image_urls'])}장)\n\n"
       f"제목: {art['title']}\n🟢 복붙: {page}\n🧵 스레드: {th_msg}\n\n📝 Blogger는 웹으로 올리세요")
for cid in tb._load_chats():
    requests.post(f"{tb.API}/sendMessage", data={"chat_id": cid, "text": msg[:4096],
                  "disable_web_page_preview": "true"}, timeout=30)
print("완료 ✅", page)
