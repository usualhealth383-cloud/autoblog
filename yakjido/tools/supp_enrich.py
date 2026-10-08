# 영양제 17종에 role(몸에서 하는 일)·foods(음식별 1회 분량 함량)·need(2025 한국인 영양소 섭취기준)를 붙인다
# 숫자는 조사 파일(foods.json·kdri_roles.json — 원문 대조본)에서만 읽고, 손으로 고르는 것은 이름·분량 표기뿐
import json,sys
import pathlib; R=str(pathlib.Path(__file__).parent/'supp-src')+'/'
F=json.load(open(R+'foods-2026-10.json')); K=json.load(open(R+'kdri2025-roles.json'))
N=K['kdri']['nutrients']; RO=K['roles']
B=['19-29','30-49','50-64','65-74','75+']
def need(key,t):
    n=N[key]; ul=n.get('ul')
    if ul and all(v is None for s in ul.values() for v in s.values()): ul=None
    elif ul:
        um=[ul['men'][b] for b in B]; uf=[ul['women'][b] for b in B]
        ul=um[0] if len(set(um+uf))==1 else {'m':um,'f':uf}
    return {'t':t,'u':n['unit'].replace('/day','').replace('µg DFE','µg'),'m':[n['men'][b] for b in B],'f':[n['women'][b] for b in B],'ul':ul}
def pick(key,rows):
    """rows: (성분표 이름 앞부분, 화면 이름, 분량 표기, 덧말|None) — 수치는 조사 파일에서"""
    fs=F[key]['foods']; out=[]
    for pre,ko,serv,note in rows:
        m=[f for f in fs if f['ko'].startswith(pre)]; assert len(m)==1,(key,pre,[f['ko'] for f in fs])
        f=m[0]; a=f['perServing']; assert a is not None
        it={'n':ko,'s':serv,'a':round(a,1) if a<100 else round(a)}
        if note: it['t']=note
        out.append(it)
    return out
FOODS={
 'iron':('iron',[('돼지 간','돼지 간','삶은 것 45 g','동물성 · 비타민 A가 아주 많아 자주 많이는 말고'),('굴','굴','살 80 g','동물성'),('멸치','멸치볶음','중멸치 15 g','동물성'),('시금치','시금치','한 접시 70 g',None),('소고기','소고기 사태','1인분 60 g','동물성'),('두부','두부','1/5모 80 g',None)],
   '고기·생선·조개의 철이 채소·콩의 철보다 몸에 잘 흡수돼요.'),
 'calcium':('calcium',[('멸치','멸치볶음','중멸치 15 g',None),('우유','우유','1컵 200 mL',None),('깻잎','깻잎','한 접시 70 g',None),('요구르트','떠먹는 요구르트','100 g',None),('미역','미역국','마른 미역 10 g',None),('두부','두부','1/5모 80 g','만드는 법에 따라 차이가 커요')],None),
 'vitd':('vitaminD',[('연어','연어구이','1토막 70 g','일본 성분표 값을 옮긴 것'),('꽁치','꽁치구이','1토막 70 g','일본 성분표 값을 옮긴 것'),('고등어','고등어','1토막 70 g','잡힌 곳에 따라 절반 아래로도 나와요'),('표고','말린 표고 불려서','30 g',None),('잔멸치','잔멸치볶음','15 g',None),('달걀','달걀','1개 60 g',None)],
   '보통 우유에는 비타민 D가 거의 없어요(강화 우유는 예외). 햇볕을 쬐면 피부에서도 만들어져요.'),
 'mg':('magnesium',[('현미밥','현미밥','1공기 210 g',None),('깻잎','깻잎','한 접시 70 g',None),('미역','미역국','마른 미역 10 g',None),('두부','두부','1/5모 80 g',None),('시금치','시금치','한 접시 70 g',None),('아몬드','아몬드','한 줌 10 g',None)],None),
 'zinc':('zinc',[('굴','굴','살 80 g',None),('돼지 간','돼지 간','삶은 것 45 g',None),('소고기','소고기 사태','1인분 60 g',None),('현미밥','현미밥','1공기 210 g',None),('돼지고기','돼지고기 목심','1인분 60 g',None),('달걀','달걀','1개 60 g',None)],None),
 'vitc':('vitaminC',[('키위','키위','100 g',None),('파프리카','빨간 파프리카','70 g',None),('딸기','딸기','100 g',None),('귤','귤','1개 100 g',None),('시금치','시금치나물','한 접시 70 g',None),('브로콜리','데친 브로콜리','70 g',None)],None),
 'vitb':('vitaminB12',[('바지락','바지락','살 80 g',None),('소 간','소 간','45 g','미국 성분표 값을 옮긴 것'),('굴','굴','살 80 g',None),('고등어','고등어','1토막 70 g',None),('멸치','멸치볶음','중멸치 15 g',None),('달걀','달걀','1개 60 g',None)],
   '비타민 B12는 고기·생선·조개·달걀에만 있어요. 채식만 하시면 부족해지기 쉬워요.'),
 'omega3':('epaDha',[('꽁치','꽁치구이','1토막 70 g','일본 성분표 값을 옮긴 것'),('고등어','고등어','1토막 70 g',None),('삼치','삼치','1토막 70 g',None),('연어','연어구이','1토막 70 g','일본 성분표 값을 옮긴 것'),('잔멸치','잔멸치볶음','15 g',None),('달걀','달걀','1개 60 g',None)],
   '등푸른 생선 한 토막이면 하루치를 몇 배 넘겨요.'),
}
LUT=[('시금치','시금치','한 접시 70 g'),('케일','케일','70 g'),('상추','로메인 상추','70 g'),('브로콜리','브로콜리','70 g'),('달걀','달걀','1개 60 g')]
NONE={'probiotic':'probiotics','coq10':'coq10','collagen':'collagen','glucosamine':'glucosamine','melatonin':'melatonin','ginseng':'ginseng','milkthistle':'milkThistle'}
NEED={'iron':('iron','권장섭취량'),'calcium':('calcium','권장섭취량'),'vitd':('vitaminD','충분섭취량'),'mg':('magnesium','권장섭취량'),'zinc':('zinc','권장섭취량'),'vitc':('vitaminC','권장섭취량'),'vitb':('vitaminB12','권장섭취량'),'omega3':('epaDha','충분섭취량')}
ROLE={'vitd':'vitaminD','omega3':'omega3','mg':'magnesium','probiotic':'probiotics','iron':'iron','calcium':'calcium','vitc':'vitaminC','vitb':'vitaminB12','lutein':'luteinZeaxanthin','coq10':'coq10','zinc':'zinc','collagen':'collagen','melatonin':'melatonin','glucosamine':'glucosamineChondroitin','ginseng':'asianGinseng','milkthistle':'milkThistle'}
p=sys.argv[1]; S=json.load(open(p,encoding='utf-8'))
for s in S:
    i=s['id']
    if i in ROLE: s['role']=RO[ROLE[i]]['ko'].rstrip('.')+'.'
    if i in FOODS:
        key,rows,note=FOODS[i]
        s['foods']={'u':N[NEED[i][0]]['unit'].split('/')[0].replace(' DFE',''),'items':pick(key,rows),'src':['rda_fct2026','mfds_nq_adult']+(['kdri2025_sum'] if True else [])}
        if note: s['foods']['note']=note
    elif i=='lutein':
        fs=F['luteinZeaxanthin']['foods']; items=[]
        for pre,ko,serv in LUT:
            f=[x for x in fs if x['ko'].startswith(pre)][0]; items.append({'n':ko,'s':serv,'a':round(f['perServing']/1000,1)})
        s['foods']={'u':'mg','items':items,'base':10,'baseLabel':'시험에서 쓴 양 10 mg','src':['usda_fdc_lutein','mfds_nq_adult'],'note':'한국 식품성분표에는 루테인 칸이 없어 미국 성분표 값이에요. 잎이 짙은 초록 채소에 많아요.'}
    elif i in NONE:
        x=F['nonNutrients'][NONE[i]]; s['foods']={'none':x['text'],'src':['fn_'+i]}
    if i in NEED: s['need']=need(*NEED[i])
    if i=='vitb': s['need']['b6']=need('vitaminB6','권장섭취량')
json.dump(S,open(p,'w',encoding='utf-8'),ensure_ascii=False,indent=1); open(p,'a').write('\n')
print({s['id']:[k for k in ('role','foods','need') if k in s] for s in S})
