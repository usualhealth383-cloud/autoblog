#!/usr/bin/env python3
"""MarkItDown 래퍼 — 자료 파일(PDF/DOCX/PPTX/XLSX/HTML/이미지 등)을 Markdown으로 변환.
사용:
  python3 tools/md_convert.py <입력파일> [출력.md]      # 파일 1개
  python3 tools/md_convert.py <폴더> --out <폴더>        # 폴더 일괄
변환 결과는 교재 집필의 '근거 텍스트'로만 쓴다 — 저작물 원문을 교재에 그대로 옮기지 않는다.
"""
import sys, pathlib, warnings, logging, os, contextlib
warnings.filterwarnings("ignore")
logging.disable(logging.WARNING)
from markitdown import MarkItDown

EXT = {'.pdf','.docx','.pptx','.xlsx','.xls','.html','.htm','.csv','.json','.xml',
       '.txt','.md','.epub','.png','.jpg','.jpeg','.zip'}

def convert(md, src: pathlib.Path, dst: pathlib.Path):
    try:
        with open(os.devnull,"w") as _n, contextlib.redirect_stderr(_n):
            r = md.convert(str(src))
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(r.text_content, encoding='utf-8')
        n = len(r.text_content)
        print(f'  ✓ {src.name} → {dst}  ({n:,}자)')
        return True
    except Exception as e:
        print(f'  ✗ {src.name}: {type(e).__name__} {e}')
        return False

def main():
    a = sys.argv[1:]
    if not a:
        print(__doc__); sys.exit(1)
    md = MarkItDown()
    src = pathlib.Path(a[0])
    if src.is_dir():
        out = pathlib.Path(a[a.index('--out')+1]) if '--out' in a else src/'_md'
        ok = sum(convert(md, f, out/(f.stem+'.md')) for f in sorted(src.rglob('*')) if f.suffix.lower() in EXT)
        print(f'완료: {ok}개')
    else:
        dst = pathlib.Path(a[1]) if len(a) > 1 and not a[1].startswith('--') else src.with_suffix('.md')
        convert(md, src, dst)

main()
