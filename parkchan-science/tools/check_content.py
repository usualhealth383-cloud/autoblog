#!/usr/bin/env python3
"""교재 데이터 점검 — 추출하면서 뜻이 바뀌는 것(지수·아래 첨자가 사라짐 등)을 막는다.

· 원본(book*/)의 <sup>·<sub> 수와 앱 데이터(data/)에 남은 첨자 수(태그 + 유니코드 첨자)가 크게 다르면 실패
· '10−10 m'·'10-15'처럼 첨자가 사라진 흔적(10 뒤에 바로 음수·지수 숫자)이 데이터 글자에 있으면 실패
사용: python3 tools/check_content.py        (추출 뒤, 빌드 전에)
"""
import json, re, glob, pathlib, sys
ROOT = pathlib.Path(__file__).resolve().parent.parent
UNI = '⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻ⁿ₀₁₂₃₄₅₆₇₈₉₊₋'
bad = []
data = {f: json.loads((ROOT / 'data' / f'{f}.json').read_text(encoding='utf-8')) for f in ('concepts', 'quizzes', 'bank', 'labs')}
def strings(x):
    if isinstance(x, str): yield x
    elif isinstance(x, list):
        for y in x: yield from strings(y)
    elif isinstance(x, dict):
        for k, y in x.items():
            if k not in ('figure', 'svg', 'id', 'lessonId'): yield from strings(y)
for f, items in data.items():
    for it in items:
        for t in strings(it):
            txt = re.sub(r'<su[pb]>.*?</su[pb]>', '', t)
            for m in re.finditer(r'(?<![\d.])10\s?[−-]\d{1,2}(?![\d.,])\s*(m|초|s|kg|g|배|J|W|L)\b', txt):
                bad.append(f'{f} {it.get("id") or it.get("lessonId")}: 첨자가 사라진 듯한 "{m[0]}" · {txt[max(0, m.start()-12):m.end()+8]}')
# 원본 대비 첨자 수(대략) — 문항·개념에 쓰인 원본 파일만
src = sum(len(re.findall(r'<su[pb]\b', open(p, encoding='utf-8').read())) for p in glob.glob(str(ROOT / 'book*' / 'lecture-edition' / 'L-*.html')))
got = sum(json.dumps(v, ensure_ascii=False).count('<sup>') + json.dumps(v, ensure_ascii=False).count('<sub>') + sum(json.dumps(v, ensure_ascii=False).count(c) for c in UNI) for k, v in data.items() if k in ('concepts', 'quizzes'))
print(f'강의용 교재 원본 첨자 {src}개 · 개념·확인 문제 데이터 첨자 {got}자')
if src and got < src * 0.8: bad.append(f'개념·확인 문제의 첨자가 원본보다 너무 적음({got} < {src}×0.8) — 추출기가 <sup>·<sub> 를 걷고 있지 않은지')
for b in bad[:30]: print('✗', b)
print('교재 데이터 점검', '통과' if not bad else f'실패 {len(bad)}건'); sys.exit(1 if bad else 0)
