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


def main():
    src = {}
    for f in sorted((ROOT / 'content').glob('sources*.json')): src.update(json.loads(f.read_text(encoding='utf-8')))
    drugs = []
    for f in sorted((ROOT / 'content').glob('drugs*.json')):
        v = json.loads(f.read_text(encoding='utf-8')); drugs += v if isinstance(v, list) else v.get('drugs', [])
    out = json.loads((DATA / 'kpic-extra.json').read_text(encoding='utf-8')) if (DATA / 'kpic-extra.json').exists() else {}
    rep = {}
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
    (DATA / 'kpic-extra.json').write_text(json.dumps(out, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    (ROOT / 'content' / 'drugRep.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print('대표 제품', len(rep))


if __name__ == '__main__':
    main()
