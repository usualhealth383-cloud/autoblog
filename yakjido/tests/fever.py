"""해열제 숫자 = 공용 해열제 부품(정본) — 11-17 현욱님 두 층 결정. 1분.
 ① 몸무게 3~80 kg × 생후 3~180개월: 1회 mL 범위·하루 최대가 부품(mL범위·doseRange)과 같다(부품이 오기 전 셈도)
 ② 쉽게 보기 한 숫자는 그 범위 위 끝을 넘지 않는다 ③ 생후 3개월 미만 화면에 mL 숫자가 없다"""
import http.server, socketserver, threading, functools, pathlib, sys, json, datetime
from playwright.sync_api import sync_playwright
D = pathlib.Path(__file__).resolve().parents[2] / 'docs' / 'yakjido'
class _Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
srv = socketserver.TCPServer(('127.0.0.1', 0), functools.partial(_Q, directory=str(D))); threading.Thread(target=srv.serve_forever, daemon=True).start()
URL = f'http://127.0.0.1:{srv.server_address[1]}/'
SEED = "localStorage.setItem('yakjido.hello.v1','1');localStorage.setItem('yakjido.consent.v1',JSON.stringify({v:'2026-10-20',at:'2026-11-17',terms:1,privacy:1}));"
bad = []
def ok(c, m):
    print(('  ✓ ' if c else '  ✘ ') + m)
    if not c: bad.append(m)
d = datetime.date.today(); y, mo = d.year, d.month - 2
if mo <= 0: mo += 12; y -= 1
with sync_playwright() as p:
    b = p.chromium.launch(executable_path='/opt/pw-browsers/chromium', args=['--no-sandbox'])
    pg = b.new_page(locale='ko-KR'); pg.add_init_script(SEED)
    pg.goto(URL + '#/kids'); pg.wait_for_function('!!window.메디나눔해열제', timeout=20000)
    r = pg.evaluate("""(()=>{const P=window.메디나눔해열제, out=[], fb=[], over=[];
      for (const k of ['apap','ibu']) for (let m=3;m<=180;m+=3) for (let w=3; w<=80; w+=0.35) {
        const r=kidDose(k,w,m); if(!r) continue; const a=mlRange(r), q=P.mL범위(k,w,m), g=P.doseRange(k,w,m);
        if (a[0]!==q.lo || a[1]!==q.hi || Math.abs(r.day-g.day)>0.5) out.push([k,m,w.toFixed(2)]);
        const one=kidOne(r); if (+one.ml > +q.hi + 1e-9) over.push([k,m,w.toFixed(2),one.ml,q.hi]); const e=P.쉬운양?P.쉬운양(k,w,m):null; if (e && !e.막힘 && String(one.ml)!==String(e.mL글)) over.push(['쉬운양≠',k,m,w.toFixed(2),one.ml,e.mL글]);
        const keep=window.메디나눔해열제; window.메디나눔해열제=null; const r2=kidDose(k,w,m), a2=mlRange(r2); window.메디나눔해열제=keep;
        if (a2[0]!==q.lo || a2[1]!==q.hi || Math.abs(r2.day-g.day)>0.5) fb.push([k,m,w.toFixed(2)]); }
      return {out:out.slice(0,5), n:out.length, fb:fb.length, fbex:fb.slice(0,3), over:over.slice(0,5), nover:over.length, 판:P.판}; })()""")
    ok(r['n'] == 0, f"부품({r['판']})과 1회 mL·하루 최대가 같다 — 다른 곳 {r['n']} {r['out']}")
    ok(r['fb'] == 0, f"부품이 오기 전 셈도 같다 — {r['fb']} {r['fbex']}")
    ok(r['nover'] == 0, f"쉽게 보기 한 숫자 = 부품 쉬운양 · ≤ 범위 위 끝 — 어긋남 {r['nover']} {r['over']}")
    pg2 = b.new_page(locale='ko-KR', timezone_id='Asia/Seoul'); pg2.add_init_script(SEED + f"localStorage.setItem('yakjido.me.v1',JSON.stringify({{child:{{name:'',birth:'{y}-{mo:02d}-{min(d.day,28):02d}',weight:5}}}}))")
    pg2.goto(URL + '#/kids'); pg2.wait_for_function('!!window.메디나눔해열제', timeout=20000); pg2.wait_for_timeout(800)
    t = pg2.inner_text('#view')
    import re
    pg.evaluate("()=>{ME.child={name:'',birth:'2024-01-01',weight:13};route();document.querySelectorAll('details').forEach(d=>d.open=true)}"); pg.wait_for_timeout(300)
    ok('기준 정함' in pg.inner_text('body') and '의료진 검토' not in pg.inner_text('body'), '화면에 «의료진 검토» 말 없음(「기준 정함」 꼴)')
    ok(pg2.locator('.dose-card').count() == 0 and '3개월이 지나면 여기에' in t and '지금 응급실' in t and not re.search(r'1회\s*\d', t), '생후 2개월 — 용량 칸 없이 위 경고 하나(응급실·119)')
    b.close()
srv.shutdown()
print('해열제 숫자:', '흠 ' + str(len(bad)) if bad else '전부 통과')
sys.exit(1 if bad else 0)
