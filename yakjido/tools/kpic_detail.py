#!/usr/bin/env python3
"""약학정보원 복약정보 모으기 — 공공 제품 화면(e약은요·낱알)에 «무슨 약·복약 안내·그림 표시·보관·DUR»을 붙인다.

2026-09-30 현욱님 「약 사전 내용도 약학정보원 참고해서 잘 보완해 … 오늘 다 꽉꽉 채워 넣도록」.
식약처 자료만으로는 제품 화면이 허가 문구 그대로라 어르신이 읽기 어려웠다. 약학정보원은 제품마다
한 줄 설명(medititle)·복약 안내(mediguide)·픽토그램·성상·보관·포장·DUR 을 갖고 있다.

짝은 «식약처 품목기준코드(kfda_code) == seq» 인 것만 — 이름이 비슷한 다른 제품 정보를 붙이지 않는다.
결과: docs/yakjido/data/kpic-guide.json {seq: {c, t, g[], p[], ch, st, bx, dur{}, pic}} (앱이 제품 화면에서 늦게 받아 씀)

사용:  python3 yakjido/tools/kpic_detail.py [--workers 3] [--limit N] [--rx]
"""
import argparse, concurrent.futures as cf, html, json, pathlib, re, sys, threading, time, urllib.parse
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from kpic_photos import Kpic, BASE, PIC, names

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT.parent / 'docs' / 'yakjido' / 'data'
OUT = DATA / 'kpic-guide.json'
LOCK = threading.Lock()


def clean(s):
    s = html.unescape(str(s or '')).replace('brbr', '\n').replace('br<P></P>', '\n')
    s = re.sub(r'<[^>]+>', '', s)
    return re.sub(r'[ \t　]+', ' ', s).strip()


def bullets(s):
    out = []
    for ln in clean(s).split('\n'):
        ln = ln.strip().lstrip('-·•').strip()
        if len(ln) >= 4 and ln not in out: out.append(ln)
    return out[:8]


def detail(k, code):
    q = urllib.parse.urlencode({'drug_cd': code, '_': int(time.time() * 1000)})
    t = k._get(f'{BASE}/searchDrug/ajax/ajax_result_drug2.asp?{q}', {
        'accept': 'application/json, text/javascript, */*; q=0.01', 'accept-language': 'ko',
        'Referer': f'{BASE}/searchDrug/result_drug.asp?drug_cd={code}'})
    v = json.loads(t); return v[0] if v else None


def pack(d):
    pic = str(d.get('drug_pic') or '').strip('|').split('|')[0]
    box = str(d.get('pack_img') or '').strip('|').split('|')[0]
    picto = re.findall(r'/pictogram/black/kor/([A-Z]\d{2})\.jpg', str(d.get('picto_img') or ''))
    dur = {k: clean(d.get('dur_' + k)) for k in ('age', 'preg', 'senior', 'dose', 'period', 'contra') if clean(d.get('dur_' + k))}
    rec = {'c': d.get('drug_code', ''), 't': clean(d.get('medititle')), 'g': bullets(d.get('mediguide')), 'p': picto,
           'ch': clean(d.get('charact_new') or d.get('charact')), 'st': clean(d.get('stmt')), 'bx': clean(d.get('drug_box'))[:160],
           'dur': dur, 'pic': pic.rsplit('/', 1)[-1] if pic.startswith(PIC) else pic, 'box': box}
    return {k: v for k, v in rec.items() if v}


def work(chunk, done, stats, delay):
    k = Kpic()
    for seq, name in chunk:
        rec = None; asked = False
        for w in names(name):
            try: res = k.search(w); asked = True
            except Exception: k.token = None; time.sleep(3); continue
            m = [r for r in res if str(r.get('kfda_code', '')).strip() == seq]
            time.sleep(delay)
            if m:
                try: d = detail(k, m[0]['drug_code']); rec = pack(d) if d else {'c': m[0]['drug_code']}
                except Exception: rec = {'c': m[0]['drug_code']}
                time.sleep(delay); break
        with LOCK:
            if rec: done[seq] = rec; stats['hit'] += 1
            elif asked: done[seq] = {}; stats['miss'] += 1
            else: stats['err'] += 1
            stats['n'] += 1
            if stats['n'] % 100 == 0:
                OUT.write_text(json.dumps(done, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
                print(f"{stats['n']:,}/{stats['todo']:,} — 찾음 {stats['hit']:,} · 없음 {stats['miss']:,} · 오류 {stats['err']} · {time.time() - stats['t0']:.0f}초", flush=True)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--workers', type=int, default=3); ap.add_argument('--limit', type=int, default=0)
    ap.add_argument('--delay', type=float, default=0.35); ap.add_argument('--rx', action='store_true'); a = ap.parse_args()
    items = {}
    for f in ['easy-index.json', 'pills.json'] + (['pills-rx.json'] if a.rx else []):
        for p in json.loads((DATA / f).read_text(encoding='utf-8')):
            if p.get('seq') and p.get('n'): items.setdefault(str(p['seq']), p['n'])
    for name, v in json.loads((ROOT / 'content' / 'productImages.json').read_text(encoding='utf-8')).items():   # 약 사전 대표 제품
        if v.get('seq'): items.setdefault(str(v['seq']), v.get('match') or name)
    done = json.loads(OUT.read_text(encoding='utf-8')) if OUT.exists() else {}
    todo = [(s, n) for s, n in items.items() if s not in done]
    if a.limit: todo = todo[:a.limit]
    stats = {'hit': 0, 'miss': 0, 'err': 0, 'n': 0, 'todo': len(todo), 't0': time.time()}
    print(f'제품 {len(items):,}개 · 남은 것 {len(todo):,}개', flush=True)
    chunks = [todo[i::a.workers] for i in range(a.workers)]
    with cf.ThreadPoolExecutor(a.workers) as ex: list(ex.map(lambda c: work(c, done, stats, a.delay), chunks))
    OUT.write_text(json.dumps(done, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    print(f"끝 — {OUT} · 찾음 {sum(1 for v in done.values() if v):,} / {len(done):,}")


if __name__ == '__main__':
    main()
