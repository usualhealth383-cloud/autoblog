#!/usr/bin/env python3
"""약손 세션의 성분·제품·질문·영양제 사전을 약지도 데이터로 옮긴다.

원본: yakjido/tools/yakson/*.json  (약손 검토본 아티팩트 2026-09-08판에서 추출)
출력: docs/yakjido/data/{lexicon,brands,qa,nutrients}.json  — 앱이 검색을 처음 쓸 때 지연 로드한다.

하는 일
 1) 약지도가 이미 깊게 쓴 성분(content/drugs*.json)과 이름·영문명으로 맞춰 `drug` 링크를 단다.
    링크가 있으면 앱은 /ingr/ 대신 /drug/ 상세로 보낸다.
 2) 일반·전문 분류를 식약처 공공데이터(pills.json·pills-rx.json·easy-index.json)와 대조해 정정한다.
 3) 영양제도 같은 방식으로 약지도 supplements 와 연결한다.
"""
import json, glob, re, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent      # yakjido/
SRC  = ROOT / 'tools' / 'yakson'
OUT  = ROOT.parent / 'docs' / 'yakjido' / 'data'

# 식약처 공공데이터 대조로 확인한 정정 (import 시점에 재확인 가능하도록 근거를 함께 적는다)
FIX = {
    'p_tol': ('rx',  '식약처 e약은요에 일반의약품이 없어 전문으로 바로잡았어요'),
    'p_mcb': ('rx',  '식약처 e약은요에 일반의약품이 없어 전문으로 바로잡았어요'),
    'r_bpp': ('otc', '식약처 낱알식별에 일반의약품(투렌정)이 있어 일반으로 바로잡았어요'),
}
NOTE = {
    'pse': '단일제는 전문의약품이에요. 약국에서는 종합감기약 등 복합제 형태로만 살 수 있습니다(식약처 e약은요 확인).',
}
RXW = {'otc': '일반', 'rx': '전문', 'both': '둘 다'}


def load(name):
    return json.loads((SRC / f'{name}.json').read_text(encoding='utf-8'))


def yakjido_drugs():
    out = {}
    for f in sorted(glob.glob(str(ROOT / 'content' / 'drugs*.json'))):
        for d in json.loads(pathlib.Path(f).read_text(encoding='utf-8')):
            out[d['id']] = d
    return out


def main():
    ING, BRAND, QADB, NUT = load('ING'), load('BRAND'), load('QADB'), load('NUT')
    mine = yakjido_drugs()
    by_en = {(d.get('en') or '').lower().split('(')[0].strip(): i for i, d in mine.items() if d.get('en')}
    by_nm = {d['name'].split('(')[0].strip(): i for i, d in mine.items()}

    lex = []
    for x in ING:
        k = FIX[x['id']][0] if x['id'] in FIX else x['k']
        link = by_en.get((x.get('en') or '').lower().split('(')[0].strip()) or by_nm.get(x['n'].split('(')[0].strip())
        o = {'id': x['id'], 'n': x['n'], 'en': x.get('en', ''), 'cls': x['cls'], 'rx': RXW[k],
             'use': x.get('use', ''), 'dose': x.get('dose', ''), 'gap': x.get('gap', ''), 'max': x.get('max', ''),
             'care': x.get('care', []), 'inter': x.get('inter', []), 'risk': x.get('risk', {}),
             'preg': x.get('preg', ''), 'kid': x.get('kid', ''), 'ex': x.get('ex', []), 'src': x.get('src', [])}
        if link:
            o['drug'] = link
        if x['id'] in FIX:
            o['fixNote'] = FIX[x['id']][1]
        if x['id'] in NOTE:
            o['fixNote'] = NOTE[x['id']]
        lex.append(o)

    br = [{'n': b['n'], 'rx': RXW[b['k']], 'ing': b.get('ing', []), 'comp': b.get('comp', ''),
           'use': b.get('use', ''), 'how': b.get('how', ''), 'who': b.get('who', '')} for b in BRAND]
    qa = [{'k': q['k'], 'a': q['a'], 'go': q.get('go')} for q in QADB]

    supps = []
    for f in sorted(glob.glob(str(ROOT / 'content' / 'supplements*.json'))):
        supps += json.loads(pathlib.Path(f).read_text(encoding='utf-8'))
    norm = lambda t: re.sub(r'[\s·\-()]|비타민', '', t).lower()
    smap = {}
    for s in supps:
        smap[norm(s['name'])] = s['id']
        for part in re.split(r'[·/]', s['name']):
            smap[norm(part)] = s['id']
    nut = []
    for x in NUT:
        o = {k: x.get(k, '') for k in ('id', 'n', 'what', 'form', 'read', 'tip', 'with', 'ul')}
        o['src'] = x.get('src', [])
        hit = smap.get(norm(x['n'].split('(')[0]))
        if hit:
            o['supp'] = hit
        nut.append(o)

    OUT.mkdir(parents=True, exist_ok=True)
    for name, data in [('lexicon', lex), ('brands', br), ('qa', qa), ('nutrients', nut)]:
        p = OUT / f'{name}.json'
        p.write_text(json.dumps(data, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
        print(f'{name}.json  {len(data):4}건  {p.stat().st_size / 1024:.0f} KB')

    meta = OUT / 'meta.json'
    m = json.loads(meta.read_text(encoding='utf-8')) if meta.exists() else {}
    m.update({'lexicon_count': len(lex), 'brands_count': len(br), 'qa_count': len(qa), 'nutrients_count': len(nut),
              'lexicon_source': '약손 성분·제품 사전(2026-09-08판) — 식약처 허가사항·DUR 기준, '
                                '분류는 식약처 e약은요·낱알식별과 대조해 정정'})
    meta.write_text(json.dumps(m, ensure_ascii=False, indent=1), encoding='utf-8')
    print(f'약지도 상세와 연결: 성분 {sum(1 for x in lex if x.get("drug"))}건 · 영양제 {sum(1 for x in nut if x.get("supp"))}건')


if __name__ == '__main__':
    main()
