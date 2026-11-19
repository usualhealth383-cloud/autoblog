# 길동무 «임상시험 찾기» — 식약처 공공데이터 임상시험 OpenAPI 받기(2026-11-19 · 현욱님 활용신청 승인 2026-11-19~2028-11-19)
#   키: 깃허브 Secrets DATA_GO_KR_KEY(값은 로그·파일 어디에도 남기지 않는다) · 약지도 yakjido/tools/fetch_mfds.py 의 page() 를 그대로 쓴다.
#   python3 gildongmu/trials/fetch_trials.py probe  — API 마다 3건만(칸 이름·전체 건수) → gildongmu/trials/probe.json
#   python3 gildongmu/trials/fetch_trials.py full   — 전부 받아 암 관련만 거른 묶음 → gildongmu/trials/cancer_trials.json
import json, os, sys, re, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'yakjido', 'tools'))
from fetch_mfds import page, key
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
if __name__ == '__main__':
    k = key(); m = (sys.argv[1:] or ['probe'])[0]
    if m == 'probe': probe(k)
    else: sys.exit('full 은 칸 이름을 본 뒤에 만든다')
