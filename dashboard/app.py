"""7단계: 승인 대시보드 (로컬 팝업 웹앱).

매일 아침 자동으로 브라우저가 열리고, 오늘의 주제 후보를 보여준다.
주제 선택(또는 직접 입력) → 본문·이미지 생성 → 미리보기 → 승인 시 발행.
승인 전에는 절대 발행하지 않는다.

실행:  python dashboard/app.py     (자동으로 브라우저가 열림)
"""
from __future__ import annotations

import json
import sys
import threading
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from flask import (Flask, abort, redirect, render_template_string,  # noqa: E402
                   request, send_from_directory, url_for)

from auto_blog import config, pipeline, strategist  # noqa: E402
from auto_blog import publishers  # noqa: E402

app = Flask(__name__)
POSTS = config.DATA_DIR / "posts"
POSTS.mkdir(parents=True, exist_ok=True)

_proposal: dict | None = None  # 오늘의 후보 캐시

CSS = """
body{font-family:-apple-system,'Segoe UI','Malgun Gothic',sans-serif;background:#f8f9fa;
margin:0;color:#212529}
.wrap{max-width:860px;margin:0 auto;padding:28px 20px 80px}
h1{font-size:26px;margin:0 0 4px}.sub{color:#868e96;font-size:14px;margin:0 0 24px}
.card{background:#fff;border:1px solid #e9ecef;border-radius:14px;padding:18px 20px;margin:0 0 14px}
.cat{display:inline-block;font-size:12px;padding:2px 10px;border-radius:10px;margin-left:8px}
.finance{background:#e6fcf5;color:#0ca678}.medical{background:#fff0f6;color:#e64980}
.entertainment{background:#f3f0ff;color:#7048e8}.general{background:#e7f5ff;color:#1971c2}
.risky{background:#fff5f5;color:#e03131}
.angle{font-size:18px;font-weight:700;margin:6px 0}
.meta{color:#868e96;font-size:13px}
.btn{display:inline-block;background:#1971c2;color:#fff;border:none;padding:9px 18px;
border-radius:9px;font-size:14px;cursor:pointer;text-decoration:none}
.btn:hover{background:#1864ab}.btn.gray{background:#868e96}.btn.green{background:#0ca678}
.btn.red{background:#e03131}.btn.ghost{background:#fff;color:#1971c2;border:1px solid #1971c2}
.row{display:flex;gap:10px;align-items:center;flex-wrap:wrap}
input,select,textarea{font-size:14px;padding:8px 10px;border:1px solid #ced4da;border-radius:8px;font-family:inherit}
.score{font-weight:800;color:#1971c2;font-size:15px}
iframe{width:100%;height:70vh;border:1px solid #e9ecef;border-radius:12px;background:#fff}
.result{background:#fff;border-radius:10px;padding:12px 16px;margin-top:8px;font-size:14px;line-height:1.8}
"""

PAGE = """<!doctype html><html lang=ko><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1">
<title>오토블로그 승인</title><style>{{css|safe}}</style></head>
<body><div class=wrap>{{body|safe}}</div></body></html>"""


def page(body: str):
    return render_template_string(PAGE, css=CSS, body=body)


def load_posts():
    items = []
    for d in sorted(POSTS.iterdir(), reverse=True):
        f = d / "article.json"
        if f.exists():
            try:
                rec = json.loads(f.read_text(encoding="utf-8"))
                rec["_dir"] = d.name
                items.append(rec)
            except json.JSONDecodeError:
                pass
    return items


@app.route("/")
def home():
    global _proposal
    if _proposal is None:
        _proposal = pipeline.propose()

    cands = _proposal["candidates"]
    cand_html = []
    for i, c in enumerate(cands):
        risky = c["category"] == "risky"
        cand_html.append(f"""
        <div class=card>
          <div class=row>
            <span class=score>{c['score']}</span>
            <span class="cat {c['category']}">{c['category']}</span>
            <span class=meta>키워드: {c['keyword']} · 검색량 {c.get('traffic') or '-'}</span>
          </div>
          <div class=angle>{c['angle']}</div>
          <div class=meta>{c.get('context','')}</div>
          <form method=post action="/generate" style="margin-top:10px">
            <input type=hidden name=idx value="{i}">
            <button class="btn {'gray' if risky else ''}">이 주제로 글 생성</button>
            {'<span class=meta style="margin-left:8px">⚠ 광고 부적합 위험</span>' if risky else ''}
          </form>
        </div>""")

    # 직접 입력 폼
    custom = """
    <div class=card>
      <div class=angle>✍ 직접 주제 입력</div>
      <form method=post action="/generate">
        <div class=row style="margin-top:8px">
          <input name=keyword placeholder="키워드 (예: ISA 계좌)" style="flex:1">
          <select name=category>
            <option value=finance>금융</option><option value=medical>의학</option>
            <option value=general selected>일반</option>
          </select>
        </div>
        <input name=angle placeholder="제목/각도 (비우면 키워드로 자동)" style="width:100%;margin-top:8px;box-sizing:border-box">
        <button class="btn ghost" style="margin-top:10px">이 주제로 글 생성</button>
      </form>
    </div>"""

    # 생성된 글 목록
    posts = load_posts()
    post_html = []
    for p in posts[:10]:
        st = p.get("status", "")
        color = {"published": "green", "rejected": "red"}.get(st, "")
        post_html.append(f"""
        <div class=card><div class=row>
          <a class="btn ghost" href="/post/{p['_dir']}">{p['article'].get('title','(제목)')}</a>
          <span class="btn {color}" style="cursor:default;pointer-events:none">{st}</span>
        </div></div>""")

    body = f"""
    <h1>📅 오늘의 글감 <a class="btn gray" href="/refresh" style="float:right">새로고침</a></h1>
    <p class=sub>수집 시각: {_proposal.get('collected_at','')[:19].replace('T',' ')} · 점수 높은 순 (금융/의학 가중, 정치·사건 자동 제외)</p>
    {''.join(cand_html)}
    {custom}
    <h1 style="margin-top:36px">📝 생성된 글</h1>
    {''.join(post_html) or '<p class=sub>아직 없음</p>'}
    """
    return page(body)


@app.route("/refresh")
def refresh():
    global _proposal
    _proposal = pipeline.propose()
    return redirect(url_for("home"))


@app.route("/generate", methods=["POST"])
def generate():
    if request.form.get("idx") is not None and _proposal:
        c = _proposal["candidates"][int(request.form["idx"])]
        topic = strategist.TopicCandidate.from_dict(c)
        ground = True  # 트렌드 주제 → 뉴스 근거 + 사실검증
    else:  # 직접 입력(개념·상식 글)
        kw = (request.form.get("keyword") or "").strip()
        if not kw:
            return redirect(url_for("home"))
        cat = request.form.get("category", "general")
        angle = (request.form.get("angle") or "").strip() or f"{kw}, 꼭 알아야 할 핵심 정리"
        topic = strategist.TopicCandidate(
            keyword=kw, category=cat, angle=angle, score=0,
            needs_medical_disclaimer=(cat == "medical"))
        ground = False  # 개념글 → 모델의 안정적 지식 사용
    rec = pipeline.generate_for_topic(
        topic, max_images=int(config.get("DASHBOARD_IMAGES", "2")), ground=ground)
    return redirect(url_for("post_view", d=rec["dir"]))


@app.route("/post/<d>")
def post_view(d):
    pdir = POSTS / d
    if not (pdir / "article.json").exists():
        abort(404)
    rec = json.loads((pdir / "article.json").read_text(encoding="utf-8"))
    st = rec.get("status", "")
    results = rec.get("publish_results")
    res_html = ""
    if results:
        rows = "<br>".join(f"<b>{k}</b>: {v}" for k, v in results.items())
        res_html = f"<div class=result>{rows}</div>"
    actions = ""
    if st == "pending_approval":
        actions = f"""
        <form method=post action="/post/{d}/approve" style="display:inline"
              onsubmit="this.querySelector('button').innerText='게시 중…';this.querySelector('button').disabled=true">
          <button class="btn green">✅ 확인 — 블로그에 게시</button></form>
        <form method=post action="/post/{d}/reject" style="display:inline;margin-left:8px">
          <button class="btn red">✕ 반려</button></form>"""
    body = f"""
    <a href="/" class="btn ghost">← 목록</a>
    <h1 style="margin-top:14px">{rec['article'].get('title','')}</h1>
    <p class=sub>상태: {st} · 본문 {rec['article'].get('char_count','?')}자</p>
    <div class=row style="margin-bottom:12px">{actions}</div>
    {res_html}
    <iframe src="/preview/{d}/preview.html"></iframe>
    """
    return page(body)


@app.route("/preview/<d>/<path:fname>")
def preview_file(d, fname):
    return send_from_directory(POSTS / d, fname)


@app.route("/post/<d>/approve", methods=["POST"])
def approve(d):
    pdir = POSTS / d
    rec = json.loads((pdir / "article.json").read_text(encoding="utf-8"))
    results = publishers.publish(rec, pdir)
    rec["status"] = "published"
    rec["publish_results"] = results
    (pdir / "article.json").write_text(json.dumps(rec, ensure_ascii=False, indent=2),
                                       encoding="utf-8")
    return redirect(url_for("post_view", d=d))


@app.route("/post/<d>/reject", methods=["POST"])
def reject(d):
    pdir = POSTS / d
    rec = json.loads((pdir / "article.json").read_text(encoding="utf-8"))
    rec["status"] = "rejected"
    (pdir / "article.json").write_text(json.dumps(rec, ensure_ascii=False, indent=2),
                                       encoding="utf-8")
    return redirect(url_for("post_view", d=d))


def _open_browser(port: int, path: str = "/"):
    """가능하면 Chrome 앱 창(주소창 없는 깔끔한 창)으로, 없으면 기본 브라우저로 연다."""
    import os
    import subprocess
    url = f"http://127.0.0.1:{port}{path}"
    chrome_paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
    ]
    for p in chrome_paths:
        if os.path.exists(p):
            subprocess.Popen([p, f"--app={url}", "--new-window", "--window-size=860,1000"])
            return
    webbrowser.open(url)


if __name__ == "__main__":
    port = int(config.get("DASHBOARD_PORT", "8780"))
    if "--no-open" not in sys.argv:
        threading.Timer(1.2, _open_browser, args=(port,)).start()
    app.run(host="127.0.0.1", port=port, debug=False)
