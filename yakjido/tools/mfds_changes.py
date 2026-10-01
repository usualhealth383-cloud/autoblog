#!/usr/bin/env python3
"""식약처 «허가사항 변경명령» 새 소식 중 약지도 일반약 성분에 걸리는 것만 골라 보여 준다.

2026-10-01 처음 손으로 150건을 대조하다 만든 도구. 기미약(트라넥삼산)이 비타민 화면에 가 있던 것,
이부프로펜 시럽 어린이 용량이 바뀐 것도 이 대조에서 나왔다 — 그래서 정기적으로 돌린다.

사용:  python3 yakjido/tools/mfds_changes.py            # 지난번 이후 새 항목만
       python3 yakjido/tools/mfds_changes.py --pages 10 --all   # 최근 500건 전부 다시 보기
       python3 yakjido/tools/mfds_changes.py --mark      # 지금 본 것을 «본 것»으로 적어 둠(mfds_seen.json)

나온 항목은 상세(getItem) → 첨부 zip/hwpx 의 변경대비표를 읽고, «대상 품목»(xlsx·상세 표)으로
제형을 꼭 확인한다 — 주사제만·처방 단일제만인 경우가 많다. 반영하면 출처 키 mfds_<성분>_<연도>.
"""
import argparse, glob, html, json, pathlib, re, subprocess, time

ROOT = pathlib.Path(__file__).resolve().parent.parent
SEEN = pathlib.Path(__file__).resolve().parent / 'mfds_seen.json'
BASE = 'https://nedrug.mfds.go.kr'


def curl(url):
    # 의약품안전나라는 연결을 자주 끊는다 — 몇 번 다시 시도
    for t in range(6):
        r = subprocess.run(['curl', '-sS', '-m', '40', url], capture_output=True)
        if r.returncode == 0 and r.stdout: return r.stdout.decode('utf-8', 'ignore')
        time.sleep(2 + t * 2)
    raise RuntimeError('받지 못함: ' + url)


def otc_names():
    """약 사전의 일반약·안전상비약 이름 → 약 id. 괄호·제형 꼬리를 떼고 세 글자 이상만."""
    out = {}
    for f in glob.glob(str(ROOT / 'content' / 'drugs*.json')):
        for d in json.loads(pathlib.Path(f).read_text(encoding='utf-8')):
            if d.get('rx') not in ('일반', '안전상비'): continue
            for n in re.split(r'[·,/]', re.sub(r'\s*\(.*', '', d['name'])):
                n = re.sub(r'(크림|연고|겔|패치|파스|정|시럽|액|안약|스프레이)$', '', n.strip())
                if len(n) >= 3: out[n] = d['id']
    return out


def rows(pages):
    for p in range(1, pages + 1):
        s = curl(f'{BASE}/CCBAR01F012/getList?page={p}&limit=50')
        for r in re.findall(r'(?s)<tr>(.*?)</tr>', s):
            cells = [re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', c))).strip()
                     for c in re.findall(r'(?s)<td[^>]*>(.*?)</td>', r)]
            link = re.search(r'infoNo=(\d+)&(?:amp;)?infoClassCode=(\d+)', r)
            if cells and link and len(cells) > 5: yield cells, link.groups()
        time.sleep(1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--pages', type=int, default=2)
    ap.add_argument('--all', action='store_true', help='본 것도 다시 보기')
    ap.add_argument('--mark', action='store_true', help='이번에 나온 것을 본 것으로 적기')
    a = ap.parse_args()
    seen = json.loads(SEEN.read_text(encoding='utf-8')) if SEEN.exists() else {}
    names = otc_names(); hits = []
    for cells, (no, cl) in rows(a.pages):
        key = f'{no}:{cl}'   # 같은 번호도 단계(의견조회 2 → 사전예고 3 → 변경명령 4)가 바뀌면 새로 본다
        ids = sorted({names[n] for n in names if n in cells[1]})
        if not ids or (key in seen and not a.all): continue
        hits.append((key, cells, ids))
    for key, c, ids in hits:
        print(f'· {c[1][:70]} | {c[2]} | 단계 {c[5]} | 반영 {c[4] or "-"} | 앱 {", ".join(ids)}')
        print(f'  {BASE}/CCBAR01F012/getList/getItem?infoNo={key.split(":")[0]}&infoClassCode={key.split(":")[1]}')
    print(f'\n새로 볼 것 {len(hits)}건 (목록 {a.pages * 50}건 중)')
    if a.mark:
        for key, c, ids in hits: seen[key] = {'t': c[1][:80], 'ids': ids, 'checked': time.strftime('%Y-%m-%d')}
        SEEN.write_text(json.dumps(seen, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
        print('본 것으로 적음 →', SEEN)


if __name__ == '__main__':
    main()
