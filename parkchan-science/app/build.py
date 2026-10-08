#!/usr/bin/env python3
"""앱 셸에 개념·문항·그림 데이터를 심어 배포용 한 파일로 만든다."""
import json, pathlib, re
ROOT = pathlib.Path(__file__).resolve().parent.parent
# 교재 데이터 점검 — 지수·첨자가 사라진 채(10−10 m) 배포되지 않게. 실패하면 빌드하지 않는다
import subprocess as _sp, sys as _sys
_chk = _sp.run([_sys.executable, str(ROOT / 'tools' / 'check_content.py')], capture_output=True, text=True)
if _chk.returncode != 0:
    print(_chk.stdout[-2000:]); raise SystemExit('✗ 교재 데이터 점검 실패 — tools/check_content.py 를 확인하세요. 배포본을 만들지 않았습니다.')
shell = (ROOT / 'app' / 'app-shell.html').read_text(encoding='utf-8')
concepts = json.loads((ROOT / 'data/concepts.json').read_text(encoding='utf-8'))
# 개념마다 '생각해 보기'(왜?) · 계산 개념의 예제→따라 풀기 — 손으로 만든 원본(data/concept_extras.json, 검사는 check_content). 학생에게 필요 없는 근거 위치(src)는 뺀다
# 2026-10-07: 앱 파일 한도(1,700 KB) 때문에 나중에 받는 more-*.json 으로 옮겼다 — 본문을 펼친 안쪽에만 보이므로 첫 화면에 필요 없다(앱이 받으면 CONCEPTS[i].x 로 붙인다)
_ex = json.loads((ROOT / 'data/concept_extras.json').read_text(encoding='utf-8'))
extras = {c['id']: {k: ({kk: vv for kk, vv in v.items() if kk != 'src'} if isinstance(v, dict) else v) for k, v in _ex[c['id']].items()} for c in concepts if _ex.get(c['id'])}
quizzes = json.loads((ROOT / 'data/quizzes.json').read_text(encoding='utf-8'))
bank = json.loads((ROOT / 'data/bank.json').read_text(encoding='utf-8'))
labs = json.loads((ROOT / 'data/labs.json').read_text(encoding='utf-8'))
quotes = json.loads((ROOT / 'data/quotes.json').read_text(encoding='utf-8'))
# 그림은 문서에 미리 그려 두지 않는다 — 필요할 때 만들도록 문자열로만 싣는다
figs = {c['id']: (ROOT / 'data' / c['figure']['file']).read_text(encoding='utf-8')
        for c in concepts if c.get('figure')}
j = lambda o: json.dumps(o, ensure_ascii=False).replace('</', '<\\/')
# 서버 연결값: app/server/config.json {"url": "...", "anonKey": "..."} 이 있으면 심고, 없으면 로컬 모드
cfg_p = ROOT / 'app' / 'server' / 'config.json'
cfg = json.loads(cfg_p.read_text(encoding='utf-8')) if cfg_p.exists() else {}
shell = shell.replace('__SB_URL__', cfg.get('url', '')).replace('__SB_KEY__', cfg.get('anonKey', ''))
shell = shell.replace('__PUSH__', 'on' if cfg.get('push') else 'off')   # 푸시: google-services.json 과 함께 켠다
print('서버 모드:', cfg.get('url') or '(없음 → 로컬 모드)')
legal = {k: (ROOT / 'app' / 'legal' / f'{k}.html').read_text(encoding='utf-8') for k in ('terms', 'privacy', 'delete')}
# 학원 연락처(app-shell 의 CFG.phone·email)를 약관·처리방침·삭제 안내에 그대로 넣는다 — 앱이 없는 사람도 볼 수 있게(Play 계정 삭제 요건)
_cfg = {k: (re.search(k + r": *'([^']*)'", shell) or [None, ''])[1] for k in ('phone', 'email', 'academy')}
_parts = [x for x in (f"전화 {_cfg['phone']}" if _cfg['phone'] else '', f"이메일 {_cfg['email']}" if _cfg['email'] else '') if x]
CONTACT = ' · '.join(_parts) if _parts else '학원 대표 전화·이메일(출시 전에 적어 넣습니다)'
if not _parts: print('! 학원 연락처(CFG.phone·CFG.email)가 비어 있습니다 — 출시 전에 채워야 계정 삭제 안내·개인정보 보호책임자 연락처가 완성됩니다')
legal = {k: v.replace('<!--CONTACT-->', CONTACT) for k, v in legal.items()}
for k, v in legal.items():
    shell = shell.replace(f'<!--LEGAL_{k.upper()}-->', v.replace('`', '&#96;').replace('${', '&#36;{'))
# 문제 은행·자료 탐구·그림(약 1.5MB)은 앱 파일과 따로 — 첫 화면을 그린 뒤 받는다(느린 4G 에서 첫 화면 10초+ → 2026-10-02).
# 파일 이름에 내용 지문을 붙여, 앱과 데이터의 판이 어긋나지 않게 한다(옛 앱은 옛 파일, 새 앱은 새 파일).
import hashlib
more = json.dumps({'bank': bank, 'labs': labs, 'figs': figs, 'extras': extras}, ensure_ascii=False, separators=(',', ':'))
MORE_NAME = 'more-' + hashlib.sha1(more.encode('utf-8')).hexdigest()[:10] + '.json'
_vb = lambda svg: (re.search(r'viewBox="0 0 ([\d.]+) ([\d.]+)"', svg) or [None, '600', '300'])
meta = {'url': MORE_NAME, 'bank': len(bank), 'labs': len(labs),
        # 소단원별 문항 수('이 소단원 문제 풀기 N문항') — 대단원 마무리·모의고사·핵심 정리 빈칸은 보통 풀이에 안 나오므로 뺀다
        'bl': {L: sum(1 for q in bank if q['lessonId'] == L and str(q.get('step')) not in ('unit', 'mock', 'recap')) for L in sorted({q['lessonId'] for q in bank})},
        'll': sorted({l['lessonId'] for l in labs}),
        'fv': {k: f"{_vb(v)[1]} {_vb(v)[2]}" for k, v in figs.items()}}
# 앱이 쓰지 않는 칸(answers — blanks 와 같은 내용, warning — 화면에 안 쓰임)은 앱 파일에서 뺀다(2026-10-07, 앱 파일 한도 1,700 KB). data/ 는 그대로
APP_DROP = ('answers', 'warning')
out = (shell.replace('<!--CONCEPTS-->', j([{k: v for k, v in c.items() if k not in APP_DROP} for c in concepts]))
            .replace('<!--QUIZZES-->', j(quizzes))
            .replace('<!--MORE_META-->', j(meta))
            .replace('<!--QUOTES-->', j(quotes)))
for _k in ('<!--BANK-->', '<!--LABS-->', '<!--FIGS-->'): assert _k not in out

# GitHub Pages 로 나가는 PWA 배포본 — manifest·service worker 가 함께 있어야 앱처럼 동작한다
pages = ROOT.parent / 'docs' / 'parkchan'
PAGE = '''<!DOCTYPE html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{t} · 박찬 과학</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700;900&display=swap">
<style>body{{margin:0;background:#FAF8F4;color:#1E2A2E;font-family:'Noto Sans KR',system-ui,sans-serif;line-height:1.75;word-break:keep-all}}main{{max-width:720px;margin:0 auto;padding:32px 20px 60px}}h1{{font-size:24px;margin:0 0 4px}}.meta{{color:#6B7A80;font-size:13px}}h4{{margin:22px 0 6px;font-size:15px}}p{{margin:0 0 10px;font-size:14.5px;color:#3A484D}}table{{border-collapse:collapse;width:100%;font-size:13px}}th,td{{border:1px solid #E2DED6;padding:6px 8px;text-align:left;vertical-align:top}}nav a{{color:#147D6F;font-weight:700;margin-right:14px;font-size:13px;text-decoration:none}}footer{{margin-top:36px;font-size:12px;color:#96A2A6}}</style></head>
<body><main><nav><a href="./">앱</a><a href="terms.html">이용약관</a><a href="privacy.html">개인정보처리방침</a><a href="delete-account.html">계정 삭제</a></nav><h1>{t}</h1>{b}<footer>박찬 과학 · 하루 한 개념</footer></main></body></html>'''
# 배포 전에 앱 스크립트 문법 검사 — 중복 선언처럼 앱 전체가 멈추는 실수를 배포본에 넣지 않는다(node 가 있을 때)
import re, shutil, subprocess, tempfile
if shutil.which('node'):
    js = '\n'.join(re.findall(r'<script>([\s\S]*?)</script>', out))
    with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False, encoding='utf-8') as f: f.write(js)
    r = subprocess.run(['node', '--check', f.name], capture_output=True, text=True)
    if r.returncode: raise SystemExit('✗ 앱 스크립트 문법 오류 — 배포하지 않습니다\n' + r.stderr[-1500:])
if pages.exists():
    (pages / 'index.html').write_text(out, encoding='utf-8')
    for old in pages.glob('more-*.json'):
        if old.name != MORE_NAME: old.unlink()
    (pages / MORE_NAME).write_text(more, encoding='utf-8')
    # 서비스 워커: 캐시 판 = 앱+데이터 지문(손으로 올리다 잊으면 옛 앱이 새 앱을 가린다), 미리 받을 데이터 파일 이름
    sw_p = pages / 'sw.js'; sw = sw_p.read_text(encoding='utf-8')
    ver = 'pcs-' + hashlib.sha1((out + more).encode('utf-8')).hexdigest()[:10]
    sw2 = re.sub(r"^const CACHE = '[^']*';", f"const CACHE = '{ver}';", sw, count=1, flags=re.M)
    sw2 = re.sub(r"^const DATA = '[^']*';", f"const DATA = './{MORE_NAME}';", sw2, count=1, flags=re.M)
    assert sw2.count(ver) == 1 and MORE_NAME in sw2, 'sw.js 의 CACHE·DATA 줄을 찾지 못했습니다'
    if sw2 != sw: sw_p.write_text(sw2, encoding='utf-8')
    for k, t, fn in (('terms', '이용약관', 'terms.html'), ('privacy', '개인정보처리방침', 'privacy.html'), ('delete', '계정·데이터 삭제 안내', 'delete-account.html')):
        (pages / fn).write_text(PAGE.format(t=t, b=legal[k]), encoding='utf-8')
    # 보호자 동의 페이지(자녀가 보낸 링크로 열림) — 서버 연결값만 심는다
    (pages / 'guide.html').write_text((ROOT / 'app' / 'guide.html').read_text(encoding='utf-8').replace('<!--CONTACT-->', CONTACT), encoding='utf-8')   # 수강생·보호자 시작 안내(2026-10-08) — 문자로 링크만 보내면 된다
    consent = (ROOT / 'app' / 'consent.html').read_text(encoding='utf-8').replace('__SB_URL__', cfg.get('url', '')).replace('__SB_KEY__', cfg.get('anonKey', ''))
    (pages / 'consent.html').write_text(consent, encoding='utf-8')
    print(f'배포본 → {pages}/index.html')
print(f'{len(out.encode())//1024} KB(+ 나중에 받는 {MORE_NAME} {len(more.encode())//1024} KB) · 개념 {len(concepts)} · 문항 {len(quizzes)} · 은행 {len(bank)} · 탐구 {len(labs)} · 글귀 {len(quotes["quotes"])} · 그림 {len(figs)}')
