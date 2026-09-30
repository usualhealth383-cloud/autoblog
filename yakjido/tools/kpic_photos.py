#!/usr/bin/env python3
"""약학정보원(health.kr) 낱알 사진 짝 찾기 — 식약처 품목기준코드(seq) → 약학정보원 약 코드·사진.

2026-09-30 현욱님 「약학정보원 사진 그냥 쓰자」. 사진 파일은 저장하지 않고 «주소»만 적는다 —
앱이 볼 때 약학정보원 서버에서 바로 불러온다(common.health.kr).

약학정보원 검색은 세션 쿠키와 CSRF 토큰이 필요해서(2025년 이후 바뀜) 휴대폰 앱이 그때그때 부를 수 없다.
그래서 여기서 제품 이름으로 한 번씩 찾아 «kfda_code == 식약처 seq» 인 것만 짝으로 적어 둔다.
이름만 비슷한 다른 제품을 붙이지 않기 위해서다(다른 약 사진이 뜨는 것이 사진이 없는 것보다 위험하다).

참고: github.com/antegral/kpic-mcp (공개 코드, 검색·상세 API 형식)

사용:  python3 yakjido/tools/kpic_photos.py [--rx] [--limit N] [--delay 0.8]
       이어서 돌리면 이미 찾은 것은 건너뛴다. 결과: docs/yakjido/data/kpic.json
       {seq: [약학정보원 코드, 사진 파일 이름 또는 ""]}
"""
import argparse, http.cookiejar, json, pathlib, re, sys, time, urllib.parse, urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT.parent / 'docs' / 'yakjido' / 'data'
OUT = DATA / 'kpic.json'
BASE = 'https://health.kr'           # www 는 301 로 넘어가며 쿠키가 떨어진다 — 처음부터 non-www
PIC = 'https://common.health.kr/shared/images/sb_photo/big3/'
UA = 'Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Mobile Safari/537.36'


class Kpic:
    def __init__(self):
        self.jar = http.cookiejar.CookieJar()
        self.op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.jar))
        self.token = None

    def _get(self, url, headers, data=None):
        req = urllib.request.Request(url, data=data, headers={'User-Agent': UA, **headers})
        with self.op.open(req, timeout=30) as r:
            return r.read().decode('utf-8', 'replace')

    def session(self):
        html = self._get(f'{BASE}/searchDrug/search_total_result.asp',
                         {'accept': 'text/html,application/xhtml+xml,*/*;q=0.8', 'accept-language': 'ko'})
        m = re.search(r"window\.csrfToken\s*=\s*[\"']([^\"']+)[\"']", html) or re.search(r'CSRF_TOKEN=([A-Za-z0-9]+)', html)
        if not m: raise RuntimeError('CSRF 토큰을 찾지 못했어요 — 약학정보원 검색 페이지 형식이 바뀌었을 수 있어요')
        self.token = m.group(1)

    def search(self, word):
        if not self.token: self.session()
        q = urllib.parse.urlencode({'search_word': word, 'csrf_token': self.token, 'search_flag': 'all', '_': int(time.time() * 1000)})
        body = urllib.parse.urlencode({'csrf_token': self.token}).encode()
        txt = self._get(f'{BASE}/searchDrug/ajax/ajax_commonSearch.asp?{q}', {
            'accept': 'application/json, text/javascript, */*; q=0.01', 'accept-language': 'ko',
            'content-type': 'application/x-www-form-urlencoded; charset=UTF-8', 'x-requested-with': 'XMLHttpRequest',
            'x-csrf-token': self.token, 'Referer': f'{BASE}/searchDrug/search_total_result.asp'}, body)
        try: v = json.loads(txt)
        except json.JSONDecodeError: self.token = None; raise RuntimeError('응답이 JSON 이 아니에요(세션 만료일 수 있음)')
        return v if isinstance(v, list) else []


def names(n):
    """「타이레놀정500밀리그람(아세트아미노펜)」 → 전체 이름, 괄호 뗀 이름 순으로 찾아본다"""
    a = n.strip(); b = re.sub(r'\(.*?\)|\[.*?\]', '', a).strip()
    return [x for x in dict.fromkeys([a, b]) if x]


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--rx', action='store_true', help='처방약(pills-rx.json)도')
    ap.add_argument('--limit', type=int, default=0); ap.add_argument('--delay', type=float, default=0.8)
    a = ap.parse_args()
    rows = json.loads((DATA / 'pills.json').read_text(encoding='utf-8'))
    if a.rx and (DATA / 'pills-rx.json').exists(): rows += json.loads((DATA / 'pills-rx.json').read_text(encoding='utf-8'))
    done = json.loads(OUT.read_text(encoding='utf-8')) if OUT.exists() else {}
    todo = [p for p in rows if p.get('seq') and str(p['seq']) not in done]
    if a.limit: todo = todo[:a.limit]
    k = Kpic(); hit = miss = err = 0
    print(f'찾을 제품 {len(todo):,}개 (이미 {len(done):,}개)', flush=True)
    for i, p in enumerate(todo, 1):
        seq = str(p['seq']); got = None; asked = False
        for w in names(p.get('n', '')):
            for attempt in (1, 2):
                try: res = k.search(w); break
                except Exception as e:
                    if attempt == 2: res = None; err += 1; print(f'  ! {w}: {e}', file=sys.stderr)
                    else: k.token = None; time.sleep(3)
            if res is None: continue
            asked = True
            m = [r for r in res if str(r.get('kfda_code', '')).strip() == seq]
            if m:
                pic = str(m[0].get('drug_pic') or '').strip('|').strip()
                got = [str(m[0].get('drug_code', '')), pic.rsplit('/', 1)[-1] if pic.startswith(PIC) else pic]
                break
            time.sleep(a.delay)
        if got: done[seq] = got; hit += 1
        elif asked: done[seq] = ['', '']; miss += 1   # 물어봤는데 없던 것만 적는다 — 접속 오류는 다음에 다시
        if err >= 20 and not hit: sys.exit('약학정보원에 닿지 않아요 — 네트워크(health.kr 허용)를 확인하세요')
        if i % 50 == 0 or i == len(todo):
            OUT.write_text(json.dumps(done, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
            print(f'{i:,}/{len(todo):,} — 짝 {hit:,} · 못 찾음 {miss:,} · 오류 {err}', flush=True)
        time.sleep(a.delay)
    withpic = sum(1 for v in done.values() if v[1])
    print(f'끝 — {OUT} · 짝 {sum(1 for v in done.values() if v[0]):,} · 사진 있음 {withpic:,}')


if __name__ == '__main__':
    main()
