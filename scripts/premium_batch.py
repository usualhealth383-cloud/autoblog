"""프리미엄 건강글 배치 페이지 생성 — data/premium/*.json(에이전트 산출)을 읽어
각 글에 사진 붙이고, 표·출처·고지문 포함 복붙 페이지(docs/health-{slug}.html) 생성.
"""
import base64 as _b64
import html
import json
import os as _os
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

SRC = config.DATA_DIR / "premium"
MAX_IMAGES = 5

PAGE = """<!doctype html><html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>{title} — 복붙</title>
<style>:root{{--navy:#13294b}}*{{box-sizing:border-box}}body{{margin:0;font-family:-apple-system,'Malgun Gothic',sans-serif;background:#f4f5f7;color:#1f2430;line-height:1.85;padding:16px}}.wrap{{max-width:720px;margin:0 auto}}.bar{{position:sticky;top:0;background:#f4f5f7;padding:10px 0;display:flex;gap:8px;flex-wrap:wrap;border-bottom:1px solid #e3e6ea;z-index:5}}button{{border:0;border-radius:10px;padding:11px 14px;font-size:15px;font-weight:700;cursor:pointer}}.main{{background:var(--navy);color:#fff;flex:1;min-width:170px}}.sub{{background:#fff;color:var(--navy);border:1.5px solid var(--navy)}}.card{{background:#fff;border-radius:14px;padding:22px;margin-top:14px;box-shadow:0 2px 10px rgba(0,0,0,.05)}}h1{{font-size:22px;line-height:1.4;color:var(--navy)}}h2{{font-size:18px;margin:1.5em 0 .4em;color:var(--navy)}}p{{white-space:pre-line}}img{{width:100%;border-radius:12px;margin:14px 0;display:block}}table{{border-collapse:collapse;width:100%;margin:14px 0;font-size:15px}}caption{{font-weight:800;color:var(--navy);text-align:left;margin-bottom:8px;font-size:16px}}th,td{{border:1px solid #dde1e6;padding:9px 12px;text-align:left}}th{{background:#eef2f7;font-weight:700}}.src{{margin-top:20px;padding:14px 18px;background:#f8f9fa;border-radius:10px;font-size:14px}}.src b{{color:var(--navy)}}.tags{{margin-top:14px;color:#2c6;font-weight:600}}.disc{{font-size:13px;color:#8a909c;margin-top:14px}}.hint{{font-size:13px;color:#7a8190}}#toast{{position:fixed;left:50%;bottom:26px;transform:translateX(-50%);background:#1f2430;color:#fff;padding:11px 18px;border-radius:22px;opacity:0;transition:.25s;font-weight:600}}#toast.on{{opacity:1}}</style></head>
<body><div class="wrap"><div class="bar">
<button class="main" onclick="copyBody()">📋 본문 전체 복사 (글+사진+표+태그)</button>
<button class="sub" onclick="copyTitle()">제목 복사</button>
<button class="sub" onclick="copyTags()">🏷 태그 복사</button></div>
<p class="hint">제목 복사 → 제목칸 · 본문 전체 복사 → 본문(사진·표·출처 같이) · Blogger/네이버에 붙여넣기</p>
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


def table_html(tb):
    if not tb or not tb.get("rows"):
        return ""
    heads = "".join(f"<th>{esc(h)}</th>" for h in tb.get("headers", []))
    rows = "".join("<tr>" + "".join(f"<td>{esc(c)}</td>" for c in r) + "</tr>" for r in tb["rows"])
    cap = f"<caption>📊 {esc(tb.get('caption',''))}</caption>" if tb.get("caption") else ""
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
        body = {"message": f"img {path}", "branch": "main",
                "content": _b64.b64encode(src.read_bytes()).decode()}
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
        for p in s.get("paragraphs", []):
            parts.append(f'<p>{esc(p)}</p>')
        url = image_urls.get(str(i)) or image_urls.get(i)
        if url:
            parts.append(f'<img src="{url}" alt="">')
        if i == 1 and tbl:   # 표는 두 번째 소제목 뒤에 배치
            parts.append(tbl); tbl = ""
    if tbl:
        parts.append(tbl)
    parts.append(sources_html(a.get("sources")))
    if a.get("disclaimer"):
        parts.append(f'<p class="disc">※ {esc(a["disclaimer"])}</p>')
    tagline = " ".join("#" + str(t).replace(" ", "") for t in a.get("tags", []))
    parts.append(f'<p class="tags" id="tags">{esc(tagline)}</p>')
    return PAGE.format(title=esc(a["title"]), body="\n".join(parts))


def chars(a):
    return sum(len(p) for s in a["sections"] for p in s.get("paragraphs", []))


done = []
for jf in sorted(SRC.glob("*.json")):
    a = json.loads(jf.read_text(encoding="utf-8"))
    slug = a.get("slug") or jf.stem
    print(f"\n=== {slug} | {a.get('title','')} | {chars(a)}자 ===")
    out_dir = config.DATA_DIR / "posts" / f"premium-{slug}"
    out_dir.mkdir(parents=True, exist_ok=True)
    imgs, _ = imgmod.generate_for_article(a, out_dir, max_images=MAX_IMAGES)
    urls = host_upsert(imgs, out_dir.name, out_dir)
    print("  사진:", len(urls))
    (ROOT / "docs" / f"health-{slug}.html").write_text(render_page(a, urls), encoding="utf-8")
    done.append((a.get("title", slug), slug, chars(a)))

print("\n=== 완료 ===")
lines = ["💊 프리미엄 건강글 페이지 생성 완료\n"]
for title, slug, c in done:
    lines.append(f"• {title} ({c}자)")
    lines.append(f"  https://usualhealth383-cloud.github.io/autoblog/health-{slug}.html")
msg = "\n".join(lines)
for cid in tb._load_chats():
    requests.post(f"{tb.API}/sendMessage", data={"chat_id": cid, "text": msg[:4096],
                  "disable_web_page_preview": "true"}, timeout=30)
print(msg)
