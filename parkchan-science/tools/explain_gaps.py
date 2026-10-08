#!/usr/bin/env python3
"""해설 공백 리포트(벤치마크 ★2) — 문제 은행에서 해설(explain)·선지별 오답 해설(wrong)이 빈 문항을 소단원·유형별로 센다.

· explain 없음: 채점 뒤 '왜'가 비는 문항 — 앱은 이때 '이 개념 다시 보기'(개념 카드) 링크를 대신 보여 준다
· wrong 없음: 전체 수와, 선지가 있는 유형(선다형 mc·자료/보기 multi)만 센 수를 따로 — OX·빈칸·서술형은 선지별 해설이 원래 없다
사용: python3 tools/explain_gaps.py [bank.json 경로] [--ids]   (경로를 안 주면 data/bank.json · --ids 면 아직 빈 문항 id 도 찍는다)
"""
import json, pathlib, sys
from collections import Counter, defaultdict

ROOT = pathlib.Path(__file__).resolve().parent.parent
TYPES = ['ox', 'blank', 'mc', 'multi', 'essay']
STEP = {'qc': '바로바로', 'auto': '자동', 1: 'STEP1', 2: 'STEP2', 3: 'STEP3'}


def empty(v):
    return not str(v or '').strip()


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    path = pathlib.Path(args[0]) if args else ROOT / 'data' / 'bank.json'
    bank = json.loads(path.read_text(encoding='utf-8'))
    no_ex = [q for q in bank if empty(q.get('explain'))]
    no_wr = [q for q in bank if empty(q.get('wrong'))]
    no_wr_ch = [q for q in no_wr if q['type'] in ('mc', 'multi')]
    neither = [q for q in bank if empty(q.get('explain')) and empty(q.get('wrong'))]
    print(f'{path} · 문항 {len(bank):,}')
    print(f'  explain 없음 {len(no_ex):,} · wrong 없음 {len(no_wr):,} (선지형 mc·multi {len(no_wr_ch):,}) · 둘 다 없음 {len(neither):,}')
    print('\n  유형별        explain없음  wrong없음  둘다없음  (전체)')
    for t in TYPES:
        n = sum(1 for q in bank if q['type'] == t)
        print(f'  {t:<12} {sum(1 for q in no_ex if q["type"] == t):>10} {sum(1 for q in no_wr if q["type"] == t):>10} {sum(1 for q in neither if q["type"] == t):>9}  ({n})')
    print('\n  출처별        explain없음  wrong없음(선지형)')
    for s, name in STEP.items():
        print(f'  {name:<12} {sum(1 for q in no_ex if q["step"] == s):>10} {sum(1 for q in no_wr_ch if q["step"] == s):>10}')
    per = defaultdict(Counter)
    for q in no_ex: per[q['lessonId']]['ex:' + q['type']] += 1
    for q in no_wr_ch: per[q['lessonId']]['wr:' + q['type']] += 1
    print('\n  소단원별(빈 것만) — explain 없음 유형 · wrong 없음(선지형) 유형')
    for l in sorted(per):
        c = per[l]
        ex = ' '.join(f'{k[3:]} {v}' for k, v in sorted(c.items()) if k.startswith('ex:'))
        wr = ' '.join(f'{k[3:]} {v}' for k, v in sorted(c.items()) if k.startswith('wr:'))
        print(f'  {l}  explain[{ex or "-"}]  wrong[{wr or "-"}]')
    if '--ids' in sys.argv:
        print('\n  explain 없는 문항:', ' '.join(q['id'] for q in no_ex))
        print('  wrong 없는 선지형:', ' '.join(q['id'] for q in no_wr_ch))


if __name__ == '__main__':
    main()
