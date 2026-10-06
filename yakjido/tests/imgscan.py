#!/usr/bin/env python3
"""사진이 «뜬» 폰 화면 훑기 — 바깥 사진을 가짜 PNG 로 채우고 증상·약(제품 칸)·제품 화면 216곳의 잘림·넘침·좁은 글자를 본다.
샌드박스에서는 식약처 사진이 안 떠서 사진 칸 CSS 가 검사에 안 걸린다(2026-10-06 약 카드 글자가 44px 칸에 갇힘).
사용: (docs/yakjido 를 8765 에 띄운 뒤) python3 yakjido/tests/imgscan.py
"""
import os, pathlib
import sys,re,io
src=(pathlib.Path(__file__).parent/'run.py').read_text(encoding='utf-8')
OV=re.search(r'OVERFLOW_JS = """(.*?)"""',src,re.S).group(1)
from playwright.sync_api import sync_playwright
from PIL import Image
b_=io.BytesIO(); Image.new('RGB',(300,300),(200,220,230)).save(b_,'PNG'); PNG=b_.getvalue()
with sync_playwright() as p:
    _c='/opt/pw-browsers/chromium-1194/chrome-linux/chrome'
    b=p.chromium.launch(**({'executable_path':_c} if os.path.exists(_c) else {}))
    pg=b.new_page(viewport={'width':360,'height':800})
    pg.route('**/*', lambda r: r.fulfill(status=200,content_type='image/png',body=PNG) if r.request.resource_type=='image' and 'localhost' not in r.request.url else r.continue_())
    pg.goto('http://localhost:8765/index.html#/home'); pg.wait_for_timeout(2500)
    pg.evaluate("localStorage.setItem('yakjido.hello.v1','1')")
    routes=pg.evaluate("()=>D.symptoms.map(s=>'/symptom/'+s.id).concat(D.drugs.map(d=>'/drug/'+d.id)).concat(['/pub/0','/pub/5','/pub/20','/drugs','/home'])")
    bad=[]
    for r in routes:
        pg.goto('http://localhost:8765/index.html#'+r); pg.wait_for_timeout(700)
        for tab in (['p3'] if r.startswith('/drug/') else []):
            try: pg.click(f'button.tab[data-p={tab}]',timeout=800); pg.wait_for_timeout(300)
            except Exception: pass
        o=pg.evaluate(OV)
        n=pg.evaluate("()=>[...document.querySelectorAll('#view b, #view small, #view span')].filter(e=>e.textContent.trim().length>6 && e.getBoundingClientRect().width>0 && e.getBoundingClientRect().width<60 && e.children.length===0).map(e=>e.textContent.trim().slice(0,12)).slice(0,3)")
        if o['ov'] or o['clip'] or n: bad.append((r,o['ov'],o['clip'],n))
    print(len(routes),'routes'); [print(x) for x in bad[:30]]
    b.close()
