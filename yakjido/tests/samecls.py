"""같은 갈래 두 약(PPI 둘 · 소염진통제 둘 · 아세트아미노펜 복합 둘)이 겹침 카드(stop/warn)로 잡히나 — 11-18 Main 안전 확인. 쓰는 법: python3 yakjido/tests/samecls.py (빌드 뒤)"""
import http.server, socketserver, threading, functools, json
from playwright.sync_api import sync_playwright
import pathlib, sys
D=str(pathlib.Path(__file__).resolve().parents[2]/'docs'/'yakjido')
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*a): pass
srv=socketserver.TCPServer(('127.0.0.1',0),functools.partial(Q,directory=D)); threading.Thread(target=srv.serve_forever,daemon=True).start()
U=f'http://127.0.0.1:{srv.server_address[1]}/'
SEED="localStorage.setItem('yakjido.hello.v1','1');localStorage.setItem('yakjido.consent.v1',JSON.stringify({v:'2026-10-20',at:'2026-11-18',terms:1,privacy:1}));"
with sync_playwright() as p:
    b=p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome',args=['--no-sandbox'])
    pg=b.new_page(); pg.add_init_script(SEED); pg.goto(U+'#/home'); pg.wait_for_function("()=>typeof ixRun==='function'&&D.drugs&&D.drugs.length")
    pg.evaluate("()=>{pubIndexSoon&&pubIndexSoon();}"); pg.wait_for_function("()=>PUB.index&&PUB.index.length>100",timeout=60000)
    r=pg.evaluate("""()=>{ME.taking=[];const dr=id=>D.drugs.find(d=>d.id===id);
      const C=[['PPI 둘(오메프라졸+에스오메프라졸 넥시움)',[dr('omeprazole'),{name:'넥시움정 20 mg',ings:ingFind('에스오메프라졸마그네슘삼수화물')}]],
        ['PPI 둘(넥시움+오엠피)',[{name:'넥시움정',ings:ingFind('에스오메프라졸')},{name:'오엠피정',ings:ingFind('오메프라졸')}]],
        ['NSAID 둘(이부프로펜+나프록센)',[dr('ibuprofen'),dr('naproxen')]],['NSAID 둘(이부프로펜+덱시부프로펜)',[dr('ibuprofen'),dr('dexibuprofen')]],
        ['NSAID 둘(아스피린+세레콕시브)',[dr('aspirin'),dr('celecoxib')]],
        ['아세트아미노펜 둘(타이레놀+판콜에이)',[dr('acetaminophen'),dr('pancol-a')]],['아세트아미노펜 복합 둘(펜잘+게보린)',[dr('penzal'),dr('geworin')]]];
      return C.map(([n,L])=>{const c=ixCards(ixRun(L));return n+' → '+(c.length?c.map(x=>x.lv+':'+String(x.t||x.title||x.h||'').replace(/<[^>]+>/g,'').slice(0,40)).join(' / '):'카드 없음 ✘')})}""")
    print('\n'.join(r)); bad=[x for x in r if not (' stop:' in x or ' warn:' in x)]
    nm=pg.evaluate("()=>{const d=D.drugs.find(x=>x.id==='omeprazole');return d.name}")
    b.close()
srv.shutdown()
print('같은 갈래 둘', len(r), '건 — 놓침', len(bad)); sys.exit(1 if bad else 0)
