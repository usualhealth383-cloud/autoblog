#!/usr/bin/env python3
"""낱알·제품 사진을 작은 판(스프라이트)으로 묶기 — 아티팩트(미리보기)에서도 진짜 사진이 보이게.

왜: 아티팩트는 보안 정책상 바깥 사이트 사진(식약처·약학정보원)을 불러오지 못해, 알약이 모두 «그린 그림»으로 나왔다
(2026-09-30 현욱님 캡처 「이거 왜이래」). 앱·웹 배포본은 그대로 식약처 주소를 쓰고, 아티팩트에만 이 판을 함께 싣는다.
식약처 낱알 사진은 약학정보원이 찍은 사진이다(사진 아래 띠에 「약학정보원」) — 현욱님 「약학정보원 사진 그냥 쓰자」.

  · 일반약 낱알 5,660장 + 약 화면 제품 사진(productImages) → 168×92 작은 사진, 64장씩 한 판(8×8)
  · 낱알 사진은 위 눈금자·아래 띠를 잘라 알약만 크게. 제품 상자는 흰 바탕에 통째로.
  · 받은 원본은 <out>/raw 에 두어 이어 돌릴 수 있게.

사용:  python3 yakjido/tools/pill_sprites.py <out 폴더> [--workers 6]
결과:  <out>/ps/NNN.jpg, <out>/ps.json {seq 또는 "p:제품이름": 번호}
"""
import argparse, concurrent.futures as cf, hashlib, io, json, pathlib, sys, time, urllib.request
from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT.parent / 'docs' / 'yakjido' / 'data'
IMG_PREFIX = 'https://nedrug.mfds.go.kr/pbp/cmn/itemImageDownload/'
W, H, COLS, ROWS = 168, 92, 8, 8
PER = COLS * ROWS
UA = {'User-Agent': 'Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 Chrome/126 Mobile Safari/537.36'}


def fetch(url, dst):
    if dst.exists() and dst.stat().st_size > 500: return True
    for i in range(3):
        try:
            b = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40).read()
            if len(b) < 500: return False
            dst.write_bytes(b); return True
        except Exception:
            time.sleep(2 + i * 3)
    return False


def thumb(path, pill):
    im = Image.open(path).convert('RGB')
    if pill:   # 식약처 낱알 사진: 위 눈금자(~9%)·아래 약학정보원 띠(~13%)를 잘라 알약만
        w, h = im.size; im = im.crop((int(w * .02), int(h * .09), int(w * .98), int(h * .86)))
        r = max(W / im.width, H / im.height); im = im.resize((round(im.width * r), round(im.height * r)), Image.LANCZOS)
        l, t = (im.width - W) // 2, (im.height - H) // 2
        return im.crop((l, t, l + W, t + H))
    bg = Image.new('RGB', (W, H), (255, 255, 255))   # 제품 상자: 잘리지 않게 통째로
    r = min(W / im.width, H / im.height); im = im.resize((max(1, round(im.width * r)), max(1, round(im.height * r))), Image.LANCZOS)
    bg.paste(im, ((W - im.width) // 2, (H - im.height) // 2)); return bg


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('out'); ap.add_argument('--workers', type=int, default=6); a = ap.parse_args()
    out = pathlib.Path(a.out); raw = out / 'raw'; ps = out / 'ps'; raw.mkdir(parents=True, exist_ok=True); ps.mkdir(exist_ok=True)
    jobs = []   # (key, url, pill?)
    for p in json.loads((DATA / 'pills.json').read_text(encoding='utf-8')):
        if p.get('img') and p.get('seq'): jobs.append((str(p['seq']), p['img'] if p['img'].startswith('http') else IMG_PREFIX + p['img'], True))
    for name, v in json.loads((ROOT / 'content' / 'productImages.json').read_text(encoding='utf-8')).items():
        if v.get('img', '').startswith('http'): jobs.append(('p:' + name, v['img'], 'itemImageDownload' in v['img']))
    fn = lambda u: raw / (hashlib.sha1(u.encode()).hexdigest()[:16] + '.jpg')
    t0 = time.time(); ok = {}
    with cf.ThreadPoolExecutor(a.workers) as ex:
        futs = {ex.submit(fetch, u, fn(u)): (k, u, pill) for k, u, pill in jobs}
        for i, f in enumerate(cf.as_completed(futs), 1):
            k, u, pill = futs[f]
            if f.result(): ok[k] = (u, pill)
            if i % 250 == 0: print(f'받음 {i:,}/{len(jobs):,} · {time.time() - t0:.0f}초', flush=True)
    keys = [k for k, _, _ in jobs if k in ok]
    idx = {}; sheet = None; n = -1
    for i, k in enumerate(keys):
        s, c = divmod(i, PER)
        if c == 0:
            if sheet: sheet.save(ps / f'{n:03d}.jpg', 'JPEG', quality=70, optimize=True, progressive=True)
            sheet = Image.new('RGB', (W * COLS, H * ROWS), (255, 255, 255)); n = s
        try: sheet.paste(thumb(fn(ok[k][0]), ok[k][1]), ((c % COLS) * W, (c // COLS) * H)); idx[k] = i
        except Exception as e: print('  사진을 못 읽음', k, e, file=sys.stderr)
    if sheet: sheet.save(ps / f'{n:03d}.jpg', 'JPEG', quality=70, optimize=True, progressive=True)
    (out / 'ps.json').write_text(json.dumps(idx, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    size = sum(f.stat().st_size for f in ps.glob('*.jpg'))
    print(f'끝 — 사진 {len(idx):,}장 · 판 {n + 1}장 · {size / 1e6:.1f} MB · 못 받음 {len(jobs) - len(ok)}')


if __name__ == '__main__':
    main()
