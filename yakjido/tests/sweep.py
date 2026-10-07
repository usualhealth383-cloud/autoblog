#!/usr/bin/env python3
"""숨은 칸까지 훑기 — 모든 화면의 탭을 하나씩 누르고 접힌 칸(details)을 다 펼쳐서, 밝은·어두운 화면 둘 다
명암비(AA)·가로 넘침·글자 잘림·손가락 크기(44px)를 본다. run.py 는 첫 탭·접힌 상태만 보므로 놓치는 것이 있었다
(2026-10-07: 수유 칩 4.0:1, 달력 날짜, 알림 방법 탭 단추 40px, 소수점 43.99px 등).
사용: (docs/yakjido 를 8765 에 띄운 뒤) python3 yakjido/tests/sweep.py   — 약 20분
"""
import re,ast,json
from playwright.sync_api import sync_playwright
import pathlib,os
src=(pathlib.Path(__file__).parent/'run.py').read_text(encoding='utf-8')
lit=lambda n: ast.literal_eval(re.search(n+r' = (""".*?""")',src,re.S).group(1))
CJS,OV,TAP=lit('CONTRAST_JS'),lit('OVERFLOW_JS'),lit('TAP_JS')
R=re.search(r'routes = pg.evaluate\("(.*?)"\s*\+\s*\n\s*"(.*?)"\)',src,re.S)
ROUTE_JS=(R.group(1)+R.group(2)).replace('\\"','"')
res={'contrast':{},'ov':{},'tap':{}}
def add(kind,key,where): res[kind].setdefault(key,[]).append(where)
with sync_playwright() as p:
    _c='/opt/pw-browsers/chromium-1194/chrome-linux/chrome'
    b=p.chromium.launch(**({'executable_path':_c} if os.path.exists(_c) else {}))
    pg=b.new_page(viewport={'width':390,'height':844})
    pg.goto('http://localhost:8765/index.html#/home'); pg.wait_for_timeout(2500)
    pg.evaluate("localStorage.setItem('yakjido.hello.v1','1');localStorage.setItem('yakjido.me.v1',JSON.stringify({age:'senior',pregnant:true,taking:['acetaminophen','cls:bp.arb'],pub:{}}))")
    pg.reload(); pg.wait_for_timeout(2500)
    routes=pg.evaluate(ROUTE_JS)
    for theme in ['light','dark']:
        pg.emulate_media(color_scheme=theme)
        for r in routes:
            pg.goto('http://localhost:8765/index.html#'+r); pg.wait_for_timeout(300)
            tabs=pg.evaluate("()=>[...document.querySelectorAll('#view .tab[data-p]')].map(b=>b.dataset.p)") or [None]
            for tb in tabs:
                if tb:
                    try: pg.click(f'#view .tab[data-p="{tb}"]',timeout=1000); pg.wait_for_timeout(100)
                    except Exception: continue
                pg.evaluate("()=>document.querySelectorAll('#view details').forEach(d=>d.open=true)"); pg.wait_for_timeout(80)
                w=f'{theme}:{r}:{tb}'
                for x in pg.evaluate(CJS): add('contrast',json.dumps(x,ensure_ascii=False)[:100],w)
                o=pg.evaluate(OV)
                for x in o['ov']+o['clip']: add('ov',str(x)[:80],w)
                for x in pg.evaluate(TAP): add('tap',str(x)[:60],w)
    b.close()
for k in res:
    print('==',k,len(res[k]))
    for key,ws in sorted(res[k].items(),key=lambda kv:-len(kv[1]))[:15]: print(' ',key,'|',len(ws),ws[:3])
