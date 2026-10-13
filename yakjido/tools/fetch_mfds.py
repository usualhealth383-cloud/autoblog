#!/usr/bin/env python3
"""식약처 공공데이터 OpenAPI 로 낱알식별·의약품 허가 목록을 «최신»으로 받기 (2026-10-13 현욱님 「낱알자료 최신 거 받는 방법」).

왜: 앱의 낱알 자료는 2022-10 벌크 CSV 라 자큐보처럼 그 뒤에 나온 약이 없다. 벌크 CSV 를 내려받던 쪽은 없어졌고,
    공공데이터포털 OpenAPI 두 개가 매달 갱신된다(둘 다 자동 승인·무료·개발 계정 하루 1만 번).
  · 15057639 식품의약품안전처_의약품 낱알식별 정보   — MdcinGrnIdntfcInfoService03/getMdcinGrnIdntfcInfoList03 (약 2만 5천 건)
  · 15095677 식품의약품안전처_의약품 제품 허가정보   — DrugPrdtPrmsnInfoService08/getDrugPrdtPrmsnInq08 (허가된 모든 제품 — 시럽·연고·주사 포함)

인증키: 공공데이터포털 «일반 인증키(Decoding)». ⛔ 파일·대화에 적지 않는다 — 환경변수 DATA_GO_KR_KEY 로만(깃허브 Secrets).
사용:   DATA_GO_KR_KEY=… python3 yakjido/tools/fetch_mfds.py [--only pills|permits]
결과:   docs/yakjido/data/pills.json · pills-rx.json (지금 앱과 같은 꼴) · yakjido/tools/permits.json([품목코드, 이름, 회사, 전문 1/일반 0, 주성분]) · meta.json 출처·날짜
        그다음 python3 yakjido/tools/build.py 가 성분 채우기·이름 목록·건수를 다시 만든다.
"""
import json, os, pathlib, re, sys, time, datetime, urllib.parse, urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT.parent / 'docs' / 'yakjido' / 'data'
BASE = 'https://apis.data.go.kr/1471000/'
PILL_OP = 'MdcinGrnIdntfcInfoService03/getMdcinGrnIdntfcInfoList03'
PERMIT_OP = 'DrugPrdtPrmsnInfoService08/getDrugPrdtPrmsnInq08'
ROWS = 100


def key():
    k = os.environ.get('DATA_GO_KR_KEY', '').strip()
    if not k: sys.exit('DATA_GO_KR_KEY 가 없습니다 — 공공데이터포털 일반 인증키를 환경변수(깃허브 Secrets)로 넣어 주세요')
    return urllib.parse.unquote(k) if '%' in k else k   # Encoding 키를 넣어도 되게


def page(op, n, k):
    q = urllib.parse.urlencode({'serviceKey': k, 'pageNo': n, 'numOfRows': ROWS, 'type': 'json'})
    for i in range(5):
        try:
            with urllib.request.urlopen(urllib.request.Request(BASE + op + '?' + q, headers={'Accept': 'application/json'}), timeout=60) as r:
                raw = r.read().decode('utf-8')
            if raw.lstrip().startswith('<'):   # 키 오류는 XML 로 온다
                msg = re.search(r'<returnAuthMsg>(.*?)</|<resultMsg>(.*?)</', raw)
                raise RuntimeError('API 오류: ' + (next(g for g in msg.groups() if g) if msg else raw[:200]))
            j = json.loads(raw)
            body = j.get('body') or j.get('response', {}).get('body') or {}
            items = body.get('items') or []
            if isinstance(items, dict): items = items.get('item') or []
            if isinstance(items, dict): items = [items]
            return int(body.get('totalCount') or 0), items
        except RuntimeError: raise
        except Exception as e:
            if i == 4: raise
            time.sleep(2 ** i)


def fetch_all(op, k, label):
    total, first = page(op, 1, k)
    out = list(first); pages = (total + ROWS - 1) // ROWS
    print(f'{label}: {total:,}건 · {pages}쪽', flush=True)
    for n in range(2, pages + 1):
        out += page(op, n, k)[1]
        if n % 50 == 0: print(f'  {n}/{pages}쪽', flush=True)
        time.sleep(.05)
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
    meta_p.write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding='utf-8')


if __name__ == '__main__':
    main()
