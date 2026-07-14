"""프리미엄 드라마 글(손수 집필) — '김부장' 6화 총정리 + 7화 예상.
드라마 분위기 AI 이미지(아빠·느와르·부성애) + (선택)공식 포스터(출처표기). 페이지+스레드+텔레그램.
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
import requests  # noqa: E402
from auto_blog import config, images as imgmod, variants  # noqa: E402
from auto_blog import telegram_bot as tb  # noqa: E402
from auto_blog.publishers import threads_upload  # noqa: E402

SLUG = "drama-kimbujang-ep7"
MAX_IMAGES = 6
# 공식 포스터를 넣고 싶으면 url·credit 채우기(정당한 인용: 비평 목적+출처표기). 비우면 미표시.
POSTER = {"url": "", "credit": "출처: SBS 「김부장」"}

ART = {
    "title": "🔥 '김부장' 6화까지 총정리 + 7화 예상 — 소지섭, 아빠의 반격이 시작된다",
    "tags": ["김부장", "김부장드라마", "소지섭", "SBS금토드라마", "서수민", "주상욱", "김부장7화",
             "김부장6화", "드라마리뷰", "드라마예상", "아빠액션", "웹툰원작드라마", "소지섭복귀작"],
    "disclaimer": "본 글에는 6화까지의 줄거리(스포일러)가 포함되어 있으며, 7화 전개는 예고편과 흐름을 바탕으로 한 개인적 예상입니다. 방영 정보는 변동될 수 있습니다.",
    "sources": ["나무위키 '김부장(드라마)'", "SBS 「김부장」 공식(예고·클립)", "위키백과 '김부장'", "언론 보도(캐스팅·편성)"],
    "table": {"caption": "드라마 '김부장' 기본 정보", "headers": ["항목", "내용"], "rows": [
        ["제목", "김부장 (Mr. Kim)"],
        ["방송", "SBS 금토드라마 (2026년 6월 26일 첫 방송)"],
        ["원작", "동명의 인기 웹툰"],
        ["편성", "10부작"],
        ["주요 출연", "소지섭(김부장), 서수민(김민지), 서지혜(림유진), 최대훈·윤경호, 주상욱, 원현준 등"],
        ["6화 방송", "2026년 7월 11일(토)"],
        ["7화 방송", "2026년 7월 17일(금) 밤 9시 50분"]]},
    "sections": [
        {"heading": "🎬 가장 평범한 아빠가, 가장 위험한 남자가 되다",
         "image_prompt": "a determined middle-aged Korean man in a plain suit standing in a dark rainy Seoul street at night, intense protective gaze, cinematic noir action thriller mood, no text",
         "paragraphs": [
            "회사에서는 눈에 띄지 않는 회계팀 부장, 집에서는 홀로 딸을 키우는 다정한 아빠. 그런 '세상에서 가장 평범한' 남자가, 딸을 지키기 위해 '세상에서 가장 위험한' 남자로 돌변한다면 어떨까요. SBS 금토드라마 '김부장'은 바로 그 아찔한 상상에서 출발합니다.",
            "2026년 6월 26일 첫 방송을 시작한 이 작품은 배우 소지섭의 복귀작으로도 화제를 모았습니다. 그리고 지난 7월 11일 방송된 6화가 소름 돋는 장면으로 마무리되면서, 오는 17일 금요일의 7화를 향한 기대가 한껏 부풀어 올랐지요. 오늘은 6화까지의 이야기를 차분히 정리하고, 7화의 전개를 함께 예상해 보려 합니다."]},
        {"heading": "📺 '김부장'은 어떤 드라마인가",
         "image_prompt": None,
         "paragraphs": [
            "'김부장'은 동명의 인기 웹툰을 원작으로 한 '아빠 유니버스' 복수 액션 드라마입니다. 상생저축은행 회계팀 부장이자 홀로 딸을 키워 온 김부장이, 유일한 삶의 이유였던 외동딸이 사라지면서 오랫동안 숨겨 왔던 과거의 본능을 깨우는 이야기가 큰 줄기입니다.",
            "주인공 김부장은 소지섭이, 딸 김민지는 서수민이, 아내 림유진은 서지혜가 연기합니다. 김부장의 오랜 동료로 최대훈(성한수)과 윤경호(박진철)가, 앞을 가로막는 악역으로 주상욱(주강찬)이 함께합니다. 여기에 김부장의 진짜 정체를 아는 특수임무국 국장 강국철 역의 원현준이 극에 팽팽한 긴장을 더합니다. 당초 8부작으로 기획됐다가 촬영 과정에서 10부작으로 늘어난 점도, 그만큼 이야기의 밀도가 높다는 뜻이겠지요."]},
        {"heading": "👨‍👧 이야기의 시작 — 딸의 실종, 그리고 봉인 해제",
         "image_prompt": "an emotional somber scene of a father holding his missing daughter's photo alone in a dim room at night, warm melancholic light, Korean drama mood, no text",
         "paragraphs": [
            "드라마 초반, 김부장은 그저 성실하고 다정한 아버지였습니다. 딸 민지를 위해서라면 무엇이든 하는, 우리 주변에서 흔히 볼 수 있는 그런 아빠 말이지요. 하지만 그 평온은 오래가지 못합니다. 하나뿐인 딸 민지가 집을 나간 뒤 그대로 실종되면서, 김부장의 세계는 송두리째 무너집니다.",
            "딸을 찾아 나선 아버지는 이내 깨닫습니다. 평범한 방법으로는 결코 딸을 되찾을 수 없다는 것을요. 그렇게 그는 오랫동안 마음속 깊이 봉인해 두었던 과거, 즉 특수요원 시절의 짐승 같은 감각을 다시 꺼내 듭니다. 딸을 위해 스스로 가장 위험한 문을 여는 이 선택이, 김부장이라는 이야기의 진짜 출발점입니다."]},
        {"heading": "⚔️ 진짜 얼굴을 드러낸 아빠, 그리고 뭉친 사람들",
         "image_prompt": "a middle-aged Korean man walking through neon-lit night streets with a serious determined face, three men behind him, noir action thriller, no text",
         "paragraphs": [
            "회차가 거듭될수록 김부장은 봉인을 하나씩 풀어냅니다. 오랜 동료였던 성한수, 박진철과 다시 뭉치며, 세 남자는 딸을 되찾기 위한 위험한 여정에 함께 뛰어듭니다. 합쳐서 100살이 넘는 '아빠들'이 보여 주는 노련하고도 살벌한 액션은, 이 드라마의 큰 재미 중 하나로 꼽혀 왔습니다.",
            "동시에 김부장의 앞에는 두 개의 벽이 놓입니다. 하나는 딸을 위협하는 악역 주강찬이고, 다른 하나는 그의 정체를 쫓는 특수임무국입니다. 국가 안보라는 신념 하나로 움직이는 국장 강국철은, 김부장의 과거를 알기에 더욱 집요하게 그를 압박합니다. 딸을 구하려는 아버지와, 그를 통제하려는 조직 사이의 긴장이 극을 점점 조여 옵니다."]},
        {"heading": "💥 6화, \"민지야 아빠 왔다\" — 소름 돋는 마지막 장면",
         "image_prompt": "a tense dark corridor scene, a lone man's silhouette confronting shadowy figures, high stakes cinematic thriller, dramatic backlight, no text",
         "paragraphs": [
            "그리고 7월 11일 방송된 6화. 김부장은 마침내 딸에게 성큼 다가섭니다. 특수임무국과 정면으로 부딪치는 위험을 무릅쓰고, 그는 딸을 구하기 위해 온몸을 던집니다. '민지야, 아빠 왔다'라는 한마디에는, 평범한 아빠가 감춰 왔던 모든 무게가 실려 있었습니다.",
            "6화의 마지막은 특히 강렬했습니다. 김부장이 고위 인사의 목에 가느다란 실을 걸어 인질로 제압하는 장면으로 마무리되며, 그가 더 이상 물러설 곳이 없는 최전선에 섰음을 선명하게 보여 주었지요. 이 서늘한 클리프행어 한 컷이, 다음 이야기를 향한 긴장을 최고조로 끌어올렸습니다."]},
        {"heading": "🔮 7화 예상 — \"너를 제거한다\", 최후의 결단",
         "image_prompt": "a lone father figure standing ready for a final confrontation at dawn in a stark urban setting, determined and resolute, cinematic action drama, no text",
         "paragraphs": [
            "공개된 7화 예고편은 '너를 제거한다'는 김부장의 서늘한 대사와 함께, 악역 주강찬을 향한 '참교육'을 예고했습니다. 딸을 지키기 위한 아버지의 '최후의 결단'이 그려질 것으로 보이는데요. 6화에서 인질극으로 판을 뒤집은 김부장이, 이제 수세에서 공세로 완전히 전환하는 국면이라 볼 수 있습니다.",
            "여기서부터는 개인적인 예상입니다. 10부작 중 7화는 후반부의 문을 여는 분기점인 만큼, 김부장이 주강찬 세력에 결정적 반격을 가하는 동시에, 그의 정체와 과거가 한층 더 드러날 가능성이 큽니다. 특수임무국 강국철과의 관계도 '적이냐 조력자냐'의 갈림길에 설 수 있고요. 무엇보다 인질로 잡은 고위 인사를 지렛대 삼아 김부장이 어떤 카드를 꺼내 드는지가 7화의 핵심 관전 포인트가 될 것입니다.",
            "다만 이 드라마가 지금까지 '예상을 뛰어넘는 전개'로 재미를 줘 온 만큼, 우리의 예측을 시원하게 배신하는 반전 한 방도 충분히 기대해 볼 만합니다."]},
        {"heading": "🤍 왜 우리는 '김부장'에 빠져드나",
         "image_prompt": "a father embracing his teenage daughter protectively in warm backlight, emotional reunion, cinematic Korean drama mood, no text",
         "paragraphs": [
            "'김부장'이 통하는 이유는 화려한 액션 때문만은 아닙니다. 그 액션의 밑바닥에 '딸을 지키려는 아버지의 마음'이라는, 누구나 공감할 수 있는 뜨거운 정서가 깔려 있기 때문이지요. 가장 평범한 사람이 가장 강해지는 순간이 오직 '사랑하는 사람을 지킬 때'라는 이야기는, 언제 봐도 가슴을 뜁니다.",
            "6화의 그 마지막 장면을 본 사람이라면, 7화까지 남은 며칠이 유독 길게 느껴질 겁니다. 오는 17일 금요일 밤, 아빠의 반격이 어디까지 나아갈지. 소지섭이 그려 낼 김부장의 다음 얼굴을, 함께 기다려 봐요."]},
    ],
}

PAGE = """<!doctype html><html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>{title} — 복붙</title>
<style>:root{{--navy:#13294b}}*{{box-sizing:border-box}}body{{margin:0;font-family:-apple-system,'Malgun Gothic',sans-serif;background:#f4f5f7;color:#1f2430;line-height:1.85;padding:16px}}.wrap{{max-width:720px;margin:0 auto}}.bar{{position:sticky;top:0;background:#f4f5f7;padding:10px 0;display:flex;gap:8px;flex-wrap:wrap;border-bottom:1px solid #e3e6ea;z-index:5}}button{{border:0;border-radius:10px;padding:11px 14px;font-size:15px;font-weight:700;cursor:pointer}}.main{{background:var(--navy);color:#fff;flex:1;min-width:170px}}.sub{{background:#fff;color:var(--navy);border:1.5px solid var(--navy)}}.card{{background:#fff;border-radius:14px;padding:22px;margin-top:14px;box-shadow:0 2px 10px rgba(0,0,0,.05)}}h1{{font-size:22px;line-height:1.4;color:var(--navy)}}h2{{font-size:18px;margin:1.5em 0 .4em;color:var(--navy)}}p{{white-space:pre-line}}img{{width:100%;border-radius:12px;margin:14px 0;display:block}}figure{{margin:14px 0}}figcaption{{font-size:12px;color:#8a909c;text-align:center;margin-top:4px}}table{{border-collapse:collapse;width:100%;margin:14px 0;font-size:15px}}caption{{font-weight:800;color:var(--navy);text-align:left;margin-bottom:8px;font-size:16px}}th,td{{border:1px solid #dde1e6;padding:9px 12px;text-align:left}}th{{background:#eef2f7;font-weight:700}}.src{{margin-top:20px;padding:14px 18px;background:#f8f9fa;border-radius:10px;font-size:14px}}.src b{{color:var(--navy)}}.tags{{margin-top:14px;color:#2c6;font-weight:600}}.disc{{font-size:13px;color:#8a909c;margin-top:14px}}.hint{{font-size:13px;color:#7a8190}}#toast{{position:fixed;left:50%;bottom:26px;transform:translateX(-50%);background:#1f2430;color:#fff;padding:11px 18px;border-radius:22px;opacity:0;transition:.25s;font-weight:600}}#toast.on{{opacity:1}}</style></head>
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


def render_page(a, image_urls, poster_url=""):
    parts = [f'<h1 id="title">{esc(a["title"])}</h1>']
    if poster_url:
        parts.append(f'<figure><img src="{poster_url}" alt="김부장 포스터"><figcaption>{esc(POSTER.get("credit",""))}</figcaption></figure>')
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

# 드라마 분위기 이미지는 AI로 생성(글과 밀접하게)
_client = imgmod._client()
_img_dir = out_dir / "images"; _img_dir.mkdir(parents=True, exist_ok=True)
imgs = {}
for i, s in enumerate(ART["sections"]):
    if not s.get("image_prompt"):
        continue
    dest = _img_dir / f"sec{i}.jpg"
    print(f"  AI 생성 sec{i}…")
    name = imgmod._generate_one(_client, s["image_prompt"], dest)
    if name:
        imgs[i] = f"images/{name}"
urls = host_upsert(imgs, out_dir.name, out_dir)
print("사진:", len(urls))

# 공식 포스터(선택): url 있으면 다운로드→호스팅(정당한 인용, 출처표기)
poster_hosted = ""
if POSTER.get("url"):
    try:
        pdata = requests.get(POSTER["url"], timeout=30).content
        (_img_dir / "poster.jpg").write_bytes(pdata)
        purls = host_upsert({"poster": "images/poster.jpg"}, out_dir.name, out_dir)
        poster_hosted = purls.get("poster", "")
        print("포스터 호스팅:", bool(poster_hosted))
    except Exception as e:
        print("포스터 실패:", str(e)[:80])

(ROOT / "docs" / f"{SLUG}.html").write_text(render_page(ART, urls, poster_hosted), encoding="utf-8")

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
msg = f"🔥 '김부장' 6화 총정리+7화 예상 완료 ({chars}자, 사진 {len(urls)}장)\n🟢 복붙: {page}\n🧵 스레드: {th_msg}"
for cid in tb._load_chats():
    requests.post(f"{tb.API}/sendMessage", data={"chat_id": cid, "text": msg[:4096], "disable_web_page_preview": "true"}, timeout=30)
print("완료 ✅", page)
