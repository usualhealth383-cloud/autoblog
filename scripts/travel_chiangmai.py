"""치앙마이 3박4일 감성 여행 가이드 — 인플루언서 톤 + 상세 코스 + 실제 맛집/카페.
딥리서치 정보 정리형(경험담 사칭 X). 사진 적극(7장). 스레드 게시 + 복붙페이지 + 텔레그램.
"""
import base64 as _b64
import html
import json
import os as _os
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

client = OpenAI(api_key=config.OPENAI_API_KEY)
MODEL = config.get("OPENAI_MODEL", "gpt-4o")
SLUG = "chiangmai-3n4d"
MAX_IMAGES = 7

GROUNDING = """[딥리서치 사실 — 출처기반, 네 표현으로. 정보 정리형(가본 척 경험담·허위 금지). 맛집은 조사된 곳을 구체적으로, 평가는 '~로 유명한/미쉐린 빕구르망'처럼]
- 무비자: 한국인 관광 무비자 90일(여권만). 치앙마이는 방콕보다 물가 20~30% 저렴(가성비·혼행·한달살기 성지).
- 분위기: 태국 북부의 '느림·감성' 도시. 붉은 벽돌 성곽의 올드타운(구시가) 안에 오래된 사원과 골목, 힙한 님만해민.
- 올드타운 사원: 왓 치앙만(치앙마이에서 가장 오래된 사원) → 도보 약 15분 왓 프라싱 → 왓 체디루앙(1411년 건립, 대지진으로 탑 윗부분이 무너져 오히려 웅장·신비. 오후 5시경 노을에 회백색 탑이 붉게 물듦).
- 도이수텝: 해발 1,676m, 정상에 왓 프라탓 도이수텝(황금 사원). 시내서 차로 약 40분. 300여 계단(케이블카 있음). 일몰·시내 파노라마 뷰가 압권 → 저녁 일정 추천.
- 님만해민: 감각적 카페·트렌디 맛집·편집숍이 모인 '힙한' 거리. 랜드마크 '원 님만(One Nimman)'은 붉은 벽돌+시계탑이 유럽 골목 느낌. 한낮 더울 때 에어컨 시원한 실내 코스로 좋음.
- 선데이 마켓: 일요일 저녁 올드타운에서 열리는 큰 야시장(수공예·먹거리).
- 맛집·카페(실제 조사): ①카오소이(북부식 코코넛커리 국수) — '카오소이 님만(Khao Soi Nimman)'이 미쉐린 빕구르망으로 유명(늘 붐빔). ②더티커피(더티라떼, 숙성우유·연유) — '아카아마 커피(Akha Ama Coffee)'가 유명. ③야시장 먹거리 코스 — 무삥(돼지고기 꼬치)+맥주 → 즉석 팟타이 → 바나나 로띠 + 땡모반(수박주스)로 '단짠단짠' 마무리.
- 시간대 동선(더위 피하기): 아침 사원(왓 치앙만·왓 프라싱) → 한낮 원 님만(실내) → 해질녘 왓 체디루앙 노을 → 도이수텝 야경. 하루 교통비 2만원 내외.
- 7월은 우기지만 하루 종일 X → 오후·저녁 1~2시간 스콜 후 갬. 오전 야외/오후 실내로. 우기엔 항공·호텔 30~50% 저렴. 준비물: 잘 마르는 신발, 얇은 겉옷(냉방), 우비/방수팩, 모기퇴치제.
- 예산(대략, 1인): 3박4일 60~100만원선(치앙마이는 저렴한 편). 식비 하루 3~5만원이면 넉넉.
"""

TASK = ("주제: 감성의 도시 '치앙마이' 3박4일 자유여행 가이드 — 상세한 일차별 코스 + 실제 맛집·카페.\n"
        "톤: **여행 인플루언서의 감성 여행 에세이**처럼, 오감을 자극하는 이쁘고 멋드러진 묘사(빛·향·"
        "골목 분위기·설렘·노을)로 써라. 상투적 문구 말고 그림이 그려지게. 단 **사실은 정확히**"
        "(경험담 사칭·허위 금지, 맛집은 조사된 곳을 구체적으로 '미쉐린 빕구르망으로 유명한' 식).\n"
        "반드시 포함: ①치앙마이의 매력·분위기 ②일차별 상세 동선(올드타운 사원·도이수텝·님만·야시장) "
        "③구체적 맛집·카페(카오소이 님만·아카아마 더티커피·야시장 단짠단짠 코스) ④7월 우기 팁 "
        "⑤예산·무비자·준비물 ⑥설레는 마무리.\n"
        "형식 지침: 이 글은 감성 여행 가이드이므로 문단 길이 제한을 풀고 **각 문단 3~5문장으로 풍부하고 "
        "묘사적으로**. 소제목은 8~11개로 많이 나눠 상세하게.\n")

SHAPE = """JSON 형식: {"title":"감성적이고 클릭하고 싶은 제목(이모지 1개,35자내)","meta_description":"120~150자",
"tags":["다양하게 10~13개(치앙마이·태국여행·도이수텝·님만해민·카오소이·감성여행 등)"],
"sections":[{"heading":"소제목(이모지)","paragraphs":["문단","문단"],"image_prompt":"그 섹션에 맞는 치앙마이 장면의 구체적 영어 사진묘사(예: Doi Suthep golden temple sunset Chiang Mai, Wat Chedi Luang ancient brick stupa, One Nimman brick plaza clock tower, khao soi curry noodle bowl, Chiang Mai night market food stalls, old town temple lantern, cozy coffee cafe latte) — 텍스트·로고 없이"}],
"disclaimer":"가격·영업시간·메뉴는 변동될 수 있으니 방문 전 최신 정보를 확인하세요."}"""


def _count(a):
    return sum(len(p) for s in a.get("sections", []) for p in s.get("paragraphs", []))


def gen_target(lo=2500, hi=3800, tries=4):
    base = TASK + GROUNDING + "\n" + SHAPE
    r = client.chat.completions.create(
        model=MODEL, response_format={"type": "json_object"}, temperature=0.8, max_tokens=8000,
        messages=[{"role": "system", "content": writer.SYSTEM}, {"role": "user", "content": base}])
    a = json.loads(r.choices[0].message.content)
    for _ in range(tries):
        c = _count(a)
        print(f"   현재 {c}자")
        if c >= lo:
            break
        r = client.chat.completions.create(
            model=MODEL, response_format={"type": "json_object"}, temperature=0.65, max_tokens=8000,
            messages=[{"role": "system", "content": writer.SYSTEM}, {"role": "user", "content":
                      f"아래 JSON 글을 더 상세하고 감성적으로 확장(같은 형식, 사실 유지, 경험담 사칭·거짓 "
                      f"금지). 소제목을 더 늘리고 각 문단을 3~5문장의 풍부한 묘사로. 전체 공백포함 "
                      f"{lo}~{hi}자.\n" + GROUNDING + "\n" + SHAPE
                      + "\n\n[현재 글]\n" + json.dumps(a, ensure_ascii=False)}])
        a = json.loads(r.choices[0].message.content)
    return a


PAGE = """<!doctype html><html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>{title} — 복붙</title>
<style>:root{{--navy:#13294b}}*{{box-sizing:border-box}}body{{margin:0;font-family:-apple-system,'Malgun Gothic',sans-serif;background:#f4f5f7;color:#1f2430;line-height:1.85;padding:16px}}.wrap{{max-width:720px;margin:0 auto}}.bar{{position:sticky;top:0;background:#f4f5f7;padding:10px 0;display:flex;gap:8px;flex-wrap:wrap;border-bottom:1px solid #e3e6ea;z-index:5}}button{{border:0;border-radius:10px;padding:11px 14px;font-size:15px;font-weight:700;cursor:pointer}}.main{{background:var(--navy);color:#fff;flex:1;min-width:170px}}.sub{{background:#fff;color:var(--navy);border:1.5px solid var(--navy)}}.card{{background:#fff;border-radius:14px;padding:22px;margin-top:14px;box-shadow:0 2px 10px rgba(0,0,0,.05)}}h1{{font-size:22px;line-height:1.4;color:var(--navy)}}h2{{font-size:18px;margin:1.5em 0 .4em;color:var(--navy)}}img{{width:100%;border-radius:12px;margin:14px 0;display:block}}.tags{{margin-top:10px;color:#2c6;font-weight:600}}.disc{{font-size:13px;color:#8a909c;margin-top:14px}}.hint{{font-size:13px;color:#7a8190}}#toast{{position:fixed;left:50%;bottom:26px;transform:translateX(-50%);background:#1f2430;color:#fff;padding:11px 18px;border-radius:22px;opacity:0;transition:.25s;font-weight:600}}#toast.on{{opacity:1}}</style></head>
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


def host_upsert(images, dirname, folder):
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
                print("  업로드 실패", idx, r.status_code)
        except requests.RequestException as e:
            print("  업로드 오류", idx, e)
    return urls


RESUME = [a for a in sys.argv[1:] if not a.startswith("--")]
if RESUME:
    out_dir = config.DATA_DIR / "posts" / RESUME[0]
    art = json.loads((out_dir / "blog.json").read_text(encoding="utf-8"))
    imgs = {int(p.stem[3:]): f"images/{p.name}" for p in sorted((out_dir / "images").glob("sec*.jpg"))}
    print(f"♻ 재개: {out_dir.name} | {_count(art)}자 | 이미지 {len(imgs)}장")
else:
    print("① 치앙마이 감성 가이드 생성(2500~3800자)…")
    art = gen_target()
    art["keyword"] = "치앙마이 3박4일"
    art["category"] = "general"
    print("   제목:", art["title"], "|", _count(art), "자 | 섹션", len(art["sections"]))
    print(f"② 사진 적극 수급(최대 {MAX_IMAGES}장)…")
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    out_dir = config.DATA_DIR / "posts" / f"{stamp}-{SLUG}"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "blog.json").write_text(json.dumps(art, ensure_ascii=False, indent=2), encoding="utf-8")
    imgs, _ = imgmod.generate_for_article(art, out_dir, max_images=MAX_IMAGES)

rec = {"article": art, "images": imgs, "dir": out_dir.name}
rec["image_urls"] = host_upsert(imgs, out_dir.name, out_dir)
print("   사진:", len(rec["image_urls"]), "장")

print("③ 복붙 페이지…")
(ROOT / "docs" / f"travel-{SLUG}.html").write_text(render_page(art, rec["image_urls"]), encoding="utf-8")

print("④ 스레드 게시…")
th_msg = "건너뜀"
if "--no-threads" not in sys.argv:
    try:
        tv = variants.make_threads(art)
        text = (tv["text"] + "\n" + " ".join(tv.get("hashtags", []))).strip()
        thumb_url = rec["image_urls"].get("0") or (next(iter(rec["image_urls"].values())) if rec["image_urls"] else None)
        if text and threads_upload.configured():
            th_msg = threads_upload.post(text, thumb_url)
    except Exception as e:
        th_msg = f"실패: {e}"
print("   스레드:", th_msg)

print("⑤ 텔레그램…")
page = f"https://usualhealth383-cloud.github.io/autoblog/travel-{SLUG}.html"
msg = (f"🇹🇭 치앙마이 3박4일 감성 가이드 완료 ({_count(art)}자, 사진 {len(rec['image_urls'])}장)\n\n"
       f"제목: {art['title']}\n🟢 복붙: {page}\n🧵 스레드: {th_msg}\n\n📝 Blogger는 웹으로 올리세요")
for cid in tb._load_chats():
    requests.post(f"{tb.API}/sendMessage", data={"chat_id": cid, "text": msg[:4096],
                  "disable_web_page_preview": "true"}, timeout=30)
print("완료 ✅", page)
