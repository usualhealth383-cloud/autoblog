#!/usr/bin/env python3
"""식약처 공공데이터 벌크 CSV → 앱용 JSON (content/public/).

입력(두 파일, nedrug.mfds.go.kr '의약품등 정보 → 공공데이터 공개'에서 내려받은 벌크 CSV):
  - e약은요:   OpenData_EasyExcelList*.csv   (제품명·업체명·주성분 + 7문항 평문)
  - 낱알식별:  OpenData_PotOpenTabletIdntfc*.csv (이미지·각인·모양·색·전문/일반)
사용:  python3 yakson/tools/import_public_data.py <easy.csv> <pills.csv>
출력:  docs/yakson/data/easy-index.json + easy-N.json(200건씩), pills.json (일반의약품·안전상비만), meta.json
라이선스: 공공데이터포털 식약처 데이터셋 — 이용허락범위 제한 없음(출처 표시 권장). 이미지 원제작 약학정보원.
"""
import csv, json, re, sys, pathlib
csv.field_size_limit(10**8)
ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT.parent / 'docs' / 'yakson' / 'data'; OUT.mkdir(parents=True, exist_ok=True)  # 배포본이 곧 원본(중복 저장 방지)

# 성분명 → 약손 성분 id (drugs.json 의 id). 복합제는 여러 id 에 매핑된다.
INGR = {
  '아세트아미노펜':'acetaminophen', '이부프로펜':'ibuprofen', '이부프로펜아르기닌':'ibuprofen', '덱시부프로펜':'dexibuprofen',
  '나프록센':'naproxen', '나프록센나트륨':'naproxen', '아스피린':'aspirin', '아스피린장용':'aspirin',
  '세티리진염산염':'cetirizine', '레보세티리진염산염':'cetirizine', '로라타딘':'loratadine', '펙소페나딘염산염':'fexofenadine',
  '클로르페니라민말레산염':'chlorpheniramine', 'd-클로르페니라민말레산염':'chlorpheniramine',
  '슈도에페드린염산염':'pseudoephedrine', '페닐레프린염산염':'phenylephrine', 'dl-메틸에페드린염산염':'methylephedrine',
  '덱스트로메토르판브롬화수소산염수화물':'dextromethorphan', '구아이페네신':'guaifenesin',
  '파모티딘':'famotidine', '알마게이트':'almagate', '인산알루미늄겔':'aluminium-phosphate', '알긴산나트륨':'alginate', '수산화마그네슘':'antacid-mg',
  '산화마그네슘':'magnesium-oxide', '비사코딜':'bisacodyl', '로페라미드염산염':'loperamide', '디옥타헤드랄스멕타이트':'smectite',
  '디펜히드라민염산염':'diphenhydramine', '독시라민숙신산염':'doxylamine', '디멘히드리네이트':'dimenhydrinate', '스코폴라민':'scopolamine',
  '케토프로펜':'ketoprofen', '피록시캄':'piroxicam', '디클로페낙디에틸암모늄':'diclofenac-topical', '디클로페낙나트륨':'diclofenac-topical',
  '록소프로펜나트륨수화물':'loxoprofen', '플루르비프로펜':'flurbiprofen', '살리실산메틸':'methyl-salicylate', 'L-멘톨':'menthol', 'l-멘톨':'menthol',
  '자일로메타졸린염산염':'xylometazoline', '클로르족사존':'chlorzoxazone', '이소프로필안티피린':'ipa', '에텐자미드':'ethenzamide', '카페인무수물':'caffeine',
  '파마브롬':'pamabrom', '퓨시드산나트륨':'fusidic-acid', '무피로신':'mupirocin', '테르비나핀염산염':'terbinafine', '트리암시놀론아세토니드':'triamcinolone',
  '폴리크레줄렌':'policresulen', '판크레아틴':'digestive-enzyme', '시메티콘':'simethicone', '카르복시메틸셀룰로오스나트륨':'artificial-tears', '히알루론산나트륨':'artificial-tears',
}
def norm(s): return re.sub(r'\s+', '', s or '')
def base_name(s): return norm(re.sub(r'\(.*?\)', '', s or ''))

def read(path):
    raw = pathlib.Path(path).read_bytes()
    for enc in ('utf-8-sig', 'cp949', 'euc-kr'):
        try: text = raw.decode(enc); break
        except UnicodeDecodeError: continue
    return list(csv.DictReader(text.splitlines()))

easy_p, pills_p = sys.argv[1], sys.argv[2]
pills_raw = read(pills_p)
pills = []
by_name = {}
for r in pills_raw:
    kind = r.get('전문일반구분', '')
    if not (kind.startswith('일반')): continue
    item = {
        'n': r['품목명'].strip(), 'm': r['업소명'].strip(), 'img': r.get('큰제품이미지', '').strip(),
        'f': (r.get('표시앞') or '').strip().replace('-', ''), 'b': (r.get('표시뒤') or '').strip().replace('-', ''),
        'sh': (r.get('의약품제형') or '').strip(), 'c': (r.get('색상앞') or '').strip(), 'c2': (r.get('색상뒤') or '').strip().replace('-', ''),
        'd': (r.get('성상') or '').strip(), 'cls': (r.get('분류명') or '').strip(), 'cvs': 1 if '안전상비' in kind else 0,
        'sz': (r.get('크기장축') or '').strip(), 'seq': (r.get('품목일련번호') or '').strip(),
    }
    pills.append(item)
    by_name.setdefault(base_name(item['n']), item)

easy = []
for r in read(easy_p):
    ingr = [x.strip() for x in (r.get('주성분') or '').split('|') if x.strip()]
    ids = sorted({INGR[i] for i in ingr if i in INGR})
    def clean(k):
        t = (r.get(k) or '').strip()
        t = t.replace('|', ', ')
        # 문장 끝에서 줄바꿈. 공백 제거본이라 최소한의 가독성만 보강
        t = re.sub(r'\.(?=[가-힣A-Za-z(])', '.\n', t)
        return t
    pill = by_name.get(base_name(r['제품명']))
    easy.append({
        'n': r['제품명'].strip(), 'm': (r.get('업체명') or '').strip(), 'i': ingr, 'map': ids,
        'e': clean('이 약의 효능은 무엇입니까?'), 'u': clean('이 약은 어떻게 사용합니까?'), 'c': clean('이 약의 사용상 주의사항은 무엇입니까?'),
        'x': clean('이 약을 사용하는 동안 주의해야 할 약 또는 음식은 무엇입니까?'), 's': clean('이 약은 어떤 이상반응이 나타날 수 있습니까?'), 'k': clean('이 약은 어떻게 보관해야 합니까?'),
        'img': pill['img'] if pill else '', 'cvs': pill['cvs'] if pill else 0, 'seq': pill['seq'] if pill else '',
    })

dump = lambda o: json.dumps(o, ensure_ascii=False, separators=(',', ':'))
# 검색용 인덱스(가벼움) + 상세는 200건씩 조각으로 — 앱은 필요할 때만 조각을 받는다
CH = 200
for old in OUT.glob('easy-*.json'): old.unlink()
index = [{'n': e['n'], 'm': e['m'], 'i': e['i'], 'map': e['map'], 'img': e['img'], 'cvs': e['cvs'], 'seq': e['seq'], 'id': i} for i, e in enumerate(easy)]
(OUT / 'easy-index.json').write_text(dump(index), encoding='utf-8')
for k in range(0, len(easy), CH):
    (OUT / f'easy-{k // CH}.json').write_text(dump([{kk: v for kk, v in e.items() if kk in ('e', 'u', 'c', 'x', 's', 'k')} for e in easy[k:k + CH]]), encoding='utf-8')
(OUT / 'pills.json').write_text(dump(pills), encoding='utf-8')
meta = {'easy_count': len(easy), 'pills_count': len(pills), 'easy_source': pathlib.Path(easy_p).name, 'pills_source': pathlib.Path(pills_p).name,
        'mapped': sum(1 for e in easy if e['map']), 'with_image': sum(1 for e in easy if e['img']),
        'license': '식품의약품안전처 공공데이터(공공데이터포털) — 이용허락범위 제한 없음, 출처 표시. 낱알 이미지 제작: 약학정보원'}
(OUT / 'meta.json').write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding='utf-8')
meta['chunk'] = CH
(OUT / 'meta.json').write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding='utf-8')
print(meta, 'index', (OUT / 'easy-index.json').stat().st_size // 1024, 'KB', 'pills.json', (OUT / 'pills.json').stat().st_size // 1024, 'KB')
