#!/usr/bin/env python3
"""약지도 처리방침·계정 지우기를 메디나눔 첫 화면(medinanum.com) 틀로 옮겨 짓는다.

  정본은 yakjido/privacy.html · yakjido/delete-account.html (앱·깃허브 페이지가 쓰는 쪽).
  메디나눔 공용 문서 폴더(yozm-health 저장소 med/_공개/)는 다섯 앱이 같은 모양(공통.css)이라, 내용은 그대로 두고 껍데기만 바꾼다.
    python3 yakjido/tools/medinanum_docs.py <med/_공개 폴더>
  → privacy-yakjido.html · delete-account-yakjido.html · img/yakjido.png
"""
import re, sys, pathlib, io
from PIL import Image
ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = pathlib.Path(sys.argv[1])
def main_of(p): s = (ROOT / p).read_text(encoding='utf-8'); return s[s.index('<main>') + 6: s.index('</main>')]

# ── 처리방침 → 공통.css 틀(머리 · 요약 · h2 흐름 · 표감 · 발) ──
m = main_of('privacy.html')
m = re.sub(r'\s*<div class="mark">.*?</div>\s*<h1>.*?</h1>\s*<p class="meta">.*?</p>', '', m, flags=re.S)
eff = re.search(r'시행일 (\d{4}년 \d+월 \d+일)', (ROOT / 'privacy.html').read_text(encoding='utf-8')).group(1)
m = m.replace('<div class="lead" id="top">', '<div class="요약">')
m = re.sub(r'</?section>', '', m)
m = m.replace('<div class="wrap"><table>', '<div class="표감"><table>')
m = re.sub(r'<footer>.*?</footer>', '', m, flags=re.S)
m = m.replace('href="delete-account.html"', 'href="delete-account-yakjido.html"')
m = re.sub(r'<td class="where">(.*?)</td>', r'<td>\1</td>', m)
priv = f'''<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>약지도 개인정보 처리방침</title>
<link rel="stylesheet" href="공통.css">
<style>body{{word-break:keep-all;overflow-wrap:break-word}}</style>
</head>
<body>
<div class="wrap">
<header class="top">
  <a class="집" href="index.html">← 메디나눔 문서 목차</a>
  <h1>약지도 개인정보 처리방침</h1>
  <p class="앱">증상에 맞는 약국 약을 의사가 고르듯 짚어 주는 앱 · 시행일 {eff}</p>
</header>
{m.strip()}

<div class="발">
  <p>메디나눔 · 운영자 박민욱</p>
  <p>문의 usualhealth383@gmail.com</p>
  <p>시행일 {eff}</p>
</div>
</div>
</body>
</html>
'''
# ── 계정 지우기 → 다른 앱의 delete-account-*.html 과 같은 모양 ──
d = (ROOT / 'delete-account.html').read_text(encoding='utf-8')
dm = main_of('delete-account.html')
dm = re.sub(r'\s*<div class="mark">.*?</div>', '', dm, flags=re.S)
dm = dm.replace('<p class="meta">', '<p class="sub">').replace('href="privacy.html"', 'href="privacy-yakjido.html"')
style = '''<style>
:root{--bg:#FFFDF8;--card:#FFFFFF;--ink:#23302E;--ink2:#4B5A57;--line:#E7E1D6;--pine:#177570;--pine-t:#E6F2F0;--warn:#8A4B12;--warn-t:#FBF1E4}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--bg:#141A19;--card:#1C2423;--ink:#E7ECEB;--ink2:#B6C1BF;--line:#2E3836;--pine:#5FB3AB;--pine-t:#1D302E;--warn:#E8B27A;--warn-t:#2E2419}}
:root[data-theme="dark"]{--bg:#141A19;--card:#1C2423;--ink:#E7ECEB;--ink2:#B6C1BF;--line:#2E3836;--pine:#5FB3AB;--pine-t:#1D302E;--warn:#E8B27A;--warn-t:#2E2419}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.7 system-ui,-apple-system,"Apple SD Gothic Neo","Malgun Gothic",sans-serif;word-break:keep-all}
main{max-width:640px;margin:0 auto;padding:32px 16px 56px}
h1{font-size:26px;line-height:1.35;margin:0 0 6px}
.sub{color:var(--ink2);margin:0 0 26px}
section{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:20px;margin:0 0 14px}
h2{font-size:18px;margin:0 0 10px}
p{margin:0 0 8px}
ol,ul{margin:6px 0 0;padding-left:22px}
li{margin:4px 0}
a{color:var(--pine)}
.path{display:inline-block;background:var(--pine-t);color:var(--pine);font-weight:700;border-radius:8px;padding:2px 8px}
.note{background:var(--warn-t);color:var(--warn);border-radius:12px;padding:12px 14px;margin-top:12px;font-size:15px}
footer{color:var(--ink2);font-size:14px;margin-top:22px}
footer p{margin:0 0 4px}
</style>'''
dele = f'''<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>약지도 — 계정과 기록 지우기</title>
<meta name="description" content="약지도 앱의 계정과 서버 기록, 이 휴대폰의 기록을 지우는 방법">
{style}
</head>
<body>
<main>{dm}</main>
</body>
</html>
'''
(OUT / 'privacy-yakjido.html').write_text(priv, encoding='utf-8')
(OUT / 'delete-account-yakjido.html').write_text(dele, encoding='utf-8')
im = Image.open(ROOT / 'icons' / 'icon-512.png' if (ROOT / 'icons' / 'icon-512.png').exists() else ROOT.parent / 'docs' / 'yakjido' / 'icon-512.png').convert('RGBA').resize((128, 128), Image.LANCZOS)
(OUT / 'img').mkdir(exist_ok=True); im.save(OUT / 'img' / 'yakjido.png', optimize=True)
print('지음', OUT / 'privacy-yakjido.html', OUT / 'delete-account-yakjido.html', OUT / 'img' / 'yakjido.png')
