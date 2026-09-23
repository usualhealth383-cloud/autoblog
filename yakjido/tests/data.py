#!/usr/bin/env python3
"""약지도 자료 무결성 — 브라우저 없이 1초. 끊긴 고리를 잡는다.
  · 증상 계획(plan)의 options/pick → 약 id 가 실제로 있는가 (lex:… 는 사전 항목이라 제외)
  · sources 키 → sources.json 에 있는가 (증상·약·계열·영양제·병용 규칙)
  · 계열 members → 약 id, 약의 class → 계열 id
  · 팁 link → 존재하는 화면인가
  · 병용 규칙 organ 아이콘 이름 → app-shell 의 I.* 에 있는가
"""
import json, glob, pathlib, re, sys
ROOT = pathlib.Path(__file__).resolve().parents[1]
C = ROOT / 'content'
def load(pat):
    out = []
    for f in sorted(glob.glob(str(C / pat))): out += json.load(open(f, encoding='utf-8'))
    return out
S, D, K, T = load('symptoms*.json'), load('drugs*.json'), load('classes*.json'), load('tips*.json')
SUP = json.load(open(C / 'supplements.json', encoding='utf-8'))
SRC = {}
for f in sorted(glob.glob(str(C / 'sources*.json'))): SRC.update(json.load(open(f, encoding='utf-8')))   # 빌드와 같이 part 파일을 합친다
IX = json.load(open(C / 'interactions.json', encoding='utf-8'))
ING = json.load(open(C / 'ingredients.json', encoding='utf-8'))
shell = (ROOT / 'app-shell.html').read_text(encoding='utf-8')
icons = set(re.findall(r"\bI\.(\w+)\s*=", shell)) | set(re.findall(r"^\s*(\w+):\s*'<svg", shell, re.M))
sid, did, kid, supid = {s['id'] for s in S}, {d['id'] for d in D}, {k['id'] for k in K}, {x['id'] for x in SUP}
quick = {f"{g['id']}" for g in ING.get('quick', [])} | {s['id'] for g in ING.get('quick', []) for s in g.get('subs', [])}
fails = []
def src_ok(owner, ids):
    for x in ids or []:
        if x not in SRC: fails.append(f'출처 없음 {owner} → {x}')
for s in S:
    for p in s.get('plan', []):
        for o in (p.get('options') or []) + ([p['pick']] if p.get('pick') else []):
            if o and not o.startswith('lex:') and o not in did: fails.append(f'증상 {s["id"]} 계획 약 없음 → {o}')
    src_ok('증상 ' + s['id'], s.get('sources'))
    if not s.get('care', {}).get('er'): fails.append(f'증상 {s["id"]} 응급 신호 없음')
for d in D:
    if d.get('class') not in kid: fails.append(f'약 {d["id"]} 계열 없음 → {d.get("class")}')
    for c in d.get('contains') or []:
        if c not in did: fails.append(f'약 {d["id"]} contains 없음 → {c}')
    src_ok('약 ' + d['id'], d.get('sources'))
for k in K:
    for m in k.get('members') or []:
        if m not in did: fails.append(f'계열 {k["id"]} member 없음 → {m}')
    src_ok('계열 ' + k['id'], k.get('sources'))
for x in SUP: src_ok('영양제 ' + x['id'], x.get('sources'))
for r in IX['rules']:
    src_ok('규칙 ' + r['id'], r.get('src'))
    if not r.get('organ') or r['organ']['ico'] not in icons: fails.append(f'규칙 {r["id"]} 장기 아이콘 없음 → {r.get("organ")}')
    if not re.search(r'\*\*', r.get('why', '') + r.get('do', '')): pass
def route_ok(link):
    m = re.match(r'^/(symptom|drug|class|supp|kinds|tips|me|schedule|pill|photo|together|bag|kids|mix|about|drugs|hello|senior|rxout)(?:/([^?]+))?', link or '')
    if not m: return False
    kind, x = m.group(1), m.group(2)
    if kind == 'symptom': return x in sid
    if kind == 'drug': return x in did
    if kind == 'class': return x in kid
    if kind == 'supp': return x is None or x in supid
    if kind == 'kinds': return x is None or x in quick
    return True
for t in T:
    if t.get('link') and not route_ok(t['link']): fails.append(f'팁 {t["id"]} 링크 없음 → {t["link"]}')
    if not t.get('link'): fails.append(f'팁 {t["id"]} 링크 비어 있음(갈 곳을 달아 주세요)')
# 처방약 대체는 «약국에서 살 수 있는 약»만 — 자기 자신이나 다른 처방약이 들어가면 화면이 거짓말을 한다
byid = {d['id']: d for d in D}
for d in D:
    a = d.get('otcAlt') or {}
    for o in (a.get('options') or []):
        t = byid.get(o)
        if o == d['id']: fails.append(f'대체 약 {d["id"]}: 자기 자신을 대체로 넣었습니다')
        elif not t: fails.append(f'대체 약 {d["id"]}: 없는 약 → {o}')
        elif t.get('rx') == '전문': fails.append(f'대체 약 {d["id"]}: 전문의약품을 대체로 넣었습니다 → {o}')
    if a.get('has') and not (a.get('options') or a.get('text')): fails.append(f'대체 약 {d["id"]}: 있다고만 하고 무엇인지 비어 있습니다')
    if d.get('rx') == '전문' and not d.get('otcAlt'): fails.append(f'처방약 {d["id"]}: otcAlt 가 없습니다(약국에 없으면 has:false 로 적어 주세요)')

# 팁에는 갈래(group)가 있어야 «알아두면 좋은 것» 화면에서 제자리에 들어간다
TIPG = {'약 이름과 고르기', '제대로 드시는 법', '조심할 것', '열·감기·배탈일 때', '보관하고 버리기', '병원·헌혈 가실 때'}
for t in T:
    if t.get('group') not in TIPG: fails.append(f'팁 {t["id"]} 갈래가 비었거나 모르는 이름 → {t.get("group")!r}')

# 「검수 대기」 화면은 검수 요청 문서에 반드시 적혀 있어야 한다 — 문서가 자료와 어긋나 14개로 남아 있었다
import pathlib as _pl
_doc = _pl.Path(__file__).resolve().parents[1] / '검수-대기.md'
if _doc.exists():
    _t = _doc.read_text(encoding='utf-8')
    for _s in S:
        if _s.get('reviewed') is False and f"`{_s['id']}`" not in _t:
            fails.append(f'검수 대기 {_s["id"]} 가 검수-대기.md 에 없습니다')
    for _d in D:
        if _d.get('reviewed') is False and f"`{_d['id']}`" not in _t:
            fails.append(f'검수 대기 약 {_d["id"]} 가 검수-대기.md 에 없습니다')
else:
    fails.append('검수-대기.md 가 없습니다')

# 통계 약어가 어르신 화면에 그대로 나오면 안 된다 — 영양제 「어디까지 입증됐나」(evidenceNote)와 출처 문구만 예외
JARGON = re.compile(r'\b(NNT|NNH|RR|HR|OR|SMD|CI|P\s*[=<]|I²|RCT|n=)\b')
def jargon(o, path, owner):
    if isinstance(o, str):
        if JARGON.search(o) and '.evidenceNote' not in path and 'srcText' not in path and 'sources' not in path and 'note' not in path.split('.')[-1]:
            fails.append(f'통계 약어 {owner}{path}: {o[:60]!r}')
    elif isinstance(o, dict):
        for k, v in o.items(): jargon(v, path + '.' + k, owner)
    elif isinstance(o, list):
        for i, v in enumerate(o): jargon(v, path + f'[{i}]', owner)
for s in S: jargon(s, '', '증상 ' + s['id'])
for d in D: jargon({k: v for k, v in d.items() if k != 'riskNote'}, '', '약 ' + d['id'])
for k in K: jargon(k, '', '계열 ' + k['id'])
for x in SUP: jargon(x, '', '영양제 ' + x['id'])
for t in T: jargon(t, '', '팁 ' + t['id'])
# 「쉬운 말 한 줄」과 「용법」의 하루 횟수가 어긋나면 안 된다.
# 신신플렉스가 한쪽엔 «하루 3번», 허가 용법엔 «1일 2회»로 적혀 있었다 — 어르신이 읽는 쪽이 1.5배였다.
_NUM = {'한': 1, '두': 2, '세': 3, '네': 4, '다섯': 5, '여섯': 6}
def _times(t):
    if not t: return None
    t = str(t).replace('1일', '하루')
    for pat in (r'하루\s*([0-9]+)\s*~\s*([0-9]+)\s*[회번]', r'하루\s*([0-9]+)\s*[회번]', r'하루\s*(한|두|세|네|다섯|여섯)\s*[회번]'):
        m = re.search(pat, t)
        if m:
            g = [int(_NUM.get(x, x)) for x in m.groups() if x]
            return (min(g), max(g))
    return None
for d in D:
    a = _times(d.get('simple')); b = _times((d.get('dose') or {}).get('interval')) or _times((d.get('dose') or {}).get('adult'))
    if a and b and not (a[0] <= b[1] and b[0] <= a[1]):
        fails.append(f'약 {d["id"]} 하루 횟수가 어긋남 — 쉬운 말 {a} · 용법 {b}')

# 어르신이 못 읽는 한자말이 다시 들어오면 멈춘다(출처 문구는 예외).
# 한 번 풀어 놓아도 새 내용을 쓸 때 습관처럼 되돌아오는 말들이다.
HARDWORD = {'부종': '붓기', '공복': '빈속', '병용': '같이 드시는', '호전': '좋아지는 것',
            '오심': '메스꺼움', '발적': '붉어짐', '장기 복용': '오래 드시는 것', '장기간': '오랫동안'}
def hardword(o, path, owner):
    if isinstance(o, str):
        if 'src' in path or 'source' in path: return
        for w, alt in HARDWORD.items():
            if w in o: fails.append(f'어려운 말 «{w}»(→{alt}) {owner}{path}: {o[:50]!r}')
    elif isinstance(o, dict):
        for k, v in o.items(): hardword(v, path + '.' + k, owner)
    elif isinstance(o, list):
        for i, v in enumerate(o): hardword(v, path + f'[{i}]', owner)
for s in S: hardword(s, '', '증상 ' + s['id'])
for d in D: hardword(d, '', '약 ' + d['id'])
for k in K: hardword(k, '', '계열 ' + k['id'])
for x in SUP: hardword(x, '', '영양제 ' + x['id'])
for t in T: hardword(t, '', '팁 ' + t['id'])
for r in IX['rules']: hardword({k: v for k, v in r.items() if k != 'src'}, '', '규칙 ' + r['id'])

# 약 122개 전부에 부작용이 적혀 있어야 한다 — 처방약 6개가 비어 있었다
for d in D:
    if not d.get('sideEffects'): fails.append(f'약 {d["id"]} 에 부작용이 비어 있습니다')
    if not d.get('children') and not (d.get('dose') or {}).get('child'):
        fails.append(f'약 {d["id"]} 에 소아 기준이 비어 있습니다')

# 「내 정보」 조건 이름은 정해진 13가지뿐이다. 없는 이름을 쓰면 그 주의는 «영원히 안 뜬다».
# 실제로 달걀 알레르기에 없는 이름(allergy)을 쓴 곳이 있었다.
VALID_FLAG = {'pregnant', 'ulcer', 'heart', 'anticoag', 'kidney', 'liver', 'alcohol',
              'asthma', 'glaucoma', 'bph', 'gout', 'diabetes', 'senior', 'child'}
for d in D:
    for a in (d.get('avoid') or []) + (d.get('caution') or []):
        if not isinstance(a, dict): continue
        for fl in (a.get('flags') or []):
            if fl not in VALID_FLAG:
                fails.append(f'약 {d["id"]} 에 없는 조건 이름 «{fl}» — 이 주의는 화면에 뜨지 않습니다')

# ── 「그런 줄 알았는데」 — 출처 없이는 한 꼭지도 실을 수 없다 ────────────────
# 흔히 듣는 말을 뒤집는 화면이라, 근거가 없으면 그냥 다른 소문이 된다.
_MY = json.load(open(C / 'myths.json', encoding='utf-8')) if (C / 'myths.json').exists() else []
_ROUTES = {'home','drugs','tips','me','together','kinds','pill','supp','kids','mix','photo',
           'schedule','about','bag','rxout','senior','myths','symptom','drug','class','guide','hello'}
for _m in _MY:
    if not _m.get('src'): fails.append(f'그런줄 {_m["id"]} 에 출처가 없습니다')
    src_ok('그런줄 ' + _m['id'], _m.get('src'))
    for _f in ('heard', 'verdict', 'n', 'body', 'group', 'icon'):
        if not _m.get(_f): fails.append(f'그런줄 {_m["id"]} 의 {_f} 가 비었습니다')
    _g = (_m.get('go') or '').lstrip('/').split('?')[0].split('/')[0]
    if _g and _g not in _ROUTES: fails.append(f'그런줄 {_m["id"]} 의 연결 화면이 없습니다 → {_m.get("go")}')
    _t = (_m.get('go') or '')
    if _t.startswith('/symptom/') and _t.split('/')[2].split('?')[0] not in sid:
        fails.append(f'그런줄 {_m["id"]} 가 없는 증상으로 갑니다 → {_t}')
    if _t.startswith('/drug/') and _t.split('/')[2].split('?')[0] not in did:
        fails.append(f'그런줄 {_m["id"]} 가 없는 약으로 갑니다 → {_t}')
    if _t.startswith('/supp/') and _t.split('/')[2].split('?')[0] not in supid:
        fails.append(f'그런줄 {_m["id"]} 가 없는 영양제로 갑니다 → {_t}')
    if _t.startswith('/class/') and _t.split('/')[2].split('?')[0] not in kid:
        fails.append(f'그런줄 {_m["id"]} 가 없는 계열로 갑니다 → {_t}')
    if _t.startswith('/tips?open='):
        if _t.split('=')[1] not in {t['id'] for t in T}: fails.append(f'그런줄 {_m["id"]} 가 없는 팁으로 갑니다 → {_t}')
for _m in _MY: hardword(_m, '', '그런줄 ' + _m['id'])
for _m in _MY: jargon(_m, '', '그런줄 ' + _m['id'])

# ── 항콜린 점수는 출처 없이 붙이지 않는다 ─────────────────────────────────
# 카페인·이소프로필안티피린·에텐자미드에 «어르신 조심» 뜻으로 ach=1 이 붙어 있었다.
# 게보린 한 알이 그것만으로 2점을 만들어, 진짜 항콜린제의 신호를 묽게 하고 있었다.
_ING = json.load(open(C / 'ingredients.json', encoding='utf-8'))
_OKSRC = {'ACB', 'KABS', '확인 필요'}
for _e in _ING.get('ing', []):
    if _e.get('ach'):
        if _e.get('achSrc') not in _OKSRC:
            fails.append(f'성분 {_e.get("k")} 의 항콜린 점수에 출처 표시가 없습니다(ACB·KABS·확인 필요 중 하나)')
    else:
        for _f in ('achSrc', 'achNote', 'achAlt'):
            if _e.get(_f):
                fails.append(f'성분 {_e.get("k")} 에 점수 없이 {_f} 만 남아 있습니다 — 화면에 안 나오는 죽은 자료입니다')

# ── 영양제 계산기와 글이 서로 다른 숫자를 말하면 안 된다 ────────────────────
# 비타민 C 의 상한이 «35 mg»(아연 값)으로 적혀 있었고, 아연 계산기는 한국 상한 35 mg 을
# 두고 40 mg 에서야 빨개졌다. 계산기 설명(note)에 적힌 mg 과 실제 경계를 맞춰 본다.
_mgre = re.compile(r'([\d,]+(?:\.\d+)?)\s*mg[^.]{0,12}상한')
for _x in SUP:
    _c = _x.get('calc') or {}
    if not (_c.get('typical') and _c.get('ulRatio')): continue
    _edge = _c['typical'] * _c['ulRatio']
    for _f in ('note', 'caveat'):
        for _n in _mgre.findall(_c.get(_f) or ''):
            _v = float(_n.replace(',', ''))
            if abs(_v - _edge) > 0.01:
                fails.append(f'영양제 {_x["id"]} — 계산기는 {_edge:g} mg 에서 경계인데 설명은 «{_v:g} mg 이 상한»이라고 합니다')

# ── 첫 화면이 가벼운지 — 어르신은 데이터가 느린 곳에서 여신다 ──────────────
# 본문을 data/core.json 으로 뺀 뒤 첫 내려받기가 1.47 MB → 0.5 MB 가 됐다(v84).
# 다시 통째로 심는 실수를 하면 여기서 걸린다.
import gzip as _gz
_idx = ROOT.parent / 'docs' / 'yakjido' / 'index.html'
_core = ROOT.parent / 'docs' / 'yakjido' / 'data' / 'core.json'
if _idx.exists():
    _b = _idx.read_bytes(); _gzkb = len(_gz.compress(_b, 6)) / 1024
    if _gzkb > 220:
        fails.append(f'첫 화면이 무겁습니다 — index.html 압축 {_gzkb:.0f} KB (한계 220 KB). 본문은 data/core.json 으로 빼야 합니다')
    if not _core.exists():
        fails.append('docs/yakjido/data/core.json 이 없습니다 — 빌드를 다시 돌리세요')
    else:
        _c = json.loads(_core.read_text(encoding='utf-8'))
        for _k in ('symptoms', 'drugs', 'sources', 'ingredients', 'interactions'):
            if not _c.get(_k): fails.append(f'core.json 에 {_k} 가 비어 있습니다')
        # 본문도 첫 화면에서 바로 받는다 — 여기가 커지면 신호 약한 곳에서 그대로 기다림이 된다.
        # (식약처 낱알 목록·성분 사전은 3.5초 뒤나 검색할 때 받으므로 첫 화면과 경쟁하지 않는다)
        _ckb = len(_gz.compress(_core.read_bytes(), 6)) / 1024
        if _ckb > 400:
            fails.append(f'본문이 무겁습니다 — core.json 압축 {_ckb:.0f} KB (한계 400 KB)')

# ── PubMed 을 근거로 쓴 출처에는 DOI 링크를 단다 ─────────────────────────
# 현욱님 규칙. DOI 가 아예 없는 옛 논문도 있어서, 그때는 「DOI 가 등록돼 있지 않다」고
# 적어 두게 했다. 둘 다 아니면 그냥 빠뜨린 것이다.
for _k, _v in SRC.items():
    _u = _v.get('url') or ''; _n = _v.get('note') or ''
    if 'PMID' in _n or 'pubmed.ncbi' in _u:
        if 'doi.org' not in _u and 'DOI 가 등록돼 있지 않은' not in _n:
            fails.append(f'출처 {_k} — PubMed 근거인데 DOI 링크가 없습니다(없는 논문이면 note 에 적어 주세요)')

# ── 숫자와 영어 단위는 한 칸 띄운다 ────────────────────────────────────
# 「3,000mg」처럼 붙여 쓴 곳이 섞여 있었다. 한글 단위(알·정·캡슐)는 붙여 쓰는 것이 맞아
# 영어 단위만 본다. 허가사항 제품명(타이레놀정 500mg)은 원문 그대로라 출처에서는 넘어간다.
_unit = re.compile(r'(?<![A-Za-z0-9.])(\d[\d,.]*)(mg|g|mL|ml|µg|mcg|IU|kg)\b')
for _p in sorted(ROOT.glob('content/*.json')):
    if _p.name.startswith('sources'): continue
    for _m in _unit.finditer(_p.read_text(encoding='utf-8')):
        fails.append(f'{_p.name} — 숫자와 단위를 붙여 썼습니다: «{_m.group(0)}»')

# ── 같은 성분의 상한을 두 곳이 다르게 말하면 안 된다 ──────────────────────
# 아연 상한이 영양제 화면에서는 35 mg, 겹침 규칙에서는 40 mg 이었다.
_ul = {'아연': '35 mg', '비타민 C': '2,000 mg'}
for _name, _want in _ul.items():
    _txt = ''.join(_p.read_text(encoding='utf-8') for _p in sorted(ROOT.glob('content/*.json')) if not _p.name.startswith('sources'))
    for _m in re.finditer(re.escape(_name) + r'[^"]{0,40}?상한[^"]{0,24}?([\d,]+)\s?mg', _txt):
        if _m.group(1) + ' mg' != _want:
            fails.append(f'{_name} 상한이 {_m.group(1)} mg 로 적힌 곳이 있습니다 — 기준은 {_want} 입니다')

# ── 「이렇게 드세요」가 계획에 없는 약을 권하면 안 된다 ────────────────────
# 기침 화면이 계획에서는 아세틸시스테인을 고르면서, 아래 안내문에서는 구아이페네신이
# 든 감기약을 권하고 있었다. 화면 하나가 서로 다른 말을 하던 자리다.
_dname = {}
for _d in D:
    _n = _d['name'].split('(')[0].strip()
    if len(_n) >= 3: _dname.setdefault(_n, _d['id'])
for _s in S:
    _ids = set()
    for _p in _s.get('plan', []):
        _ids |= set(_p.get('options') or [])
        if _p.get('pick'): _ids.add(_p['pick'])
    # 「그 약은 이 자리에 안 맞는다」고 설명하는 문장은 권하는 것이 아니다 — 그 문장만 따로 본다
    _no = ('잘 듣지 않', '권하지', '피하', '낫습니다', '양이 적', '아니', '대신')
    for _line in (_s.get('how') or []):
        for _sent in re.split(r'(?<=[.!?])\s+', _line):
            for _n, _i in _dname.items():
                if _n in _sent and _i not in _ids and _n != '카페인' and not any(_k in _sent for _k in _no):
                    fails.append(f'증상 {_s["id"]} — 「이렇게 드세요」는 «{_n}»을 권하는데 계획 칸에는 없습니다')

# ── 아이콘 — 정본은 JSON 이고, 증상 56가지는 서로 달라야 한다 ────────────
# 2026-09-22: 앱 안에 ICON_BY_ID 라는 덮어쓰기 표가 있어서 자료를 고쳐도 화면이 안 바뀌었다.
# 그리고 증상 56가지가 아이콘 19개를 나눠 쓰고 있었다(물방울 하나가 7가지를 맡았다).
_shell = (ROOT / 'app-shell.html').read_text(encoding='utf-8')
if 'ICON_BY_ID' in _shell:
    fails.append('app-shell.html 에 ICON_BY_ID 같은 아이콘 덮어쓰기 표가 생겼습니다 — 정본은 content 의 icon 입니다')
_ICON = set(re.findall(r"^I\.(\w+)\s*=\s*'<svg", _shell, re.M))
_m = re.search(r'^const I = \{(.*?)^\};', _shell, re.S | re.M)
if _m: _ICON |= {k for k, _ in re.findall(r"(\w+)\s*:\s*'(<svg.*?</svg>)'", _m.group(1), re.S)}
_seen = {}
for _s in S:
    _ic = _s.get('icon')
    if not _ic: fails.append(f'증상 {_s["id"]} 에 icon 이 없습니다')
    elif _ic not in _ICON: fails.append(f'증상 {_s["id"]} 의 아이콘 «{_ic}» 이 app-shell.html 에 없습니다 — 알약 그림으로 대체돼 버립니다')
    elif _ic in _seen: fails.append(f'증상 «{_seen[_ic]}» 와 «{_s["id"]}» 가 같은 아이콘 «{_ic}» 을 씁니다 — 어르신이 골라야 하는 화면입니다')
    else: _seen[_ic] = _s['id']
_quick = [{'id': _g.get('id'), 'icon': _g.get('ico')} for _g in (ING.get('quick') or [])]
for _name, _rows in (('계열', K), ('그런줄', _MY), ('담기 계열', _quick)):
    _u = {}
    for _r in _rows:
        _ic = _r.get('icon')
        if _ic and _ic not in _ICON: fails.append(f'{_name} {_r.get("id")} 의 아이콘 «{_ic}» 이 없습니다')
        elif _ic and _ic in _u: fails.append(f'{_name} «{_u[_ic]}» 와 «{_r.get("id")}» 가 같은 아이콘 «{_ic}» 을 씁니다')
        elif _ic: _u[_ic] = _r.get('id')

print(f'증상 {len(S)} · 약 {len(D)} · 계열 {len(K)} · 영양제 {len(SUP)} · 팁 {len(T)} · 그런줄 {len(_MY)} · 규칙 {len(IX["rules"])} · 출처 {len(SRC)}')
if fails:
    print('실패', len(fails)); [print('  ✗', f) for f in fails]; sys.exit(1)
print('✓ 자료 고리 전부 연결')
