"""약 상자 바코드 조각 만들기(11-18) — 심평원 약가마스터 «의약품표준코드» CSV → 업체별 조각 JSON.
쓰는 법: python3 yakjido/tools/barcode_build.py <CSV 또는 CSV.gz 경로>
 · 원본 CSV 는 공개 저장소에 올리지 않는다(yozm-health _자료/받은함 에 둠). 여기엔 앱에 필요한 열만 뽑은 조각만.
 · 이용허락: 공공데이터포털 15067462 「공공저작물 : 출처표시(제1유형)」 — 출처를 _about.json·화면 「자세히」에 적는다.
 · 거르기: 취소일자 있는 줄 빼기 · 880 으로 시작하는 13자리만 · 전문의약품·일반의약품만(한약재·원료·의약외품 빼기).
 · 조각: docs/yakjido/data/barcode/<업체 4자리>.json = { "p": [[품목기준코드, 제품명, "전|일"], …], "c": { 바코드 뒤 6자리: p 의 번호 } } — 같은 제품의 포장 크기별 바코드가 이름을 한 번만 쓰게
 · 이음 비율: 약지도 자료(e약은요·낱알)의 품목기준코드와 몇 줄이 이어지는지 _about.json 에."""
import sys, gzip, io, csv, json, re, pathlib, collections, datetime
ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT.parent / 'docs' / 'yakjido' / 'data' / 'barcode'   # 배포본에 바로(한 벌만 · build.py 는 이 폴더를 지우지 않고 기내 목록에도 넣지 않음)
src = pathlib.Path(sys.argv[1])
fh = io.TextIOWrapper(gzip.open(src) if src.suffix == '.gz' else open(src, 'rb'), encoding='cp949', errors='replace')
r = csv.reader(fh); h = next(r); I = {k.strip(): i for i, k in enumerate(h)}
need = ['한글상품명', '품목기준코드', '전문일반구분', '표준코드', '취소일자']
miss = [k for k in need if k not in I]
if miss: sys.exit('열이 없습니다: ' + ', '.join(miss))
D = pathlib.Path(__file__).resolve().parents[2] / 'docs' / 'yakjido' / 'data'
ours = set()
for f in ('easy-index.json', 'pills.json', 'pills-rx.json'):
    try: ours |= {x.get('seq') for x in json.load(open(D / f)) if x.get('seq')}
    except Exception: pass
chunks = collections.defaultdict(dict); n = collections.Counter()
for row in r:
    n['줄'] += 1
    if row[I['취소일자']].strip(): n['취소'] += 1; continue
    code, seq, kind = row[I['표준코드']].strip(), row[I['품목기준코드']].strip(), row[I['전문일반구분']].strip()
    if kind not in ('전문의약품', '일반의약품'): n['약 아님'] += 1; continue
    if not re.fullmatch(r'880\d{10}', code): n['형식 다름'] += 1; continue
    name = re.sub(r'\s+', ' ', row[I['한글상품명']]).strip()[:60]
    chunks[code[3:7]][code] = [seq, name, '전' if kind == '전문의약품' else '일']
    n['담음'] += 1; n['이어짐'] += seq in ours
OUT.mkdir(exist_ok=True)
for old in OUT.glob('*.json'): old.unlink()
size = 0
for k, v in chunks.items():
    P, ix, C = [], {}, {}
    for code, (seq, name, kd) in sorted(v.items()):
        if seq not in ix: ix[seq] = len(P); P.append([seq, name, kd])
        C[code[7:]] = ix[seq]
    s = json.dumps({'p': P, 'c': C}, ensure_ascii=False, separators=(',', ':')); (OUT / f'{k}.json').write_text(s, encoding='utf-8'); size += len(s.encode())
about = {'출처': '건강보험심사평가원_약가마스터_의약품표준코드(공공데이터포털 15067462) · 공공저작물 출처표시(제1유형)', '기준': re.search(r'(\d{8})', src.name).group(1) if re.search(r'(\d{8})', src.name) else '',
         '만든날': datetime.date.today().isoformat(), '세기': dict(n), '조각': len(chunks), '바이트': size, '이어진비율': round(n['이어짐'] / max(1, n['담음']), 3)}
(OUT / '_about.json').write_text(json.dumps(about, ensure_ascii=False, indent=1), encoding='utf-8')
print(json.dumps(about, ensure_ascii=False))
