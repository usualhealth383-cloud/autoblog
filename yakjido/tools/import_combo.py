#!/usr/bin/env python3
"""약손 COMBO(증상별 조합) 가운데 약지도에 없는 증상을 content/symptoms.part6.json 으로 옮긴다.

약손 원본에는 «현욱님 임상 검수 전» 표시가 붙은 항목이 많다. 약지도는 모든 화면에
「전문의 검수」 도장을 달고 있으므로, 검수 전 항목에는 reviewed:false 를 넣어
앱이 도장 대신 「검수 대기」로 표시하게 한다. 검수를 마치면 이 값을 지우면 된다.

성분 연결
 - 약지도가 깊게 쓴 성분이 있으면 그 id 를 쓴다.
 - 없으면 'lex:<약손 id>' 로 두어 앱이 성분 사전(lexicon)에서 풀어 쓴다.
"""
import json, glob, pathlib, re

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / 'tools' / 'yakson'
LEXP = ROOT.parent / 'docs' / 'yakjido' / 'data' / 'lexicon.json'

# 약지도에 대응 증상이 없어 새로 넣는 것 (손으로 대조해 고름)
NEW = ['sprain', 'tendon', 'plantar', 'coldsore', 'eczema', 'acne', 'vaginitis', 'pms', 'meno', 'fatigue']

GROUP = {'근골격계': '통증', '피부': '알레르기·피부', '여성': '여성 건강', '기타': '수면·기타'}
ICON = {'sprain': 'band', 'tendon': 'band', 'plantar': 'band', 'coldsore': 'cross', 'eczema': 'leaf',
        'acne': 'flower', 'vaginitis': 'drop', 'pms': 'moon', 'meno': 'temp', 'fatigue': 'leaf'}
TAGS = {
    'sprain': ['발목', '삠', '접질', '염좌', '타박상', '멍', '삐끗'],
    'tendon': ['손목', '팔꿈치', '건초염', '테니스엘보', '힘줄', '방아쇠수지', '시큰'],
    'plantar': ['족저근막염', '발뒤꿈치', '발바닥', '첫걸음', '뒤꿈치'],
    'coldsore': ['입술', '물집', '헤르페스', '포진', '입술물집', '따끔'],
    'eczema': ['습진', '아토피', '건조', '가려움', '피부', '각질'],
    'acne': ['여드름', '뾰루지', '좁쌀', '피지', '트러블'],
    'vaginitis': ['질염', '냉', '가려움', '칸디다', '분비물', '외음부'],
    'pms': ['생리전', 'PMS', '월경전증후군', '붓기', '예민', '가슴통증'],
    'meno': ['갱년기', '폐경', '안면홍조', '열감', '식은땀', '홍조'],
    'fatigue': ['피로', '기력', '무기력', '피곤', '만성피로', '기운없'],
}


def main():
    C = {c['id']: c for c in json.loads((SRC / 'COMBO.json').read_text(encoding='utf-8'))}
    L = {x['id']: x for x in json.loads(LEXP.read_text(encoding='utf-8'))}
    mine = set()
    for f in sorted(glob.glob(str(ROOT / 'content' / 'drugs*.json'))):
        for d in json.loads(pathlib.Path(f).read_text(encoding='utf-8')):
            mine.add(d['id'])

    def opt(iid):
        """약손 성분 id → 약지도 조합에서 쓸 id"""
        x = L.get(iid)
        if x and x.get('drug') and x['drug'] in mine:
            return x['drug']
        return 'lex:' + iid if x else None

    def clean(t):
        return re.sub(r'«(.+?)»', r'**\1**', str(t or '')).strip()

    out = []
    for sid in NEW:
        c = C[sid]
        src = c.get('src') or []
        reviewed = not any(('검수 전' in s) or ('검수 필요' in s) for s in src)
        plan = []
        for i, (iid, why) in enumerate(c.get('first') or []):
            o = opt(iid)
            if not o:
                continue
            plan.append({'slot': '1순위' if i == 0 else '함께',
                         'title': (L[iid]['n'] if str(o).startswith('lex:') else clean(why).split('—')[0].strip() or L[iid]['n']),
                         'why': clean(why), 'options': [o], 'pick': o})
        # 슬롯 이름은 서로 달라야 한다 — 같은 이름이 겹치면 화면에서 구분이 안 된다
        ADD = ['더할 것', '그다음', '보조']
        for j, (iid, why) in enumerate(c.get('add') or []):
            o = opt(iid)
            if not o:
                continue
            plan.append({'slot': ADD[j] if j < len(ADD) else f'보조{j}',
                         'title': (L[iid]['n'] if str(o).startswith('lex:') else clean(why).split('—')[0].strip() or L[iid]['n']),
                         'why': clean(why), 'options': [o], 'pick': o, 'optional': True})
        dr = c.get('dr')
        if dr:
            # 처방 슬롯에는 «전문의약품만» 넣는다. 약손 dr.items 에는 otc 도 섞여 있어
            # 그대로 쓰면 일반의약품이 '처방 필요'로 잘못 표시된다.
            opts = [opt(i) for i, k in (dr.get('items') or []) if k == 'rx']
            opts = [o for o in opts if o]
            if opts:
                plan.append({'slot': '처방', 'title': '병원에서는 이렇게 합니다',
                             'why': clean(dr.get('text')), 'options': opts, 'otc': False})
        s = {
            'id': sid, 'group': GROUP.get(c['grp'], '수면·기타'), 'icon': ICON.get(sid, 'pill'),
            'name': c['t'], 'short': c['s'], 'tags': TAGS.get(sid, []),
            'lead': clean(c.get('pharm', [''])[0]),
            'planTitle': c['t'] + ' — 이렇게 하세요', 'planLabel': c['s'],
            'plan': plan,
            'how': [clean(t) for t in (c.get('pharm') or [])[1:3]] or [clean(c.get('days'))],
            'pharmacy': ([clean(c.get('ask'))] if c.get('ask') else []) + [clean(t) for t in (c.get('pharm') or [])[3:5]],
            'selfcare': [clean(t) for t in (c.get('pharm') or [])[1:]][:4],
            'avoid': [clean(t) for t in (c.get('avoid') or [])],
            'notWorking': {'title': '나아지지 않으면', 'steps': [t for t in [clean(c.get('days')), clean(c.get('fail'))] if t]},
            'care': {'pharmacy': [c['s']], 'clinic': [clean(c.get('fail'))] if c.get('fail') else [],
                     'er': [clean(t) for t in (c.get('red') or [])]},
            'faq': [],
            'srcText': src,
        }
        if not reviewed:
            s['reviewed'] = False
        out.append(s)

    p = ROOT / 'content' / 'symptoms.part6.json'
    p.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding='utf-8')
    print(f'symptoms.part6.json {len(out)}건')
    for s in out:
        lex = sum(1 for pl in s['plan'] for o in pl['options'] if str(o).startswith('lex:'))
        print(f"  {'검수대기' if s.get('reviewed') is False else '검수완료'}  {s['id']:10} {s['name']:22} 슬롯 {len(s['plan'])} (사전성분 {lex})")


if __name__ == '__main__':
    main()
