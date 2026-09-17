#!/usr/bin/env python3
"""증상 계획의 슬롯 ↔ 실제 약 이름 대조표를 뽑는다.
자동으로 옳고 그름을 가릴 수 없는 자리(예: 화상 물집 칸에 치질 연고가 들어간 사고)를
사람이 한 번에 훑어보기 위한 표다. 새 계획을 넣거나 고치면 이것을 돌려 눈으로 본다.
    python3 yakjido/tools/plan_audit.py > yakjido/계획-약-대조표.md
"""
import json, glob, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = {}
for f in glob.glob(os.path.join(ROOT, 'content', 'drugs*.json')):
    for d in json.load(open(f, encoding='utf-8')): D[d['id']] = d
LX = {}
lex = os.path.join(os.path.dirname(ROOT), 'docs', 'yakjido', 'data', 'lexicon.json')
if os.path.exists(lex):
    o = json.load(open(lex, encoding='utf-8'))
    for x in (o if isinstance(o, list) else o.get('items', [])):
        if isinstance(x, dict) and 'id' in x: LX[x['id']] = x.get('n', '')
def nm(o):
    if o.startswith('lex:'): return LX.get(o[4:], '(사전에 없음) ' + o)
    return D.get(o, {}).get('name', '(약 사전에 없음) ' + o)
print('# 계획 ↔ 약 대조표\n')
print('증상 화면의 각 칸에 실제로 어떤 약이 걸려 있는지 그대로 뽑은 표예요. 칸 제목과 약 이름이 어긋나면 그 자리가 잘못된 것입니다.\n')
n = 0
for f in sorted(glob.glob(os.path.join(ROOT, 'content', 'symptoms*.json'))):
    for s in json.load(open(f, encoding='utf-8')):
        rows = [(pl, o) for pl in s.get('plan', []) for o in pl.get('options', [])]
        if not rows: continue
        print(f"\n## {s['name']}" + ('  · 검수 대기' if s.get('reviewed') is False else ''))
        print('| 칸 | 제목 | 걸린 약 |')
        print('|---|---|---|')
        for pl, o in rows:
            mark = ' ⟨첫 선택⟩' if pl.get('pick') == o else ''
            print(f"| {pl.get('slot','')} | {pl.get('title','').replace('|','·')} | {nm(o)}{mark} |")
            n += 1
print(f"\n---\n\n전부 {n}자리.")
