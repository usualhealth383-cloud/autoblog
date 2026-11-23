"""11-19 생활 상식 30문(현욱님) — 제목·바꿔 말한 질문 40개가 묻기 답으로 그 글에 닿고(40/40) 찾기 1위인지(39/40 — 「변비, 약 말고」는 변비 증상 화면이 1위). python3 yakjido/tests/life.py (빌드 뒤)"""
import json,http.server,socketserver,threading,functools,pathlib
from playwright.sync_api import sync_playwright
R=pathlib.Path(__file__).resolve().parents[2]; D=R/'docs'/'yakjido'
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(s,*a): pass
srv=socketserver.TCPServer(('127.0.0.1',0),functools.partial(Q,directory=str(D)));threading.Thread(target=srv.serve_forever,daemon=True).start()
SEED="localStorage.setItem('yakjido.hello.v1','1');localStorage.setItem('yakjido.consent.v1',JSON.stringify({v:'2026-10-20',at:'2026-11-18',terms:1,privacy:1}))"
L=json.load(open(R/'yakjido'/'content'/'tips.life.json'))
QS=[(t['id'],t['title']) for t in L]+[('life-vitc','비타민C 많이 먹으면 어떻게 돼요'),('life-vitc-cold','비타민 C 먹으면 감기 안 걸려요?'),('life-nasal-spray','코 스프레이 매일 뿌려도 돼요?'),('life-shampoo','설페이트 프리 샴푸 쓰면 머리 덜 빠지나요'),('life-when-er','이 정도면 병원 가야 하나요'),('life-broccoli','브로콜리 몸에 좋아요?'),('life-honey-baby','8개월 아기 꿀 먹여도 돼요?'),('life-stack','영양제 여러 개 같이 먹어도 되나요'),('life-water','물 하루에 몇 잔 마셔야 해요'),('life-cold-abx','감기인데 항생제 먹어야 하나요')]
with sync_playwright() as p:
    b=p.chromium.launch(executable_path='/opt/pw-browsers/chromium',args=['--no-sandbox']);pg=b.new_context(locale='ko-KR',service_workers='block').new_page();pg.add_init_script(SEED)
    pg.goto(f'http://127.0.0.1:{srv.server_address[1]}/?old=1#/home');pg.wait_for_function("()=>window.__답짓기 && D.drugs && D.drugs.length")
    pg.evaluate("()=>{lexLoad();pubIndexSoon();findLoad();return ensureCore&&ensureCore()}");pg.wait_for_function("()=>(D.tips||[]).some(t=>t.id&&t.id.startsWith('life-'))",timeout=60000);pg.wait_for_timeout(1500)
    ok1=ok2=0;bad=[]
    for want,q in QS:
        r=pg.evaluate("q=>{const a=window.__답짓기(q);const s=search(q)[0];return {a:a&&(a.위험?'위험':JSON.stringify(a.단||[])),top:s?s.h:''}}",q)
        a_ok=want in (r['a'] or ''); s_ok=r['top']=='/tips?open='+want
        ok1+=a_ok; ok2+=s_ok
        if not(a_ok and s_ok): bad.append((q,want,a_ok,r['top']))
    print('답',ok1,'/',len(QS),'· 찾기 1위',ok2,'/',len(QS))
    for x in bad: print(' ',x)
    b.close()
import sys; sys.exit(0 if ok1 == len(QS) and ok2 >= len(QS) - 1 else 1)
