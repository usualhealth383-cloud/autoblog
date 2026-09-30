#!/usr/bin/env python3
"""약 사전 성분의 대표 제품 — 제품 목록이 「콜히친 정제」처럼 이름이 없는 성분도 「약사 안내」를 달게.

허가사항 출처(label_<성분>, 의약품안전나라 제품 상세 itemSeq)를 대표 제품으로 삼아 약학정보원 복약정보를 받아
docs/yakjido/data/kpic-extra.json {seq: {...}} 과 content/drugRep.json {성분 id: [seq, 제품 이름]} 에 적는다.
(수집 중인 kpic-guide.json 과 따로 둬 서로 덮어쓰지 않게. build.py 가 둘을 합쳐 조각낸다)
"""
import json, pathlib, re, sys, time
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from kpic_photos import Kpic, names
from kpic_detail import detail, pack

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT.parent / 'docs' / 'yakjido' / 'data'

# 허가사항 출처가 없거나 그 제품이 약학정보원에 없는 성분 — 제품 목록에 적힌 제품을 직접 찾는다.
# (찾을 말, 제품 이름에 들어갈 말, 약학정보원 성분표(sunbcontent)에 반드시 있어야 할 성분) — 성분이 안 맞으면 붙이지 않는다.
MANUAL = {
    'chlorzoxazone': ('신신플렉스', '신신플렉스정', 'chlorzoxazone'),
    'relax-combo': ('리렉스담', '리렉스담정', 'chlorzoxazone'),
    'albendazole': ('다산알벤다졸', '다산알벤다졸정', 'albendazole'),
    'flurbiprofen': ('스트렙실', '스트렙실', 'flurbiprofen'),
    'chlorpheniramine': ('판콜에이', '판콜에이내복액', 'chlorpheniramine'),
    'phenylephrine': ('판콜에이', '판콜에이내복액', 'phenylephrine'),
    'pseudoephedrine': ('슈다페드', '슈다페드정', 'pseudoephedrine'),
    'artificial-tears': ('리프레쉬', '리프레쉬플러스', 'carboxymethylcellulose'),
    'tylenol-cold': ('타이레놀콜드', '타이레놀콜드에스정', 'acetaminophen'),
    'oxytetracycline-eye': ('테라마이신', '테라마이신안연고', 'oxytetracycline'),
    'colchicine': ('콜킨', '콜킨정', 'colchicine'),
    'allopurinol': ('자이로릭', '자이로릭정', 'allopurinol'),
    'azithromycin': ('아지트로마이신', '지스로맥스정250mg', 'azithromycin'),
    'cyclobenzaprine': ('cyclobenzaprine', '시클펜정', 'cyclobenzaprine'),
    'udca': ('우루사정', '우루사정100', 'ursodeoxycholic'),
    'urea-cream': ('유리아크림', '한미유리아크림', 'urea'),
    'eye-decongestant': ('나조린', '나조린점안액', 'naphazoline'),
    'allergy-eyedrop': ('알러콘', '알러콘점안액', 'ketotifen'),
    'oral-contraceptive': ('에이리스', '에이리스정', 'levonorgestrel'),
    'clonixin': ('클로나인', '클로나인연질캡슐', 'clonixin'),
    'vitamin-d-rx': ('디맥', '디맥정7000IU', 'cholecalciferol'),
}


def manual(k, out, rep):
    for did, (word, pick, ingr) in MANUAL.items():
        if did in rep: continue
        try: res = k.search(word)
        except Exception as e: print(did, '검색 실패', e); continue
        hit = [r for r in res if pick in str(r.get('drug_name', '')) and str(r.get('kfda_code', '')).strip()]
        time.sleep(0.4)
        if not hit: print(did, '— 제품 없음', word); continue
        seq = str(hit[0]['kfda_code']).strip()
        try: dd = detail(k, hit[0]['drug_code'])
        except Exception as e: print(did, '상세 실패', e); continue
        time.sleep(0.4)
        if not dd or ingr not in str(dd.get('sunbcontent', '')).lower().replace(' ', ''):
            print(did, '— 성분 불일치', hit[0]['drug_name'], str((dd or {}).get('sunbcontent', ''))[:80]); continue
        out[seq] = pack(dd)
        if out[seq].get('t') or out[seq].get('g'):
            n = len([x for x in str(dd.get('sunbcontent', '')).split('#') if x.strip()])   # 성분 수 — 복합제면 화면에 알린다
            rep[did] = [seq, hit[0]['drug_name']] + ([n] if n > 1 else []); print(did, seq, hit[0]['drug_name'], '✓', flush=True)


def main():
    src = {}
    for f in sorted((ROOT / 'content').glob('sources*.json')): src.update(json.loads(f.read_text(encoding='utf-8')))
    drugs = []
    for f in sorted((ROOT / 'content').glob('drugs*.json')):
        v = json.loads(f.read_text(encoding='utf-8')); drugs += v if isinstance(v, list) else v.get('drugs', [])
    out = json.loads((DATA / 'kpic-extra.json').read_text(encoding='utf-8')) if (DATA / 'kpic-extra.json').exists() else {}
    # 이미 찾은 대표 제품은 지킨다 — 한 번 검색이 실패(네트워크)했다고 빠지면 「약사 안내」 탭이 사라진다
    repf = ROOT / 'content' / 'drugRep.json'
    rep = json.loads(repf.read_text(encoding='utf-8')) if repf.exists() else {}
    k = Kpic()
    for d in drugs:
        s = src.get('label_' + d['id'].replace('-', '_'))
        if not s: continue
        m = re.search(r'itemSeq=(\d+)', s.get('url', '')); name = re.sub(r'^식약처 허가사항 — ', '', s.get('label', '')).split(' (')[0].strip()
        if not m or not name: continue
        seq = m.group(1)
        if seq not in out:
            got = None
            for w in names(name):
                try: res = k.search(w)
                except Exception: time.sleep(3); continue
                hit = [r for r in res if str(r.get('kfda_code', '')).strip() == seq]
                time.sleep(0.4)
                if hit:
                    try: dd = detail(k, hit[0]['drug_code']); got = pack(dd) if dd else None
                    except Exception: got = None
                    break
            out[seq] = got or {}
        if out[seq]: rep[d['id']] = [seq, re.sub(r'\(.*?\)', '', name).strip()]
        print(d['id'], seq, name, '✓' if out[seq] else '—', flush=True)
    manual(k, out, rep)
    (DATA / 'kpic-extra.json').write_text(json.dumps(out, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    (ROOT / 'content' / 'drugRep.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print('대표 제품', len(rep))


if __name__ == '__main__':
    main()
