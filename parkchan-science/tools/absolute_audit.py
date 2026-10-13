#!/usr/bin/env python3
"""단정 표현 점검 — 조건을 빼고 일반화한 문장(늘·반드시·모든·~만·전부·무조건·절대…)을 뽑아 사람이 보게 한다.

2026-10-13 GPT 검수 ③에서 나온 과학 오류 대부분이 이 꼴이었다:
'MRI 는 늘 극저온' · '식물만 세포벽' · '반드시 다른 물질은 산소를 잃는다' · '상대적인 움직임이 정의의 전부' · '무색이면 산성 또는 중성'.
막는 검사가 아니라 검토 목록이다(맞는 단정도 많다 — '모든 물질은 원자로 되어 있다'). 새로 쓰거나 고친 쪽은 이 목록으로 한 번 훑는다.
· 대상: 본책 book*/chapter-*/chapter.html 의 개념 본문·날개·보강·해설 문장 + data/concept_extras.json
· 이미 조건이 붙은 문장(…에서는·…때·…경우·…무시하면·대략·보통·대부분)은 따로 표시해 뒤로 보낸다
출력: review/단정-표현-점검.md (소단원별) · 마지막 줄 ABSOLUTE n
사용: python3 tools/absolute_audit.py [소단원 코드 ...]
"""
import re, sys, glob, json, pathlib
from bs4 import BeautifulSoup
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import extract_bank as eb

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / 'review' / '단정-표현-점검.md'
# 단정 낱말 — '만'은 명사 뒤 보조사로 쓰인 것만(…만 있다/…만이/…에만)
ABS = re.compile(r'((?<![가-힣])늘(?= )|항상|언제나|반드시|무조건|절대(?![ ]?(온도|영도|값|등급|연대))|(?<![가-힣])모든(?= )|전부|오직|오로지|결코|어떤 경우에도|예외 ?없이|[가-힣]{1,8}(?:에|에게|에서|으로|로)만(?= )|[가-힣]{1,8}만(?= (있|이 |가능|일어|생기|생긴|쓰|한다|된다|해당)))')
SOFT = re.compile(r'(에서는|일 때|할 때|경우|무시하면|무시할|대략|보통|대부분|흔히|주로|가운데|이라면|라면|조건|범위에서|교과서에서는|고교|이 단원)')
SKIP = re.compile(r'(바로알기|모두 고른|옳은 것만|있는 대로|모두 몇|모두 쓰|만큼|만에|만 원|만 년|만 km|만들|만나|만약|만족|만화|만조)')

def sentences(txt):
    for s in re.split(r'(?<=[다요음함])\.\s+|(?<=[.?!])\s+|\n', txt):
        s = re.sub(r'\s+', ' ', s).strip()
        if 8 <= len(s) <= 220: yield s

codes = set(sys.argv[1:])
rows = {}
for f in sorted(glob.glob(str(ROOT / 'book*/chapter-*/chapter.html'))) + [str(ROOT / 'book/sample-chapter/chapter.html')]:
    p = pathlib.Path(f); code = eb.lesson_code(p)
    if codes and code not in codes: continue
    s = BeautifulSoup(p.read_text(encoding='utf-8'), 'html.parser')
    for x in s.select('svg, style, script, .folio, .anstable, .choices'): x.decompose()
    seen = set()
    for el in s.select('.main p, .main li, .wing p, .wing li, .plus-sec p, .plus-sec li, .psol p, .sol p, .gist li, .gist p, td'):
        for t in sentences(el.get_text(' ', strip=True)):
            if t in seen or SKIP.search(t) or not ABS.search(t): continue
            seen.add(t); rows.setdefault(code, []).append(('본책', t))
try:
    ex = json.loads((ROOT / 'data' / 'concept_extras.json').read_text(encoding='utf-8'))
    def walk(v, key):
        if isinstance(v, str):
            for t in sentences(re.sub('<[^>]+>', ' ', v)):
                if ABS.search(t) and not SKIP.search(t): rows.setdefault(key[:4], []).append(('앱 보충', t))
        elif isinstance(v, dict):
            for k, w in v.items(): walk(w, key if len(key) >= 4 else str(k))
        elif isinstance(v, list):
            for w in v: walk(w, key)
    walk(ex, '')
except FileNotFoundError: pass

n = 0; out = ['# 단정 표현 점검 목록', '', '조건 없이 일반화한 문장을 사람이 확인한다. **굵게** = 조건 표지(…에서는·경우·대략…)가 없는 것 — 먼저 볼 것.', '']
for code in sorted(rows):
    if codes and code not in codes: continue
    items = sorted(set(rows[code]), key=lambda r: (bool(SOFT.search(r[1])), r[1]))
    out.append(f'## {code} ({len(items)})')
    for src, t in items:
        hard = not SOFT.search(t); n += hard
        t2 = ABS.sub(lambda m: f'〔{m.group(0)}〕', t)
        out.append(f'- {"**" if hard else ""}{t2}{"**" if hard else ""} · {src}')
    out.append('')
OUT.write_text('\n'.join(out) + '\n', encoding='utf-8')
print(f'{OUT.relative_to(ROOT)} — 소단원 {len(rows)} · 조건 없는 단정 {n} · 전체 {sum(len(set(v)) for v in rows.values())}')
print(f'ABSOLUTE {n}')
