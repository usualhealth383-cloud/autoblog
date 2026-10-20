#!/usr/bin/env python3
"""법 문서(app/legal/*.html) 번호 검사 — 항목을 끼워 넣다가 ①②… 순서·문장이 깨지는 것을 막는다.

2026-10-13: 개인정보처리방침 3절에 ⑯을 끼워 넣다가 ⑮ 문장이 잘려 이어 붙은 일이 있었다(GPT 검수 #5).
· 장(h4) 제목 번호: 1. 2. 3의2. … 또는 제1조 제8조의2 … 가 차례대로인가(법령 관례대로 '3' 다음 '3의2')
· 각 장 안에서 줄 첫머리 ①②③… 가 ①부터 하나씩 늘어나는가('⑪의1 ⑪의2'처럼 '의 N' 붙은 하위 항목은 허용)
· 한 줄 가운데에 다른 항목 번호가 끼어 있지 않은가(줄 첫머리가 아닌 ①~⑳ 뒤에 ':' 가 오면 잘린 항목으로 본다)
· 줄이 조사(부터·에서·까지…)로 끝나거나 '파기1년'처럼 끝말 뒤에 숫자가 바로 붙은 곳(잘라 붙인 흔적)
· 【확인 필요】·TODO 같은 채우지 않은 자리(공개 웹 문서로 나감)
· 빈 줄(<br><br>), 끝나지 않은 괄호 · 표 칸은 ' | ' 로 나눠 본다
· 문서 머리 '판'과 앱 TERMS_VER(가입 때 계정에 남는 판)이 같은가
마지막 줄: LEGAL OK / LEGAL FAIL
사용: python3 tools/legal_check.py [파일 ...]
"""
import re, sys, glob, pathlib
from bs4 import BeautifulSoup

ROOT = pathlib.Path(__file__).resolve().parent.parent
CIRC = '①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳'
files = sys.argv[1:] or sorted(glob.glob(str(ROOT / 'app/legal/*.html'))) + [str(ROOT / 'app/consent.html')]
bad = []

def head_key(t):
    m = re.match(r'\s*(?:제\s*)?(\d+)\s*(?:조)?\s*(?:의\s*(\d+))?', t)
    return (int(m.group(1)), int(m.group(2) or 0)) if m and m.group(1) else None

for f in files:
    name = pathlib.Path(f).name
    raw = pathlib.Path(f).read_text(encoding='utf-8')
    for m in re.finditer(r'[【\[]\s*확인 필요\s*[】\]]|TODO|XXX', raw): bad.append(f'{name}: 채우지 않은 자리 {m.group(0)} — 공개 문서에 나가면 안 됨(초안은 review/gpt/법문서-초안/)')
    if re.search(r'<br>\s*<br>', raw): bad.append(f'{name}: 빈 줄(<br><br>)')
    s = BeautifulSoup(raw, 'html.parser')
    prev = None
    for h in s.find_all('h4'):
        ht = h.get_text(' ', strip=True); k = head_key(ht)
        if k and prev and not (k[0] == prev[0] and (k[1] == prev[1] + 1 or prev[1] == 0 and k[1] == 2) or k[0] == prev[0] + 1 and k[1] == 0):
            bad.append(f'{name}: 장 번호 순서 {prev} → {k} ({ht[:20]})')
        if k: prev = k
        body = []
        for sib in h.find_next_siblings():
            if sib.name == 'h4': break
            for br in sib.find_all('br'): br.replace_with('\n')
            for c in sib.find_all(['td', 'th']): c.insert_after(' | ')   # 표 칸끼리 붙어 '기록처리한'처럼 보이지 않게(2026-10-14 보유 기간 표)
            for tr in sib.find_all('tr'): tr.insert_after('\n')
            for li in sib.find_all(['li', 'p']): li.insert_after('\n')
            body.append(sib.get_text(''))
        lines = [ln.strip() for ln in '\n'.join(body).split('\n') if ln.strip()]
        want, sub = 1, 0
        for ln in lines:
            m = re.match(rf'([{CIRC}])\s*(?:의\s*(\d+))?', ln)
            if m:
                n = CIRC.index(m.group(1)) + 1; k2 = int(m.group(2) or 0)
                if k2:
                    if n != want - 1 or k2 != sub + 1: bad.append(f'{name} [{ht[:16]}]: 하위 항목 {m.group(0)} 순서(앞 항목 {CIRC[want-2] if want > 1 else "없음"}의{sub})')
                    sub = k2
                else:
                    if n != want: bad.append(f'{name} [{ht[:16]}]: {m.group(1)} 자리에 {CIRC[want-1]} 이어야 함 — "{ln[:30]}"')
                    want, sub = n + 1, 0
            for mm in re.finditer(rf'(?<=.)([{CIRC}])(?:의\s*\d+)?\s*[^:：)\s]{{1,25}}\s*[:：]', ln[1:] if m else ln):
                bad.append(f'{name} [{ht[:16]}]: 줄 가운데 항목 번호 {mm.group(1)} — 잘려 이어 붙은 항목? "{ln[:40]}"')
            if re.search(r'(부터|에서|까지|으로|에게|및|또는)$', ln): bad.append(f'{name} [{ht[:16]}]: 줄이 조사로 끝남(잘린 문장?) — "…{ln[-30:]}"')
            if re.search(r'(파기|삭제|지움|보관|처리)\d', ln): bad.append(f'{name} [{ht[:16]}]: 끝말 뒤에 숫자가 붙음(다른 문장이 이어 붙음?) — "{ln[:40]}"')
            if ln.count('(') != ln.count(')'): bad.append(f'{name} [{ht[:16]}]: 괄호 짝 — "{ln[:40]}"')

# 가입 때 계정에 남는 약관 판(TERMS_VER)이 공개 문서 머리의 '판'과 같은가 — 2026-10-14: 문서는 10-13 판인데 앱은 10-02 를 남기고 있었다
_shell = (ROOT / 'app/app-shell.html').read_text(encoding='utf-8'); _tv = re.search(r"const TERMS_VER = '([0-9-]+)'", _shell)
for nm in ('privacy.html', 'terms.html'):
    _m = re.search(r'판 ([0-9]{4}-[0-9]{2}-[0-9]{2})', (ROOT / 'app/legal' / nm).read_text(encoding='utf-8'))
    if _tv and _m and _m.group(1) != _tv.group(1): bad.append(f'{nm}: 문서 판 {_m.group(1)} ≠ 앱 TERMS_VER {_tv.group(1)}(가입 때 남는 동의 판)')
for b in bad: print('  ✗', b)
print(f'LEGAL {"OK" if not bad else "FAIL"} — 파일 {len(files)}' + (f' · 문제 {len(bad)}' if bad else ''))
sys.exit(1 if bad else 0)
