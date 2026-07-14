"""프리미엄 드라마 글 — '김부장' 7화 예상(두괄식) + 예고편 단서 분석.
영상 2편(예고편 상세분석) 전면 반영. AI 사진 X. 실사 스틸/포스터 자리 3곳.
"""
import html
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import requests  # noqa: E402
from auto_blog import config, variants  # noqa: E402
from auto_blog import telegram_bot as tb  # noqa: E402
from auto_blog.publishers import threads_upload  # noqa: E402

SLUG = "drama-kimbujang-ep7"
TABLE_AFTER = 8  # '어떤 드라마' 소개 섹션 뒤에 표

ART = {
    "title": "🔥 '김부장' 7화 예상 — 원작 최고 하이라이트 '트럭 납치'가 온다 (예고편 단서 총분석)",
    "tags": ["김부장", "김부장7화", "김부장예고", "김부장예상", "소지섭", "SBS금토드라마", "김부장웹툰",
             "박태준유니버스", "주강찬", "박진철", "남실장", "김부장6화", "드라마예상", "트럭납치"],
    "disclaimer": "본 글은 6화까지의 줄거리, 7화 예고편, 원작 웹툰 설정을 바탕으로 한 '예상'입니다(스포일러 주의). 실제 방송은 예고편 해석·원작과 다르게 각색될 수 있습니다.",
    "sources": ["SBS 「김부장」 7화 예고편·티저·클립", "네이버웹툰 「김부장」(박태준 유니버스)", "나무위키 '김부장' 관련 문서", "언론 보도(편성·회차)"],
    "table": {"caption": "드라마 '김부장' 기본 정보", "headers": ["항목", "내용"], "rows": [
        ["방송", "SBS 금토드라마 (10부작)"],
        ["원작", "네이버웹툰 「김부장」 (박태준 유니버스)"],
        ["주요 인물", "김부장(소지섭)·민지(서수민)·주강찬·박진철·성한수·남실장 등"],
        ["7화 방송", "7월 17일(금) 밤"]]},
    "sections": [
        # ── 두괄식: 7화 예상 먼저 ──
        {"heading": "🔥 결론부터 — 7화, 원작 팬이 기다린 '그 장면'이 옵니다",
         "paragraphs": [
            "먼저 핵심부터 말씀드릴게요. 오는 17일 방송되는 '김부장' 7화에는, 원작 웹툰에서 최고의 하이라이트로 꼽히는 '트럭 납치 신', 그리고 악역 주강찬과 김부장이 처음으로 정면으로 맞붙는 장면이 담길 것으로 보입니다. 원작을 아는 팬이라면 '드디어 그 장면!'이라며 무릎을 칠 대목이죠.",
            "6화 마지막, 김부장이 고위 인사의 목에 가느다란 실을 걸어 제압하며 '민지야, 아빠 왔다'라고 내뱉던 그 서늘한 엔딩. 사실 그건 폭풍의 예고편에 불과했습니다. 공개된 7화 예고편을 프레임 단위로 뜯어보면, 진짜 전쟁은 이제부터거든요.",
            "그래서 오늘은 7화가 어떻게 흘러갈지, 예고편 속 단서와 원작의 흐름을 근거로 하나하나 상세히 예상해 보겠습니다. (스포일러가 포함되어 있으니, 원치 않으시면 여기서 멈춰 주세요.)"]},
        {"heading": "🚗 예상 ① 인질극 그 후 — 딸과의 재회, 그리고 탈출",
         "paragraphs": [
            "7화는 6화의 인질극을 곧바로 이어받을 것으로 보입니다. 안보차관 임도현을 인질로 붙잡아 둔 채, 김부장은 마침내 딸 민지 앞에 섭니다. '아빠 왔으니까 걱정하지 마'—짧지만 이 한마디에 담긴 무게가 상당합니다.",
            "민지는 이미 지난 회차에서, 평범한 아빠인 줄로만 알았던 그가 사실은 전직 요원이었다는 것, 그리고 자신이 위험에 빠지자 봉인돼 있던 본능이 폭발했다는 사실을 알게 됐거든요. 든든함과 미안함이 뒤섞인 복잡한 표정이 예고편에 스쳐 지나갑니다.",
            "하지만 재회의 기쁨은 짧습니다. 요원 정상아가 건물 밖으로 나온 김부장을 막아서며 '딸을 찾았으니 약속대로 자수하라'고 압박할 것으로 보이죠. 문제는 악역 주강찬이 자기 딸을 지키기 위해 민지까지 없애려 한다는 겁니다. 이대로 김부장이 순순히 잡혀 들어가면 민지의 안전은 보장되지 않습니다. 결국 김부장은 동료들과 함께 탈출을 택할 수밖에 없습니다."]},
        {"heading": "🚛 예상 ② 원작 최고의 명장면, '트럭 납치'가 재현된다",
         "paragraphs": [
            "여기서부터가 원작 팬들이 손꼽아 기다린 대목입니다. 탈출하던 김부장 일행의 차량. 갑자기 사이드미러가 박살 나고, 뒤로는 두 대의 차량이 매섭게 따라붙습니다. 그리고 앞을 가로막는 거대한 트럭. 도로 한복판에서 김부장의 차는 그대로 포위당하고 맙니다.",
            "원작 웹툰에서는 뒤에서 대형 트럭이 밀어붙이는 방식이지만, 드라마에서는 지게차 등을 활용해 각색됐을 가능성이 점쳐집니다. 양옆 트럭에서 복면을 쓴 남자들이 쏟아져 나와 일행이 차 밖으로 나오지 못하게 막고, 차량은 통째로 트럭 안으로 실려 납치됩니다.",
            "이 모든 것을 지시한 건 주강찬입니다. 그는 부하 남실장과 통화하며 '마무리까지 내 눈으로 직접 확인하겠다'는 뜻을 내비치죠. 산 채로 잡아와 자기 눈앞에서 처리하겠다는, 서늘하고 치밀한 계획인 셈입니다."]},
        {"heading": "💤 예상 ③ 트럭 안의 사투 — 박진철 vs 남실장",
         "paragraphs": [
            "납치된 트럭 안에는 함정이 기다리고 있습니다. 양쪽에서 뿜어져 나오는 수면 마취 가스. 괴력의 사나이 박진철이 철제 결박을 부수고 빠져나오지만, '잠깐만 자고 있어'라는 대사와 함께 동료 성한수가 먼저 스르르 쓰러지고, 결국 박진철마저 가스에 무너집니다. 그 존재감만큼은 이 짧은 장면에서도 확실히 각인되죠.",
            "원작에서는 이 장면이 곧바로 명승부로 이어집니다. 박진철이 잠든 사이, 성한수가 주강찬의 오른팔 남실장과 맞붙지만 점점 밀리며 목숨이 위태로운 지경까지 몰립니다. 그때 깨어난 박진철이 남실장을 완전히 압도하는데, 남실장이 살기 위해 달리는 트럭에서 뛰어내리려 할 만큼 일방적인 승부였습니다.",
            "수준급 실력자로 통하던 남실장을 이렇게 몰아붙이는 박진철의 액션이, 드라마에서 어떤 그림으로 재현될지가 7화 최대의 볼거리입니다."]},
        {"heading": "💉 예상 ④ 특임국의 결단 — 김부장, '제거 대상'이 되다",
         "paragraphs": [
            "동시에 김부장에게는 원작에서도 손꼽히는 위기가 닥칩니다. 그의 정체가 국가기관 특임국의 골칫거리로 떠오른 것이죠. 작전명 '땅강아지'로 불리던 김부장의 존재가 남북 관계까지 복잡하게 만들자, 특임국은 '차라리 먼저 제거하는 편이 낫다'는 냉정한 결론에 이릅니다.",
            "예고편에는 안대를 쓴 김부장에게 위험천만한 주사가 투여되는 장면이 담겼습니다. 극심한 고통에 몸부림치는 그의 모습은, 앞서 티저에서 포박당했던 박진철·성한수처럼 어딘가에 따로 감금되어 심문당하고 있음을 암시합니다.",
            "다만 희망은 있습니다. 블라인드 틈으로 이 상황을 조용히 지켜보는 누군가가 있거든요. 정상아나 조력자 '세탁소 임씨'처럼, 결정적인 순간 김부장을 구해낼 인물일 가능성이 큽니다."]},
        {"heading": "🥊 예상 ⑤ 클라이맥스 — 주강찬과의 '남자 대 남자'",
         "paragraphs": [
            "그리고 마침내, 김부장과 주강찬이 정면으로 마주합니다. 상의를 벗어 던진 주강찬은 여유로운 표정으로 김부장을 도발하죠. 흥미로운 건 그의 태도입니다. 자식을 위해서라면 물불 가리지 않는 김부장을 보며, 그는 '너도 딸을 찾느라 눈에 보이는 게 없었겠지'라며 오히려 묘한 동질감을 느낍니다.",
            "심지어 남실장마저 꺾은 김부장의 실력을 탐내, '한 달에 1억'을 제시하며 스카우트를 시도하기까지 합니다. 하지만 돌아오는 건 김부장의 싸늘한 분노뿐이죠.",
            "'너나 나나 아직 아빠로서는 한참 부족하니, 그냥 남자 대 남자로 이야기하자.' 김부장의 이 대사와 함께 둘의 맨몸 대결이 불붙습니다. 주먹이 오가지만, 주강찬은 이내 깨닫습니다. 이 남자를 힘으로는 절대 이길 수 없다는 사실을요."]},
        {"heading": "📱 예상 ⑥ 진짜 반전 — '대한민국은 주먹이 다가 아니다'",
         "paragraphs": [
            "궁지에 몰린 주강찬은 마지막 카드를 꺼냅니다. '대한민국은 주먹이 다가 아니다.' 휴대폰에 저장된 유력 인사들의 연락처를 보여주며, 권력과 인맥으로 김부장을 짓밟겠다고 협박하는 겁니다. 흔한 악역의 최후 발악처럼 보이죠.",
            "그런데 바로 그 순간, 원작은 통쾌한 반전을 숨겨 뒀습니다. 김부장이 그 '실세'에게 곧바로 연락해, 주강찬의 회사 '주영건설'의 해체를 의뢰해 버리는 겁니다. 이내 주강찬의 휴대폰이 요란하게 울리기 시작합니다. 회사에 심상찮은 문제가 터지고 있다는 다급한 보고들.",
            "주먹도, 권력도, 인맥도 한순간에 무너진 주강찬에게 남은 건 김부장의 응징뿐입니다. 원작 독자들이 짜릿함을 주체하지 못했던 바로 그 장면이죠. 다만 10부작 드라마인 만큼, 이 카타르시스를 어떤 방식으로 각색해 터뜨릴지는 끝까지 지켜봐야 할 부분입니다."]},
        {"heading": "🔍 예고편 '단서' 총정리 — 이런 것까지 숨어 있었다",
         "paragraphs": [
            "본격적인 예상을 마쳤으니, 예고편 곳곳에 심어진 디테일도 짚어 볼게요. 알고 보면 놓치기 아까운 단서들입니다.",
            "▶ 옷차림의 시점 — 김부장이 검은 티가 아닌 셔츠 차림으로 등장하는 컷은, 인질극과는 다른 시간대의 장면임을 시사합니다. 예고가 여러 시점을 교차 편집했다는 뜻이죠.",
            "▶ 블라인드 너머의 조력자 — 갇힌 김부장을 조용히 지켜보는 정체불명의 인물. 결정적 순간의 구원자일 가능성이 큽니다.",
            "▶ '금이빨'의 정체 — 선글라스를 벗는 금이빨(틀니로 추정되는) 캐릭터가 눈에 띄는데, 앞으로의 전개에서 어떤 역할을 맡을지 눈여겨볼 떡밥입니다.",
            "▶ 마지막 식사 — 오크색 테이블에 정갈하게 놓인 반찬. 김부장이 민지의 증명사진을 꼭 쥔 채, 특임국으로 자진해 향하기 전 마지막 식사를 하는 장면으로 해석됩니다. 아빠의 비장한 각오가 느껴지는 대목이죠."]},
        # ── 두괄식 뒤: 배경(소개·요약) ──
        {"heading": "📺 그런데, '김부장'이 어떤 드라마였죠?",
         "paragraphs": [
            "여기까지 따라오셨다면 이미 푹 빠지셨을 텐데요. 잠깐 기본 정보를 정리하고 가겠습니다. '김부장'은 SBS 금토드라마로, '외모지상주의'로 유명한 박태준 유니버스의 인기 액션 웹툰을 원작으로 합니다.",
            "겉보기엔 평범한 저축은행 부장이지만 사실은 전직 특수요원이었던 아빠 김부장(소지섭)이, 실종된 딸 민지(서수민)를 되찾기 위해 오랫동안 봉인해 둔 본능을 깨우는 '아빠 액션' 드라마이지요. 총 10부작이며, 7화는 오는 17일 금요일 밤에 방송됩니다. (아래 표 참고)"]},
        {"heading": "⚡ 6화까지, 짧게 짚고 갑니다",
         "paragraphs": [
            "딸 민지가 사라진 뒤, 김부장은 평범한 방법으로는 결코 딸을 되찾을 수 없다는 걸 깨닫습니다. 사건의 배후엔 지역 유지의 얼굴을 한 조직폭력배 보스 주강찬이 있었고, 그는 자기 딸의 잘못을 덮기 위해 권력과 조직을 총동원해 김부장 부녀를 벼랑 끝으로 몰았습니다.",
            "김부장은 옛 동료들과 다시 뭉쳐 봉인했던 감각을 하나씩 되살리고, 특임국과의 정면 대치를 뚫고 6화에서 마침내 딸 앞에 섭니다. 그리고 인질극이라는 초강수로 판을 뒤집은 채, 이야기는 숨 가쁘게 7화로 넘어갑니다. 수세에 몰렸던 아빠가 드디어 칼자루를 쥔 순간이지요."]},
        {"heading": "🤍 17일 금요일 밤, 절대 놓치지 마세요",
         "paragraphs": [
            "정리하면 7화에는 '트럭 납치'라는 원작 최고의 하이라이트, 박진철의 압도적인 액션, 그리고 주강찬을 향한 통쾌한 응징까지—한 회에 몰아넣기 아까울 만큼 굵직한 장면들이 대기하고 있습니다. 방대한 원작의 명장면들을 드라마가 어떤 호흡으로 풀어낼지가 관건입니다.",
            "6화의 인질극이 '시작을 알리는 총성'이었다면, 7화는 본격적인 전면전의 서막입니다. 딸을 지키려는 아빠의 반격이 어디까지, 얼마나 매섭게 나아갈지. 오는 17일 금요일 밤, 소지섭의 '김부장'이 보여 줄 다음 한 방을 직접 확인해 보세요. 예고편을 이미 여러 번 돌려 본 분이라면, 이 며칠이 유독 길게 느껴질 겁니다."]},
    ],
}

# 실사 스틸/포스터 자리(3곳) — 섹션 인덱스 기준
IMG_SPOTS = {0: "① 여기에 공식 포스터 (출처: SBS 「김부장」)",
             2: "② 여기에 '트럭 납치' 예고 장면 스틸",
             5: "③ 여기에 김부장 vs 주강찬 대면 스틸"}

PAGE = """<!doctype html><html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>{title} — 복붙</title>
<style>:root{{--navy:#13294b}}*{{box-sizing:border-box}}body{{margin:0;font-family:-apple-system,'Malgun Gothic',sans-serif;background:#f4f5f7;color:#1f2430;line-height:1.9;padding:16px}}.wrap{{max-width:720px;margin:0 auto}}.bar{{position:sticky;top:0;background:#f4f5f7;padding:10px 0;display:flex;gap:8px;flex-wrap:wrap;border-bottom:1px solid #e3e6ea;z-index:5}}button{{border:0;border-radius:10px;padding:11px 14px;font-size:15px;font-weight:700;cursor:pointer}}.main{{background:var(--navy);color:#fff;flex:1;min-width:170px}}.sub{{background:#fff;color:var(--navy);border:1.5px solid var(--navy)}}.card{{background:#fff;border-radius:14px;padding:22px;margin-top:14px;box-shadow:0 2px 10px rgba(0,0,0,.05)}}h1{{font-size:22px;line-height:1.4;color:var(--navy)}}h2{{font-size:18px;margin:1.5em 0 .4em;color:var(--navy)}}p{{white-space:pre-line}}.imgspot{{margin:14px 0;padding:26px;border:2px dashed #c3ccd6;border-radius:12px;text-align:center;color:#8a909c;font-size:14px;background:#fbfcfd}}table{{border-collapse:collapse;width:100%;margin:14px 0;font-size:15px}}caption{{font-weight:800;color:var(--navy);text-align:left;margin-bottom:8px;font-size:16px}}th,td{{border:1px solid #dde1e6;padding:9px 12px;text-align:left}}th{{background:#eef2f7;font-weight:700}}.src{{margin-top:20px;padding:14px 18px;background:#f8f9fa;border-radius:10px;font-size:14px}}.src b{{color:var(--navy)}}.tags{{margin-top:14px;color:#2c6;font-weight:600}}.disc{{font-size:13px;color:#8a909c;margin-top:14px}}.hint{{font-size:13px;color:#7a8190}}#toast{{position:fixed;left:50%;bottom:26px;transform:translateX(-50%);background:#1f2430;color:#fff;padding:11px 18px;border-radius:22px;opacity:0;transition:.25s;font-weight:600}}#toast.on{{opacity:1}}</style></head>
<body><div class="wrap"><div class="bar">
<button class="main" onclick="copyBody()">📋 본문 전체 복사 (글+표+태그)</button>
<button class="sub" onclick="copyTitle()">제목 복사</button>
<button class="sub" onclick="copyTags()">🏷 태그 복사</button></div>
<p class="hint">본문 복사 → 붙여넣기 후, 점선 자리에 <b>공식 포스터·실사 스틸</b>을 직접 넣으세요(출처 표기 권장)</p>
<div class="card"><div id="body">{body}</div></div></div>
<div id="toast"></div><script>
const TITLE=document.getElementById('title').textContent;
const tagsEl=document.getElementById('tags');
const TAGS=tagsEl?tagsEl.textContent.replace(/#/g,' ').replace(/\\s+/g,' ').trim():'';
function toast(m){{const t=document.getElementById('toast');t.textContent=m;t.classList.add('on');setTimeout(()=>t.classList.remove('on'),1600)}}
function copyTitle(){{navigator.clipboard.writeText(TITLE).then(()=>toast('제목 복사됨!')).catch(()=>toast('실패'))}}
function copyTags(){{navigator.clipboard.writeText(TAGS).then(()=>toast('태그 복사됨!(# 없이)')).catch(()=>toast('실패'))}}
function copyBody(){{const b=document.getElementById('body');const s=window.getSelection();const r=document.createRange();r.selectNodeContents(b);s.removeAllRanges();s.addRange(r);let ok=false;try{{ok=document.execCommand('copy')}}catch(e){{}}s.removeAllRanges();toast(ok?'본문 복사됨! 붙여넣기':'실패 — 직접 드래그')}}
</script></body></html>"""


def esc(t):
    return html.escape(str(t))


def table_html(tbl):
    heads = "".join(f"<th>{esc(h)}</th>" for h in tbl.get("headers", []))
    rows = "".join("<tr>" + "".join(f"<td>{esc(c)}</td>" for c in r) + "</tr>" for r in tbl["rows"])
    cap = f"<caption>📊 {esc(tbl.get('caption',''))}</caption>" if tbl.get("caption") else ""
    return f"<table>{cap}<thead><tr>{heads}</tr></thead><tbody>{rows}</tbody></table>"


def render_page(a):
    parts = [f'<h1 id="title">{esc(a["title"])}</h1>']
    tbl = table_html(a["table"])
    for i, s in enumerate(a["sections"]):
        parts.append(f'<h2>{esc(s["heading"])}</h2>')
        for p in s["paragraphs"]:
            parts.append(f'<p>{esc(p)}</p>')
        if i in IMG_SPOTS:
            parts.append(f'<div class="imgspot">🖼 {esc(IMG_SPOTS[i])}</div>')
        if i == TABLE_AFTER and tbl:
            parts.append(tbl); tbl = ""
    lis = "".join(f"<li>{esc(x)}</li>" for x in a["sources"])
    parts.append(f'<div class="src"><b>📚 참고 자료</b><ul style="margin:6px 0 0;padding-left:18px">{lis}</ul></div>')
    parts.append(f'<p class="disc">※ {esc(a["disclaimer"])}</p>')
    tagline = " ".join("#" + str(t).replace(" ", "") for t in a["tags"])
    parts.append(f'<p class="tags" id="tags">{esc(tagline)}</p>')
    return PAGE.format(title=esc(a["title"]), body="\n".join(parts))


chars = sum(len(p) for s in ART["sections"] for p in s["paragraphs"])
print("글자수:", chars, "| 섹션", len(ART["sections"]), "| 이미지 자리", len(IMG_SPOTS))
(ROOT / "docs" / f"{SLUG}.html").write_text(render_page(ART), encoding="utf-8")

th_msg = "건너뜀"
if "--no-threads" not in sys.argv:
    try:
        tv = variants.make_threads(ART)
        text = (tv["text"] + "\n" + " ".join(tv.get("hashtags", []))).strip()
        if text and threads_upload.configured():
            th_msg = threads_upload.post(text)
    except Exception as e:
        th_msg = f"실패: {e}"
print("스레드:", th_msg)

page = f"https://usualhealth383-cloud.github.io/autoblog/{SLUG}.html"
msg = f"🔥 '김부장' 7화 예상 전면 재작성(영상 반영·두괄식) 완료 ({chars}자)\n🟢 복붙: {page}\n🧵 스레드: {th_msg}"
for cid in tb._load_chats():
    requests.post(f"{tb.API}/sendMessage", data={"chat_id": cid, "text": msg[:4096], "disable_web_page_preview": "true"}, timeout=30)
print("완료 ✅", page)
