#!/usr/bin/env python3
"""오늘의 한 마디 — 출처 주소를 직접 열어 원문이 그 페이지에 실제로 있는지 대조한다.

· 페이지(HTML·텍스트)를 받아 태그를 걷고, 글자·숫자만 남겨 비교(띄어쓰기·문장부호·따옴표 차이는 무시)
· 원문(orig)에서 연속 18글자(짧으면 전체)가 페이지에 있으면 PASS, 원문이 없으면 번역(ko)의 연속 10글자로 본다
· 한문은 번체/간체 차이를 흡수(opencc 가 있으면)
결과: PASS / FAIL(페이지엔 열리는데 문장이 없음) / NOPAGE(주소가 안 열림) / NOURL
사용: python3 tools/verify_quotes.py <JSON 파일 …>   → 끝에 요약, --json 결과파일 로 저장 가능
"""
import json, re, sys, os, glob, html, unicodedata, urllib.request, urllib.parse, urllib.error, concurrent.futures as cf
try:
    from opencc import OpenCC; _t2s = OpenCC('t2s').convert
except Exception:
    _t2s = lambda s: s

UA = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36', 'Accept-Language': 'ko,en;q=0.8'}
_cache = {}
# 한문 이체자(같은 글자, 다른 모양) — 한국 판본에 흔한 글자를 표준자로
VARIANT = str.maketrans({'靑': '青', '愼': '慎', '彫': '凋', '楡': '榆', '飮': '饮', '偸': '偷', '晩': '晚', '敎': '教', '淸': '清', '靜': '静', '爭': '争', '卽': '即', '旣': '既', '眞': '真', '黃': '黄', '强': '強', '姸': '妍', '緖': '绪', '內': '内', '爲': '为', '說': '说', '刱': '創', '昜': '人'})   # 昜: 실록 전산본이 반복 부호(人人)를 이 글자로 옮긴 곳


def norm(s):
    s = html.unescape(s or ''); s = unicodedata.normalize('NFKC', s)
    s = s.replace('’', "'").replace('‘', "'").replace('“', '"').replace('”', '"')
    s = s.translate(VARIANT)
    return _t2s(re.sub(r'[\W_]+', '', s).lower())


def fetchable(url):
    """사람이 보는 주소 → 원문을 그대로 받을 수 있는 주소 (GitHub 화면 → raw 파일, Gutenberg 책 소개 → 본문 텍스트)"""
    m = re.match(r'https://github\.com/([^/]+)/([^/]+)/blob/([^/]+)/(.+)', url)
    if m: return f'https://raw.githubusercontent.com/{m[1]}/{m[2]}/{m[3]}/{m[4]}'
    m = re.match(r'https://github\.com/([^/]+)/([^/]+)/tree/([^/]+)/(.+)', url)
    if m: return f'https://raw.githubusercontent.com/{m[1]}/{m[2]}/{m[3]}/{m[4].rstrip("/")}/text.txt'
    m = re.match(r'https?://(?:www\.)?gutenberg\.org/ebooks/(\d+)/?$', url)
    if m: return f'https://www.gutenberg.org/cache/epub/{m[1]}/pg{m[1]}.txt'
    return url


def page(url):
    url = urllib.parse.quote(fetchable(url), safe=':/?&=%#+,;@~!$*()')
    if url in _cache: return _cache[url]
    import time
    raw = None
    for n in range(3):   # 중간에 끊기는 연결이 있어 세 번까지
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=40) as r:
                raw = r.read(8_000_000); cs = r.headers.get_content_charset() or 'utf-8'
            break
        except urllib.error.HTTPError as e:
            if e.code in (403, 404, 410): break
            time.sleep(2 * (n + 1))
        except Exception:
            time.sleep(2 * (n + 1))
    try:
        if raw is None: raise ValueError('no page')
        t = raw.decode(cs, 'replace')
        t = re.sub(r'(?is)<(script|style)[^>]*>.*?</\1>', ' ', t); t = re.sub(r'<[^>]+>', ' ', t)
        _cache[url] = norm(t)
    except Exception as e:
        _cache[url] = None
    return _cache[url]


def windows(s, n):
    if len(s) <= n: return [s] if s else []
    step = max(1, (len(s) - n) // 4)
    return [s[i:i+n] for i in range(0, len(s) - n + 1, step)]


CORPUS = None
def load_corpus(d):
    global CORPUS; parts = []
    for f in glob.glob(os.path.join(d, '**', '*.txt'), recursive=True) + glob.glob(os.path.join(d, '**', '*.json'), recursive=True):
        try: parts.append(norm(open(f, encoding='utf-8', errors='ignore').read()))
        except Exception: pass
    CORPUS = '\n'.join(parts)


def segs(t):
    return [norm(x) for x in re.split(r'…|\.\.\.|⋯', t or '') if len(norm(x)) >= 2]


def in_corpus(q):
    o = q.get('orig') or ''
    return bool(CORPUS and re.search(r'[\u4e00-\u9fff]', o) and segs(o) and all(x in CORPUS for x in segs(o)))


def check(q):
    st, info = check_url(q)
    if st != 'PASS' and in_corpus(q): return 'PASS', '원전 전집 대조'
    return st, info


def check_url(q):
    url = (q.get('url') or '').strip()
    if not url.startswith('http'): return 'NOURL', ''
    p = page(url)
    if p is None or len(p) < 12: return 'NOPAGE', url
    o, k = norm(q.get('orig')), norm(q.get('ko'))
    sg = segs(q.get('orig'))
    if len(sg) > 1 and all(x in p for x in sg): return 'PASS', f'생략 {len(sg)}조각'
    cands = windows(o, 18) if o else windows(k, 10)
    hit = sum(1 for w in cands if w in p)
    if cands and hit >= max(1, len(cands) // 2): return 'PASS', f'{hit}/{len(cands)}'
    if k and not o:
        return 'FAIL', f'{hit}/{len(cands)}'
    # 원문이 없고 번역만 있는 페이지(한국어 해설)도 인정
    kc = windows(k, 10); kh = sum(1 for w in kc if w in p)
    if kc and kh >= max(1, len(kc) // 2): return 'PASS', f'ko {kh}/{len(kc)}'
    return 'FAIL', f'{hit}/{len(cands)}'


if __name__ == '__main__':
    out = sys.argv[sys.argv.index('--json') + 1] if '--json' in sys.argv else None
    if '--corpus' in sys.argv: load_corpus(sys.argv[sys.argv.index('--corpus') + 1])
    files = [a for a in sys.argv[1:] if not a.startswith('--') and a.endswith('.json') and a != out]
    items = []
    for f in files:
        d = json.load(open(f, encoding='utf-8')); d = d['quotes'] if isinstance(d, dict) else d
        items += [(f.split('/')[-1], q) for q in d]
    urls = {q.get('url') for _, q in items if (q.get('url') or '').startswith('http')}
    with cf.ThreadPoolExecutor(12) as ex: list(ex.map(page, urls))
    res, cnt = [], {}
    for f, q in items:
        st, info = check(q); cnt[st] = cnt.get(st, 0) + 1
        res.append({'file': f, 'id': q.get('id'), 'who': q.get('who'), 'ko': q.get('ko', '')[:30], 'status': st, 'info': info, 'url': q.get('url', '')})
        if st != 'PASS': print(f'{st:6} {f:14} {q.get("who","")} · {q.get("ko","")[:28]} · {info}')
    print('요약', cnt, '· 전체', len(items))
    if out: json.dump(res, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
