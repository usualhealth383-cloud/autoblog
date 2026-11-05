#!/usr/bin/env python3
"""[확인 필요] 가 붙은 자리를 전부 모아 검수용 표로 뽑는다.

원문을 못 본 값을 «맞다»고 적지 않는 것이 이 앱의 원칙이라,
그 자리가 어디인지는 늘 한눈에 보여야 한다.

쓰기: python3 yakjido/tools/chk_list.py   (→ yakjido/확인필요-목록.md)
"""
import io, json, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
rows = []
for f in sorted((ROOT / 'content').glob('*.json')):
    if 'sources' in f.name:
        continue
    d = json.load(io.open(f, encoding='utf-8'))

    def walk(o, path, who):
        if isinstance(o, dict):
            nw = o.get('id') or o.get('name') or who
            for k, v in o.items():
                walk(v, path + '/' + k, nw)
        elif isinstance(o, list):
            for v in o:
                walk(v, path, who)
        elif isinstance(o, str) and '[확인 필요]' in o:
            rows.append((f.stem, str(who), path.strip('/'), o.strip()))

    walk(d, '', '')

by = {}
for a, b, c, t in rows:
    by.setdefault(a, []).append((b, c, t))

out = ['# [확인 필요] 목록 — 원문을 확인하지 못한 값들 (내부용)', '',
       '11-05 현욱님 결정: 화면에는 「확인 필요」·「자료 확인 중」 딱지를 띄우지 않는다(사용자를 더 불안하게 함). '
       '원천 2곳 대조를 마치지 못한 항목은 여기 모아 GPT 검수 묶음으로 보낸다. 자료 안에 「[확인 필요]」를 쓰면 data.py 가 막는다.', '',
       f'## 자료 글 속 [확인 필요] — {len(rows)}곳', '',
       '| 어디 | 무엇 | 칸 | 문장 |', '|---|---|---|---|']
for k in sorted(by):
    for b, c, t in by[k]:
        out.append(f"| {k} | {b} | {c} | {t.replace('|', '·')[:120]} |")

lex = json.load(io.open(ROOT.parent / 'docs' / 'yakjido' / 'data' / 'lexicon.json', encoding='utf-8'))
unv = [x for x in lex if x.get('unv')]
out += ['', f'## 성분 사전 — 원천 대조 못 한 항목 {len(unv)}개 (화면 딱지 없음)', '',
        '대부분 약이 아니거나 국내 허가 제품이 없어 허가 문구로 대조할 수 없었던 것.', '',
        '| id | 이름 | 갈래 |', '|---|---|---|']
out += [f"| {x['id']} | {x['n']} | {str(x.get('cls', '')).replace('|', '·')} |" for x in unv]

(ROOT / '확인필요-목록.md').write_text('\n'.join(out) + '\n', encoding='utf-8')
print(f'확인필요-목록.md — 자료 {len(rows)}곳 · 사전 {len(unv)}개')
