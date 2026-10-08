#!/usr/bin/env python3
"""식약처 «회수·폐기» 공지를 품목코드(itemSeq)로 받아 content/recalls.json 에 적는다.

2026-10-01 벤치마크(의약품안전나라 회수·판매중지 목록)에서 시작. 회수는 «제품 전체»가 아니라
«특정 제조번호»만이라, 앱은 제품에 빨간 딱지를 붙이지 않고 «이 제조번호만 회수 — 집에 있는 약 확인»으로 조용히 알린다.
회수된 제조번호 중 하나라도 사용기한이 남아 있으면(집에 남아 있을 수 있으면) 싣는다.
사용기한이 적혀 있지 않으면 회수일로부터 2년까지 싣는다.

사용:  python3 yakjido/tools/mfds_recalls.py            # 최근 공지 넉 쪽(400건)
       python3 yakjido/tools/mfds_recalls.py --pages 8
"""
import argparse, datetime, html, json, pathlib, re, subprocess, time

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / 'content' / 'recalls.json'
BASE = 'https://nedrug.mfds.go.kr'


def curl(url):
    # 의약품안전나라는 연결을 자주 끊는다 — 몇 번 다시 시도
    for t in range(6):
        r = subprocess.run(['curl', '-sS', '-m', '40', url], capture_output=True)
        if r.returncode == 0 and r.stdout: return r.stdout.decode('utf-8', 'ignore')
        time.sleep(2 + t * 2)
    raise RuntimeError('받지 못함: ' + url)


def nm(x): return re.sub(r'\(.*?\)|<.*?>|\s', '', str(x))


def txt(x): return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', x))).strip()


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--pages', type=int, default=10); a = ap.parse_args()
    today = datetime.date.today(); keep = {}; n_all = 0
    for p in range(1, a.pages + 1):
        s = curl(f'{BASE}/pbp/CCBAI01/getList?page={p}&limit=100')
        for r in re.findall(r'(?s)<tr>(.*?)</tr>', s):
            seq = re.search(r'getItemDetail\?itemSeq=(\d+)', r); note = re.search(r'targetItemSeq=(\d+)', r)
            if not seq: continue
            n_all += 1
            name = txt(re.search(r'(?s)<a [^>]*itemSeq=[^>]*>(.*?)</a>', r).group(1))
            why = txt(re.search(r'(?s)회수사유</span>\s*<span title="([^"]*)"', r).group(1)) if '회수사유' in r else ''
            # 제조번호는 «제조번호[사용기한]» 칸의 title 속성에 전부 들어 있다(화면 글자는 «...»로 잘림)
            lots_raw = next((t for t in re.findall(r'<td[^>]*title="([^"]*)"', r) if '[' in t and '$' not in t), '')
            day = re.search(r'회수명령일자</span>\s*<span>([\d-]{10})', r)
            day = day.group(1) if day else ''
            lots = [(m.group(1).strip(), m.group(2)) for m in re.finditer(r'([^,\[\]]+)\[([\d-]*)\]', html.unescape(lots_raw))]
            exps = [datetime.date.fromisoformat(e) for _, e in lots if re.fullmatch(r'\d{4}-\d{2}-\d{2}', e)]
            if exps: alive = max(exps) >= today
            else: alive = bool(day) and datetime.date.fromisoformat(day) >= today - datetime.timedelta(days=730)
            if not alive: continue
            keep.setdefault(seq.group(1), []).append({'n': name, 'd': day, 'why': why, 'lots': [l for l, _ in lots][:8],
                                                      'exp': max(exps).isoformat() if exps else '', 'id': note.group(1) if note else ''})
        time.sleep(1)
    # 앱이 보여 줄 수 있는 제품만 남긴다(본문 묶음 400 KB 한도) — 품목코드가 같거나, 품목코드가 없는 e약은요 항목은 이름이 같을 때
    D = ROOT.parent / 'docs' / 'yakjido' / 'data'
    idx = json.loads((D / 'easy-index.json').read_text(encoding='utf-8'))
    seqs = {e['seq'] for e in idx if e.get('seq')}
    seqs |= {v.get('seq') for v in json.loads((ROOT / 'content' / 'productImages.json').read_text(encoding='utf-8')).values() if v.get('seq')}
    if (D / 'pills.json').exists():
        pl = json.loads((D / 'pills.json').read_text(encoding='utf-8')); pl = pl if isinstance(pl, list) else pl.get('items', [])
        seqs |= {x.get('seq') for x in pl if isinstance(x, dict) and x.get('seq')}
    names = {nm(e['n']) for e in idx if not e.get('seq')}
    keep = {k: v for k, v in keep.items() if k in seqs or any(nm(x['n']) in names for x in v)}
    OUT.write_text(json.dumps(keep, ensure_ascii=False, separators=(',', ':')) + '\n', encoding='utf-8')
    print(f'공지 {n_all}건 중 아직 집에 남아 있을 수 있고 앱에 나오는 제품 {sum(len(v) for v in keep.values())}건 ({len(keep)}개 품목) → {OUT}')


if __name__ == '__main__':
    main()
