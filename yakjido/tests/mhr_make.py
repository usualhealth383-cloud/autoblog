"""시험용 가짜 «나의건강기록 투약 이력» PDF 두 개(그냥 · 암호 1234)를 만든다 — 실제 칸 모양은 실제 파일이 오면 맞춘다(11-19)."""
import datetime, pathlib, sys
from playwright.sync_api import sync_playwright
from pypdf import PdfReader, PdfWriter
H = pathlib.Path(__file__).resolve().parent; F = H.parents[1] / 'docs' / 'yakjido' / 'fonts'
d = lambda n: (datetime.date.today() - datetime.timedelta(days=n)).strftime('%Y.%m.%d')
R = [(d(5), '○○약국', '타이레놀정500밀리그램', '아세트아미노펜', '3', '30'), (d(10), '○○약국', '노바스크정5밀리그램', '암로디핀베실산염', '1', '90'),
     (d(12), '○○약국', '넥시움정20밀리그램', '에스오메프라졸마그네슘삼수화물', '1', '28'), (d(40), '△△약국', '무코스타정(레바미피드)', '레바미피드', '3', '7'),
     (d(60), '△△약국', '가나다라마바사정', '모르는성분', '1', '5'), (d(400), '□□약국', '판콜에이내복액', '아세트아미노펜 외', '3', '3')]
font = next(iter(sorted(F.glob('*.woff2'))), None)
html = ('<html><head><meta charset="utf-8"><style>' + (f"@font-face{{font-family:P;src:url('{font.as_uri()}')}}" if font else '') + 'body{font-family:P,sans-serif;font-size:12px}td,th{border:1px solid #999;padding:4px}</style></head><body>'
        '<h2>내가 먹는 약 — 투약 이력 (최근 1년)</h2><p>성명: 홍길동 · 조회일 ' + d(0) + '</p><table><tr><th>조제일자</th><th>조제기관</th><th>약품명</th><th>성분명</th><th>1일 투여횟수</th><th>투약일수</th></tr>'
        + ''.join('<tr>' + ''.join(f'<td>{c}</td>' for c in r) + '</tr>' for r in R) + '</table><p>건강보험심사평가원 자료</p></body></html>')
out = H / 'q'; (out / 'mhr.html').write_text(html, encoding='utf-8')
with sync_playwright() as p:
    b = p.chromium.launch(executable_path='/opt/pw-browsers/chromium', args=['--no-sandbox']); pg = b.new_page(); pg.goto((out / 'mhr.html').as_uri()); pg.wait_for_timeout(500)
    pg.pdf(path=str(out / '가짜_투약이력.pdf'), format='A4'); b.close()
(out / 'mhr.html').unlink()
w = PdfWriter(clone_from=str(out / '가짜_투약이력.pdf')); w.encrypt('1234', algorithm='RC4-128'); w.write(str(out / '가짜_투약이력_암호1234.pdf'))
print('ok', [x.name for x in out.glob('가짜*')])
