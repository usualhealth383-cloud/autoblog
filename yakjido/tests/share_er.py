# 외부 검수 2차 #3 — 부모님께 보내기: 증상(sym:)을 함께 담고, 받는 화면에 «바로 119» 신호가 보이는지(서버는 가짜 응답)
# 쓰기: python3 yakjido/tests/share_er.py
import http.server, socketserver, threading, functools, json, sys
from playwright.sync_api import sync_playwright
import pathlib
D=str(pathlib.Path(__file__).resolve().parents[2]/'docs'/'yakjido')
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*a): pass
srv=socketserver.TCPServer(('127.0.0.1',0),functools.partial(Q,directory=D)); threading.Thread(target=srv.serve_forever,daemon=True).start()
url=f'http://127.0.0.1:{srv.server_address[1]}/'
SEED="localStorage.setItem('yakjido.hello.v1','1');localStorage.setItem('yakjido.consent.v1',JSON.stringify({v:'2026-10-20',at:'2026-10-14',terms:1,privacy:1}))"
VIS="()=>{const w=document.createTreeWalker(document.querySelector('#view'),NodeFilter.SHOW_TEXT);let o='';while(w.nextNode()){const p=w.currentNode.parentElement;if(p&&p.offsetParent!==null&&p.getClientRects().length){const r=p.getBoundingClientRect();if(r.width>0&&r.height>0)o+=w.currentNode.textContent}}return o.replace(/\\s+/g,' ')}"
CAP=[]
with sync_playwright() as p:
    b=p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome', args=['--no-sandbox'])
    ctx=b.new_context(viewport={'width':390,'height':844}); ctx.add_init_script(SEED)
    def h(route):
        body=json.loads(route.request.post_data or '{}'); CAP.append(body)
        if body.get('action')=='create': route.fulfill(status=200,content_type='application/json',body=json.dumps({'code':'A'*22,'expires_at':'2030-01-01'}),headers={'Access-Control-Allow-Origin':'*'})
        else: route.fulfill(status=200,content_type='application/json',body=json.dumps({'items':[{'id':'ibuprofen','name':'이부프로펜','product':''},{'id':'sym:headache','name':'두통'}],'label':'엄마','note':None,'expires_at':'2030-01-01','bought_at':None}),headers={'Access-Control-Allow-Origin':'*'})
    ctx.route('**/yak-share',h)
    pg=ctx.new_page(); errs=[]; pg.on('pageerror',lambda e: errs.append(str(e)))
    pg.goto(url+'#/send?s=headache'); pg.wait_for_timeout(1200)
    pg.check('#send-ok'); pg.evaluate("()=>{navigator.share=undefined; navigator.clipboard.writeText=async t=>{window.__T=t}}")
    pg.click('text=보내기 >> nth=-1'); pg.wait_for_timeout(1500)
    its=[c.get('items') for c in CAP if c.get('action')=='create']; fails=[]
    if not its or not any(i['id']=='sym:headache' for i in its[0]): fails.append('보낼 때 증상(sym:) 줄이 없음')
    if '바로 119' not in (pg.evaluate('window.__T') or ''): fails.append('보내는 글에 119 줄 없음')
    pg.goto(url+'#/p/'+'A'*22); pg.wait_for_timeout(1800)
    t=pg.inner_text('#view')
    if '바로 119' not in t: fails.append('받는 화면에 119 신호 없음')
    if pg.evaluate("()=>document.querySelectorAll('.ps-item').length")!=1: fails.append('증상 줄이 약 목록에 섞임')
    if errs: fails.append('JS 오류 '+errs[0])
    b.close()
    print('부모님 링크 응급 신호(외부 검수 2차 #3):', '통과' if not fails else fails); raise SystemExit(1 if fails else 0)
