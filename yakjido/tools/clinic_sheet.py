#!/usr/bin/env python3
"""진료 대조표 — 53개 증상의 「병원에서는」 한 줄만 모아 둔 검수용 문서.

현욱님이 폰에서 훑어보고 틀린 줄만 번호로 짚으시라고 만든다.
사용: python3 yakjido/tools/clinic_sheet.py  →  yakjido/진료-대조표.md
"""
import json, glob, re, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
syms = []
for f in sorted(glob.glob(str(ROOT / 'content' / 'symptoms*.json'))):
    syms += json.loads(pathlib.Path(f).read_text(encoding='utf-8'))
drugs = {}
for f in sorted(glob.glob(str(ROOT / 'content' / 'drugs*.json'))):
    for d in json.loads(pathlib.Path(f).read_text(encoding='utf-8')): drugs[d['id']] = d

plain = lambda t: re.sub(r'\*\*', '', str(t or '')).strip()
groups = {}
for s in syms: groups.setdefault(s.get('group', '기타'), []).append(s)

out = ['# 진료 대조표 — 「병원에서는」 53줄', '',
       '현욱님이 훑어보시라고 만든 표입니다. **병원에서는** 칸만 모아 두었습니다.',
       '틀린 줄만 번호로 알려 주시면(예: 12번 — 이건 이렇게 처방한다) 그대로 고치겠습니다.',
       '약국 칸과 화면 전체는 `계획-약-대조표.md`에 있습니다.', '']
n = 0
for g, ss in groups.items():
    out += [f'## {g}', '']
    for s in ss:
        n += 1
        rx = [drugs[o]['name'] for p in s.get('plan', []) for o in p.get('options', [])
              if o in drugs and drugs[o].get('rx') == '전문']
        out.append(f"**{n}. {s['name']}**" + (' · **검수 대기**' if s.get('reviewed') is False else ''))
        out.append('> ' + (plain((s.get('triage') or {}).get('clinic')) or '(비어 있음)'))
        if rx: out.append('  \n  화면에 있는 처방약: ' + ', '.join(dict.fromkeys(rx)))
        out.append('')
(ROOT / '진료-대조표.md').write_text('\n'.join(out), encoding='utf-8')
print(f'진료-대조표.md — {n}줄')
