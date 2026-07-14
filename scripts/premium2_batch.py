"""프리미엄 2차 배치 — data/premium2/*.json → 복붙 페이지 생성.
무료 스톡 사진만 사용(AI 폴백 없음 = 비용 0), docs/img/{slug}/ 커밋 후 raw URL 참조.
두괄식·네이버 홈판 스타일 기준으로 작성된 글을 렌더링한다.

사용: python scripts/premium2_batch.py [--no-telegram]
"""
import html
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
from auto_blog import config, images as imgmod  # noqa: E402
from auto_blog import telegram_bot as tb  # noqa: E402

SRC = config.DATA_DIR / "premium2"
IMG_ROOT = ROOT / "docs" / "img"
RAW = "https://raw.githubusercontent.com/usualhealth383-cloud/autoblog/main/docs/img/"
PAGES = "https://usualhealth383-cloud.github.io/autoblog/"
MAX_IMAGES = 4

PAGE = """<!doctype html><html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>{title} — 복붙</title>
<style>:root{{--navy:#13294b}}*{{box-sizing:border-box}}body{{margin:0;font-family:-apple-system,'Malgun Gothic',sans-serif;background:#f4f5f7;color:#1f2430;line-height:1.85;padding:16px}}.wrap{{max-width:720px;margin:0 auto}}.bar{{position:sticky;top:0;background:#f4f5f7;padding:10px 0;display:flex;gap:8px;flex-wrap:wrap;border-bottom:1px solid #e3e6ea;z-index:5}}button{{border:0;border-radius:10px;padding:11px 14px;font-size:15px;font-weight:700;cursor:pointer}}.main{{background:var(--navy);color:#fff;flex:1;min-width:170px}}.sub{{background:#fff;color:var(--navy);border:1.5px solid var(--navy)}}.card{{background:#fff;border-radius:14px;padding:22px;margin-top:14px;box-shadow:0 2px 10px rgba(0,0,0,.05)}}h1{{font-size:22px;line-height:1.4;color:var(--navy)}}h2{{font-size:18px;margin:1.5em 0 .4em;color:var(--navy)}}p{{white-space:pre-line;margin:.7em 0}}img{{width:100%;border-radius:12px;display:block;margin:16px 0}}table{{border-collapse:collapse;width:100%;margin:14px 0;font-size:15px}}caption{{font-weight:800;color:var(--navy);text-align:left;margin-bottom:8px;font-size:16px}}th,td{{border:1px solid #dde1e6;padding:9px 12px;text-align:left}}th{{background:#eef2f7;font-weight:700}}.src{{margin-top:20px;padding:14px 18px;background:#f8f9fa;border-radius:10px;font-size:14px}}.src b{{color:var(--navy)}}.tags{{margin-top:14px;color:#2c6;font-weight:600}}.disc{{font-size:13px;color:#8a909c;margin-top:14px}}.hint{{font-size:13px;color:#7a8190}}#toast{{position:fixed;left:50%;bottom:26px;transform:translateX(-50%);background:#1f2430;color:#fff;padding:11px 18px;border-radius:22px;opacity:0;transition:.25s;font-weight:600}}#toast.on{{opacity:1}}</style></head>
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
function copyBody(){{const b=document.getElementById('body');const s=window.getSelection();const r=document.createRange();r.selectNodeContents(b);s.removeAllRanges();s.addRange(r);let ok=false;try{{ok=document.execCommand('copy')}}catch(e){{}}s.removeAllRanges();toast(ok?'글+사진 복사됨! 붙여넣기':'실패 — 직접 드래그')}}
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


def fetch_stock_only(article, slug):
    """무료 스톡만 사용(AI 폴백 없음) → {섹션idx: raw URL}"""
    out = IMG_ROOT / slug
    out.mkdir(parents=True, exist_ok=True)
    secs = article.get("sections", [])
    idxs = [i for i, s in enumerate(secs) if s.get("image_prompt")]
    if len(idxs) > MAX_IMAGES:
        step = len(idxs) / MAX_IMAGES
        idxs = [idxs[int(i * step)] for i in range(MAX_IMAGES)]
    urls = {}
    for i in idxs:
        dest = out / f"sec{i}.jpg"
        try:
            name = imgmod._fetch_stock(imgmod._stock_query(secs[i]["image_prompt"]), dest)
        except Exception as e:
            print(f"    섹션{i} 스톡 실패: {type(e).__name__}")
            name = None
        if name and dest.exists():
            urls[i] = f"{RAW}{slug}/{dest.name}"
            print(f"    섹션{i}: 스톡 ✓")
    return urls


def render(a, urls):
    parts = [f'<h1 id="title">{esc(a["title"])}</h1>']
    tbl = table_html(a.get("table"))
    n = len(a["sections"])
    tbl_at = 1 if n > 2 else 0     # 두괄식: 결론 뒤 두 번째 섹션에 표
    for i, s in enumerate(a["sections"]):
        parts.append(f'<h2>{esc(s["heading"])}</h2>')
        for p in s.get("paragraphs", []):
            parts.append(f'<p>{esc(p)}</p>')
        if i in urls:
            parts.append(f'<img src="{urls[i]}" alt="{esc(s["heading"])}">')
        if i == tbl_at and tbl:
            parts.append(tbl); tbl = ""
    if tbl:
        parts.append(tbl)
    if a.get("sources"):
        lis = "".join(f"<li>{esc(x)}</li>" for x in a["sources"])
        parts.append(f'<div class="src"><b>📚 참고 자료</b><ul style="margin:6px 0 0;padding-left:18px">{lis}</ul></div>')
    if a.get("disclaimer"):
        parts.append(f'<p class="disc">※ {esc(a["disclaimer"])}</p>')
    tagline = " ".join("#" + str(t).replace(" ", "") for t in a.get("tags", []))
    parts.append(f'<p class="tags" id="tags">{esc(tagline)}</p>')
    return PAGE.format(title=esc(a["title"]), body="\n".join(parts))


def chars(a):
    return sum(len(p) for s in a["sections"] for p in s.get("paragraphs", []))


done = []
for jf in sorted(SRC.glob("*.json")):
    try:
        a = json.loads(jf.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"❌ {jf.name} JSON 오류: {e}")
        continue
    slug = a.get("slug") or jf.stem
    print(f"\n=== {slug} | {chars(a)}자 | 섹션 {len(a['sections'])} ===")
    urls = fetch_stock_only(a, slug)
    (ROOT / "docs" / f"{slug}.html").write_text(render(a, urls), encoding="utf-8")
    done.append((a.get("title", slug), slug, chars(a), len(urls), len(a.get("sources", []))))

print(f"\n=== 완료: {len(done)}편 ===")
lines = ["✨ 프리미엄 신규 글 (두괄식·홈판스타일·근거표·무료실사)\n"]
for title, slug, c, ni, ns in done:
    print(f"  {slug}: {c}자, 사진 {ni}, 출처 {ns}")
    lines.append(f"• {title}\n  {c}자 · 사진{ni} · 출처{ns}\n  {PAGES}{slug}.html")
msg = "\n".join(lines)

if "--no-telegram" not in sys.argv and done:
    for cid in tb._load_chats():
        requests.post(f"{tb.API}/sendMessage", data={"chat_id": cid, "text": msg[:4096],
                      "disable_web_page_preview": "true"}, timeout=30)
    print("\n텔레그램 전송 완료")
