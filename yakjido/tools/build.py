#!/usr/bin/env python3
"""약지도 앱 빌드 — content/*.json 을 app-shell.html 에 심어 docs/yakjido/index.html 로 낸다.

사용:  python3 yakjido/tools/build.py
- content/ 의 모든 JSON 을 하나의 DATA 객체로 합친다(파일명 = 키).
- public/ 에 공공데이터(e약은요·낱알식별) 추출본이 있으면 함께 심는다.
- 배포본은 GitHub Pages(docs/yakjido/) 로 나간다. manifest·sw 는 같은 폴더에 둔다.
"""
import json, pathlib, re, datetime, hashlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
shell = (ROOT / 'app-shell.html').read_text(encoding='utf-8')
data = {}
for p in sorted((ROOT / 'content').glob('*.json')):
    if p.name.startswith('_'): continue
    key = p.stem.split('.')[0]          # drugs.part2.json → drugs 에 합침
    v = json.loads(p.read_text(encoding='utf-8'))
    if key in data and isinstance(v, list): data[key].extend(v)
    elif key in data and isinstance(v, dict): data[key].update(v)
    else: data[key] = v
pub = ROOT.parent / 'docs' / 'yakjido' / 'data'   # 공공데이터는 import_public_data.py 가 여기에 직접 쓴다
if (pub / 'meta.json').exists():
    data['public'] = json.loads((pub / 'meta.json').read_text(encoding='utf-8'))  # 건수·출처만 인라인, 본문은 data/ 로 지연 로드
# 「제품 이름으로 찾기」가 제품 사전 357개만 세던 것 — 실제로는 e약은요·낱알식별의 약국 약과 처방약까지 이름으로 찾는다(2026-10-13 현욱님 「엄청 많을건데」).
# 처방약 낱알 자료(5 MB)는 무거워 이름·품목코드·회사만 뽑은 names-rx.json 을 검색 때 받는다. 건수는 같은 품목기준코드를 한 번만 센다.
if (pub / 'pills-rx.json').exists() and (pub / 'pills.json').exists() and (pub / 'easy-index.json').exists():
    import re as _r0
    _nm = lambda t: _r0.sub(r'\(.*?\)|[\s\-·.]', '', str(t or '')).lower()
    _rx = json.loads((pub / 'pills-rx.json').read_text(encoding='utf-8'))
    _ot = json.loads((pub / 'pills.json').read_text(encoding='utf-8'))
    _ez = json.loads((pub / 'easy-index.json').read_text(encoding='utf-8'))
    _seen, _rxl = set(), []
    for _x in _rx:
        if _x.get('seq') and _x['seq'] not in _seen: _seen.add(_x['seq']); _rxl.append([_x['n'], _x['seq'], _x.get('m', '')])
    _oseq = {x['seq'] for x in _ot if x.get('seq')} | {x['seq'] for x in _ez if x.get('seq')}
    _onm = {_nm(x['n']) for x in _ot} | {_nm(x['n']) for x in _ez if x.get('seq')}
    _otc = len(_oseq) + len({_nm(x['n']) for x in _ez if not x.get('seq') and _nm(x['n']) not in _onm})
    # 식약처 허가 목록(tools/fetch_mfds.py → tools/permits.json, 시럽·연고·주사까지 모든 허가 제품)이 있으면 그 이름도 — 처방약은 [이름, 코드, 회사], 낱알·e약은요에 없는 약국 약은 끝에 0
    _pm = ROOT / 'tools' / 'permits.json'
    if _pm.exists():
        for _s, _n, _m, _r, _i in json.loads(_pm.read_text(encoding='utf-8')):
            if not _s or _s in _seen or _s in _oseq: continue
            if _r == 1: _seen.add(_s); _rxl.append([_n, _s, _m])
            elif _nm(_n) not in _onm: _oseq.add(_s); _onm.add(_nm(_n)); _otc += 1; _rxl.append([_n, _s, _m, 0])
    # 검색 때 받는 파일이라 가볍게(압축 576 → 약 400 KB, 10-14): 병원에서만 쓰는 주사·수액·검사 키트는 빼고(집에서 쓰는 펜형 주사는 남김),
    _hosp = _r0.compile(r'주사(?!기)|주[0-9][0-9.]*\s*(?:밀리|그램|마이크로|단위|mg|g|mL|IU)|주\(|수액|키트|조영|투석액|관류액|흡입마취')
    _keep = _r0.compile(r'펜|프리필드')
    _rxl = [x for x in _rxl if not (_hosp.search(x[0]) and not _keep.search(x[0]))]
    _rxl = [[x[0], x[1], ''] + x[3:] for x in _rxl]   # 회사 이름은 뺀다(같은 이름은 함량이 이름에 있어 구별된다) — 약 화면에서 낱알 자료로 보인다
    (pub / 'names-rx.json').write_text(json.dumps(_rxl, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    data['public'].update({'prod_otc': _otc, 'prod_rx': sum(1 for x in _rxl if len(x) == 3)})
# 낱알 사진은 식약처 서버 주소를 그대로 쓴다(저장 안 함). docs/yakjido/img/ 에 파일이 있을 때만 그것을 우선.
imgdir = ROOT.parent / 'docs' / 'yakjido' / 'img'
for v in (data.get('productImages') or {}).values():
    iid = v['img'].rstrip('/').split('/')[-1]
    for ext in ('.webp', '.jpg'):
        if (imgdir / (iid + ext)).exists(): v['img'] = 'img/' + iid + ext; break
# 약학정보원 복약정보(tools/kpic_detail.py) — 제품 화면이 그 제품 조각만 받게 16개로 나눈다(2026-09-30)
kg = pub / 'kpic-guide.json'
if kg.exists():
    _g = json.loads(kg.read_text(encoding='utf-8')); _kd = pub / 'kg'; _kd.mkdir(exist_ok=True)
    if (pub / 'kpic-extra.json').exists():   # 약 사전 대표 제품(tools/kpic_rep.py) — 수집 파일과 따로 받은 것
        for _s, _v in json.loads((pub / 'kpic-extra.json').read_text(encoding='utf-8')).items():
            if _v and not _g.get(_s): _g[_s] = _v
    # 128조각 — 처방약까지 1만 9천 개가 되자 16조각이면 한 조각이 1.3 MB 였다(제품 하나 보려고 휴대폰이 1.3 MB를 받는다).
    # 조각 번호는 앱의 kgShard 와 똑같이 «품목코드 % KG_N».
    KG_N = 128
    _sh = [{} for _ in range(KG_N)]
    for _seq, _v in _g.items():
        if _v: _sh[(int(str(_seq)) if str(_seq).isdigit() else 0) % KG_N][_seq] = _v
    for _old in _kd.glob('*.json'): _old.unlink()
    for _i, _d in enumerate(_sh): (_kd / f'{_i}.json').write_text(json.dumps(_d, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
if not (pub / 'kpic.json').exists(): (pub / 'kpic.json').write_text('{}', encoding='utf-8')   # 없으면 앱이 404 를 낸다
# ── 삽화(art/) ────────────────────────────────────────────────────────────
# yakjido/art/ 에 PNG 를 넣어 두기만 하면 배포본으로 복사되고, 앱은 있는 그림만 그린다.
# 파일이 없으면 D.art 목록에 안 들어가서 화면에 빈 자리도 안 생긴다.
ART_NAMES = ['hero-home', 'guide-1-where', 'guide-2-pharmacy', 'guide-3-take', 'photo-guide',
             'pill-search', 'schedule', 'supp-label', 'kids-dose', 'easy-mode',
             'me-safety', 'tips', 'empty-search']
artsrc = ROOT / 'art'
artdst = ROOT.parent / 'docs' / 'yakjido' / 'art'
MAXW = {'easy-mode': 300}                  # 88px 원형이라 작게, 나머지는 900px 이면 2배 화면까지 충분
found = []
if artsrc.exists():
    for name in ART_NAMES:
        f = next((artsrc / (name + e) for e in ('.webp', '.png', '.jpg') if (artsrc / (name + e)).exists()), None)
        if not f: continue
        artdst.mkdir(parents=True, exist_ok=True)
        try:
            from PIL import Image
            im = Image.open(f).convert('RGB'); cap = MAXW.get(name, 900); long = max(im.size)
            if long > cap:
                r = cap / long; im = im.resize((round(im.width * r), round(im.height * r)), Image.LANCZOS)
            im.save(artdst / (name + '.webp'), 'WEBP', quality=82, method=6)
        except Exception as e:
            (artdst / (name + f.suffix)).write_bytes(f.read_bytes()); print('그림 변환 실패, 원본 복사:', name, e)
        found.append(name)
for stale in (artdst.glob('*') if artdst.exists() else []):      # 지운 그림은 배포본에서도 지운다
    if stale.stem not in found: stale.unlink()
data['art'] = found

# ── 첫 화면 자료와 나머지를 나눈다 ────────────────────────────────────────
# 첫 화면(어디가 불편하세요 · 증상 타일 · 검색)에 필요한 것은 «이름·갈래·아이콘·
# 한 줄 설명»뿐이다. 나머지 본문(계획·복용법·출처 …)은 data/core.json 으로 빼서
# 화면이 뜬 뒤에 받는다. 받아 오면 같은 객체에 그대로 덧씌우므로(Object.assign)
# 화면 함수는 하나도 바꾸지 않아도 된다.
SLIM = {
    'symptoms':    ['id', 'group', 'icon', 'name', 'short', 'tags', 'reviewed'],
    'drugs':       ['id', 'name', 'class', 'rx'],   # simple(한 줄 먹는 법)도 본문으로 — 첫 화면(홈·처음 안내)은 본문이 오면 다시 그리고(mergeCore → redraw) 알림도 다시 건다(2026-10-14 외부 검수 2차 반영으로 첫 화면 232 KB, 압축 약 3 KB 줄임)   # for(쓰임)도 본문으로 — 약 사전·검색은 본문이 오면 다시 그린다(10-14 화면 개편으로 첫 화면 226 KB)   # tagline 도 본문으로(증상·약 화면은 본문을 받은 뒤 그려진다, 10-14 첫 화면 예산)   # en(영어 이름)은 본문으로 — 첫 화면 목록엔 안 보인다(10-14 많이 찾는 약 타일로 224 KB 넘침)
    'supplements': ['id', 'name', 'tags', 'brands', 'evidence'],   # en(영어 이름)은 본문으로 — 화면에 안 보이고(외부 검수 2차 #59) 검색만 씀(10-14 첫 화면 228 KB)
    'classes':     ['id', 'name', 'short', 'icon'],
    'tips':        ['id', 'group', 'icon', 'title'],
    'askdoc':      ['id', 'icon', 'q'],               # 홈은 개수·검색은 질문만 — 대답은 본문과 함께(2026-10-13 검수 반영으로 첫 화면 220 KB)   # 홈은 제목만 쓴다 — 본문은 팁 화면(본문 받은 뒤)에서(2026-10-06 첫 화면 220 KB)
}
CORE_KEYS = ['sources', 'ingredients', 'interactions', 'kids', 'productImages', 'suppRules', 'myths', 'recalls', 'drugRep']   # drugRep: 약 화면(본문 받은 뒤)에서만 씀 — 첫 화면 220 KB 예산
# 약 화면에서만 쓰는 칸(자주 묻는 질문·부작용 빈도)은 data/detail.json 으로 한 번 더 뺀다.
# 본문과 «동시에» 받기 시작하고, 약 화면만 이것까지 기다린다 — core.json 400 KB 예산(2026-10-04)
DETAIL = {'drugs': ['faq', 'sideFreq', 'lact', 'tips', 'interactions', 'riskNote', 'sideEffects', 'stop', 'lead', 'onset', 'duration'],   # lead·onset·duration: 자세한 약 화면(vDrug)에서만 — 10-14 외부 검수 2차 반영(제품 용법·메타 본문 이동)으로 core 401 KB   # sideEffects·stop: 약 화면(읽어 주기 포함)에서만 — 10-14 투석·출처 보강으로 core 401 KB   # tips·interactions: 약 화면에서만(2026-10-13 검수 반영으로 core 400 KB) · riskNote: 약 화면 「부담 정도」 막대 아래 설명만(10-13 아이 나이 칸·병용 규칙 추가로 core 400 KB)
          'supplements': ['foods', 'need', 'faq', 'evidenceNote', 'priceTip'],
          'classes': ['table', 'notes', 'verdict']}   # 계열 비교 화면에서만 — 10-14 쉬운 말·알아두면 좋은 것 보강으로 core 402 KB
detail = {k: [{'id': o['id'], **{f: o[f] for f in fs if f in o}} for o in data[k] if any(f in o for f in fs)] for k, fs in DETAIL.items()}
for k, fs in DETAIL.items():
    data[k] = [{f: v for f, v in o.items() if f not in fs} for o in data[k]]
# 출처의 _memo(내부 검수 메모)는 앱에 싣지 않는다 — 원본에만 남김(2026-10-13 자체 검수 4-01)
if isinstance(data.get('sources'), dict):
    data['sources'] = {k: ({f: x for f, x in v.items() if not f.startswith('_')} if isinstance(v, dict) else v) for k, v in data['sources'].items()}
inline, core = {}, {}
for k, v in data.items():
    if k in SLIM:
        fs = SLIM[k]
        inline[k] = [{f: o[f] for f in fs if f in o} for o in v]
        rest = [{f: o[f] for f in o if f not in fs or f == 'id'} for o in v]
        core[k] = [o for o in rest if len(o) > 1]
    elif k in CORE_KEYS:
        core[k] = v
    else:
        inline[k] = v                       # meta · art · public · tips 는 작아서 그대로 둔다
# meta 의 「이 앱에 대해(about)·이렇게 만들었어요(method)」는 설정 화면(본문을 받은 뒤에만 그려짐)에서만 쓴다 — 본문에는 meta 전체를 싣고
# (mergeCore 가 D.meta 를 본문 것으로 바꾼다) 첫 화면에서는 뺀다(2026-10-14 외부 검수 2차 반영으로 첫 화면 예산, 압축 약 0.9 KB)
if isinstance(inline.get('meta'), dict):
    core['meta'] = inline['meta']; inline['meta'] = {k: v for k, v in inline['meta'].items() if k not in ('about', 'method')}

jc = json.dumps(core, ensure_ascii=False, separators=(',', ':'))
j = json.dumps(inline, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
stamp = datetime.date.today().isoformat()
# 낱알식별(pills.json) 중 성분 칸이 빈 일반약을 «같은 품목기준코드(seq)»의 e약은요 성분으로 채운다 — 이름 짐작 없이 코드가 같을 때만.
# 사진으로 담은 약의 겹침 판정(같은 성분 두 번)이 성분을 몰라 초록으로 나오던 것(2026-10-13 자체 검수 3-03). 다시 돌려도 같은 결과.
_pd = ROOT.parent / 'docs' / 'yakjido' / 'data'
if (_pd / 'pills.json').exists() and (_pd / 'easy-index.json').exists():
    _seq = {x['seq']: x['i'] for x in json.loads((_pd / 'easy-index.json').read_text(encoding='utf-8')) if x.get('seq') and x.get('i')}
    _pl = json.loads((_pd / 'pills.json').read_text(encoding='utf-8')); _n = 0
    for _x in _pl:
        if not _x.get('ingr') and _x.get('seq') in _seq: _x['ingr'] = '|'.join(_seq[_x['seq']]); _n += 1
    # 그래도 빈 것은 식약처 의약품 상세 «원료약품 및 분량»을 품목기준코드별로 받아 둔 tools/pill-ingr.json 으로(2026-10-13 실사용 검수 2차 A3 —
    # 판콜에이캡슐·펜잘나이트·게보린쿨다운이 성분 없이 담겨 타이레놀과의 겹침을 놓치던 것). 받는 도구: tools/pill_ingr_scrape.py
    _pi = ROOT / 'tools' / 'pill-ingr.json'
    _pi = json.loads(_pi.read_text(encoding='utf-8')) if _pi.exists() else {}
    for _x in _pl:
        if not _x.get('ingr') and _pi.get(_x.get('seq')): _x['ingr'] = '|'.join(_pi[_x['seq']]); _n += 1
    import re as _rb; _r0b = _rb.compile('[가-힣]')
    _pm = ROOT / 'tools' / 'permits.json'   # 식약처 허가 목록의 주성분(품목기준코드가 같을 때만)
    if _pm.exists():
        _pmi = {x[0]: x[4] for x in json.loads(_pm.read_text(encoding='utf-8')) if x[4] and _r0b.search(x[4])}   # 한글 성분만 — 허가 목록 칸은 영어라 성분 사전과 안 맞는다(10-14)
        for _x in _pl:
            # 허가 목록의 한글 주성분이 있으면 그것이 원본이다 — 이름 끝 괄호는 맛 이름일 때가 있다(「트로앤텍트로키(페퍼민트)」가 페퍼민트 캡슐로 읽히던 것, 10-14)
            if _pmi.get(_x.get('seq')) and _x.get('ingr') != _pmi[_x['seq']]: _x['ingr'] = _pmi[_x['seq']]; _n += 1
    if _n:
        (_pd / 'pills.json').write_text(json.dumps(_pl, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
        print(f'낱알 성분 채움 {_n}건(같은 품목기준코드 · 식약처 상세)')
    if _pm.exists() and (_pd / 'pills-rx.json').exists():   # 처방약 낱알도 허가 목록의 한글 주성분으로(이름 괄호에 없는 복합 성분까지)
        _pr = json.loads((_pd / 'pills-rx.json').read_text(encoding='utf-8')); _m = 0
        for _x in _pr:
            if _pmi.get(_x.get('seq')) and _x.get('ingr') != _pmi[_x['seq']]: _x['ingr'] = _pmi[_x['seq']]; _m += 1
        if _m: (_pd / 'pills-rx.json').write_text(json.dumps(_pr, ensure_ascii=False, separators=(',', ':')), encoding='utf-8'); print(f'처방약 낱알 성분 {_m}건 허가 목록대로')
jd = json.dumps(detail, ensure_ascii=False, separators=(',', ':'))
# 본문 판(DATAV)은 core·detail·지연 로드 자료 내용의 해시 — 같은 날 두 번 빌드해도 내용이 바뀌면 휴대폰이 새 본문을 받는다(2026-10-13 자체 검수 5-02)
_lazy = b''.join(f.read_bytes() for f in sorted((ROOT.parent / 'docs' / 'yakjido' / 'data').rglob('*.json')) if f.name not in ('core.json', 'detail.json') or f.parent.name != 'data')   # 지연 로드 자료도 바뀌면 판이 바뀐다(5-02)
datav = hashlib.sha1((jc + jd).encode('utf-8') + _lazy).hexdigest()[:10]
out = shell.replace('<!--DATA-->', j).replace('__BUILD__', stamp).replace('__DATAV__', datav)
# 2026-10-13 상용화 점검 — 배포본에서는 «줄 전체가 주석»인 /* … */ 덩어리를 뺀다(원본은 그대로). 휴대폰마다 개발 메모 수백 개를 내려받던 것 —
# 첫 화면 압축 225 → 192 KB. 줄 중간·코드 뒤의 주석은 건드리지 않는다(문자열 안일 수 있어서).
import re as _re
out = _re.sub(r'(?m)^[ \t]*/\*(?:(?!\*/).)*?\*/[ \t]*\n', '', out, flags=_re.S)
# 줄 앞 들여쓰기도 뺀다(압축 약 2 KB) — 화면 글은 HTML 이 빈칸을 접고, 줄바꿈을 살리는 칸(pre-line)도 줄 앞 빈칸은 버린다.
# 들여쓰기가 뜻을 갖는 글(pre·pre-wrap)은 셸에 없다(2026-10-13, 제품 이름 검색 확대로 첫 화면 225 KB → 예산 224 KB)
out = _re.sub(r'(?m)^[ \t]+', '', out)
pages = ROOT.parent / 'docs' / 'yakjido'
pages.mkdir(parents=True, exist_ok=True)
(pages / 'index.html').write_text(out, encoding='utf-8')
(pages / 'data').mkdir(parents=True, exist_ok=True)
(pages / 'data' / 'core.json').write_text(jc, encoding='utf-8')
(pages / 'data' / 'detail.json').write_text(jd, encoding='utf-8')
print(f'첫 화면 {len(out)/1024:.0f} KB · 본문 data/core.json {len(jc)/1024:.0f} KB')
# 서비스워커 캐시 이름 = 배포 파일 내용의 해시 — 내용이 같으면 같은 이름(파이썬 hash() 는 실행마다 달라 매번 바뀌던 것, 2026-10-13)
_srvjs = (ROOT / 'srv.js').read_text(encoding='utf-8') if (ROOT / 'srv.js').exists() else ''
_srvjs += (ROOT / 'find.js').read_text(encoding='utf-8') if (ROOT / 'find.js').exists() else ''   # 찾기 부품도 바뀌면 캐시 이름이 바뀌게(10-14)
_srvjs += ''.join((ROOT / f).read_text(encoding='utf-8') for f in ('terms.html', 'privacy.html') if (ROOT / f).exists())   # 앱 안에서 읽는 약관·방침도(오프라인 캐시, 10-14)
cache_id = hashlib.sha1((out + jc + jd + _srvjs).encode('utf-8')).hexdigest()[:8]
sw = ROOT / 'sw.js'
if sw.exists():
    s = re.sub(r"const CACHE = '[^']*'", f"const CACHE = 'yakjido-{stamp}-{cache_id}'", sw.read_text(encoding='utf-8'))
    (pages / 'sw.js').write_text(s, encoding='utf-8')
for name in ('manifest.webmanifest', 'privacy.html', 'terms.html', 'delete-account.html', 'srv.js', 'find.js'):   # terms.html = 약지도 이용약관(첫 동의 화면·설정에서 앱 안으로 읽음, 10-14)   # find.js = 공용 찾기 부품 + 약지도 쪽(검색을 처음 쓸 때 받음, Z8)
    # delete-account.html = 스토어 「계정 삭제 URL」(메디나눔 안내 2026-10-13)   # srv.js = 계정·기록 이어 두기(따로 받는 파일)   # privacy.html = 스토어에 적는 개인정보처리방침 주소
    src = ROOT / name
    if src.exists():
        (pages / name).write_text(src.read_text(encoding='utf-8'), encoding='utf-8')
# 메디나눔 공통 이름(privacy-<앱>.html · delete-account-<앱>.html)으로도 같은 쪽을 둔다 — 옛 주소(privacy.html)는 스토어에 이미 적혀 있어 그대로 둔다
for name, alias in (('privacy.html', 'privacy-yakjido.html'), ('terms.html', 'terms-yakjido.html'), ('delete-account.html', 'delete-account-yakjido.html')):
    if (pages / name).exists(): (pages / alias).write_text((pages / name).read_text(encoding='utf-8'), encoding='utf-8')
for ic in (ROOT / 'icons').glob('*'):
    (pages / ic.name).write_bytes(ic.read_bytes())

# ── 앱 아이콘 ──────────────────────────────────────────────────────────────
# 정본은 **현욱님이 주신 art/icon-1024.png** 다. 빌드는 이 파일을 «읽기만» 한다.
#
# 2026-09-21 사고: 예전 빌드는 art/icon.svg 로 art/icon-1024.png 를 «덮어썼다».
# 현욱님이 원본 파일을 올려 주셔도 빌드 한 번이면 지워지는 구조였다.
# → 이제 art/ 안에는 아무것도 쓰지 않는다. 내보내는 곳은 docs/ 뿐이다.
#
# icon.svg 는 «같은 그림을 벡터로 옮긴 보조본»이다. 작은 크기에서 더 선명해서
# docs/ 아이콘을 구울 때만 쓰고, 래스터 원본과 어긋나면 래스터가 이긴다.
src_icon = None
for ext in ('.png', '.webp', '.jpg'):
    f = ROOT / 'art' / ('icon-1024' + ext)
    if f.exists(): src_icon = f; break
svg_icon = ROOT / 'art' / 'icon.svg'
mask_svg = ROOT / 'art' / 'icon-maskable.svg'
SIZES = ((1024, 'icon-1024.png'), (512, 'icon-512.png'), (192, 'icon-192.png'), (180, 'icon-180.png'))
if src_icon:
    try:
        from PIL import Image
        before = src_icon.read_bytes()              # 빌드가 원본을 건드렸는지 끝에서 확인한다
        im = Image.open(src_icon).convert('RGBA')
        if im.width != im.height:
            side = min(im.width, im.height); im = im.crop((0, 0, side, side))
        bg = Image.new('RGBA', im.size, (250, 248, 243, 255))
        bg.alpha_composite(im); im = bg.convert('RGB')
        baked = False
        if svg_icon.exists():
            try:                                     # 벡터가 있으면 크기마다 다시 그린다(가장자리가 산다)
                import cairosvg
                for size, name in SIZES:
                    cairosvg.svg2png(url=str(svg_icon), write_to=str(pages / name), output_width=size, output_height=size)
                cairosvg.svg2png(url=str(mask_svg if mask_svg.exists() else svg_icon),
                                 write_to=str(pages / 'icon-maskable-512.png'), output_width=512, output_height=512)
                baked = True
            except Exception as e:
                print('아이콘 벡터 굽기 건너뜀(래스터로 대신):', e)
        if not baked:
            for size, name in SIZES:
                im.resize((size, size), Image.LANCZOS).save(pages / name, 'PNG')
            # ── 안드로이드용 maskable 아이콘 ────────────────────────────────
            # 런처가 아이콘을 동그라미·네모·물방울로 잘라낸다. 규칙은 둘이다.
            #   ① 바탕색이 네 변 끝까지 차 있어야 한다 (안 그러면 원 밖에 흰 테가 생긴다)
            #   ② 그림은 «가운데 지름 80% 원» 안에 들어와야 한다 (밖은 잘려 나간다)
            # 예전 코드는 80% 로 줄여 (6,6) 픽셀 색으로 채웠는데, 그 자리가 크림색 여백이라
            # 정확히 ①을 어겼다. 지금은 파란 바탕의 그라데이션을 좌표 1차식으로 맞춰 새로 깔고,
            # 그림만 떼어 안전원에 맞게 줄여 얹는다.
            try:
                import numpy as _np
                _sq = im.crop((int(im.width * .1), int(im.height * .1),
                               int(im.width * .9), int(im.height * .9))).resize((512, 512), Image.LANCZOS)
                _a = _np.array(_sq).astype(float)
                _alpha = _np.clip((_a.sum(axis=2) - 430) / 130.0, 0, 1)      # 흰·연파랑 그림만 1 에 가깝다
                _yy, _xx = _np.mgrid[0:512, 0:512]
                _ok = _alpha < 0.05
                _A = _np.stack([_xx[_ok], _yy[_ok], _np.ones(_ok.sum())], axis=1)
                _bg = _np.zeros((512, 512, 3))
                for _c in range(3):
                    _k, *_ = _np.linalg.lstsq(_A, _a[:, :, _c][_ok], rcond=None)
                    _bg[:, :, _c] = _k[0] * _xx + _k[1] * _yy + _k[2]
                _ys, _xs = _np.where(_alpha > 0.5)
                _r = _np.sqrt((_xs - 256.) ** 2 + (_ys - 256.) ** 2).max()
                _s = max(64, int(512 * (200.0 / _r)))                        # 안전원 반지름 205 보다 조금 안쪽
                _art = Image.fromarray(_np.dstack([_a, _alpha * 255]).astype('uint8'), 'RGBA').resize((_s, _s), Image.LANCZOS)
                _out = Image.fromarray(_np.clip(_bg, 0, 255).astype('uint8'), 'RGB').convert('RGBA')
                _out.alpha_composite(_art, ((512 - _s) // 2, (512 - _s) // 2))
                _out.convert('RGB').save(pages / 'icon-maskable-512.png', 'PNG')
            except Exception as _e:
                print('maskable 아이콘은 단순 확대로 대신합니다:', _e)
                im.resize((640, 640), Image.LANCZOS).crop((64, 64, 576, 576)).save(pages / 'icon-maskable-512.png', 'PNG')
        assert src_icon.read_bytes() == before, 'ERROR: 빌드가 art/ 의 아이콘 원본을 고쳤습니다'
        print(f'앱 아이콘 ← art/{src_icon.name}' + (' + icon.svg' if baked else '') + ' (원본은 읽기만 합니다)')
    except Exception as e:
        print('아이콘 재생성 건너뜀:', e)

counts = {k: (len(v) if isinstance(v, (list, dict)) else 1) for k, v in data.items()}
print(f'배포본 → {pages}/index.html · {len(out)//1024} KB · {counts}')
print('삽화:', ', '.join(found) if found else '없음 (yakjido/art/ 에 PNG 를 넣으면 자동 반영)')
