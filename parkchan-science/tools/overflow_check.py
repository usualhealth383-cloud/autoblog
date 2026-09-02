import subprocess, re, sys, pathlib, html as h, json
src = pathlib.Path(sys.argv[1]).resolve()
js = """
<script>
function run(){
  const MM=96/25.4, out=[];
  document.querySelectorAll('.page').forEach((pg,i)=>{
    const pr=pg.getBoundingClientRect();
    const main=pg.querySelector('.main'), qc=pg.querySelector('.quickcheck');
    let mainBot=null, qcTop=null, maxBot=0, maxEl='';
    if(main){ [...main.querySelectorAll('*')].forEach(el=>{const r=el.getBoundingClientRect(); if(r.height>0&&r.bottom>maxBot){maxBot=r.bottom;maxEl=el.tagName+'.'+(el.className||'').split(' ')[0];}}); mainBot=+((maxBot-pr.top)/MM).toFixed(1);}
    if(qc){ qcTop=+((qc.getBoundingClientRect().top-pr.top)/MM).toFixed(1); }
    // absolute deepest element except folio
    let deep=0, dEl='';
    [...pg.querySelectorAll('*')].forEach(el=>{ if(el.closest('.folio'))return; const r=el.getBoundingClientRect(); if(r.height>0&&r.bottom>deep){deep=r.bottom;dEl=el.tagName+'.'+(el.className||'').split(' ')[0];}});
    out.push({p:i+1, mainBot, qcTop, deep:+((deep-pr.top)/MM).toFixed(1), dEl, maxEl});
  });
  const pre=document.createElement('pre'); pre.id='rep';
  pre.textContent='BEGIN'+JSON.stringify(out)+'END'; document.body.appendChild(pre);
}
if(document.readyState==='complete') run(); else window.addEventListener('load',()=>document.fonts?document.fonts.ready.then(run):run());
</script>
"""
html_txt = src.read_text(encoding='utf-8')
tmp = src.parent/'_m.html'
tmp.write_text(html_txt.replace('</body>', js+'</body>'), encoding='utf-8')
dom = subprocess.run(['/opt/pw-browsers/chromium','--headless=new','--no-sandbox','--disable-gpu','--virtual-time-budget=5000','--dump-dom',f'file://{tmp}'],capture_output=True,text=True,timeout=120).stdout
tmp.unlink()
m = re.search(r"<pre id=\"rep\">BEGIN(.*?)END</pre>", dom, re.S)
for row in json.loads(h.unescape(m.group(1))):
    flag = ''
    if row['qcTop'] and row['mainBot'] and row['mainBot'] > row['qcTop']: flag='OVERLAP'
    if row['deep'] > 256: flag += ' DEEP>256'
    print(row, flag)
