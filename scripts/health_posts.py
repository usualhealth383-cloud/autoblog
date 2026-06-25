"""건강상식 3편 — 딥리서치 근거 기반(의료 안전). 각 글:
생성(1500~2000자) → 사진 → GitHub 호스팅 → 스레드 자동게시 → 복붙페이지(docs/) → 텔레그램.
Blogger는 현재 한도(403)라 페이지에서 수동/추후 발행.
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

MED_RULE = ("\n[의료 안전 필수] 일반 건강 상식으로만 쓴다. 진단·처방·치료효과 단정 금지. "
            "'~로 알려져 있다/연구에 따르면' 식 표현. 지병 있으면 전문가 상담 권유. disclaimer에 의학 고지문.")

SHAPE = """JSON 형식: {"title":"클릭하고 싶은 제목(이모지 1개,35자내)","meta_description":"120~150자",
"tags":["다양하게 10~13개(핵심+관련+롱테일)"],
"sections":[{"heading":"소제목(이모지)","paragraphs":["문단","문단"],"image_prompt":"섹션 핵심 소재의 구체적 영어 사진묘사(텍스트·로고 없이, 음식·생활·건강 장면)"}],
"disclaimer":"의학 고지문"}"""

TOPICS = [
    {"slug": "water", "title": "하루 물 8잔 신화",
     "grounding": """[딥리서치 사실 — 출처기반, 네 표현으로]
- '하루 8잔(약 2L)' 권고는 모두에게 똑같이 적용되지 않는다. 연령·성별·활동량·날씨·먹는 음식의 수분에 따라 필요량이 다르다.
- '하루 8잔/2L'처럼 규정화하는 건 과학적으로 부적절하다는 연구가 있다(정확한 필요량은 객관적 측정이 사실상 불가).
- 미국 국립의학아카데미(NAM): 하루 총 수분 권장 — 성인 남성 약 3.7L(15.5컵), 여성 약 2.7L(11.5컵). 단 이는 '음식 포함 총량'(음식으로 20%가량 섭취).
- 더 개인 맞춤 기준으로 '체중(kg)×30ml'가 흔히 쓰인다.
- 체내 수분이 1~2%만 부족해도 심한 갈증·피로를 느낀다. 갈증, 소변 색(진한 노란색=부족)으로 체크.
- 과다 주의: 1~2시간 내 너무 많이 마시면 '저나트륨혈증(물 중독)' — 혈중 나트륨이 낮아져 무기력·두통·구역·경련, 심하면 발작·혼수까지. 조금씩 자주가 안전.
- 운동 후엔 벌컥 들이켜기보다 나눠 마시기(땀 많이 나면 나트륨 보충도).
- 커피·차의 카페인은 이뇨작용(커피는 마신 양의 약 2배, 차는 약 1.5배를 소변으로 배출)이라 물을 완전히 대체하긴 어렵다. 수분 보충엔 맹물이 최고.
- 좋은 습관: 기상 직후 한 잔, 식사 사이사이 조금씩, 소변 색을 신호등처럼 체크.
- 결론: 숫자에 집착보다 '목마르면 마시고, 골고루 자주, 한 번에 과하지 않게'가 핵심.""",
     "task": "주제: '하루 물 8잔' 진짜 마셔야 할까? 수분 섭취의 진실과 내게 맞는 양 찾기."},
    {"slug": "sleep", "title": "잠 잘 자는 법",
     "grounding": """[딥리서치 사실 — 출처기반, 네 표현으로]
- 취침 1~2시간 전부터 빛을 줄이고 일정한 루틴을 반복하면 뇌가 '수면 모드'로 전환된다.
- 아침 햇빛 + 낮 활동이 밤의 수면호르몬(멜라토닌) 분비를 돕는 가장 자연스러운 방법.
- 침실은 어둡고 조용하고 시원하게(권장 15~20℃). 규칙적인 취침·기상 시간 유지.
- 스마트폰·태블릿·TV의 블루라이트는 멜라토닌 분비를 억제해 수면 리듬을 깬다.
- 잠들기 2~3시간 전 체온이 떨어져야 멜라토닌이 나오고 쉽게·깊이 잠든다(따뜻한 샤워 후 체온 하강을 활용).
- 자기 전 과도한 카페인·알코올은 피한다(카페인은 불면·잦은 각성·수면질 저하).
- 4-7-8 호흡법(앤드류 웨일 박사): 코로 4초 들이쉬고 → 7초 참고 → 입으로 8초 길게 내쉬기, 4세트. 하루 1~2회 꾸준히 하면 긴장 이완에 도움.
- 미세한 빛도 각성을 부르니 암막커튼·안대로 차단.
- 부족한 잠은 주말에 1~2시간만 늦게 일어나거나 30분 이내 짧은 낮잠으로 보충(낮잠이 길면 밤잠 방해).
- 취침 직전 고강도 운동은 체온·교감신경을 높여 방해 → 운동은 취침 3시간 전까지.
- 자다 깼을 땐 시계·폰으로 시간 확인 금지. 15분 지나도 안 오면 침대 밖에서 독서·가벼운 스트레칭 후 돌아오기.
- 결론: 빛·체온·루틴·카페인 4가지 + 호흡법만 관리해도 꿀잠에 가까워진다.""",
     "task": "주제: 잠 안 올 때 진짜 효과 있는 방법. 약 없이 꿀잠 자는 과학적 습관."},
    {"slug": "egg", "title": "계란 하루 몇 개",
     "grounding": """[딥리서치 사실 — 출처기반, 네 표현으로]
- 미국심장협회(AHA): 건강한 일반 성인은 하루 달걀 1개(주 7개) 또는 흰자 2개까지 무리 없다. 일부 연구는 하루 2개까지도 무방.
- 심장질환·고콜레스테롤·당뇨가 있으면 노른자 주 4개 이하로 제한 권고.
- 최신 핵심: 달걀 섭취를 볼 때 전문가가 더 주목하는 건 '콜레스테롤'이 아니라 '포화지방'이다.
- 호주 사우스오스트레일리아대 연구: 하루 달걀 2개라도 나머지 식단의 포화지방을 낮게 유지하면 오히려 나쁜 콜레스테롤(LDL)이 하락했다.
- 삶은 달걀 1개 = 포화지방 약 1.6g. 하루 포화지방 권장은 약 20~22g 이하.
- 계란은 '완전 단백질' — 1개로 필수 아미노산 전부 + 13가지 필수 비타민·미네랄. 저칼로리·포만감으로 다이어트에도 유용.
- 노른자엔 콜린(1개 약 215mg, 두뇌·기억력), 루테인·지아잔틴(눈 건강), 엽산(태아 신경발달)이 풍부 → 흰자만 먹기보다 노른자까지 골고루가 영양밀도↑.
- 조리법: 기름 많이 쓰는 프라이보다 삶기·수란이 포화지방을 덜 더한다(반숙·완숙은 취향).
- 결론: 핵심은 '개수'보다 전체 식단(포화지방)과 개인 건강 상태. 골고루·적당히가 답.""",
     "task": "주제: 계란 하루 몇 개까지 괜찮을까? 콜레스테롤의 오해와 진실."},
]


def _count(a):
    return sum(len(p) for s in a.get("sections", []) for p in s.get("paragraphs", []))


def gen_target(task, grounding, lo=1500, hi=2100, tries=4):
    base = task + MED_RULE + "\n" + grounding + "\n" + SHAPE
    r = client.chat.completions.create(
        model=MODEL, response_format={"type": "json_object"}, temperature=0.75, max_tokens=6000,
        messages=[{"role": "system", "content": writer.SYSTEM}, {"role": "user", "content": base}])
    a = json.loads(r.choices[0].message.content)
    for _ in range(tries):
        c = _count(a)
        if c >= lo:
            break
        r = client.chat.completions.create(
            model=MODEL, response_format={"type": "json_object"}, temperature=0.6, max_tokens=6000,
            messages=[{"role": "system", "content": writer.SYSTEM}, {"role": "user", "content":
                      f"아래 JSON 글을 더 알차게 확장하라(같은 형식, 사실 유지, 거짓 추가 금지). 전체 문단 "
                      f"글자수 합계 공백포함 {lo}~{hi}자로." + MED_RULE + "\n" + grounding + "\n" + SHAPE
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


docs = ROOT / "docs"
report = []
for t in TOPICS:
    print(f"\n=== {t['title']} ===")
    art = gen_target(t["task"], t["grounding"])
    art["keyword"] = t["title"]
    art["category"] = "medical"
    print("  제목:", art["title"], "|", _count(art), "자")
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    out_dir = config.DATA_DIR / "posts" / f"{stamp}-health-{t['slug']}"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "blog.json").write_text(json.dumps(art, ensure_ascii=False, indent=2), encoding="utf-8")
    imgs, thumb = imgmod.generate_for_article(art, out_dir, max_images=3)
    rec = {"article": art, "images": imgs, "dir": out_dir.name}
    rec["image_urls"] = dp._host_images_on_github(rec, out_dir)
    print("  이미지:", len(rec["image_urls"]), "장")
    # 복붙 페이지
    page_path = docs / f"health-{t['slug']}.html"
    page_path.write_text(render_page(art, rec["image_urls"]), encoding="utf-8")
    # 스레드
    th_msg = "건너뜀"
    if "--no-threads" in sys.argv:
        th_msg = "건너뜀(이미 게시됨)"
    else:
        try:
            tv = variants.make_threads(art)
            text = (tv["text"] + "\n" + " ".join(tv.get("hashtags", []))).strip()
            thumb_url = rec["image_urls"].get("0") or (next(iter(rec["image_urls"].values())) if rec["image_urls"] else None)
            if text and threads_upload.configured():
                th_msg = threads_upload.post(text, thumb_url)
        except Exception as e:
            th_msg = f"실패: {e}"
    print("  스레드:", th_msg)
    report.append({"title": art["title"], "slug": t["slug"], "threads": th_msg, "chars": _count(art)})

print("\n=== 텔레그램 보고 ===")
lines = ["💊 건강상식 3편 완료 (스레드 자동게시 + 복붙페이지)\n"]
for r in report:
    lines.append(f"• {r['title']} ({r['chars']}자)")
    lines.append(f"  🟢 https://usualhealth383-cloud.github.io/autoblog/health-{r['slug']}.html")
    lines.append(f"  🧵 {r['threads']}")
lines.append("\n📝 Blogger는 한도 풀리면 같은 글로 발행하세요.")
msg = "\n".join(lines)
for cid in tb._load_chats():
    requests.post(f"{tb.API}/sendMessage", data={"chat_id": cid, "text": msg[:4096],
                  "disable_web_page_preview": "true"}, timeout=30)
print("완료 ✅")
print(msg)
