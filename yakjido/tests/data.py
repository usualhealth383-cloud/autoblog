#!/usr/bin/env python3
"""약지도 자료 무결성 — 브라우저 없이 1초. 끊긴 고리를 잡는다.
  · 증상 계획(plan)의 options/pick → 약 id 가 실제로 있는가 (lex:… 는 사전 항목이라 제외)
  · sources 키 → sources.json 에 있는가 (증상·약·계열·영양제·병용 규칙)
  · 계열 members → 약 id, 약의 class → 계열 id
  · 팁 link → 존재하는 화면인가
  · 병용 규칙 organ 아이콘 이름 → app-shell 의 I.* 에 있는가
"""
import json, glob, pathlib, re, sys
ROOT = pathlib.Path(__file__).resolve().parents[1]
C = ROOT / 'content'
def load(pat):
    out = []
    for f in sorted(glob.glob(str(C / pat))): out += json.load(open(f, encoding='utf-8'))
    return out
S, D, K, T = load('symptoms*.json'), load('drugs*.json'), load('classes*.json'), load('tips*.json')
SUP = json.load(open(C / 'supplements.json', encoding='utf-8'))
SRC = {}
for f in sorted(glob.glob(str(C / 'sources*.json'))): SRC.update(json.load(open(f, encoding='utf-8')))   # 빌드와 같이 part 파일을 합친다
IX = json.load(open(C / 'interactions.json', encoding='utf-8'))
ING = json.load(open(C / 'ingredients.json', encoding='utf-8'))
shell = (ROOT / 'app-shell.html').read_text(encoding='utf-8')
icons = set(re.findall(r"\bI\.(\w+)\s*=", shell)) | set(re.findall(r"^\s*(\w+):\s*'<svg", shell, re.M))
sid, did, kid, supid = {s['id'] for s in S}, {d['id'] for d in D}, {k['id'] for k in K}, {x['id'] for x in SUP}
quick = {f"{g['id']}" for g in ING.get('quick', [])} | {s['id'] for g in ING.get('quick', []) for s in g.get('subs', [])}
fails = []
def src_ok(owner, ids):
    for x in ids or []:
        if x not in SRC: fails.append(f'출처 없음 {owner} → {x}')
for s in S:
    for p in s.get('plan', []):
        for o in (p.get('options') or []) + ([p['pick']] if p.get('pick') else []):
            if o and not o.startswith('lex:') and o not in did: fails.append(f'증상 {s["id"]} 계획 약 없음 → {o}')
    src_ok('증상 ' + s['id'], s.get('sources'))
    if not s.get('care', {}).get('er'): fails.append(f'증상 {s["id"]} 응급 신호 없음')
for d in D:
    if d.get('class') not in kid: fails.append(f'약 {d["id"]} 계열 없음 → {d.get("class")}')
    for c in d.get('contains') or []:
        if c not in did: fails.append(f'약 {d["id"]} contains 없음 → {c}')
    src_ok('약 ' + d['id'], d.get('sources'))
for k in K:
    for m in k.get('members') or []:
        if m not in did: fails.append(f'계열 {k["id"]} member 없음 → {m}')
    src_ok('계열 ' + k['id'], k.get('sources'))
for x in SUP: src_ok('영양제 ' + x['id'], x.get('sources'))
for r in IX['rules']:
    src_ok('규칙 ' + r['id'], r.get('src'))
    if not r.get('organ') or r['organ']['ico'] not in icons: fails.append(f'규칙 {r["id"]} 장기 아이콘 없음 → {r.get("organ")}')
    if not re.search(r'\*\*', r.get('why', '') + r.get('do', '')): pass
def route_ok(link):
    m = re.match(r'^/(symptom|drug|class|supp|kinds|tips|me|schedule|pill|photo|together|bag|kids|mix|about|drugs|hello)(?:/([^?]+))?', link or '')
    if not m: return False
    kind, x = m.group(1), m.group(2)
    if kind == 'symptom': return x in sid
    if kind == 'drug': return x in did
    if kind == 'class': return x in kid
    if kind == 'supp': return x is None or x in supid
    if kind == 'kinds': return x is None or x in quick
    return True
for t in T:
    if t.get('link') and not route_ok(t['link']): fails.append(f'팁 {t["id"]} 링크 없음 → {t["link"]}')
    if not t.get('link'): fails.append(f'팁 {t["id"]} 링크 비어 있음(갈 곳을 달아 주세요)')
print(f'증상 {len(S)} · 약 {len(D)} · 계열 {len(K)} · 영양제 {len(SUP)} · 팁 {len(T)} · 규칙 {len(IX["rules"])} · 출처 {len(SRC)}')
if fails:
    print('실패', len(fails)); [print('  ✗', f) for f in fails]; sys.exit(1)
print('✓ 자료 고리 전부 연결')
