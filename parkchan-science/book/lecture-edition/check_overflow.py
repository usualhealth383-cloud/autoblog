#!/usr/bin/env python3
"""강의용 교재 페이지 넘침 검사 — 각 .page에서 폴리오를 제외한 가장 깊은 요소의 바닥(mm)을 측정.
   사용: python3 check_overflow.py L-2203.html   (257mm 초과 시 DEEP 플래그, 종료코드 1)"""
import subprocess, re, sys, pathlib, html as h, json
src = pathlib.Path(sys.argv[1]).resolve()
css = (src.parent / 'lecture.css').read_text(encoding='utf-8')
js = """
<script>
function run(){
  const MM=96/25.4, out=[];
  document.querySelectorAll('.page').forEach((pg,i)=>{
    const pr=pg.getBoundingClientRect();
    let deep=0, dEl='';
    [...pg.querySelectorAll('*')].forEach(el=>{ if(el.closest('.folio')||el.closest('.tagband'))return; const r=el.getBoundingClientRect(); if(r.height>0&&r.bottom>deep){deep=r.bottom;dEl=el.tagName+'.'+(el.className||'').split(' ')[0];}});
    out.push({p:i+1, deep:+((deep-pr.top)/MM).toFixed(1), dEl});
  });
  const pre=document.createElement('pre'); pre.id='rep';
  pre.textContent='BEGIN'+JSON.stringify(out)+'END'; document.body.appendChild(pre);
}
if(document.readyState==='complete') run(); else window.addEventListener('load',()=>document.fonts?document.fonts.ready.then(run):run());
</script>
"""
html_txt = src.read_text(encoding='utf-8').replace('<link rel="stylesheet" href="lecture.css">', '<style>\n'+css+'\n</style>')
tmp = src.parent / ('_ov_' + src.name)
tmp.write_text(html_txt.replace('</body>', js+'</body>'), encoding='utf-8')
dom = subprocess.run(['/opt/pw-browsers/chromium','--headless=new','--no-sandbox','--disable-gpu','--virtual-time-budget=5000','--dump-dom',f'file://{tmp}'],capture_output=True,text=True,timeout=180).stdout
tmp.unlink()
m = re.search(r"<pre id=\"rep\">BEGIN(.*?)END</pre>", dom, re.S)
bad = 0
for row in json.loads(h.unescape(m.group(1))):
    flag = ' DEEP>257 (넘침)' if row['deep'] > 257 else ''
    if flag: bad += 1
    print(f"p{row['p']:>2}  deep={row['deep']:>6}mm  {row['dEl']}{flag}")
print('OVERFLOW FAIL' if bad else 'OVERFLOW PASS')
sys.exit(1 if bad else 0)
