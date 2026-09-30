#!/usr/bin/env python3
"""약 화면 「이 성분이 든 제품」 사진 — 약학정보원 상자(포장)·제품 사진으로 채우기.

2026-09-30 현욱님 「약학정보원 사진 그냥 쓰자」. 낱알 자료에 없는 시럽·연고·겔·파스·산제가 비어 있었다(218개 중 137개).
우리 제품 이름에는 식약처 코드가 없어 «이름»으로 맞춘다 — 그래서 **정규화한 이름이 같거나, 약학정보원 이름이 우리 이름으로 시작하는 것만** 받는다.
엉뚱한 제품 사진이 붙는 것이 사진이 없는 것보다 나쁘므로, 결과는 --dry 로 먼저 눈으로 본다.

사용:  python3 yakjido/tools/kpic_products.py --dry     # 무엇이 붙을지 보기
       python3 yakjido/tools/kpic_products.py           # content/productImages.json 에 적기
"""
import argparse, glob, json, pathlib, re, sys, time
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from kpic_photos import Kpic, PIC

ROOT = pathlib.Path(__file__).resolve().parent.parent
PI = ROOT / 'content' / 'productImages.json'


def norm(s):
    s = re.sub(r'\(.*?\)|\[.*?\]', '', str(s))
    s = re.sub(r'밀리그(램|람)', 'mg', s).replace('％', '%')
    return re.sub(r'[\s·\-_/]', '', s).lower()


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--dry', action='store_true'); a = ap.parse_args()
    drugs = []
    for f in sorted(glob.glob(str(ROOT / 'content' / 'drugs*.json'))):
        v = json.loads(pathlib.Path(f).read_text(encoding='utf-8')); drugs += v if isinstance(v, list) else v.get('drugs', [])
    pi = json.loads(PI.read_text(encoding='utf-8'))
    names = list(dict.fromkeys(p['name'] for d in drugs for p in d.get('products', []) if p.get('name') and p['name'] not in pi))
    k = Kpic(); got = {}; none = []
    for n in names:
        if re.search(r'\s등$|·.*·', n): none.append((n, '여러 제품을 묶은 이름')); continue
        want = norm(n); word = re.sub(r'\(.*?\)', '', n).strip()
        # 약학정보원 검색은 띄어쓰기가 있으면 0건 — 붙여 쓴 이름, 그다음 상표(첫 낱말)로 넓게 찾고 짝은 이름으로만 맞춘다
        res = []
        for w in dict.fromkeys([word.replace(' ', ''), word, word.split(' ')[0]]):
            if len(w) < 2: continue
            try: res = k.search(w)
            except Exception as e: res = []; time.sleep(2)
            if any(norm(r.get('drug_name', '')).startswith(want) for r in res): break
            time.sleep(0.4)
        cand = [r for r in res if norm(r.get('drug_name', '')) == want] or [r for r in res if norm(r.get('drug_name', '')).startswith(want)]
        cand = [r for r in cand if str(r.get('pack_img') or '').strip('|') or str(r.get('drug_pic') or '').strip('|')]
        if not cand: none.append((n, f'이름이 같은 제품 없음(검색 {len(res)}건)')); time.sleep(0.5); continue
        r = cand[0]
        img = str(r.get('pack_img') or '').strip('|').split('|')[0] or str(r.get('drug_pic') or '').strip('|').split('|')[0]
        got[n] = {'img': img, 'match': r.get('drug_name', ''), 'kpic': r.get('drug_code', ''), 'seq': str(r.get('kfda_code', '')), 'src': '약학정보원'}
        print(f'  ✓ {n}  →  {r.get("drug_name")}  ({"상자" if r.get("pack_img") else "낱알"})', flush=True)
        time.sleep(0.5)
    print(f'\n붙일 것 {len(got)} · 못 찾음 {len(none)}')
    for n, why in none: print(f'  · {n} — {why}')
    if not a.dry:
        pi.update(got); PI.write_text(json.dumps(pi, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
        print('적음 →', PI)


if __name__ == '__main__':
    main()
