"""부정 말 시험(11-18 Main · 너스텝 교훈) — 「A 말고/빼고/대신/아니고/아닌 B」에서 A(뺀 약)로 안내하면 오안내.
 찾기 1위와 묻기 답의 첫 약 이름이 뺀 약이면 실패. 쓰는 법: python3 yakjido/tests/negation.py (빌드 뒤)"""
import http.server, socketserver, threading, functools, pathlib, sys, json
from playwright.sync_api import sync_playwright
D = pathlib.Path(__file__).resolve().parents[2] / 'docs' / 'yakjido'
# (질문, 빼야 할 것 — 1위·답 첫머리에 나오면 안 되는 이름 조각)
Q = [('타이레놀 말고 이부', '타이레놀'), ('타이레놀 말구 다른 진통제', '타이레놀'), ('아스피린 빼고 진통제', '아스피린'), ('이부프로펜 대신 먹을 약', '이부프로펜'),
     ('부루펜 아니고 해열제', '부루펜'), ('게보린 아닌 두통약', '게보린'), ('판콜 말고 감기약', '판콜'), ('탁센 빼고 생리통약', '탁센'),
     ('타이레놀 말고 아이 해열제', '타이레놀'), ('이부 말고 타이레놀', '이부프로펜'), ('펜잘 대신 뭐 먹어요', '펜잘'), ('아세트아미노펜 아니고 소염제', '아세트아미노펜'),
     ('나프록센 빼고 진통제', '나프록센'), ('지르텍 말고 알레르기약', '지르텍'), ('훼스탈 대신 소화제', '훼스탈'), ('개비스콘 아니고 속쓰림약', '개비스콘'),
     ('스트렙실 말고 목 아플 때', '스트렙실'), ('부스코판 빼고 배 아플 때', '부스코판'), ('챔프 말구 해열제', '챔프'), ('이지엔 아닌 진통제', '이지엔')]
class _Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
srv = socketserver.TCPServer(('127.0.0.1', 0), functools.partial(_Q, directory=str(D))); threading.Thread(target=srv.serve_forever, daemon=True).start()
URL = f'http://127.0.0.1:{srv.server_address[1]}/?old=1'
SEED = "localStorage.setItem('yakjido.hello.v1','1');localStorage.setItem('yakjido.consent.v1',JSON.stringify({v:'2026-10-20',at:'2026-11-18',terms:1,privacy:1}))"
with sync_playwright() as p:
    b = p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome', args=['--no-sandbox'])
    pg = b.new_context(locale='ko-KR', timezone_id='Asia/Seoul', service_workers='block').new_page(); pg.add_init_script(SEED); pg.goto(URL + '#/home')
    pg.wait_for_function("()=>typeof search==='function' && D.drugs && D.drugs.length && window.__답짓기")
    pg.evaluate("()=>{lexLoad();pubIndexSoon();findLoad();}"); pg.wait_for_function("()=>!LEX.loading && PUB.index && PUB.index.length>100", timeout=60000); pg.wait_for_timeout(1500)
    R = pg.evaluate("""L=>L.map(([q,x])=>{ const s=search(q), t1=s[0]?s[0].t:'', h1=s[0]?s[0].h:''; let a=null; try{a=window.__답짓기(q)}catch(e){};
      const f=a?(a.위험?a.위험.말:(a.결||'')):'', ex=(window.__부정&&window.__부정(q)||{}).ids||[], d0=JSON.stringify((a&&a.단||[])[0]||'');
      const exd=ex.some(i=>h1.split('?')[0]==='/drug/'+i);
      return {q, x, top:t1, first:f.slice(0,60), badS: t1.replace(/\\s/g,'').includes(x) || exd, badA: f.slice(0,24).includes(x) || ex.some(i=>d0.includes('/drug/'+i))}; })""", Q)
    b.close()
srv.shutdown()
bad = [r for r in R if r['badS'] or r['badA']]
for r in R: print(('✘ ' if (r['badS'] or r['badA']) else '✓ ') + r['q'], '| 1위:', r['top'], '| 답:', r['first'])
print(f'부정 말 {len(Q)} — 오안내 {len(bad)} (찾기 1위 {sum(r["badS"] for r in R)} · 묻기 답 {sum(r["badA"] for r in R)})')
sys.exit(1 if bad else 0)
