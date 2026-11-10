#!/usr/bin/env python3
"""약지도 디자인 점검기(2026-10-22 · 메디나눔 「디자인 만족도 100」 — 공용 점검기 _도구/검증_*.mjs 를 약지도 화면에 맞춰 옮김).

재는 것(화면마다 · 폭 320/360/390 · 글자 보통/가장 크게 · 밝게/어둡게 중 필요한 조합만):
  ① 손가락 — 누를 수 있는 것을 화면 가운데로 옮겨 놓고, 가운데에서 사방으로 elementFromPoint 가 그것을 돌려주는 데까지(36px 아래면 결함)
  ② 칸 속의 칸 — 테두리·그림자 있는 상자가 폭 차 24px 안쪽으로 또 그런 상자 안에 바로 든 곳
  ③ 글자 크기 — 「가장 크게」(22px)에서 화면 글자가 실제로 커지는지(보통 대비 1.2배 미만인 글자 덩어리)
  ④ 넘침 — 320px · 가장 크게에서 가로 넘침(스크롤 상자 안은 뺌)
  ⑤ 빈 화면 — 기록 없는 사람으로 열었을 때 누를 것이 하나도 없는 화면
  ⑥ 행동 깊이 — 첫 누를 것(뒤로·탭·검색 빼고)이 처음 화면 높이의 몇 배 아래에 있나(1.5 넘으면 결함)
  ⑦ 정렬(11-10 현욱님 「정렬 깨진 것 없는지 쭉 확인」) — 폭 60% 넘는 단추 글자 가운데(중심 차 ≤ 6px) · 글자 잘림 0 · 같은 목록 왼쪽 끝 일치 · 보이는 글자 겹침 0 · 위쪽 빈 띠 200px 이상 0 · 아이콘·글자 세로 가운데(≤ 3px)
     320·360·390·420 × 보통·가장 크게(밝게) + 390 어둡게
쓰는 법: python3 yakjido/tests/design.py  (docs/yakjido 를 띄워 잰다 — 빌드 뒤에)
"""
import http.server, socketserver, threading, functools, pathlib, sys
from playwright.sync_api import sync_playwright

# 시험 브라우저는 한국어로 연다(10-27 — 안 정하면 en-US 라 영어 화면이 된다). 시간대는 그대로(UTC — 알림 시험이 이 시계에 맞춰져 있다, UTC 는 나라 판단에서 건너뛰어 ko-KR → KR). en-US+서울 → 119 는 i18n.py 가 따로 본다
from playwright.sync_api import Browser as _B
_np, _nc = _B.new_page, _B.new_context
_B.new_page = lambda self, **k: _np(self, **{'locale': 'ko-KR', **k})
_B.new_context = lambda self, **k: _nc(self, **{'locale': 'ko-KR', **k})

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

ALIGN = r"""()=>{const W=document.documentElement.clientWidth, V=document.getElementById('view')||document.body, out=[];
const vis=e=>{const r=e.getBoundingClientRect();if(!r.width||!r.height)return null;const cs=getComputedStyle(e);if(cs.visibility==='hidden'||cs.display==='none'||+cs.opacity===0)return null;if(r.width<=2&&r.height<=2||cs.clip&&cs.clip!=='auto')return null;let d=e.closest('details');while(d){if(!d.open){const sm=d.querySelector(':scope>summary');if(!(sm&&sm.contains(e)))return null;}d=d.parentElement&&d.parentElement.closest('details');}return r;};
const tx=e=>{const R=document.createRange(),w=document.createTreeWalker(e,NodeFilter.SHOW_TEXT);let L=null,n;while((n=w.nextNode())){if(!n.textContent.trim()||n.parentElement.closest('svg'))continue;{const pr=n.parentElement.getBoundingClientRect();if(pr.width<=2&&pr.height<=2)continue;}R.selectNodeContents(n);const b=R.getBoundingClientRect();if(b.width){L=L?{l:Math.min(L.l,b.left),r:Math.max(L.r,b.right),t:Math.min(L.t,b.top),b:Math.max(L.b,b.bottom)}:{l:b.left,r:b.right,t:b.top,b:b.bottom};}}return L;};
const tr=e=>{const R=document.createRange();let L=null;for(const n of e.childNodes){if(n.nodeType===3&&n.textContent.trim()){R.selectNodeContents(n);const b=R.getBoundingClientRect();if(b.width){L=L?{l:Math.min(L.l,b.left),r:Math.max(L.r,b.right),t:Math.min(L.t,b.top),b:Math.max(L.b,b.bottom)}:{l:b.left,r:b.right,t:b.top,b:b.bottom};}}}return L;};
const nm=e=>(e.className&&typeof e.className==='string'?e.className.split(' ')[0]:e.tagName.toLowerCase())+' «'+(e.innerText||'').trim().slice(0,14)+'»';
/* ① 넓은 단추 글자 가운데 */
for(const e of V.querySelectorAll('.btn,.call,.door-go,.go-cart')){const r=vis(e);if(!r||r.width<W*0.6)continue;const t=(()=>{const R=document.createRange();R.selectNodeContents(e);const b=R.getBoundingClientRect();return b.width?{l:b.left,r:b.right,h:b.height}:null;})();if(!t)continue;if(t.h>parseFloat(getComputedStyle(e).fontSize)*1.9)continue;   /* 두 줄로 꺾인 단추는 줄마다 가운데라 묶음 중심이 어긋나 보여도 정상 */
 const d=Math.abs((t.l+t.r)/2-(r.left+r.right)/2);if(d>6)out.push('가운데 '+Math.round(d)+'px '+nm(e));}
/* ② 글자 잘림 */
for(const e of V.querySelectorAll('*')){if(e.children.length)continue;const r=vis(e);if(!r||!(e.textContent||'').trim())continue;const cs=getComputedStyle(e);
 if((cs.textOverflow==='ellipsis'||cs.overflow==='hidden'||cs.overflowX==='hidden')&&e.scrollWidth>e.clientWidth+1&&!e.closest('svg'))out.push('잘림 '+nm(e));}
/* ③ 같은 목록 왼쪽 끝 */
for(const L of V.querySelectorAll('ul,ol,.rows,.rows-l,.buy,.dose-list,.chips.s4')){const ks=[...L.children].map(c=>[c,vis(c)]).filter(x=>x[1]&&getComputedStyle(x[0]).position!=='absolute');if(ks.length<2)continue;
 const g=getComputedStyle(L);if(g.display==='flex'&&g.flexDirection.startsWith('row')||g.display.includes('grid')&&g.gridTemplateColumns.split(' ').length>1)continue;
 const l0=ks[0][1].left;const bad=ks.filter(x=>Math.abs(x[1].left-l0)>2);if(bad.length)out.push('왼쪽 끝 '+nm(L)+' '+Math.round(bad[0][1].left-l0)+'px');}
/* ④ 보이는 글자 겹침 — 줄마다의 글 상자(getClientRects)끼리. 여러 줄로 꺾인 글을 한 상자로 보면 옆 줄 굵은 글과 겹친 것처럼 보인다 */
const T=[], LR=[];for(const e of V.querySelectorAll('*')){if(e.closest('svg,.sr,.toast,[aria-hidden="true"]'))continue;const t=tr(e);if(!t||!vis(e))continue;if(t.r-t.l<2)continue;T.push([e,t]);
 const R=document.createRange(),rs=[];for(const n of e.childNodes){if(n.nodeType===3&&n.textContent.trim()){R.selectNodeContents(n);for(const q of R.getClientRects())if(q.width>2)rs.push(q);}}LR.push([e,rs]);}
const fixd=e=>{for(let x=e;x&&x!==document.body;x=x.parentElement){const p=getComputedStyle(x).position;if(p==='sticky'||p==='fixed')return true;}return false;};
for(let i=0;i<LR.length&&out.length<40;i++)for(let j=i+1;j<LR.length;j++){const [a,A]=LR[i],[b,B]=LR[j];if(a.contains(b)||b.contains(a))continue;let hit=false;
 for(const p of A){for(const q of B){const ox=Math.min(p.right,q.right)-Math.max(p.left,q.left), oy=Math.min(p.bottom,q.bottom)-Math.max(p.top,q.top);if(ox>4&&oy>0.4*Math.min(p.height,q.height)){hit=true;break;}}if(hit)break;}
 if(hit&&!fixd(a)&&!fixd(b)){out.push('겹침 '+nm(a)+' × '+nm(b));break;}}
/* ⑤ 위쪽 빈 띠 */
const tops=[...T.map(x=>x[1]),...[...V.querySelectorAll('img,svg,canvas,input,select,button,.card,.sec')].map(e=>vis(e)).filter(Boolean).map(r=>({t:r.top,b:r.bottom}))].filter(t=>t.t>0&&t.t<1600).map(t=>[t.t,t.b]).sort((a,b)=>a[0]-b[0]);let lb=null;for(const [t,b] of tops){if(lb!=null&&t-lb>=200){out.push('빈 띠 '+Math.round(t-lb)+'px @'+Math.round(lb));break;}lb=lb==null?b:Math.max(lb,b);}
/* ⑥ 아이콘·글자 세로 가운데 */
for(const e of V.querySelectorAll('button,a,summary,.chip,.badge')){const r=vis(e);if(!r)continue;const s=[...e.children].find(c=>c.tagName==='svg'||c.tagName==='SVG');if(!s)continue;const t=tx(e);if(!t)continue;const sr=s.getBoundingClientRect();if(!sr.height)continue;
 if(t.b-t.t>parseFloat(getComputedStyle(e).fontSize)*1.9)continue;   /* 두 줄 이상이면 아이콘은 첫 줄·가운데 어느 쪽도 정상 */ const d=Math.abs((sr.top+sr.bottom)/2-(t.t+t.b)/2);if(d>3)out.push('아이콘 세로 '+Math.round(d)+'px '+nm(e));}
return [...new Set(out)].slice(0,8);}"""

def main():
    fails = []
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome', args=['--no-sandbox'])
        def page(w, fs='17px', theme='light'):
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
        a, z = page(390, '17px'), page(390, '23px')
        for r in ['/home', '/symptom/headache', '/drug/acetaminophen', '/me?t=set', '/rx/bp', '/kids']:
            go(a, r); go(z, r); A = a.evaluate(TEXTS); Z = z.evaluate(TEXTS)
            small = [k for k in A if k in Z and A[k] and Z[k] / A[k] < 1.2]
            if small: fails.append(f'③ 글자 크기 {r}: 가장 크게에서 안 커지는 글 {len(small)}곳 — {[s.split("|")[1] for s in small[:3]]}')
        a.close(); z.close()
        # ④ 넘침 — 320 · 가장 크게 · 밝게/어둡게
        for th in ('light', 'dark'):
            pg = page(320, '23px', th)
            for r in ROUTES:
                go(pg, r); o = pg.evaluate(OVER)
                if o: fails.append(f'④ 넘침 320·가장 크게·{th} {r}: {o}')
            pg.close()
        # ⑦ 정렬 — 320·360·390·420 × 보통·가장 크게(밝게) + 390 어둡게
        for w, fs, th in [(w, fs, 'light') for w in (320, 360, 390, 420) for fs in ('17px', '23px')] + [(390, '17px', 'dark'), (390, '23px', 'dark')]:
            pg = page(w, fs, th)
            for r in ROUTES:
                go(pg, r); al = pg.evaluate(ALIGN)
                if al: fails.append(f'⑦ 정렬 {w}·{fs}·{th} {r}: {al}')
            pg.close()
        b.close()
    print(f'디자인 점검 — 화면 {len(ROUTES)}개')
    if fails:
        print('결함', len(fails)); [print('  ✗', f) for f in fails]; sys.exit(1)
    print('✓ 결함 0 — 손가락 36px · 칸 속의 칸 · 글자 크기 · 320 넘침 · 빈 화면 · 행동 깊이 · 정렬(가운데·잘림·왼쪽 끝·겹침·빈 띠·아이콘)')

if __name__ == '__main__':
    main()
