"""프리미엄 영화 리뷰(손수 집필) — '한란'(2025). 딥리서치 근거, 표·출처, 저작권 안전 이미지.
페이지(docs/movie-hanran.html) + 스레드 + 텔레그램."""
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
import requests  # noqa: E402
from auto_blog import config, images as imgmod, variants  # noqa: E402
from auto_blog import telegram_bot as tb  # noqa: E402
from auto_blog.publishers import threads_upload  # noqa: E402

SLUG = "movie-hanran"
MAX_IMAGES = 6

ART = {
    "title": "🎬 영화 '한란' 리뷰 — 겨울 난초처럼, 꺾이지 않은 모녀의 생존기",
    "tags": ["한란", "영화한란", "김향기", "하명미감독", "제주4·3", "한국영화", "시대극", "2025영화",
             "영화리뷰", "영화추천", "모성애", "제주도영화", "넷플릭스영화"],
    "disclaimer": "본 글에는 일부 줄거리(스포일러)가 포함되어 있습니다. 개봉·상영·관람등급(12세 이상) 정보는 변동될 수 있으니 극장·OTT에서 확인하세요.",
    "sources": ["나무위키 '한란'", "씨네21 영화 상세정보", "김향기 인터뷰(EN·네이트 연예, 2025.11)", "민들뉴스", "세계일보", "위키트리"],
    "table": {"caption": "영화 '한란' 기본 정보", "headers": ["항목", "내용"], "rows": [
        ["제목", "한란 (Hallan)"],
        ["감독", "하명미"],
        ["개봉", "2025년 11월 26일"],
        ["러닝타임", "118분"],
        ["관람등급", "12세 이상 관람가"],
        ["주요 출연", "김향기(고아진), 김민채(강해생), 황정남(박중사)"],
        ["장르·배경", "시대극 드라마 · 1948년 제주"]]},
    "sections": [
        {"heading": "🎬 조용하지만 오래 남는 영화 한 편",
         "image_prompt": "a quiet cinema screen glowing softly in a dark empty theater, cinematic mood, no text, no logos",
         "paragraphs": [
            "어떤 영화는 요란한 홍보 없이도 마음 깊은 곳에 오래 머뭅니다. 2025년 11월에 개봉한 '한란'이 바로 그런 작품입니다. 극장에서 크게 화제가 되지는 않았지만, 본 사람들의 입에서 입으로 '먹먹하다', '여운이 가시지 않는다'는 말이 번지며 조용히 존재감을 키워 온 영화이지요.",
            "이 글은 아직 이 작품을 만나지 못한 분들을 위한 안내이자, 이미 보신 분들과 나누고 싶은 감상이기도 합니다. 큰 줄거리는 담되, 영화의 깊은 감정을 직접 느끼실 수 있도록 결정적인 장면은 아껴 두었습니다."]},
        {"heading": "📽️ 영화 '한란', 어떤 작품인가",
         "image_prompt": None,
         "paragraphs": [
            "'한란'은 하명미 감독이 연출하고 배우 김향기가 주연을 맡은 시대극 드라마입니다. 2025년 11월 26일에 개봉했으며, 러닝타임은 118분, 12세 이상 관람가입니다.",
            "배경은 1948년의 제주입니다. 아역 시절부터 사랑받아 온 김향기가 이번에는 한 아이의 엄마 '아진'으로 분해, 한층 깊어진 얼굴을 보여 줍니다. 엄마를 애타게 찾는 딸 '해생' 역은 김민채가 맡아, 두 사람의 이야기가 영화의 심장을 이룹니다."]},
        {"heading": "🌸 '한란'이라는 제목에 담긴 뜻",
         "image_prompt": "a single delicate wild orchid blooming among cold rocks in winter, soft light, resilient and beautiful, no text",
         "paragraphs": [
            "영화를 이해하는 첫 번째 열쇠는 제목에 있습니다. '한란'은 한라산에서만 자생하는 난초로, 겨울의 추위 속에서도 꽃을 피워내는 강인한 식물입니다. 천연기념물 제191호로 지정될 만큼 귀하게 여겨지지요.",
            "돌과 바람, 척박한 환경을 견디며 끝내 꽃을 피우는 한란의 모습은 이 영화가 그리려는 '생존'과 '희망'의 상징 그 자체입니다. 가장 혹독한 계절에 피어나는 꽃처럼, 가장 어두운 시대를 건너는 모녀의 이야기라는 뜻을 제목 하나에 오롯이 담아낸 셈입니다."]},
        {"heading": "📖 산으로 간 엄마, 마을에 남은 딸",
         "image_prompt": "a misty forest trail on a mountain in Jeju Korea, moody and cinematic, foggy atmosphere, no text, no people",
         "paragraphs": [
            "1948년 제주, 토벌대를 피해 사람들은 한라산으로 몸을 숨깁니다. 엄마 '아진' 역시 산으로 피신하지만, 그 혼란 속에서 마을에 두고 온 딸 '해생'과 뜻하지 않게 생이별을 하게 됩니다.",
            "산을 오르던 아진은 군인들이 마을을 모두 불태웠다는 소식을 듣습니다. 딸이 홀로 남겨졌다는 생각에, 그녀는 모든 위험을 무릅쓰고 다시 산을 내려가기로 결심합니다. 딸을 찾아 하산하는 엄마와, 엄마를 찾아 산을 오르는 딸. 서로를 향해 걷는 두 사람의 절박한 여정이 영화의 큰 줄기를 이룹니다.",
            "산과 바다를 넘나드는 이 여정은 단순한 추격이나 재난의 이야기가 아닙니다. '어떻게든 살아서 다시 만나겠다'는, 사랑의 또 다른 이름에 가깝습니다."]},
        {"heading": "🏔️ 1948년 제주, 그 시대를 마주하는 법",
         "image_prompt": "dramatic Jeju coastal cliffs and sea under a grey winter sky, wild nature, solemn mood, no text, no people",
         "paragraphs": [
            "'한란'의 배경이 되는 1948년의 제주는 우리 현대사에 깊은 상처로 남은 시기입니다. 영화는 그 아픈 역사를 큰 목소리로 주장하기보다, 그 시대를 살아 낸 한 사람 한 사람의 얼굴과 마음으로 조용히 담아냅니다.",
            "김향기는 한 인터뷰에서 당시의 증언집을 읽으며 마음이 많이 괴로웠다고, 실제로 고통을 겪은 분들의 이야기라 더욱 조심스러웠다고 밝히기도 했습니다. 그 진심 어린 태도가 화면 곳곳에 스며 있어, 관객은 '역사'라는 거대한 단어 대신 한 엄마의 떨리는 손끝을 통해 그 시대를 마주하게 됩니다."]},
        {"heading": "🎭 이 영화를 특별하게 만드는 것들",
         "image_prompt": "misty Hallasan mountain forest in winter, atmospheric Jeju landscape, cinematic wide view, no text, no people",
         "paragraphs": [
            "첫째는 단연 김향기의 연기입니다. 제주 아낙의 투박함 속에 숨은 섬세한 모성애를, 그녀는 과장 없이 완숙하게 그려냅니다. 산을 넘고 바다에 몸을 던지는 고된 장면까지 직접 소화하며, '김향기라는 배우에겐 정말 향기가 있다'는 관객평이 나올 만큼 깊은 인상을 남깁니다.",
            "둘째는 '진짜'에 대한 집요함입니다. 제작진은 배우들의 자연스러운 제주 방언을 위해 현지인 중심의 '대사 닥터'를 열 명 남짓 두고 거의 일대일로 리허설을 진행했고, 촬영은 100퍼센트 동시 녹음으로 이뤄졌다고 합니다. 김향기는 촬영 약 3개월 전부터 인물을 연구하고 제주를 직접 답사하며 제주어를 익혔습니다.",
            "셋째는 제주의 풍광입니다. 실제 제주 곳곳의 산과 숲을 누비며 담아낸 화면은 그 자체로 아름다우면서도, 인물들이 통과해야 하는 혹독한 자연을 실감 나게 전합니다. 아름다움과 서늘함이 공존하는 이 배경이 영화의 정서를 한층 깊게 만듭니다."]},
        {"heading": "💬 본 사람들이 입을 모아 말하는 것",
         "image_prompt": None,
         "paragraphs": [
            "'한란'을 본 관객들의 반응은 한결같이 따뜻하고, 또 먹먹합니다. '처음부터 끝까지 손을 꼭 쥐고 보게 된다', '영화가 끝나고도 여운이 오래 남는다'는 감상이 이어졌습니다.",
            "흥미로운 점은, 극장 관객 수는 크지 않았음에도 입소문을 타고 온라인에서 뜨거운 호평을 얻었다는 사실입니다. 화려한 볼거리 대신 진심과 정성으로 승부한 작품이 어떻게 관객의 마음을 움직이는지 보여 주는 좋은 예이지요. 김향기의 연기는 해외에서도 호평을 받았다고 전해집니다."]},
        {"heading": "🤍 마무리 — 가장 추운 곳에서 피는 꽃",
         "image_prompt": "a warm hopeful winter sunrise over a snowy mountain, gentle light breaking through, serene and moving, no text",
         "paragraphs": [
            "'한란'은 편하게 즐기는 오락 영화는 아닙니다. 무거운 시대와 아픈 이별을 정면으로 마주해야 하니까요. 하지만 그 무게를 견디고 나면, 어떤 상황에서도 '살아서 다시 만나자'는 마음이 얼마나 강한지를 오래 곱씹게 됩니다.",
            "가장 추운 겨울에 꽃을 피우는 한란처럼, 이 영화는 가장 어두운 시대에도 꺾이지 않은 사랑과 생명을 이야기합니다. 조용한 영화 한 편에서 깊은 울림을 얻고 싶은 분이라면, 그리고 김향기라는 배우의 새로운 얼굴을 만나고 싶은 분이라면, '한란'은 충분히 시간을 내어 볼 가치가 있는 작품입니다."]},
    ],
}

PAGE = """<!doctype html><html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>{title} — 복붙</title>
<style>:root{{--navy:#13294b}}*{{box-sizing:border-box}}body{{margin:0;font-family:-apple-system,'Malgun Gothic',sans-serif;background:#f4f5f7;color:#1f2430;line-height:1.85;padding:16px}}.wrap{{max-width:720px;margin:0 auto}}.bar{{position:sticky;top:0;background:#f4f5f7;padding:10px 0;display:flex;gap:8px;flex-wrap:wrap;border-bottom:1px solid #e3e6ea;z-index:5}}button{{border:0;border-radius:10px;padding:11px 14px;font-size:15px;font-weight:700;cursor:pointer}}.main{{background:var(--navy);color:#fff;flex:1;min-width:170px}}.sub{{background:#fff;color:var(--navy);border:1.5px solid var(--navy)}}.card{{background:#fff;border-radius:14px;padding:22px;margin-top:14px;box-shadow:0 2px 10px rgba(0,0,0,.05)}}h1{{font-size:22px;line-height:1.4;color:var(--navy)}}h2{{font-size:18px;margin:1.5em 0 .4em;color:var(--navy)}}p{{white-space:pre-line}}img{{width:100%;border-radius:12px;margin:14px 0;display:block}}table{{border-collapse:collapse;width:100%;margin:14px 0;font-size:15px}}caption{{font-weight:800;color:var(--navy);text-align:left;margin-bottom:8px;font-size:16px}}th,td{{border:1px solid #dde1e6;padding:9px 12px;text-align:left}}th{{background:#eef2f7;font-weight:700}}.src{{margin-top:20px;padding:14px 18px;background:#f8f9fa;border-radius:10px;font-size:14px}}.src b{{color:var(--navy)}}.tags{{margin-top:14px;color:#2c6;font-weight:600}}.disc{{font-size:13px;color:#8a909c;margin-top:14px}}.hint{{font-size:13px;color:#7a8190}}#toast{{position:fixed;left:50%;bottom:26px;transform:translateX(-50%);background:#1f2430;color:#fff;padding:11px 18px;border-radius:22px;opacity:0;transition:.25s;font-weight:600}}#toast.on{{opacity:1}}</style></head>
<body><div class="wrap"><div class="bar">
<button class="main" onclick="copyBody()">📋 본문 전체 복사 (글+사진+표+태그)</button>
<button class="sub" onclick="copyTitle()">제목 복사</button>
<button class="sub" onclick="copyTags()">🏷 태그 복사</button></div>
<p class="hint">제목 복사 → 제목칸 · 본문 전체 복사 → 본문(사진·표 같이) · Blogger/네이버에 붙여넣기</p>
<div class="card"><div id="body">{body}</div></div></div>
<div id="toast"></div><script>
const TITLE=document.getElementById('title').textContent;
const tagsEl=document.getElementById('tags');
const TAGS=tagsEl?tagsEl.textContent.replace(/#/g,' ').replace(/\\s+/g,' ').trim():'';
function toast(m){{const t=document.getElementById('toast');t.textContent=m;t.classList.add('on');setTimeout(()=>t.classList.remove('on'),1600)}}
function copyTitle(){{navigator.clipboard.writeText(TITLE).then(()=>toast('제목 복사됨!')).catch(()=>toast('실패'))}}
function copyTags(){{navigator.clipboard.writeText(TAGS).then(()=>toast('태그 복사됨!(# 없이)')).catch(()=>toast('실패'))}}
function copyBody(){{const b=document.getElementById('body');const s=window.getSelection();const r=document.createRange();r.selectNodeContents(b);s.removeAllRanges();s.addRange(r);let ok=false;try{{ok=document.execCommand('copy')}}catch(e){{}}s.removeAllRanges();toast(ok?'글+사진+표 복사됨! 붙여넣기':'실패 — 직접 드래그')}}
</script></body></html>"""


def esc(t):
    return html.escape(str(t))


def table_html(tbl):
    if not tbl or not tbl.get("rows"):
        return ""
    heads = "".join(f"<th>{esc(h)}</th>" for h in tbl.get("headers", []))
    rows = "".join("<tr>" + "".join(f"<td>{esc(c)}</td>" for c in r) + "</tr>" for r in tbl["rows"])
    cap = f"<caption>📊 {esc(tbl.get('caption',''))}</caption>" if tbl.get("caption") else ""
    return f"<table>{cap}<thead><tr>{heads}</tr></thead><tbody>{rows}</tbody></table>"


def sources_html(srcs):
    if not srcs:
        return ""
    lis = "".join(f"<li>{esc(s)}</li>" for s in srcs)
    return f'<div class="src"><b>📚 참고 자료</b><ul style="margin:6px 0 0;padding-left:18px">{lis}</ul></div>'


def host_upsert(images, dirname, folder):
    repo = _os.environ.get("GITHUB_REPOSITORY"); token = _os.environ.get("GITHUB_TOKEN")
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
        body = {"message": f"img {path}", "branch": "main", "content": _b64.b64encode(src.read_bytes()).decode()}
        if sha:
            body["sha"] = sha
        try:
            r = requests.put(api, headers=h, json=body, timeout=60)
            if r.status_code in (200, 201):
                urls[str(idx)] = f"https://raw.githubusercontent.com/{repo}/main/{path}"
        except requests.RequestException:
            pass
    return urls


def render_page(a, image_urls):
    parts = [f'<h1 id="title">{esc(a["title"])}</h1>']
    tbl = table_html(a.get("table"))
    for i, s in enumerate(a["sections"]):
        parts.append(f'<h2>{esc(s["heading"])}</h2>')
        for p in s["paragraphs"]:
            parts.append(f'<p>{esc(p)}</p>')
        url = image_urls.get(str(i)) or image_urls.get(i)
        if url:
            parts.append(f'<img src="{url}" alt="">')
        if i == 1 and tbl:
            parts.append(tbl); tbl = ""
    if tbl:
        parts.append(tbl)
    parts.append(sources_html(a.get("sources")))
    if a.get("disclaimer"):
        parts.append(f'<p class="disc">※ {esc(a["disclaimer"])}</p>')
    tagline = " ".join("#" + str(t).replace(" ", "") for t in a.get("tags", []))
    parts.append(f'<p class="tags" id="tags">{esc(tagline)}</p>')
    return PAGE.format(title=esc(a["title"]), body="\n".join(parts))


chars = sum(len(p) for s in ART["sections"] for p in s["paragraphs"])
print("글자수:", chars, "| 섹션", len(ART["sections"]))
stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
out_dir = config.DATA_DIR / "posts" / f"{stamp}-{SLUG}"
out_dir.mkdir(parents=True, exist_ok=True)
(out_dir / "blog.json").write_text(json.dumps(ART, ensure_ascii=False, indent=2), encoding="utf-8")
imgs, _ = imgmod.generate_for_article(ART, out_dir, max_images=MAX_IMAGES)
urls = host_upsert(imgs, out_dir.name, out_dir)
print("사진:", len(urls))
(ROOT / "docs" / f"{SLUG}.html").write_text(render_page(ART, urls), encoding="utf-8")

th_msg = "건너뜀"
if "--no-threads" not in sys.argv:
    try:
        tv = variants.make_threads(ART)
        text = (tv["text"] + "\n" + " ".join(tv.get("hashtags", []))).strip()
        thumb = urls.get("0") or (next(iter(urls.values())) if urls else None)
        if text and threads_upload.configured():
            th_msg = threads_upload.post(text, thumb)
    except Exception as e:
        th_msg = f"실패: {e}"
print("스레드:", th_msg)

page = f"https://usualhealth383-cloud.github.io/autoblog/{SLUG}.html"
msg = f"🎬 영화 '한란' 리뷰 완료 ({chars}자, 사진 {len(urls)}장)\n🟢 복붙: {page}\n🧵 스레드: {th_msg}"
for cid in tb._load_chats():
    requests.post(f"{tb.API}/sendMessage", data={"chat_id": cid, "text": msg[:4096], "disable_web_page_preview": "true"}, timeout=30)
print("완료 ✅", page)
