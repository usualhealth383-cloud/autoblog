#!/usr/bin/env python3
"""e약은요 색인의 «성분 → 앱 약 id» 연결(map)을 다시 맞춘다.

원본 가져오기(import_public_data.py)는 벌크 CSV 가 있어야 돌지만, 연결만 고치는 일은
이미 받아 둔 easy-index.json 으로 충분하다. 새 약을 넣을 때마다 여기 표에 성분명을 더하면
용량 대조(dose_audit)·약국 처방 대조(rx_audit)가 그 약까지 훑는다.

제형을 보는 연결이 있다. 클로트리마졸은 «질정이면 질염약, 크림이면 무좀약»이다.
사용:  python3 yakjido/tools/remap_easy.py        (--dry 로 미리보기)
"""
import json, pathlib, sys, collections
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from pharmform import formclass

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT.parent / 'docs' / 'yakjido' / 'data'

# 성분명(식약처 표기) → 앱 약 id
INGR = {
  '아세트아미노펜':'acetaminophen', '이부프로펜':'ibuprofen', '이부프로펜아르기닌':'ibuprofen', '덱시부프로펜':'dexibuprofen',
  '나프록센':'naproxen', '나프록센나트륨':'naproxen', '아스피린':'aspirin', '아스피린장용':'aspirin',
  '세티리진염산염':'cetirizine', '레보세티리진염산염':'cetirizine', '로라타딘':'loratadine', '펙소페나딘염산염':'fexofenadine',
  '클로르페니라민말레산염':'chlorpheniramine', 'd-클로르페니라민말레산염':'chlorpheniramine',
  '슈도에페드린염산염':'pseudoephedrine', '페닐레프린염산염':'phenylephrine', 'dl-메틸에페드린염산염':'methylephedrine',
  '덱스트로메토르판브롬화수소산염수화물':'dextromethorphan', '구아이페네신':'guaifenesin',
  '파모티딘':'famotidine', '알마게이트':'almagate', '인산알루미늄겔':'aluminium-phosphate', '알긴산나트륨':'alginate',
  # 한 성분이 «제산제로도 변비약으로도» 쓰인다 — 둘 다 이어 준다
  '수산화마그네슘':['antacid-mg', 'magnesium-oxide'], '산화마그네슘':'magnesium-oxide', '비사코딜':'bisacodyl',
  '로페라미드염산염':'loperamide', '디옥타헤드랄스멕타이트':'smectite',
  '디펜히드라민염산염':'diphenhydramine', '디펜히드라민':'diphenhydramine', '독시라민숙신산염':'doxylamine',
  '디멘히드리네이트':'dimenhydrinate', '스코폴라민':'scopolamine',
  '케토프로펜':'ketoprofen', '피록시캄':'piroxicam', '디클로페낙디에틸암모늄':'diclofenac-topical', '디클로페낙나트륨':'diclofenac-topical',
  '록소프로펜나트륨수화물':'loxoprofen', '플루르비프로펜':'flurbiprofen', '살리실산메틸':'methyl-salicylate',
  'L-멘톨':'menthol', 'l-멘톨':'menthol',
  '자일로메타졸린염산염':'xylometazoline', '클로르족사존':'chlorzoxazone', '이소프로필안티피린':'ipa',
  '에텐자미드':'ethenzamide', '카페인무수물':'caffeine', '파마브롬':'pamabrom',
  '퓨시드산나트륨':'fusidic-acid', '무피로신':'mupirocin', '테르비나핀염산염':'terbinafine', '테르비나핀':'terbinafine',
  '트리암시놀론아세토니드':'triamcinolone', '폴리크레줄렌':'policresulen', '판크레아틴':'digestive-enzyme',
  '시메티콘':'simethicone', '카르복시메틸셀룰로오스나트륨':'artificial-tears', '히알루론산나트륨':'artificial-tears',
  # ── 2026-09 보강: 성분명만 걸려 있던 약국 약들 ──
  '폴리에틸렌글리콜4000':'peg', '폴리에틸렌글리콜3350':'peg',
  '과산화벤조일':'benzoyl-peroxide', '가수과산화벤조일':'benzoyl-peroxide',
  '히드로코르티손':'topical-steroid', '히드로코르티손아세테이트':'topical-steroid',
  '프레드니솔론발레로아세테이트':'topical-steroid',
  '아시클로버':'acyclovir-cream',
  '아모롤핀염산염':'amorolfine', '디오스민':'diosmin', '벤지다민염산염':'benzydamine',
  '클로르헥시딘글루콘산염액':'chlorhexidine', '글루콘산클로르헥시딘액':'chlorhexidine',
  '아세틸시스테인':'acetylcysteine',
  # ── 2026-09-21 보강 ①: 앱에 «이미 있는 약»인데 식약처 표기가 달라 안 붙던 것 ──
  # 4,766개 일반약 중 46%가 우리 약으로 이어지지 않았다. 대부분 염 이름·표기 차이였다.
  '트리메부틴말레산염':'trimebutine', '트리메부틴':'trimebutine',
  '베타메타손발레레이트':'topical-steroid', '베타메타손디프로피오네이트':'topical-steroid',
  '덱사메타손':'topical-steroid', '덱사메타손아세테이트':'topical-steroid',
  '프레드니솔론':'topical-steroid', '프레드니솔론아세테이트':'topical-steroid',
  '카르바조크롬':'gum-combo', '리소짐염산염':'gum-combo',
  '옥수수불검화정량추출물':'corn-unsap',
  '콜레칼시페롤':'vitamin-d-rx', '콜레칼시페롤농축분말':'vitamin-d-rx', '콜레칼시페롤과립':'vitamin-d-rx',
  '농축콜레칼시페롤':'vitamin-d-rx', '농축콜레칼시페롤과립':'vitamin-d-rx', '비타민D3':'vitamin-d-rx',
  '펠비낙':'felbinac',
  '리파제':'digestive-enzyme', '브로멜라인':'digestive-enzyme', '비오디아스타제':'digestive-enzyme',
  '디아스타제·프로테아제·셀룰라제':'digestive-enzyme', '디아스타제':'digestive-enzyme',
  '판셀라제':'digestive-enzyme', '판프로신':'digestive-enzyme', '크리아제-PEG':'digestive-enzyme',
  '탄산수소나트륨':'antacid-mg', '탄산마그네슘':'antacid-mg', '글리세로인산마그네슘':'antacid-mg',
  '건조수산화알루미늄겔':'aluminium-phosphate', '메타규산알루민산마그네슘':'aluminium-phosphate',
  '침강탄산칼슘':'aluminium-phosphate',
  '자일리톨':'xylitol-gum',
  '부틸스코폴라민브롬화물':'butylscopolamine', '스코폴리아엑스':'butylscopolamine',
  '비타민B1':'thiamine-like', '나프록센나트륨수화물':'naproxen',
  '이소프로필안티피린':'ipa', '아세트아미노펜(서방정)':'acetaminophen',
  '크로모글리크산나트륨':'artificial-tears',
  '폴리비닐알코올':'artificial-tears', '트레할로스':'artificial-tears',
  '클로르페니라민':'chlorpheniramine',
  '옥시메타졸린염산염':'xylometazoline', '나파졸린염산염':'xylometazoline',
  '브롬헥신염산염':'guaifenesin',
  # ── 2026-09-21 보강 ②: 새로 넣은 약 6종 ──
  '에르도스테인':'erdosteine', '암브록솔염산염':'ambroxol', '암브록솔':'ambroxol',
  '포비돈요오드':'povidone-iodine', '알벤다졸':'albendazole',
  '겐타마이신황산염':'genta-steroid-cream',
  '바실루스리케니포르미스균':'probiotic-otc', '바실루스서브틸리스균':'probiotic-otc',
  '사카로마이세스보울라디':'probiotic-otc', '락토바실루스아시도필루스':'probiotic-otc',
  '비피더스균':'probiotic-otc', '유산균':'probiotic-otc',
}
# 성분이 «영양제 화면»으로 가는 것 — 비타민·미네랄 복합제가 일반의약품으로도 팔린다.
# 이것이 빠져 있어 1,000개 넘는 제품이 어디로도 이어지지 않았다.
SUPP = {
  '피리독신염산염':'vitb', '티아민질산염':'vitb', '티아민염산염':'vitb', '벤포티아민':'vitb', '푸르설티아민':'vitb',
  '리보플라빈':'vitb', '리보플라빈부티레이트':'vitb', '리보플라빈포스페이트나트륨':'vitb',
  '니코틴산아미드':'vitb', '판토텐산칼슘':'vitb', '폴산':'vitb', '비오틴':'vitb', 'd-비오틴':'vitb',
  '시아노코발라민':'vitb', '시아노코발라민1000배산':'vitb', '메코발라민':'vitb', '히드록소코발라민':'vitb',
  '아스코르브산':'vitc', '아스코르브산과립97%':'vitc', '아스코르브산97%과립':'vitc', '제피아스코르브산':'vitc',
  '푸마르산철':'iron', '폴리사카리드철착염':'iron', '건조황산철':'iron',
  '유비데카레논':'coq10',
  '콘드로이틴설페이트나트륨':'glucosamine', '글루코사민황산염':'glucosamine', '글루코사민염산염':'glucosamine',
  '밀크시슬열매건조엑스':'milkthistle', '실리마린':'milkthistle',
  '루테인':'lutein',
}
# 같은 성분이라도 제형에 따라 다른 약으로 간다
BY_FORM = {'클로트리마졸': {'insert':'clotrimazole-vag', 'skin':'clotrimazole', 'liquid':'clotrimazole'}}

def main():
    idx = json.loads((DATA/'easy-index.json').read_text(encoding='utf-8'))
    before = sum(1 for e in idx if e.get('map'))
    added = collections.Counter()
    for e in idx:
        ids = set()
        for i in e.get('i', []):
            if i in INGR:
                v = INGR[i]
                ids.update(v if isinstance(v, (list, tuple)) else [v])
            if i in SUPP: ids.add('supp:' + SUPP[i])
            if i in BY_FORM:
                got = BY_FORM[i].get(formclass(e['n']))
                if got: ids.add(got)
        ids = sorted(ids)
        for d in ids:
            if d not in (e.get('map') or []): added[d] += 1
        e['map'] = ids
    after = sum(1 for e in idx if e.get('map'))
    if '--dry' not in sys.argv:
        (DATA/'easy-index.json').write_text(json.dumps(idx, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    print(f'연결된 제품 {before} → {after}건')
    for d, n in added.most_common(): print(f'  + {d}: {n}건')

main()
