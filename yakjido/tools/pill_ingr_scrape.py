#!/usr/bin/env python3
# 낱알(pills.json) 중 성분 칸이 빈 약국약의 성분을 식약처 의약품 상세(getItemDetail «원료약품 및 분량»)에서 품목기준코드별로 받아
# yakjido/tools/pill-ingr.json 에 쌓는다(이어 받기 됨). build.py 가 이 파일로 빈 ingr 을 채운다. 2026-10-13 실사용 검수 2차 A3.
# 쓰기: cd yakjido/tools && python3 pill_ingr_scrape.py   (한 분에 10~20개)
import json, re, subprocess, sys, time, os, concurrent.futures as cf
P=json.load(open('/home/user/autoblog/docs/yakjido/data/pills.json'))
IX=json.load(open('/home/user/autoblog/docs/yakjido/data/easy-index.json'))
seqix={x['seq'] for x in IX if x.get('seq') and x['i']}
TARGET={'해열.진통.소염제','진해거담제','항히스타민제'}
emp=[p for p in P if not p.get('rx') and not p.get('ingr') and p['seq'] not in seqix]
emp.sort(key=lambda p: p.get('cls') not in TARGET)   # 감기·진통·기침·알레르기 먼저
OUT='pill-ingr.json'
done=json.load(open(OUT)) if os.path.exists(OUT) else {}
def fetch(seq):
    for k in range(5):
        try:
            r=subprocess.run(['curl','-sS','-m','40','-L',f'https://nedrug.mfds.go.kr/pbp/CCBBB01/getItemDetail?itemSeq={seq}'],capture_output=True,timeout=60)
            h=r.stdout.decode('utf-8','ignore')
            if 'aasda' in h or '원료약품' in h:
                names=[]
                for m in re.finditer(r'"itemSeq":"(\d+)".*?"ingrName":"((?:[^"\\]|\\.)*)"', h):
                    if m.group(1)!=seq: continue
                    n=json.loads('"'+m.group(2)+'"').strip()
                    if n and n not in names: names.append(n)
                return names
        except Exception as e: pass
        time.sleep(2+k*2)
    return None
todo=[p['seq'] for p in emp if p['seq'] not in done]
print('todo',len(todo),'done',len(done),flush=True)
with cf.ThreadPoolExecutor(8) as ex:
    for i,(seq,res) in enumerate(zip(todo, ex.map(fetch, todo))):
        if res is not None: done[seq]=res
        if i%20==0:
            json.dump(done,open(OUT,'w'),ensure_ascii=False); print(i,len(done),flush=True)
json.dump(done,open(OUT,'w'),ensure_ascii=False); print('END',len(done))
