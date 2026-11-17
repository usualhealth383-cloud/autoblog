# -*- coding: utf-8 -*-
"""배포 묶음 파일 검사 — 모든 앱 공통 (2026-11-18 Main · CS 알약 _낱알.js 사고)
# 약지도 사본(11-17 Main) — 정본은 yozm-health _도구/묶음파일검사.py. data.py 가 docs/yakjido 에 부른다
실제 사이트는 없는 길을 앱 첫 화면(index.html)으로 돌려준다 → 「파일 없음」이 오류 없이 깨진 화면이 된다.
그래서 묶음(_배포) 안 글 파일(html·js·css·json·webmanifest)이 부르는 «로컬 파일»을 모두 찾아
  ① 묶음 안에 있는가  ② 있으면 첫 글자가 <!doctype / <html 이 아닌가(js·css·json 인데 html 이면 결함)
를 본다. 실행 중에 이름을 이어 붙여 부르는 파일(예: '약자료/' + id + '.js')은 여기서 못 본다 — 그런 앱은 자기 브라우저 검사를 함께(_도구/검증_CS묶음파일.mjs).
쓰는 법: python3 _도구/묶음파일검사.py <묶음 폴더> [--조용히]   · 배포_묶기.py 가 끝에 부른다. 결함이 있으면 끝 코드 1.
"""
import os, re, sys
글확장 = ('.html', '.js', '.mjs', '.css', '.json', '.webmanifest')
부를확장 = r'(?:js|mjs|css|json|webmanifest|png|jpg|jpeg|webp|svg|ico|woff2?|gif|txt|xml)'
# 따옴표·괄호 안 상대 길 — 스킴(http:, data:)·「//」·「#」·빈칸·이어 붙이기 조각(끝이 / 또는 앞이 +)은 뺀다
길꼴 = re.compile(r'''(?<![\w$.+])(["'`(])((?:\./|/)?(?:[\w가-힣%-]+/)*[\w가-힣%.@-]+\.''' + 부를확장 + r''')(?:[?#][^"'`)\s]*)?(?=["'`)])''')
def 검사(묶, 조용히=False):
    묶 = os.path.abspath(묶); 결함 = []; 본 = 0; 셈 = 0
    for 뿌리, _, 파일들 in os.walk(묶):
        for f in 파일들:
            if not f.endswith(글확장): continue
            p = os.path.join(뿌리, f)
            try: s = open(p, encoding='utf-8', errors='ignore').read()
            except Exception: continue
            s = re.sub(r'/\*.*?\*/|<!--.*?-->', ' ', s, flags=re.S); s = re.sub(r'(?m)(^|[^:\'"\\])//[^\n]*', r'\1', s)   # 주석 속 개발 파일 이름은 빼기
            s = re.sub(r'''download\s*[=:]\s*["'][^"']*["']|\.download\s*=\s*[^;]+''', ' ', s)   # 내려받기 이름(파일을 부르지 않음)
            for m in 길꼴.finditer(s):
                u = m.group(2)
                if u.startswith('//') or ':' in u.split('/')[0]: continue
                앞 = s[max(0, m.start() - 1):m.start()]
                if 앞 in '+': continue
                기준 = 묶 if u.startswith('/') else 뿌리
                대상 = os.path.normpath(os.path.join(기준, u.lstrip('/')))
                대상 = os.path.normpath(os.path.join(기준, __import__('urllib.parse').parse.unquote(u.lstrip('/'))))
                if not 대상.startswith(묶): continue
                셈 += 1
                if not os.path.isfile(대상):
                    # 묶음 뿌리 기준으로도 한 번 더(앱이 첫 화면 기준 상대 길을 쓰는 경우가 많다)
                    다른 = os.path.normpath(os.path.join(묶, __import__('urllib.parse').parse.unquote(u.lstrip('./'))))
                    # 약지도: loadJSON('x.json') 은 data/ 를, 오프라인 목록의 말 파일은 data/i18n/ 을 앞에 붙인다
                    더 = [os.path.join(묶, 'data', u.lstrip('./')), os.path.join(묶, 'data', 'i18n', u.lstrip('./'))]
                    if os.path.isfile(다른): 대상 = 다른
                    elif any(os.path.isfile(x) for x in 더): 대상 = next(x for x in 더 if os.path.isfile(x))
                    else: 결함.append(('없음', os.path.relpath(p, 묶), u)); continue
                본 += 1
                if 대상.endswith(('.js', '.mjs', '.css', '.json', '.webmanifest')):
                    try: 첫 = open(대상, 'rb').read(200).decode('utf-8', 'ignore').lstrip('﻿ \t\r\n').lower()
                    except Exception: 첫 = ''
                    if 첫.startswith('<!doctype') or 첫.startswith('<html'):
                        결함.append(('html', os.path.relpath(p, 묶), u))
    중복없음 = sorted(set(결함))
    if not 조용히 or 중복없음:
        print('묶음 파일 검사 %s — 부르는 길 %d · 확인 %d · 결함 %d' % (os.path.relpath(묶), 셈, 본, len(중복없음)))
        for k, a, u in 중복없음[:40]: print('  ❌ %s · %s 가 부르는 %s' % ('없는 파일(사이트에선 첫 화면이 대신 감)' if k == '없음' else 'HTML 이 들어 있음', a, u))
    return len(중복없음)
if __name__ == '__main__':
    n = 검사(sys.argv[1], '--조용히' in sys.argv)
    sys.exit(1 if n else 0)
