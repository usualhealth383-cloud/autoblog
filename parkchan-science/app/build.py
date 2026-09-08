#!/usr/bin/env python3
"""앱 셸에 개념·문항·그림 데이터를 심어 배포용 한 파일로 만든다."""
import json, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
shell = (ROOT / 'app' / 'app-shell.html').read_text(encoding='utf-8')
concepts = json.loads((ROOT / 'data/concepts.json').read_text(encoding='utf-8'))
quizzes = json.loads((ROOT / 'data/quizzes.json').read_text(encoding='utf-8'))
bank = json.loads((ROOT / 'data/bank.json').read_text(encoding='utf-8'))
labs = json.loads((ROOT / 'data/labs.json').read_text(encoding='utf-8'))
quotes = json.loads((ROOT / 'data/quotes.json').read_text(encoding='utf-8'))
figs = [f'<div data-id="{c["id"]}">{(ROOT / "data" / c["figure"]["file"]).read_text(encoding="utf-8")}</div>'
        for c in concepts if c.get('figure')]
j = lambda o: json.dumps(o, ensure_ascii=False).replace('</', '<\\/')
# 서버 연결값: app/server/config.json {"url": "...", "anonKey": "..."} 이 있으면 심고, 없으면 로컬 모드
cfg_p = ROOT / 'app' / 'server' / 'config.json'
cfg = json.loads(cfg_p.read_text(encoding='utf-8')) if cfg_p.exists() else {}
shell = shell.replace('__SB_URL__', cfg.get('url', '')).replace('__SB_KEY__', cfg.get('anonKey', ''))
print('서버 모드:', cfg.get('url') or '(없음 → 로컬 모드)')
legal = {k: (ROOT / 'app' / 'legal' / f'{k}.html').read_text(encoding='utf-8') for k in ('terms', 'privacy', 'delete')}
for k, v in legal.items():
    shell = shell.replace(f'<!--LEGAL_{k.upper()}-->', v.replace('`', '&#96;').replace('${', '&#36;{'))
out = (shell.replace('<!--CONCEPTS-->', j(concepts))
            .replace('<!--QUIZZES-->', j(quizzes))
            .replace('<!--BANK-->', j(bank))
            .replace('<!--LABS-->', j(labs))
            .replace('<!--QUOTES-->', j(quotes))
            .replace('<!--FIGS-->', '\n'.join(figs)))

# GitHub Pages 로 나가는 PWA 배포본 — manifest·service worker 가 함께 있어야 앱처럼 동작한다
pages = ROOT.parent / 'docs' / 'parkchan'
PAGE = '''<!DOCTYPE html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{t} · 박찬 과학</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700;900&display=swap">
<style>body{{margin:0;background:#FAF8F4;color:#1E2A2E;font-family:'Noto Sans KR',system-ui,sans-serif;line-height:1.75;word-break:keep-all}}main{{max-width:720px;margin:0 auto;padding:32px 20px 60px}}h1{{font-size:24px;margin:0 0 4px}}.meta{{color:#6B7A80;font-size:13px}}h4{{margin:22px 0 6px;font-size:15px}}p{{margin:0 0 10px;font-size:14.5px;color:#3A484D}}table{{border-collapse:collapse;width:100%;font-size:13px}}th,td{{border:1px solid #E2DED6;padding:6px 8px;text-align:left;vertical-align:top}}nav a{{color:#147D6F;font-weight:700;margin-right:14px;font-size:13px;text-decoration:none}}footer{{margin-top:36px;font-size:12px;color:#96A2A6}}</style></head>
<body><main><nav><a href="./">앱</a><a href="terms.html">이용약관</a><a href="privacy.html">개인정보처리방침</a><a href="delete-account.html">계정 삭제</a></nav><h1>{t}</h1>{b}<footer>박찬 과학 · 하루 한 개념</footer></main></body></html>'''
if pages.exists():
    (pages / 'index.html').write_text(out, encoding='utf-8')
    for k, t, fn in (('terms', '이용약관', 'terms.html'), ('privacy', '개인정보처리방침', 'privacy.html'), ('delete', '계정·데이터 삭제 안내', 'delete-account.html')):
        (pages / fn).write_text(PAGE.format(t=t, b=legal[k]), encoding='utf-8')
    print(f'배포본 → {pages}/index.html')
print(f'{len(out)//1024} KB · 개념 {len(concepts)} · 문항 {len(quizzes)} · 은행 {len(bank)} · 탐구 {len(labs)} · 글귀 {len(quotes["quotes"])} · 그림 {len(figs)}')
