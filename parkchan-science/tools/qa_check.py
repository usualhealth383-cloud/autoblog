#!/usr/bin/env python3
"""조판 기하 검증기 — 빌드마다 자동 실행되어 레이아웃 규칙 위반을 잡는다.

검사 항목:
  R1 콘텐츠 하한선: 어떤 요소도 페이지 하단 보호구역(쪽번호 영역) 침범 금지
  R2 괘선 최소 간격: 서로 다른 요소의 가로 괘선끼리 2.5mm 미만 접근 금지
  R3 괘선 교차: 가로 괘선이 세로 괘선(날개단 구분선 등)을 관통 금지
  R4 그림 참조: 발문에 '그림'이 있으면 해당 문항 안에 figure 필수
사용: python3 qa_check.py <chapter.html> [--floor-mm 258]
위반이 있으면 exit 1.
"""
import json, re, subprocess, sys, tempfile, pathlib

CHROME = "/opt/pw-browsers/chromium"

JS = """
<script id="qa-script">
function qaRun(){
  const MM = 96/25.4, FLOOR_MM = %FLOOR%, GAP_MM = 2.5;
  const out = {floor:[], gap:[], cross:[], fig:[]};
  const pages = [...document.querySelectorAll('.page, .sheet')];
  pages.forEach((pg, pi) => {
    const pr = pg.getBoundingClientRect();
    const floorY = pr.top + FLOOR_MM*MM;
    const hRules = [], vRules = [];
    [...pg.querySelectorAll('*')].forEach(el => {
      if (el.closest('.folio') || el.classList.contains('folio')) return;
      if (el.closest('svg')) return;
      const r = el.getBoundingClientRect();
      if (r.width === 0 && r.height === 0) return;
      // R1: 하한선 (오프너 배지 등 절대요소 포함, folio 제외)
      if (r.bottom > floorY + 0.6*MM && r.top < floorY)
        out.floor.push({p:pi+1, el:qaName(el), overmm:+((r.bottom-floorY)/MM).toFixed(1)});
      // 괘선 수집
      const cs = getComputedStyle(el);
      const bt = parseFloat(cs.borderTopWidth)||0, bb = parseFloat(cs.borderBottomWidth)||0;
      const bl = parseFloat(cs.borderLeftWidth)||0, br2 = parseFloat(cs.borderRightWidth)||0;
      const isBox = bt>0.1 && bb>0.1 && bl>0.1 && br2>0.1;   // 상자형은 제외
      if (!isBox){
        if (bt>0.1) hRules.push({el, y:r.top, x1:r.left, x2:r.right});
        if (bb>0.1) hRules.push({el, y:r.bottom, x1:r.left, x2:r.right});
        if (bl>0.1 && r.height > 8*MM) vRules.push({el, x:r.left, y1:r.top, y2:r.bottom});
        if (br2>0.1 && r.height > 8*MM) vRules.push({el, x:r.right, y1:r.top, y2:r.bottom});
      }
    });
    // R2: 서로 다른 요소의 가로 괘선 접근 (같은 요소·부모자식 제외)
    for (let i=0;i<hRules.length;i++) for (let j=i+1;j<hRules.length;j++){
      const a=hRules[i], b=hRules[j];
      if (a.el===b.el || a.el.contains(b.el) || b.el.contains(a.el)) continue;
      const gap = Math.abs(a.y-b.y)/MM;
      const xOverlap = Math.min(a.x2,b.x2) - Math.max(a.x1,b.x1);
      if (gap < %GAP% && xOverlap > 10*MM)
        out.gap.push({p:pi+1, a:qaName(a.el), b:qaName(b.el), gapmm:+gap.toFixed(2)});
    }
    // R3: 가로 괘선이 세로 괘선 관통
    hRules.forEach(h => vRules.forEach(v => {
      if (h.el===v.el || h.el.contains(v.el) || v.el.contains(h.el)) return;
      if (h.x1 < v.x-1 && h.x2 > v.x+1 && h.y > v.y1+1 && h.y < v.y2-1)
        out.cross.push({p:pi+1, h:qaName(h.el), v:qaName(v.el)});
    }));
    // R4: '그림' 언급 문항에 figure 존재
    [...pg.querySelectorAll('.q')].forEach(q => {
      const stem = q.querySelector('.stem');
      if (stem && /그림/.test(stem.textContent) && !q.querySelector('figure'))
        out.fig.push({p:pi+1, q:(q.querySelector('.qno')||{}).textContent||'?'});
    });
  });
  const pre = document.createElement('pre'); pre.id='qa-report';
  pre.textContent = 'QA-REPORT-BEGIN' + JSON.stringify(out) + 'QA-REPORT-END';
  document.body.appendChild(pre);
}
function qaName(el){
  return el.tagName.toLowerCase() + (el.className && typeof el.className==='string' ? '.'+el.className.split(' ')[0] : '');
}
if (document.readyState === 'complete') qaRun();
else window.addEventListener('load', () => document.fonts ? document.fonts.ready.then(qaRun) : qaRun());
</script>
"""

def main():
    src = pathlib.Path(sys.argv[1]).resolve()
    floor = "258"; gap = "2.5"
    if "--floor-mm" in sys.argv: floor = sys.argv[sys.argv.index("--floor-mm")+1]
    html = src.read_text(encoding="utf-8")
    js = JS.replace("%FLOOR%", floor).replace("%GAP%", gap)
    tmp = src.parent / "_qa_tmp.html"
    tmp.write_text(html.replace("</body>", js + "</body>"), encoding="utf-8")
    try:
        dom = subprocess.run([CHROME, "--headless=new", "--no-sandbox", "--disable-gpu",
                              "--virtual-time-budget=5000", "--dump-dom", f"file://{tmp}"],
                             capture_output=True, text=True, timeout=120).stdout
    finally:
        tmp.unlink(missing_ok=True)
    m = re.search(r'<pre id="qa-report">QA-REPORT-BEGIN(.*?)QA-REPORT-END</pre>', dom, re.S)
    if not m:
        print("QA FAIL: 리포트 생성 실패 (렌더링 오류)"); sys.exit(2)
    import html as htmlmod
    rep = json.loads(htmlmod.unescape(m.group(1)))
    bad = False
    for key, label in [("floor","R1 하한선 침범"), ("gap","R2 괘선 간격 미달"),
                       ("cross","R3 괘선 교차"), ("fig","R4 그림 참조 누락")]:
        for v in rep[key]:
            bad = True
            print(f"  ✗ {label}: {v}")
    if bad:
        print("QA FAIL"); sys.exit(1)
    print(f"QA PASS — {src.name}: 하한선·괘선 간격·괘선 교차·그림 참조 모두 통과")

if __name__ == "__main__":
    main()
