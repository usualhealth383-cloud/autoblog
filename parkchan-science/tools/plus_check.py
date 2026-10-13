#!/usr/bin/env python3
"""'시험에 나오는 보강' 쪽 점검(docs/22) — 소단원 하나씩. data/ 는 건드리지 않는다(여러 장을 동시에 써도 안전).

· 자리: 보강 쪽이 첫 STEP 머리(.step-head) 앞 · 보강 쪽 안에 .quickcheck/.q/.step-head/.lab/.anstable 없음 · 폴리오 있음 · CSS(.plus-h) 있음
· 개념 칸: 제목(.psec) · 한 줄 정리(.pkey) · data-concept 가 그 소단원 개념 수 안
· 문항: 번호 1..N 이어짐 · 해설(.psol) 짝 · 형식별 정답(선지형 ①~⑤ 그리고 선지 5개, OX 는 O/X, 빈칸은 발문에 ＿＿＿, 합답형은 <보기> ㄱ)
        · 선지형·합답형 바로알기(.wrongbox) · 개수(문항 6~10, 개념 2~4) · 형식 섞임
· 글: 숫자와 단위 붙여 쓰기('9.8m/s'), 겹낫표·겹화살괄호
사용: python3 tools/plus_check.py book/chapter-08/chapter.html      끝 줄 PLUS OK / PLUS FAIL
"""
import sys, re, json, pathlib
from collections import Counter
from bs4 import BeautifulSoup
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import extract_bank as eb

ROOT = pathlib.Path(__file__).resolve().parent.parent
path = pathlib.Path(sys.argv[1]).resolve()
src = path.read_text(encoding='utf-8'); soup = BeautifulSoup(src, 'html.parser')
code = eb.lesson_code(path); bad, warn = [], []

pages = soup.select('div.page')
plus = [p for p in pages if 'plus' in (p.get('class') or [])]
if not plus: print(f'{code}: 보강 쪽 없음'); print('PLUS FAIL'); sys.exit(1)
first_step = next((i for i, p in enumerate(pages) if p.select_one('.step-head')), None)
for p in plus:
    i = pages.index(p)
    if first_step is not None and i > first_step: bad.append(f'보강 쪽(쪽 {i + 1})이 첫 STEP 쪽(쪽 {first_step + 1}) 뒤에 있음')
    for sel in ('.quickcheck', '.q', '.step-head', '.lab', '.anstable'):
        if p.select_one(sel): bad.append(f'보강 쪽에 {sel} — 기존 문항 id 가 밀린다')
    if not p.select_one('.folio'): bad.append('보강 쪽에 폴리오 없음')
    if not p.select_one('.runhead'): warn.append('보강 쪽에 runhead 없음')
if '.plus-h' not in src: bad.append('CSS(.plus-h …) 없음 — docs/22 2절')

concepts = json.loads((ROOT / 'data' / 'concepts.json').read_text(encoding='utf-8'))
nmax = max((int(c['no']) for c in concepts if c['lessonId'] == code), default=0)
eb.LESSON_SET = {c['lessonId'] for c in concepts}
items, secs = eb.parse_plus(path)

if not 2 <= len(secs) <= 4: warn.append(f'보강 개념 {len(secs)}칸(권장 2~4)')
for s in soup.select('.plus-sec'):
    t = s.select_one('.psec'); nm = t.get_text(strip=True) if t else '(제목 없음)'
    if not t: bad.append('보강 개념 칸에 제목(.psec) 없음')
    if not s.select_one('.pkey'): warn.append(f'「{nm}」 한 줄 정리(.pkey) 없음')
    cn = int(s.get('data-concept') or 0)
    if not cn: bad.append(f'「{nm}」 data-concept 없음')
    elif nmax and eb.lec_no(code, cn) > nmax: bad.append(f'「{nm}」 data-concept={cn} → 개념 {eb.lec_no(code, cn)} > 개념 수 {nmax}')
    for f in s.select('figure'):
        if not f.select_one('figcaption'): warn.append(f'「{nm}」 그림에 figcaption 없음')

if not 6 <= len(items) <= 10: warn.append(f'보강 문항 {len(items)}개(권장 6~10)')
ns = [int(el.get('data-n') or 0) for el in soup.select('.pq')]
if ns != list(range(1, len(ns) + 1)): bad.append(f'문항 번호가 1부터 이어지지 않음: {ns}')
sol_ns = [s.get('data-n') for s in soup.select('.psol')]
for d, c in Counter(sol_ns).items():
    if c > 1: bad.append(f'해설 {d}번이 {c}개')
types = Counter()
for el, it in zip(soup.select('.pq'), items):
    n = el.get('data-n'); typ = it['type']; types[typ] += 1; tag = f'{code}-p{n}({typ})'
    if typ not in ('mc', 'multi', 'ox', 'blank', 'essay'): bad.append(f'{tag}: 모르는 data-type'); continue
    pn = el.select_one('.pqno')
    if not pn or pn.get_text(strip=True) != n: bad.append(f'{tag}: 보이는 번호(.pqno) {pn.get_text(strip=True) if pn else "없음"} ≠ data-n {n}')
    if n not in sol_ns: bad.append(f'{tag}: 해설(.psol data-n="{n}") 없음')
    if not it['explain'].strip(): bad.append(f'{tag}: 해설 글이 비었음')
    cn = int(el.get('data-concept') or 0)
    if not cn: warn.append(f'{tag}: data-concept 없음')
    elif nmax and eb.lec_no(code, cn) > nmax: bad.append(f'{tag}: data-concept={cn} > 개념 수 {nmax}')
    if typ in ('mc', 'multi'):
        if not it['answer']: bad.append(f'{tag}: 정답(data-answer ①~⑤) 없음')
        if len(it['choices']) != 5: bad.append(f'{tag}: 선지 {len(it["choices"])}개(5개여야)')
        elif it['answer'] and not 1 <= it['answer'] <= 5: bad.append(f'{tag}: 정답 번호 범위 밖')
        if len(set(re.sub(r'\s+', '', c) for c in it['choices'])) != len(it['choices']): bad.append(f'{tag}: 같은 선지가 두 번')
        sol = soup.select_one(f'.psol[data-n="{n}"]')
        if sol and not sol.select_one('.wrongbox') and typ == 'mc': warn.append(f'{tag}: 바로알기(.wrongbox) 없음')
        if sol and it['answer']:
            lead = sol.find('p'); m = lead and re.search('[①②③④⑤]', lead.get_text())
            if m and eb.mark_no(m[0]) != it['answer']: bad.append(f'{tag}: 해설 첫머리 {m[0]} ≠ 정답 {eb.MARKS[it["answer"] - 1]}')
    if typ == 'multi':
        if 'ㄱ' not in it.get('source', '') or 'ㄴ' not in it.get('source', ''): bad.append(f'{tag}: <보기> ㄱ·ㄴ 문장이 안 읽힘(.bogi-box 안 .bt 머리)')
    if typ == 'ox' and it['answer'] not in ('O', 'X'): bad.append(f'{tag}: OX 정답은 O 또는 X')
    if typ == 'blank':
        if not it['answer']: bad.append(f'{tag}: 빈칸 정답 없음')
        if '＿' not in it['stem']: bad.append(f'{tag}: 발문에 빈칸(＿＿＿) 없음')
    if typ == 'essay' and it['answer']: warn.append(f'{tag}: 서술형은 data-answer 를 비운다')

# 형식 섞임(docs/22: ox·blank 2~3 · mc 2~3 · multi 2~3)
if types['mc'] + types['multi'] < 3: warn.append(f'선지형이 적음 {dict(types)}')
if types['ox'] + types['blank'] < 1: warn.append(f'OX·빈칸 없음 {dict(types)}')
if not any(it['figure'] or it.get('data') or it.get('table') for it in items): warn.append('자료(그림·표·자료 상자)형 문항이 없음')

# 글 규칙(보강 쪽 글자만)
text = ' '.join(p.get_text(' ', strip=True) for p in plus)
for p in plus:
    for s in p.select('svg'): s.extract()
text_ns = ' '.join(p.get_text(' ', strip=True) for p in plus)
for m in re.finditer(r'(?<![A-Za-z\d.])\d+(?:\.\d+)?(?:m/s²?|km/s|km|cm|mm|kg|N/kg|m|N|J|W|Hz|°C|g|L|mL|mol|K)(?![A-Za-z])', text_ns):
    bad.append(f'숫자와 단위 붙여 씀: …{text_ns[max(0, m.start() - 10):m.end() + 6]}…')
for ch in '«»『』':
    if ch in text: bad.append(f'금지 괄호 {ch}')

print(f'{code} {path.parent.name}: 보강 쪽 {len(plus)} · 개념 {len(secs)} · 문항 {len(items)} {dict(types)}')
for it in items: print(f'  {it["id"]} {it["type"]:5} 정답 {it["answer"]!s:6} 그림 {"○" if it["figure"] else "·"}  {re.sub(r"</?[a-zA-Z][^>]*>", "", it["stem"])[:60]}')
for w in warn: print('  ! ' + w)
for b in bad: print('  ✗ ' + b)
print('PLUS OK' if not bad else f'PLUS FAIL {len(bad)}')
sys.exit(1 if bad else 0)
