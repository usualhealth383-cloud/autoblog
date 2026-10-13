#!/usr/bin/env python3
"""식약처 공공데이터 OpenAPI 로 낱알식별·의약품 허가 목록을 «최신»으로 받기 (2026-10-13 현욱님 「낱알자료 최신 거 받는 방법」).

왜: 앱의 낱알 자료는 2022-10 벌크 CSV 라 자큐보처럼 그 뒤에 나온 약이 없다. 벌크 CSV 를 내려받던 쪽은 없어졌고,
    공공데이터포털 OpenAPI 두 개가 매달 갱신된다(둘 다 자동 승인·무료·개발 계정 하루 1만 번).
  · 15057639 식품의약품안전처_의약품 낱알식별 정보   — MdcinGrnIdntfcInfoService03/getMdcinGrnIdntfcInfoList03 (약 2만 5천 건)
  · 15095677 식품의약품안전처_의약품 제품 허가정보   — DrugPrdtPrmsnInfoService08/getDrugPrdtPrmsnInq08 (허가된 모든 제품 — 시럽·연고·주사 포함)
  · 15075057 식품의약품안전처_의약품개요정보(e약은요) — DrbEasyDrugInfoService/getDrbEasyDrugList (easy-index·easy-N, 성분은 허가 목록에서)
  · 15095679 식품의약품안전처_의약외품 제품 허가 정보 — QdrgPrdtPrmsnInfoService03/getQdrgPrdtPrmsnInfoInq03 (tools/quasi.json 에만, 앱 반영은 갈래를 본 뒤)

인증키: 공공데이터포털 «일반 인증키(Decoding)». ⛔ 파일·대화에 적지 않는다 — 환경변수 DATA_GO_KR_KEY 로만(깃허브 Secrets).
사용:   DATA_GO_KR_KEY=… python3 yakjido/tools/fetch_mfds.py [--only pills|permits|easy|quasi]
결과:   docs/yakjido/data/pills.json · pills-rx.json (지금 앱과 같은 꼴) · yakjido/tools/permits.json([품목코드, 이름, 회사, 전문 1/일반 0, 주성분]) · meta.json 출처·날짜
        그다음 python3 yakjido/tools/build.py 가 성분 채우기·이름 목록·건수를 다시 만든다.
"""
import json, os, pathlib, re, sys, time, datetime, urllib.parse, urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT.parent / 'docs' / 'yakjido' / 'data'
BASE = 'https://apis.data.go.kr/1471000/'
PILL_OP = 'MdcinGrnIdntfcInfoService03/getMdcinGrnIdntfcInfoList03'
PERMIT_OP = 'DrugPrdtPrmsnInfoService08/getDrugPrdtPrmsnInq08'
EASY_OP = 'DrbEasyDrugInfoService/getDrbEasyDrugList'   # 15075057 의약품개요정보(e약은요) — 성분 칸이 없어 허가 목록 주성분을 품목코드로 붙인다
QUASI_OP = 'QdrgPrdtPrmsnInfoService03/getQdrgPrdtPrmsnInfoInq03'   # 15095679 의약외품 제품 허가 정보(가그린·파스류 일부·소독제 등, 10-14 현욱님 신청)
ROWS = 100


def key():
    k = os.environ.get('DATA_GO_KR_KEY', '').strip()
    if not k: sys.exit('DATA_GO_KR_KEY 가 없습니다 — 공공데이터포털 일반 인증키를 환경변수(깃허브 Secrets)로 넣어 주세요')
    return urllib.parse.unquote(k) if '%' in k else k   # Encoding 키를 넣어도 되게


def _xml_items(raw):
    import xml.etree.ElementTree as ET
    root = ET.fromstring(raw)
    code = root.findtext('.//resultCode') or root.findtext('.//returnReasonCode') or ''
    if code not in ('00', '0', ''):
        raise RuntimeError('API 오류: ' + (root.findtext('.//resultMsg') or root.findtext('.//returnAuthMsg') or code))
    items = [{c.tag: (c.text or '') for c in it} for it in root.iter('item')]
    return int(root.findtext('.//totalCount') or 0), items


def page(op, n, k, rows=ROWS, extra=None):
    base = op if op.startswith('http') else BASE + op
    q = urllib.parse.urlencode({'serviceKey': k, 'pageNo': n, 'numOfRows': rows, 'type': 'json', '_type': 'json', **(extra or {})})
    for i in range(6):
        try:
            with urllib.request.urlopen(urllib.request.Request(base + '?' + q, headers={'Accept': 'application/json'}), timeout=90) as r:
                raw = r.read().decode('utf-8')
            if raw.lstrip().startswith('<'):   # 키 오류·XML 만 주는 서비스(국립중앙의료원)
                return _xml_items(raw)
            j = json.loads(raw)
            body = j.get('body') or j.get('response', {}).get('body') or {}
            items = body.get('items') or []
            if isinstance(items, dict): items = items.get('item') or []
            if isinstance(items, dict): items = [items]
            return int(body.get('totalCount') or 0), items
        except RuntimeError: raise
        except Exception as e:
            if i == 5: raise
            time.sleep(2 ** i)


def fetch_all(op, k, label, extra=None, want=500, workers=6):
    """한 쪽에 몇 건까지 주는지는 서비스마다 다르다 — 500 을 청해 보고 덜 주면 그 수로 다시 센다. 여러 쪽을 동시에(하루 한도 안)."""
    import concurrent.futures as cf
    total, first = page(op, 1, k, want, extra)
    rows = want if (len(first) >= want or len(first) >= total) else len(first)
    if rows != want and rows: total, first = page(op, 1, k, rows, extra)
    rows = rows or want
    pages = (total + rows - 1) // rows
    print(f'{label}: {total:,}건 · 한 쪽 {rows}건 · {pages}쪽', flush=True)
    got = {1: first}
    with cf.ThreadPoolExecutor(workers) as ex:
        futs = {ex.submit(page, op, n, k, rows, extra): n for n in range(2, pages + 1)}
        for i, f in enumerate(cf.as_completed(futs), 1):
            got[futs[f]] = f.result()[1]
            if i % 100 == 0: print(f'  {i}/{pages}쪽', flush=True)
    out = [x for n in sorted(got) for x in got[n]]
    if len(out) < total * .98: sys.exit(f'{label}: {len(out)}/{total} 만 받음 — 중간에 끊겼습니다. 기존 자료는 그대로 둡니다')
    return out


s = lambda v: str(v or '').strip()


def pills(k):
    rows = fetch_all(PILL_OP, k, '낱알식별')
    out = []
    for r in rows:
        kind = s(r.get('ETC_OTC_NAME'))
        if not kind: continue
        nm = s(r.get('ITEM_NAME'))
        mm = re.search(r'\(([^()]*)\)\s*$', nm)
        img = s(r.get('ITEM_IMAGE'))
        out.append({   # import_public_data.py(벌크 CSV)와 같은 꼴 — 앱 코드는 그대로
            'n': nm, 'm': s(r.get('ENTP_NAME')), 'img': img.rstrip('/').split('/')[-1] if img else '',
            'f': s(r.get('PRINT_FRONT')).replace('-', ''), 'b': s(r.get('PRINT_BACK')).replace('-', ''),
            'sh': s(r.get('DRUG_SHAPE')), 'c': s(r.get('COLOR_CLASS1')), 'c2': s(r.get('COLOR_CLASS2')).replace('-', ''),
            'cls': s(r.get('CLASS_NAME')), 'cvs': 1 if '안전상비' in kind else 0, 'sz': s(r.get('LENG_LONG')), 'seq': s(r.get('ITEM_SEQ')),
            'rx': 1 if kind.startswith('전문') else 0, 'ln': s(r.get('LINE_FRONT')).replace('-', ''),
            'ingr': mm.group(1) if mm and not mm.group(1).startswith('수출') else '',
            'fm': s(r.get('FORM_CODE_NAME')),   # 제형(필름코팅정·경질캡슐제·연질캡슐제 …) — 낱알 검색 「겉모습」 거르기
        })
    seen, uniq = set(), []
    for x in out:   # 같은 품목이 두 번 오는 일이 있다
        if x['seq'] and x['seq'] in seen: continue
        seen.add(x['seq']); uniq.append(x)
    return uniq


def permits(k):
    rows = fetch_all(PERMIT_OP, k, '의약품 허가 목록')
    out = []
    for r in rows:
        if s(r.get('CANCEL_NAME')) not in ('', '정상'): continue          # 취소·취하는 뺀다
        ing = '|'.join(x.strip() for x in re.split(r'[|]', re.sub(r'\[[^\]]*\]', '', s(r.get('ITEM_INGR_NAME')))) if x.strip())
        out.append([s(r.get('ITEM_SEQ')), s(r.get('ITEM_NAME')), s(r.get('ENTP_NAME')), 1 if s(r.get('SPCLTY_PBLC')).startswith('전문') else 0, ing])
    return out


def easy(k, permits_rows):
    rows = fetch_all(EASY_OP, k, 'e약은요')
    ing = {x[0]: [i for i in x[4].split('|') if i] for x in permits_rows if x[4]}
    pl = {}
    for f in ('pills.json', 'pills-rx.json'):
        if (OUT / f).exists():
            for x in json.loads((OUT / f).read_text(encoding='utf-8')): pl[x['seq']] = x
    def clean(t):
        t = re.sub(r'<[^>]+>', '', s(t)).replace('|', ', ')
        return re.sub(r'\.(?=[가-힣A-Za-z(])', '.\n', t)   # import_public_data.py 와 같은 줄바꿈
    out = []
    for r in rows:
        seq = s(r.get('itemSeq')); p = pl.get(seq)
        warn, atpn = clean(r.get('atpnWarnQesitm')), clean(r.get('atpnQesitm'))
        out.append({'n': s(r.get('itemName')), 'm': s(r.get('entpName')), 'i': ing.get(seq, []), 'map': [],
                    'e': clean(r.get('efcyQesitm')), 'u': clean(r.get('useMethodQesitm')), 'c': (warn + '\n' + atpn).strip() if warn else atpn,
                    'x': clean(r.get('intrcQesitm')), 's': clean(r.get('seQesitm')), 'k': clean(r.get('depositMethodQesitm')),
                    'img': s(r.get('itemImage')) or (('https://nedrug.mfds.go.kr/pbp/cmn/itemImageDownload/' + p['img']) if p and p.get('img') else ''),
                    'cvs': p['cvs'] if p else 0, 'seq': seq})
    return out


def quasi(k):
    rows = fetch_all(QUASI_OP, k, '의약외품 허가 목록')
    out = []
    for r in rows:
        if s(r.get('CANCEL_CODE_NAME')) not in ('', '정상'): continue
        out.append([s(r.get('ITEM_SEQ')), s(r.get('ITEM_NAME')), s(r.get('ENTP_NAME')), s(r.get('CLASS_NO_NAME')), s(r.get('MAIN_INGR'))[:200]])
    return out


def main():
    only = sys.argv[sys.argv.index('--only') + 1] if '--only' in sys.argv else ''
    k = key(); today = datetime.date.today().isoformat()
    dump = lambda o: json.dumps(o, ensure_ascii=False, separators=(',', ':'))
    meta_p = OUT / 'meta.json'; meta = json.loads(meta_p.read_text(encoding='utf-8'))
    if only in ('', 'pills'):
        P = pills(k)
        if len(P) < 15000: sys.exit(f'낱알 {len(P)}건 — 너무 적어 기존 자료를 그대로 둡니다')
        (OUT / 'pills.json').write_text(dump([x for x in P if not x['rx']]), encoding='utf-8')
        (OUT / 'pills-rx.json').write_text(dump([x for x in P if x['rx']]), encoding='utf-8')
        meta.update({'pills_count': len(P), 'pills_otc': sum(1 for x in P if not x['rx']), 'pills_source': f'식약처 의약품 낱알식별 정보 OpenAPI {today}'})
        print(f'낱알 {len(P):,}건(약국 약 {meta["pills_otc"]:,})')
    if only in ('', 'permits'):
        R = permits(k)
        if len(R) < 20000: sys.exit(f'허가 목록 {len(R)}건 — 너무 적어 기존 자료를 그대로 둡니다')
        (ROOT / 'tools' / 'permits.json').write_text(dump(R), encoding='utf-8')   # 앱에 싣지 않음 — build.py 가 이름 목록·성분 채우기에만 씀
        meta.update({'permits_count': len(R), 'permits_source': f'식약처 의약품 제품 허가정보 OpenAPI {today}'})
        print(f'허가 제품(정상) {len(R):,}건')
    if only in ('', 'easy'):
        try:   # e약은요가 실패해도 위 자료는 그대로 쓴다(옛 e약은요 파일은 다 받은 뒤에만 바꾼다)
            pm = ROOT / 'tools' / 'permits.json'
            PR = R if only == '' else (json.loads(pm.read_text(encoding='utf-8')) if pm.exists() else [])
            E = easy(k, PR)
            if len(E) < 4000: sys.exit(f'e약은요 {len(E)}건 — 너무 적어 기존 자료를 그대로 둡니다')
            CH = 200
            for old in OUT.glob('easy-*.json'): old.unlink()
            (OUT / 'easy-index.json').write_text(dump([{'n': e['n'], 'm': e['m'], 'i': e['i'], 'map': e['map'], 'img': e['img'], 'cvs': e['cvs'], 'seq': e['seq'], 'id': i} for i, e in enumerate(E)]), encoding='utf-8')
            for c in range(0, len(E), CH):
                (OUT / f'easy-{c // CH}.json').write_text(dump([{kk: v for kk, v in e.items() if kk in ('e', 'u', 'c', 'x', 's', 'k')} for e in E[c:c + CH]]), encoding='utf-8')
            meta.update({'easy_count': len(E), 'with_image': sum(1 for e in E if e['img']), 'easy_source': f'식약처 의약품개요정보(e약은요) OpenAPI {today}', 'chunk': CH})
            print(f'e약은요 {len(E):,}건(성분 붙음 {sum(1 for e in E if e["i"]):,}) — 성분→약 연결은 remap_easy.py 가 다시 맞춤')
        except (Exception, SystemExit) as e:
            print('e약은요 받기 실패 — 옛 자료 그대로:', e)
    if only in ('', 'quasi'):
        try:   # 의약외품은 있으면 좋은 것 — 실패해도 위 두 자료는 그대로 쓴다
            Q = quasi(k)
            (ROOT / 'tools' / 'quasi.json').write_text(dump(Q), encoding='utf-8')   # 앱에 아직 싣지 않음 — 갈래(CLASS_NO_NAME)를 보고 넣을 것을 고른다
            meta.update({'quasi_count': len(Q), 'quasi_source': f'식약처 의약외품 제품 허가 정보 OpenAPI {today}'})
            print(f'의약외품(정상) {len(Q):,}건')
        except (Exception, SystemExit) as e:
            print('의약외품 받기 실패 — 건너뜀:', e)
    meta_p.write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding='utf-8')


if __name__ == '__main__':
    main()
