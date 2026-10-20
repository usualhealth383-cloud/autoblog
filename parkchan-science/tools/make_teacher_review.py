#!/usr/bin/env python3
"""교사 감수표 — 본책 '시험에 나오는 보강'·'실력 다지기' 쪽(2026-10-13 새로 씀)을 사람이 빠르게 확인하도록 한 장에 모은다.

· 소단원마다: 보강 개념 칸 제목(쪽) · 문항(쪽 · 꼴 · 정답 · 발문 앞부분 · 해설 첫 문장) · 확인 칸(정답 하나? · 사실 · 범위 · 표현)
· 맨 앞: 감수 방법 · 먼저 볼 것(2026년 이후 자료 · 교과서 관행값과 최근 측정값을 함께 적은 곳)
출력: review/교사-감수표-보강.html (+ 같은 이름 .pdf)
사용: python3 tools/make_teacher_review.py
"""
import re, glob, html, pathlib, subprocess
from bs4 import BeautifulSoup
import sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import extract_bank as eb

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / 'review' / '교사-감수표-보강.html'
TYPE = {'mc': '5지 선다', 'multi': '합답형', 'ox': 'OX', 'blank': '빈칸', 'essay': '서술형'}
clip = lambda t, n: (t[:n] + '…') if len(t) > n else t
SUP = str.maketrans('0123456789+-−n()', '⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁻ⁿ⁽⁾'); SUB = str.maketrans('0123456789+-−()', '₀₁₂₃₄₅₆₇₈₉₊₋₋₍₎')
def plain(el):
    if not el: return ''
    el = __import__('copy').copy(el)
    for x in el.find_all(['sup', 'sub']):   # 위·아래 첨자는 유니코드로(10⁸ · H₂O) — 감수표에서 '10 8'로 뭉개지지 않게
        t = x.get_text(); m = SUP if x.name == 'sup' else SUB
        x.replace_with(t.translate(m) if all(c in '0123456789+-−n()' for c in t) else ('^' + t if x.name == 'sup' else '_' + t))
    return re.sub(r' (?=[⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻ⁿ₀₁₂₃₄₅₆₇₈₉₊₋])', '', re.sub(r'\s+', ' ', el.get_text(' ', strip=True)))

files = sorted(glob.glob(str(ROOT / 'book/chapter-i*/chapter.html'))) + [str(ROOT / 'book/sample-chapter/chapter.html')] + \
    sorted(f for f in glob.glob(str(ROOT / 'book/chapter-[0-9]*/chapter.html'))) + sorted(glob.glob(str(ROOT / 'book2/chapter-*/chapter.html')))
rows, total = [], {'sec': 0, 'p': 0, 'u': 0}
for f in files:
    p = pathlib.Path(f); code = eb.lesson_code(p); s = BeautifulSoup(p.read_text(encoding='utf-8'), 'html.parser')
    title = plain(s.select_one('.opener h1, h1')) or code
    book = '통합과학2' if 'book2' in f else '통합과학1'
    folio = lambda el: (lambda pg: plain(pg.select_one('.folio .num')) if pg else '?')(el.find_parent('div', class_='page'))
    secs = [(plain(x.select_one('.psec')), folio(x)) for x in s.select('.plus-sec')]
    qs = []
    for el in s.select('.pq'):
        up = any('up' in (pg.get('class') or []) for pg in el.find_parents('div'))
        n = el.get('data-n'); g = 'u' if up else 'p'
        stem = el.select_one('.stem'); st = plain(stem)
        st = re.sub(r'^\d+\s*', '', st); st = re.sub(r'\s*●[●○]*○*\s*$', '', st)
        sol = next((x for x in s.select('.psol') if x.get('data-n') == n and any('up' in (pg.get('class') or []) for pg in x.find_parents('div')) == up), None)
        first = plain(sol.find('p')) if sol else ''
        qs.append((g, n, folio(el), TYPE.get(el.get('data-type'), el.get('data-type')), el.get('data-answer') or '(채점 기준)', clip(st, 90), clip(first, 110)))
        total[g] += 1
    total['sec'] += len(secs)
    if secs or qs: rows.append((book, code, title, secs, qs))

e = html.escape
parts = [f'''<!doctype html><html lang="ko"><meta charset="utf-8"><title>교사 감수표 — 보강·실력 다지기</title>
<style>
@page{{ size:A4; margin:12mm 11mm; }}
body{{ font-family:'Noto Sans KR','Pretendard',sans-serif; font-size:9pt; line-height:1.5; color:#1F2A33; word-break:keep-all; }}
h1{{ font-size:15pt; margin:0 0 2mm; }} h2{{ font-size:11.5pt; margin:6mm 0 1.5mm; color:#3B3F9E; break-after:avoid; }}
.lead{{ background:#F4F5FB; border-radius:2mm; padding:3mm 4mm; margin:2mm 0 4mm; }}
.lead li{{ margin:0.6mm 0; }}
table{{ width:100%; border-collapse:collapse; margin:1mm 0 3mm; }} th{{ background:#3B3F9E; color:#fff; font-size:8pt; padding:1mm 1.5mm; }}
td{{ border-bottom:0.2mm solid #D5D9E0; padding:1mm 1.5mm; vertical-align:top; font-size:8.3pt; }} tr{{ break-inside:avoid; }}
td.c{{ text-align:center; white-space:nowrap; }} td.box{{ width:18mm; color:#9AA4AE; font-size:7.5pt; white-space:nowrap; }}
.secs{{ font-size:8.3pt; color:#4A5560; margin:0 0 1mm; }} .sum{{ font-weight:800; }}
</style>
<h1>교사 감수표 — 본책 '시험에 나오는 보강' · '실력 다지기'</h1>
<p class="sum">소단원 {len(rows)}개 · 보강 개념 칸 {total['sec']} · 보강 문항 {total['p']} · 실력 다지기 문항 {total['u']} (2026-10-13 새로 씀, 쪽 번호는 합본 기준)</p>
<div class="lead"><b>부탁드리는 것</b><ul>
<li>문항마다 오른쪽 칸에 <b>✓</b>(문제 없음) 또는 <b>✗ + 메모</b>. 보실 것: ① 정답이 하나뿐인가 ② 사실·수치가 맞는가 ③ 2022 교육과정 범위 안인가(넘으면 '(심화)' 표시가 있는가) ④ 표현이 학생에게 분명한가.</li>
<li>문항 전문·그림·해설은 합본 PDF 해당 쪽에 있습니다(표의 '쪽'). 이 표는 길잡이입니다.</li>
<li><b>먼저 봐 주실 것</b> — 2026년 자료(2203: 2026년 5월 432 ppm · 2016~2025년 약 1.26 ℃ · 2026년 9월 엘니뇨 주의보), 교과서 관행값과 최근 측정값을 함께 적은 곳(2204 지구 에너지원 비율 0.013 % · 최근 측정 약 0.03 %), 지질시대 구분 기준을 '화석의 급변이 주된 기준 + 부정합도 함께'로 적은 곳(2101).</li>
<li>값이 '가상의 자료'로 밝혀진 표·그래프는 계산만 맞는지 보시면 됩니다.</li></ul></div>
''']
for book, code, title, secs, qs in rows:
    parts.append(f'<h2>{e(book)} · {e(code)} {e(title)}</h2>')
    if secs: parts.append('<p class="secs">보강 개념 칸: ' + ' · '.join(f'{e(t)}({e(pg)}쪽)' for t, pg in secs) + '</p>')
    parts.append('<table><tr><th>번호</th><th>쪽</th><th>꼴</th><th>정답</th><th>발문(앞부분)</th><th>해설 첫 문장</th><th>확인</th></tr>')
    for g, n, pg, ty, a, st, so in qs:
        parts.append(f'<tr><td class="c">{"보강" if g == "p" else "실력"} {e(n)}</td><td class="c">{e(pg)}</td><td class="c">{e(ty)}</td><td class="c">{e(a)}</td><td>{e(st)}</td><td>{e(so)}</td><td class="box">✓ / ✗</td></tr>')
    parts.append('</table>')
OUT.write_text('\n'.join(parts) + '\n</html>\n', encoding='utf-8')
pdf = OUT.with_suffix('.pdf')
subprocess.run(['/opt/pw-browsers/chromium', '--headless=new', '--no-sandbox', '--disable-gpu', '--no-pdf-header-footer', f'--print-to-pdf={pdf}', OUT.as_uri()], stderr=subprocess.DEVNULL, check=True)
print(f'{OUT.relative_to(ROOT)} · {pdf.relative_to(ROOT)} — 소단원 {len(rows)} · 개념 칸 {total["sec"]} · 보강 {total["p"]} · 실력 {total["u"]}')
