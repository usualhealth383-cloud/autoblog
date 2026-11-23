"""11-23 Main 숨긴 시험 220(yozm-health _도구/시험_약지도_숨긴말.json · 하청이 앱을 보지 않고 씀). 문장은 출력하지 않는다 — 숫자만.
앱 답의 급함: 119(응급 카드) · 오늘진료(경고 카드이거나 오늘·바로 진료·응급실 말) · 집에서(그 밖) · 답없음.
쓰는 법: python3 yakjido/tests/hidden220.py [묶음번호…] [--show 1]  (--show 는 묶음 1 만 허용: 고칠 때 그 묶음 문장·답을 tsv 로)"""
import sys, json, pathlib, collections, re, http.server, socketserver, threading, functools
from playwright.sync_api import sync_playwright
R = pathlib.Path(__file__).resolve().parents[2]; D = R / 'docs' / 'yakjido'
SRC = pathlib.Path('/home/user/yozm-health/_도구/시험_약지도_숨긴말.json')
args = [a for a in sys.argv[1:] if not a.startswith('--')]; SHOW = '--show' in sys.argv
BUN = set(int(a) for a in args) if args else {1, 2, 3}
if SHOW and BUN != {1}: sys.exit('문장 보기는 묶음 1 만 — 2 는 숫자만, 3 은 출시 직전까지 열지 않기')
Q = [x for x in json.load(open(SRC))['물음'] if x['묶음'] in BUN]
class H(http.server.SimpleHTTPRequestHandler):
    def log_message(s, *a): pass
srv = socketserver.TCPServer(('127.0.0.1', 0), functools.partial(H, directory=str(D))); threading.Thread(target=srv.serve_forever, daemon=True).start()
SEED = "localStorage.setItem('yakjido.hello.v1','1');localStorage.setItem('yakjido.consent.v1',JSON.stringify({v:'2026-10-20',at:'2026-11-18',terms:1,privacy:1}))"
with sync_playwright() as p:
    b = p.chromium.launch(executable_path='/opt/pw-browsers/chromium', args=['--no-sandbox'])
    pg = b.new_context(locale='ko-KR', timezone_id='Asia/Seoul', service_workers='block').new_page(); pg.add_init_script(SEED)
    pg.goto(f'http://127.0.0.1:{srv.server_address[1]}/?old=1#/home'); pg.wait_for_function("()=>window.__답짓기 && D.drugs && D.drugs.length")
    pg.evaluate("()=>{lexLoad();pubIndexSoon();findLoad();return ensureCore()}"); pg.wait_for_function("()=>!LEX.loading && PUB.index && PUB.index.length>100", timeout=60000); pg.wait_for_timeout(1500)
    A = pg.evaluate("""L=>L.map(q=>{let a=null;try{a=window.__답짓기(q)}catch(e){}
      const tx=x=>Array.isArray(x)?x.map(tx).join(' / '):x&&typeof x==='object'?(x.t||x.말||''):String(x||'');
      if(!a) return {lv:'답없음',t:''}; if(a.위험) return {lv:'119',t:tx(a.위험.말)};
      const t=[a.결||'',tx(a.할||[])].join(' ');
      return {lv:(a.위||/오늘|바로\\s*(진료|병원|응급실)|지금\\s*(병원|진료|응급실)|응급실|119/.test(t))?'오늘진료':'집에서',t:t}})""", [x['말'] for x in Q])
    b.close()
srv.shutdown()
def tally(S, tag):
    c = collections.Counter
    n119 = [x for x, a in S if x['급함'] == '지금119']; today = [x for x, a in S if x['급함'] == '오늘진료']
    m1 = sum(1 for x, a in S if x['급함'] == '지금119' and a['lv'] != '119')
    m1a = sum(1 for x, a in S if x['급함'] == '지금119' and a['lv'] == '오늘진료'); m1b = m1 - m1a
    m2 = sum(1 for x, a in S if x['급함'] == '오늘진료' and a['lv'] in ('집에서', '답없음'))
    m3 = sum(1 for x, a in S if x['급함'] == '오늘진료' and a['lv'] == '119')
    m4 = sum(1 for x, a in S if x['함정'] and a['lv'] == '119')
    m5 = sum(1 for x, a in S if a['lv'] == '답없음')
    m6 = c(a['lv'] for x, a in S if x['애매'])
    home119 = sum(1 for x, a in S if x['급함'] in ('집에서', '며칠안') and not x['함정'] and a['lv'] == '119')
    ok = lambda x, a: (x['급함'] == '지금119' and a['lv'] == '119') or (x['급함'] == '오늘진료' and a['lv'] == '오늘진료') or (x['급함'] == '며칠안' and a['lv'] in ('오늘진료', '집에서')) or (x['급함'] == '집에서' and a['lv'] in ('집에서', '답없음'))
    acc = sum(1 for x, a in S if ok(x, a)); over = sum(1 for x, a in S if x['급함'] == '집에서' and a['lv'] == '오늘진료')
    print(f"{tag}: 단계 정확도 {acc}/{len(S)} · 집에서→오늘진료(과하게) {over}")
    print(f"{tag}: ① 지금119 놓침 {m1}/{len(n119)}(오늘로 {m1a} · 집·답없음 {m1b}) · ② 오늘진료→집에서 {m2}/{len(today)} · ③ 오늘진료→119 {m3} · ④ 함정 거짓 경보 {m4}/{sum(1 for x,a in S if x['함정'])} · 집에서·며칠안(함정 아님)→119 {home119} · 답 없음 {m5}/{len(S)} · ⑥ 애매 {dict(m6)}")
S = list(zip(Q, A))
for k in sorted(BUN): tally([s for s in S if s[0]['묶음'] == k], f'묶음 {k}')
if len(BUN) > 1: tally(S, '전체')
if SHOW:
    out = ['번\t급함\t갈래\t함정\t애매\t앱\t말\t앱 첫 줄']
    for x, a in S: out.append('\t'.join(map(str, [x['번'], x['급함'], x['갈래'], x['함정'], x['애매'], a['lv'], x['말'], a['t'][:90]])).replace('\n', ' '))
    (R / 'yakjido' / 'tests' / 'q' / '숨긴220_묶음1_답.tsv').write_text('\n'.join(out) + '\n')
