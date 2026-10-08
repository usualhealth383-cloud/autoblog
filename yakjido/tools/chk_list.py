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

out = ['# [확인 필요] 목록 — 원문을 확인하지 못한 값들', '',
       f'모두 **{len(rows)}곳**입니다. 화면에는 회색 칩으로 「확인 필요」라고 떠 있습니다.',
       '원문을 못 본 값을 «맞다»고 적지 않는 것이 원칙이라 이렇게 두었습니다.',
       '아시는 값은 알려 주시면 바로 채우고, 나머지는 원문을 받는 대로 채웁니다.', '',
       '| 어디 | 무엇 | 칸 | 문장 |', '|---|---|---|---|']
for k in sorted(by):
    for b, c, t in by[k]:
        out.append(f"| {k} | {b} | {c} | {t.replace('|', '·')[:120]} |")

(ROOT / '확인필요-목록.md').write_text('\n'.join(out) + '\n', encoding='utf-8')
print(f'확인필요-목록.md — {len(rows)}곳')
