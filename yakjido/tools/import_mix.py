#!/usr/bin/env python3
"""약손 조합(COMBO) 가운데 «같이 먹어도 되나요» 묶음을 약지도 데이터로 옮긴다.

증상 조합(감기·두통 …)은 import_combo.py 가 다루고, 여기서는 grp 가 「같이 먹기 — …」인
37건을 따로 뽑는다. 약끼리·지병 약·영양제·음식술·사람에 따라 다섯 갈래다.

출력: docs/yakjido/data/mixes.json  (검색을 처음 쓸 때 지연 로드)
성분 id 는 약지도 해설이 있으면 그 id, 없으면 'lex:<약손 id>' 로 둔다.
"""
import json, glob, pathlib, re

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / 'tools' / 'yakson'
OUT = ROOT.parent / 'docs' / 'yakjido' / 'data'
LEXP = OUT / 'lexicon.json'


def main():
    C = json.loads((SRC / 'COMBO.json').read_text(encoding='utf-8'))
    L = {x['id']: x for x in json.loads(LEXP.read_text(encoding='utf-8'))}
    mine = set()
    for f in sorted(glob.glob(str(ROOT / 'content' / 'drugs*.json'))):
        for d in json.loads(pathlib.Path(f).read_text(encoding='utf-8')):
            mine.add(d['id'])

    def opt(iid):
        x = L.get(iid)
        if not x:
            return None
        return x['drug'] if (x.get('drug') and x['drug'] in mine) else 'lex:' + iid

    clean = lambda t: re.sub(r'«(.+?)»', r'**\1**', str(t or '')).strip()
    def sentence(t):
        """약손의 한 줄 설명은 «…겹치는» 처럼 꾸미는 말로 끝난다.
           목록에서는 읽히지만 상세 화면에서는 문장이 잘린 것처럼 보여서 끝을 맺어 준다."""
        t = clean(t)
        return t if (not t or re.search(r'(요|다|\.|!|\?)$', t)) else t + ' 경우예요.'
    out = []
    for c in C:
        grp = c.get('grp', '')
        if not grp.startswith('같이 먹기'):
            continue
        kind = grp.split('—')[-1].strip() if '—' in grp else '기타'
        items = []
        for iid, why in (c.get('first') or []) + (c.get('add') or []):
            o = opt(iid)
            if not o:
                continue
            items.append({'id': o, 'n': L[iid]['n'], 'why': clean(why), 'rx': L[iid]['rx']})
        out.append({
            'id': c['id'], 'kind': kind, 't': c['t'], 's': sentence(c['s']),
            'kw': c.get('kw') or [],
            'items': items,
            'how': [clean(t) for t in (c.get('pharm') or [])],
            'avoid': [clean(t) for t in (c.get('avoid') or [])],
            'days': clean(c.get('days')), 'fail': clean(c.get('fail')),
            'red': [clean(t) for t in (c.get('red') or [])],
            'ask': clean(c.get('ask')),
            'dr': clean((c.get('dr') or {}).get('text')) if c.get('dr') else '',
            'src': c.get('src') or [],
        })
    p = OUT / 'mixes.json'
    p.write_text(json.dumps(out, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    print(f'mixes.json {len(out)}건  {p.stat().st_size / 1024:.0f} KB')
    import collections
    for k, n in collections.Counter(x['kind'] for x in out).most_common():
        print(f'  {k:10} {n}건')
    meta = OUT / 'meta.json'
    m = json.loads(meta.read_text(encoding='utf-8'))
    m['mixes_count'] = len(out)
    meta.write_text(json.dumps(m, ensure_ascii=False, indent=1), encoding='utf-8')


if __name__ == '__main__':
    main()
