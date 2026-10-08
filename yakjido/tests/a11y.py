#!/usr/bin/env python3
"""접근성 검사 — axe-core(웹 접근성 표준 검사기)로 모든 화면과 탭을 훑는다.
구글 플레이 사전 출시 보고서의 접근성 검사기와 같은 계열 규칙(이름·라벨·aria·제목 순서·중복 id 등).
명암비는 run.py 가 따로 보므로 여기서는 끈다. (2026-10-08 출시 점검에서 처음 돌려 3종류를 고침)
사용: (docs/yakjido 를 8765 에 띄운 뒤) python3 yakjido/tests/a11y.py   — 약 20분. 처음 한 번 axe-core 를 npm 으로 받는다.
"""
import re, json, sys, pathlib, collections, subprocess, os
from playwright.sync_api import sync_playwright
HERE = pathlib.Path(__file__).resolve().parent
AXE_DIR = HERE / '.axe'; AXE = AXE_DIR / 'node_modules' / 'axe-core' / 'axe.min.js'
if not AXE.exists():
    AXE_DIR.mkdir(exist_ok=True)
    subprocess.run(['npm', 'install', '--silent', '--prefix', str(AXE_DIR), 'axe-core@4'], check=True)
src = (HERE / 'run.py').read_text(encoding='utf-8')
R = re.search(r'routes = pg.evaluate\("(.*?)"\s*\+\s*\n\s*"(.*?)"\)', src, re.S)
ROUTE_JS = (R.group(1) + R.group(2)).replace('\\"', '"')
AXE_SRC = AXE.read_text(encoding='utf-8')
URL = os.environ.get('YAKJIDO_URL', 'http://localhost:8765/index.html')
res = collections.defaultdict(lambda: {'n': 0, 'impact': '', 'help': '', 'where': [], 'nodes': []})
with sync_playwright() as p:
    _c = '/opt/pw-browsers/chromium-1194/chrome-linux/chrome'
    b = p.chromium.launch(**({'executable_path': _c} if os.path.exists(_c) else {}))
    pg = b.new_page(viewport={'width': 390, 'height': 844})
    pg.goto(URL + '#/home'); pg.wait_for_timeout(2000)
    pg.evaluate("localStorage.setItem('yakjido.hello.v1','1');localStorage.setItem('yakjido.me.v1',JSON.stringify({age:'senior',pregnant:true,taking:['acetaminophen','cls:bp.arb'],pub:{}}))")
    pg.reload(); pg.wait_for_timeout(2000)
    for r in pg.evaluate(ROUTE_JS):
        pg.goto(URL + '#' + r); pg.wait_for_timeout(350)
        for tb in (pg.evaluate("()=>[...document.querySelectorAll('#view .tab[data-p]')].map(b=>b.dataset.p)") or [None]):
            if tb:
                try: pg.click(f'#view .tab[data-p="{tb}"]', timeout=1000); pg.wait_for_timeout(80)
                except Exception: continue
            if not pg.evaluate("()=>!!window.axe"): pg.add_script_tag(content=AXE_SRC)
            for v in pg.evaluate("""async()=>{const r=await axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21a','wcag21aa','best-practice']},rules:{'color-contrast':{enabled:false}}});
                return r.violations.map(v=>({id:v.id,impact:v.impact,help:v.help,nodes:v.nodes.slice(0,3).map(n=>(n.target||[]).join(' ')+' | '+(n.html||'').slice(0,120))}))}"""):
                e = res[v['id']]; e['n'] += 1; e['impact'] = v['impact']; e['help'] = v['help']
                if len(e['where']) < 4: e['where'].append(f'{r}:{tb}')
                for nd in v['nodes']:
                    if nd not in e['nodes'] and len(e['nodes']) < 4: e['nodes'].append(nd)
    b.close()
order = {'critical': 0, 'serious': 1, 'moderate': 2, 'minor': 3}
for k, v in sorted(res.items(), key=lambda kv: (order.get(kv[1]['impact'], 9), -kv[1]['n'])):
    print(f"✗ {k} [{v['impact']}] ×{v['n']} — {v['help']}"); print('   at', v['where']); [print('   ·', n) for n in v['nodes']]
if res: print(f'접근성 실패 {len(res)}종'); sys.exit(1)
print('✓ 접근성 — axe 위반 0 (명암비 제외, run.py 에서 따로)')
