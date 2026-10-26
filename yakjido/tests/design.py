#!/usr/bin/env python3
"""약지도 디자인 점검기(2026-10-22 · 메디나눔 「디자인 만족도 100」 — 공용 점검기 _도구/검증_*.mjs 를 약지도 화면에 맞춰 옮김).

재는 것(화면마다 · 폭 320/360/390 · 글자 보통/가장 크게 · 밝게/어둡게 중 필요한 조합만):
  ① 손가락 — 누를 수 있는 것을 화면 가운데로 옮겨 놓고, 가운데에서 사방으로 elementFromPoint 가 그것을 돌려주는 데까지(36px 아래면 결함)
  ② 칸 속의 칸 — 테두리·그림자 있는 상자가 폭 차 24px 안쪽으로 또 그런 상자 안에 바로 든 곳
  ③ 글자 크기 — 「가장 크게」(22px)에서 화면 글자가 실제로 커지는지(보통 대비 1.2배 미만인 글자 덩어리)
  ④ 넘침 — 320px · 가장 크게에서 가로 넘침(스크롤 상자 안은 뺌)
  ⑤ 빈 화면 — 기록 없는 사람으로 열었을 때 누를 것이 하나도 없는 화면
  ⑥ 행동 깊이 — 첫 누를 것(뒤로·탭·검색 빼고)이 처음 화면 높이의 몇 배 아래에 있나(1.5 넘으면 결함)
쓰는 법: python3 yakjido/tests/design.py  (docs/yakjido 를 띄워 잰다 — 빌드 뒤에)
"""
import http.server, socketserver, threading, functools, pathlib, sys
from playwright.sync_api import sync_playwright

# 시험 브라우저는 한국어·서울 시간대로 연다(10-27 다섯 언어 — 안 정하면 en-US·UTC 라 영어 화면이 된다. 나라는 시간대가 먼저라 i18n.py 가 en-US+서울 → 119 를 따로 본다)
from playwright.sync_api import Browser as _B
_np, _nc = _B.new_page, _B.new_context
_B.new_page = lambda self, **k: _np(self, **{'locale': 'ko-KR', 'timezone_id': 'Asia/Seoul', **k})
_B.new_context = lambda self, **k: _nc(self, **{'locale': 'ko-KR', 'timezone_id': 'Asia/Seoul', **k})

D = pathlib.Path(__file__).resolve().parent.parent.parent / 'docs' / 'yakjido'
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
srv = socketserver.TCPServer(('127.0.0.1', 0), functools.partial(Q, directory=str(D)))
threading.Thread(target=srv.serve_forever, daemon=True).start()
URL = f'http://127.0.0.1:{srv.server_address[1]}/'
SEED = "localStorage.setItem('yakjido.hello.v1','1');localStorage.setItem('yakjido.consent.v1',JSON.stringify({v:'2026-10-20',at:'2026-10-14',terms:1,privacy:1}))"
ROUTES = ['/home', '/symptom/headache', '/symptom/msk', '/symptom/cold', '/symptom/diarrhea', '/symptom/fever', '/show/headache', '/send',
          '/bag', '/drug/acetaminophen', '/drug/ibuprofen?full=1', '/search?q=타이레놀', '/supp', '/supp/calcium', '/kids', '/schedule',
          '/vitals', '/me?t=meds', '/me?t=body', '/me?t=set', '/together', '/kinds', '/kinds/bp', '/rx', '/rx/bp', '/about', '/myths', '/drugs']

READ_ONLY = {'/about', '/myths'}  # 읽는 화면(근거·오해 풀이) — 글이 먼저인 것이 맞다

FINGER = """()=>{const out=[];const own=(el,x,y)=>{const e=document.elementFromPoint(x,y);return !!e&&(e===el||el.contains(e)||[...(el.labels||[])].some(l=>l===e||l.contains(e)))};
 for(const el of document.querySelectorAll('#view button, #view a[href], #view summary, #view [role=button], #view input[type=checkbox], #view input[type=radio], nav.tabbar a, nav.tabbar button')){
  const r0=el.getBoundingClientRect(); if(!r0.width||!r0.height||getComputedStyle(el).visibility==='hidden') continue;
  try{el.scrollIntoView({block:'center'})}catch(e){} const r=el.getBoundingClientRect(); if(r.top<0||r.bottom>innerHeight) continue;
  const cx=Math.round(r.left+r.width/2), cy=Math.round(r.top+r.height/2); if(!own(el,cx,cy)) continue;
  const go=(dx,dy)=>{let n=0;while(n<30&&own(el,cx+dx*(n+1),cy+dy*(n+1)))n++;return n};
  const w=go(-1,0)+go(1,0)+1, h=go(0,-1)+go(0,1)+1;
  if(w<36||h<36) out.push((el.tagName.toLowerCase()+'.'+String(el.className||'').trim().split(/\\s+/)[0])+' '+w+'×'+h+' «'+(el.textContent||el.getAttribute('aria-label')||'').trim().replace(/\\s+/g,' ').slice(0,16)+'»'); }
 return [...new Set(out)]; }"""
NEST = """()=>{const box=e=>{const s=getComputedStyle(e);return (parseFloat(s.borderTopWidth)>0&&s.borderTopStyle!=='none'&&parseFloat(s.borderLeftWidth)>0)||(s.boxShadow&&s.boxShadow!=='none')};
 const out=[]; for(const e of document.querySelectorAll('#view *')){ if(!box(e)||!e.offsetParent) continue; const p=e.parentElement; if(!p||!box(p)) continue;
  const a=e.getBoundingClientRect(), b=p.getBoundingClientRect(); if(a.width<120||b.width-a.width>24||a.height<30) continue;
  if(/^(INPUT|BUTTON|SELECT|TEXTAREA|IMG|SVG)$/.test(e.tagName)) continue;
  out.push(p.className.toString().split(' ')[0]+' > '+e.className.toString().split(' ')[0]); } return [...new Set(out)]; }"""
TEXTS = """()=>{const m={};const w=document.createTreeWalker(document.querySelector('#view'),NodeFilter.SHOW_TEXT);let i=0;
 while(w.nextNode()){const p=w.currentNode.parentElement,t=w.currentNode.textContent.trim(); if(!p||!t||t.length<2||!p.offsetParent) continue;
  const k=(p.className||p.tagName)+'|'+t.slice(0,20); if(!(k in m)) m[k]=parseFloat(getComputedStyle(p).fontSize); if(++i>400) break;} return m; }"""
OVER = """()=>{const W=document.documentElement.clientWidth;const out=[];for(const e of document.querySelectorAll('#view *')){const r=e.getBoundingClientRect();if(!r.width||r.right<=W+1)continue;
 let q=e.parentElement,sc=false;while(q&&q.id!=='view'){const s=getComputedStyle(q);if(/(auto|scroll|hidden)/.test(s.overflowX)){sc=true;break}q=q.parentElement}if(sc)continue;
 out.push((e.tagName.toLowerCase()+'.'+String(e.className||'').split(' ')[0])+' +'+Math.round(r.right-W)+'px')}return [...new Set(out)].slice(0,4)}"""
DEPTH = """()=>{const H=innerHeight;window.scrollTo(0,0);let best=null;for(const el of document.querySelectorAll('#view button, #view a[href], #view summary, #view input')){
 if(el.closest('.top,.topfind,.tabs,.stabs,.dtabs,.back,.search,.view-seg,.crumb')) continue; const r=el.getBoundingClientRect(); if(!r.width||!r.height) continue;
 const y=r.top+scrollY; if(best===null||y<best) best=y;} return best===null?null:+(best/H).toFixed(2);}"""

def main():
    fails = []
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome', args=['--no-sandbox'])
        def page(w, fs='16px', theme='light'):
            pg = b.new_page(viewport={'width': w, 'height': 800})
            pg.add_init_script(SEED + f";localStorage.setItem('yakjido.fs','{fs}');localStorage.setItem('yakjido.theme','{theme}')")
            pg.goto(URL + '#/home'); pg.wait_for_function("()=>typeof CORE!=='undefined' && CORE===2", timeout=20000); pg.wait_for_timeout(400)
            return pg
        def go(pg, r):
            pg.evaluate("h=>{location.hash=h; route();}", r); pg.wait_for_timeout(450)
        # ① 손가락 · ② 칸 속의 칸 · ⑥ 행동 깊이 · ⑤ 빈 화면 — 390 보통(새 사람)
        pg = page(390)
        for r in ROUTES:
            go(pg, r)
            f = pg.evaluate(FINGER)
            if f: fails.append(f'① 손가락 {r}: {f[:4]}')
            n = pg.evaluate(NEST)
            if n: fails.append(f'② 칸 속의 칸 {r}: {n[:3]}')
            d = pg.evaluate(DEPTH)
            if d is None: fails.append(f'⑤ 빈 화면 {r}: 누를 것이 없어요')
            elif d > 1.5 and r not in READ_ONLY: fails.append(f'⑥ 행동 깊이 {r}: 첫 누를 것이 {d}화면 아래')
        pg.close()
        # ③ 글자 크기 — 보통 vs 가장 크게(같은 화면 같은 글 덩어리)
        a, z = page(390, '16px'), page(390, '22px')
        for r in ['/home', '/symptom/headache', '/drug/acetaminophen', '/me?t=set', '/rx/bp', '/kids']:
            go(a, r); go(z, r); A = a.evaluate(TEXTS); Z = z.evaluate(TEXTS)
            small = [k for k in A if k in Z and A[k] and Z[k] / A[k] < 1.2]
            if small: fails.append(f'③ 글자 크기 {r}: 가장 크게에서 안 커지는 글 {len(small)}곳 — {[s.split("|")[1] for s in small[:3]]}')
        a.close(); z.close()
        # ④ 넘침 — 320 · 가장 크게 · 밝게/어둡게
        for th in ('light', 'dark'):
            pg = page(320, '22px', th)
            for r in ROUTES:
                go(pg, r); o = pg.evaluate(OVER)
                if o: fails.append(f'④ 넘침 320·가장 크게·{th} {r}: {o}')
            pg.close()
        b.close()
    print(f'디자인 점검 — 화면 {len(ROUTES)}개')
    if fails:
        print('결함', len(fails)); [print('  ✗', f) for f in fails]; sys.exit(1)
    print('✓ 결함 0 — 손가락 36px · 칸 속의 칸 · 글자 크기 · 320 넘침 · 빈 화면 · 행동 깊이')

if __name__ == '__main__':
    main()
