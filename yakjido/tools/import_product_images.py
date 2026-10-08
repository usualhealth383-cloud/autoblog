#!/usr/bin/env python3
"""제품 «상자» 사진 붙이기 — 연고·겔·파스·시럽·질정까지.

왜 필요한가
  지금 앱이 쓰는 사진은 「의약품 낱알식별 정보」 하나뿐이다. 그 자료에는 **알약만** 들어 있어
  (일반 5,660건, 전부 사진 있음) 볼타렌 에멀겔·케토톱·아시클로버 크림 같은 것은 사진이 아예 없다.
  식약처 「의약품 제품 허가정보」에는 제품 상자 사진 칸이 있으므로, 그것을 받아 붙인다.

받는 곳 (둘 중 편한 쪽)
  A) 벌크 CSV — nedrug.mfds.go.kr → 의약품등 정보 → 공공데이터 공개 → 「의약품 제품 허가정보」
  B) OpenAPI  — data.go.kr/data/15095677/openapi.do (인증키 필요, 무료)
  ※ 약학정보원(health.kr) 사진은 공공누리가 아니다. 저작권 확인 없이 쓰지 않는다.

쓰는 법
  python3 yakjido/tools/import_product_images.py <허가정보.csv>          # 붙이기
  python3 yakjido/tools/import_product_images.py <허가정보.csv> --peek   # 컬럼 이름만 보기

컬럼 이름이 자료마다 달라서, 이미지처럼 보이는 칸을 스스로 찾아 보고한다.
붙인 결과는 content/productImages.json 에 «box» 로 들어가고, 낱알 사진보다 뒤에 쓰인다.
출처 표시: 식품의약품안전처 의약품 제품 허가정보(공공누리 제1유형).
"""
import csv, json, re, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from pharmform import formclass
csv.field_size_limit(10**8)
ROOT = pathlib.Path(__file__).resolve().parent.parent

def read(path):
    raw = pathlib.Path(path).read_bytes()
    for enc in ('utf-8-sig', 'cp949', 'euc-kr'):
        try: return list(csv.DictReader(raw.decode(enc).splitlines()))
        except UnicodeDecodeError: continue
    raise SystemExit('인코딩을 읽지 못했습니다 — utf-8/cp949/euc-kr 이 아닙니다')

def norm(s):
    s = re.sub(r'\(.*?\)', '', str(s or ''))
    return re.sub(r'[\s·,／/]+', '', s).lower()

def pick_cols(rows):
    """이미지 URL 칸과 제품명 칸을 스스로 찾는다."""
    keys = list(rows[0].keys()) if rows else []
    img = [k for k in keys if re.search(r'이미지|IMG|IMAGE', k, re.I)]
    name = [k for k in keys if re.search(r'품목명|제품명|ITEM_NAME|PRDT', k, re.I)]
    return img, name, keys

def main():
    if len(sys.argv) < 2: raise SystemExit(__doc__)
    rows = read(sys.argv[1])
    img_cols, name_cols, keys = pick_cols(rows)
    if '--peek' in sys.argv or not img_cols or not name_cols:
        print('컬럼', len(keys), '개:'); print(' · '.join(keys))
        print('\n이미지로 보이는 칸:', img_cols or '없음')
        print('제품명으로 보이는 칸:', name_cols or '없음')
        if not img_cols: print('\n→ 이미지 칸이 없습니다. 다른 자료를 받아야 합니다(위 설명 참고).')
        return
    IMG, NAME = img_cols[0], name_cols[0]
    print(f'이미지 칸 「{IMG}」 · 제품명 칸 「{NAME}」 로 읽습니다')

    box = {}
    for r in rows:
        u = (r.get(IMG) or '').strip()
        if not u.startswith('http'): continue
        box.setdefault(norm(r.get(NAME)), (r.get(NAME, '').strip(), u))
    print(f'사진이 있는 제품 {len(box):,}건')

    drugs = [x for f in sorted(ROOT.glob('content/drugs*.json'))
             for x in json.loads(f.read_text(encoding='utf-8'))]
    out_p = ROOT / 'content' / 'productImages.json'
    out = json.loads(out_p.read_text(encoding='utf-8')) if out_p.exists() else {}
    added = 0
    for d in drugs:
        for pr in (d.get('products') or []):
            raw = str(pr.get('name') or '').strip()
            if not raw or raw in out: continue          # 낱알 사진이 이미 있으면 그대로 둔다
            key = norm(raw)
            hit = box.get(key)
            if not hit:                                  # 앞자리 일치 — 회사 이름이 붙는 일이 많다
                cands = [v for k, v in box.items() if k.startswith(key) or key.startswith(k)]
                cands = [c for c in cands if formclass(c[0]) == formclass(raw)]
                hit = sorted(cands, key=lambda t: len(t[0]))[0] if cands else None
            if hit and formclass(hit[0]) == formclass(raw):
                out[raw] = {'img': hit[1], 'match': hit[0], 'src': 'box'}
                added += 1
    out_p.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding='utf-8')
    print(f'상자 사진 {added}건 새로 붙였습니다 → content/productImages.json (전체 {len(out)}건)')
    print('다음: python3 yakjido/tools/build.py 로 배포본을 다시 만드세요.')

main()
