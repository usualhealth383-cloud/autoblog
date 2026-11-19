# 길동무 «임상시험 찾기» — 식약처 공공데이터 임상시험 OpenAPI 받기(2026-11-19 · 현욱님 활용신청 승인 2026-11-19~2028-11-19)
#   키: 깃허브 Secrets DATA_GO_KR_KEY(값은 로그·파일 어디에도 남기지 않는다) · 약지도 yakjido/tools/fetch_mfds.py 의 page() 를 그대로 쓴다.
#   python3 gildongmu/trials/fetch_trials.py probe  — API 마다 3건만(칸 이름·전체 건수) → gildongmu/trials/probe.json
#   python3 gildongmu/trials/fetch_trials.py full   — 전부 받아 암 관련만 거른 묶음 → gildongmu/trials/cancer_trials.json
import json, os, sys, re, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'yakjido', 'tools'))
from fetch_mfds import page, key, fetch_all
import ast, collections
API = {
  '임상시험정보':  'https://apis.data.go.kr/1471000/MdcinClincTestInfoService02/getMdcinClincTestInfoList02',          # 15056835
  '계획상세':      'https://apis.data.go.kr/1471000/ClncExamPlanDtlService03/getClncExamPlanDtlInq03',                  # 15090589
  '선정기준':      'https://apis.data.go.kr/1471000/ClncExamPlanSlctnStndrdService03/getClncExamPlanSlctnStndrdInq03',  # 15090368
  '제외기준':      'https://apis.data.go.kr/1471000/ClncExamPlanExStndrdService03/getClncExamPlanExStndrdInq03',        # 15090376
  '시험책임자':    'https://apis.data.go.kr/1471000/ClncExamPlanTestPscgService04/getClncExamPlanTestPscgInq04',        # 15090384
  '실시기관':      'https://apis.data.go.kr/1471000/ClinicTestOprtnInsttInfoService02/getClinicTestOprtnInsttInfo02',   # 15058129
}
OUT = os.path.dirname(__file__)
def probe(k):
    r = {}
    for n, op in API.items():
        try:
            total, items = page(op, 1, k, 3)
            r[n] = {'건수': total, '칸': sorted({c for it in items for c in it}), '보기': [{c: (str(v)[:80]) for c, v in it.items()} for it in items[:2]]}
            print(f'{n}: {total:,}건 · 칸 {len(r[n]["칸"])}개', flush=True)
        except Exception as e:
            r[n] = {'오류': str(e)[:200]}; print(f'{n}: 오류 {str(e)[:120]}', flush=True)
        time.sleep(1)
    json.dump(r, open(os.path.join(OUT, 'probe.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

암말 = re.compile(r'암|종양|백혈병|림프종|골수종|육종|흑색종|교모세포|신경모세포|중피종|cancer|carcinoma|tumou?r|neoplasm|oncolog|leukemia|lymphoma|myeloma|sarcoma|melanoma|glioma|glioblastoma|malignan', re.I)
def 풀기(it):   # 제외기준·시험책임자는 item 이 글(dict 모양)로 온다
    if isinstance(it, dict) and set(it) == {'item'}:
        v = it['item']
        if isinstance(v, str):
            try: v = ast.literal_eval(v)
            except Exception: return {}
        if isinstance(v, list): v = v[0] if v else {}
        return v if isinstance(v, dict) else {}
    return it
s_ = lambda v: '' if v in (None, 'None') else str(v).strip()
def full(k):
    plans = [풀기(x) for x in fetch_all(API['계획상세'], k, '계획상세')]
    분포 = {'TRGT_DISS_CD_NM': collections.Counter(s_(x.get('TRGT_DISS_CD_NM')) for x in plans).most_common(40),
          'STATUS': collections.Counter(s_(x.get('STATUS')) for x in plans).most_common(20),
          'CLINIC_STEP_NM': collections.Counter(s_(x.get('CLINIC_STEP_NM')) for x in plans).most_common(20)}
    암 = [x for x in plans if re.search(r'oncolog|cancer|tumou?r|neoplas', s_(x.get('TRGT_DISS_CD_NM')), re.I) or 암말.search(s_(x.get('TRGT_DISS_NM')) + ' ' + s_(x.get('TRGT_DISS_DTL_ETC')))]
    번 = {s_(x.get('CLNC_TEST_SN')) for x in 암}
    def 모으기(이름, 칸들):
        d = collections.defaultdict(list)
        for x in fetch_all(API[이름], k, 이름):
            x = 풀기(x); sn = s_(x.get('CLNC_TEST_SN'))
            if sn in 번: d[sn].append({c: s_(x.get(c)) for c in 칸들 if s_(x.get(c))})
        return d
    선 = 모으기('선정기준', ['CHOOSE_EXCL_STDR', 'GENDER', 'AGE'])
    제 = 모으기('제외기준', ['CHOOSE_EXCL_STDR'])
    책 = collections.defaultdict(set)   # 사람 이름은 싣지 않는다 — 기관 이름만
    for x in fetch_all(API['시험책임자'], k, '시험책임자'):
        x = 풀기(x); sn = s_(x.get('CLNC_TEST_SN'))
        if sn in 번:
            for c in ('LAB_NAME', 'EXAM_INSTT_NM', 'INSTT_NM', 'CLNC_INSTT_NM', 'HOSP_NM'):
                if s_(x.get(c)): 책[sn].add(s_(x.get(c)))
    책칸 = sorted({c for x in fetch_all(API['시험책임자'], k, '시험책임자칸')[:5] for c in 풀기(x)})
    기관 = [{c: s_(x.get(c)) for c in ('LAB_SEQ', 'LAB_NAME', 'ADDR1', 'APPOINT_DATE')} for x in fetch_all(API['실시기관'], k, '실시기관')]
    keep = ('CLNC_TEST_SN', 'CLNC_TEST_TITLE', 'CLNC_TEST_ENG_TITLE', 'TRGT_DISS_CD_NM', 'TRGT_DISS_NM', 'TRGT_DISS_DTL_ETC', 'CLINIC_STEP_NM', 'STATUS', 'CLST_APRV_DT',
            'CLST_BGNG_DT', 'CLST_END_DT', 'LAST_TRGTER_SLCTN_DT', 'TEST_COMPLETION_DT', 'CLINICAL_PERIOD', 'TESTEE_CNT_INFO', 'PRDT_NM', 'ORGN_DEV_BSSH_NM', 'ADDR', 'IVSGT_PURPS', 'PLCB_YN', 'RNDM_ASSG_CD_NM')
    out = []
    for x in 암:
        sn = s_(x.get('CLNC_TEST_SN')); r = {c: s_(x.get(c)) for c in keep if s_(x.get(c))}
        r['선정'] = 선.get(sn, []); r['제외'] = 제.get(sn, []); r['기관'] = sorted(책.get(sn, [])); out.append(r)
    meta = {'받은때': time.strftime('%Y-%m-%d'), '출처': '식품의약품안전처 공공데이터(공공데이터포털 15090589·15090368·15090376·15090384·15058129)', '계획상세전체': len(plans), '암': len(out), '분포': 분포, '시험책임자칸': 책칸}
    json.dump({'meta': meta, '시험': out, '실시기관': 기관}, open(os.path.join(OUT, 'cancer_trials.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    json.dump(meta, open(os.path.join(OUT, 'cancer_meta.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('암 시험', len(out), '/', len(plans), flush=True)

def fix(k):   # 11-19 — 제외기준·시험책임자만 다시(item 안에 dict 로 오는 것을 못 풀었던 것)
    f = os.path.join(OUT, 'cancer_trials.json'); d = json.load(open(f, encoding='utf-8'))
    번 = {x['CLNC_TEST_SN'] for x in d['시험']}; 제 = collections.defaultdict(list); 책 = collections.defaultdict(set); 칸 = set()
    for x in fetch_all(API['제외기준'], k, '제외기준'):
        x = 풀기(x); sn = s_(x.get('CLNC_TEST_SN'))
        if sn in 번 and s_(x.get('CHOOSE_EXCL_STDR')): 제[sn].append({'CHOOSE_EXCL_STDR': s_(x.get('CHOOSE_EXCL_STDR'))})
    for x in fetch_all(API['시험책임자'], k, '시험책임자'):
        x = 풀기(x); 칸 |= set(x); sn = s_(x.get('CLNC_TEST_SN'))
        if sn in 번:
            for c, v in x.items():   # 기관 칸만(사람 이름 칸은 싣지 않는다)
                if re.search(r'INSTT|LAB_NAME|HOSP|ORG', c) and not re.search(r'BSSH|ORGN_DEV', c) and s_(v): 책[sn].add(s_(v))
    for x in d['시험']:
        x['제외'] = 제.get(x['CLNC_TEST_SN'], []); x['기관'] = sorted(책.get(x['CLNC_TEST_SN'], []))
    d['meta']['시험책임자칸'] = sorted(칸); d['meta']['제외있음'] = sum(1 for x in d['시험'] if x['제외']); d['meta']['기관있음'] = sum(1 for x in d['시험'] if x['기관'])
    json.dump(d, open(f, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    json.dump(d['meta'], open(os.path.join(OUT, 'cancer_meta.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('제외 있음', d['meta']['제외있음'], '기관 있음', d['meta']['기관있음'], '칸', sorted(칸), flush=True)
if __name__ == '__main__':
    k = key(); m = (sys.argv[1:] or ['probe'])[0]
    if m == 'probe': probe(k)
    elif m == 'fix': fix(k)
    else: full(k)
