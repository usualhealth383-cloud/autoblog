# 약지도 콘텐츠 스키마 (content/*.json)

빌드(tools/build.py)가 이 폴더의 JSON을 파일명 키로 합쳐 `DATA` 전역에 심는다.
모든 임상 수치는 `sources`에 근거가 있어야 한다. 근거가 없으면 값 대신 `"[확인 필요]"`.

## meta.json
```
{ "version": "0.1", "reviewed": "2026-09", "reviewer": "내과 전문의 검수(박현욱)",
  "disclaimer": "…", "sources_global": [ {"id":"cnt2013","label":"…","url":"…"} ] }
```

## symptoms.json  — 증상 → 선택 가이드 (홈 히어로)
```
[{ "id":"msk-pain", "name":"근육·관절·허리 통증", "group":"통증", "icon":"bone",
   "tags":["허리","어깨","무릎","담","삐끗"],
   "lead":"한 줄 요약(두괄식)",
   "plan":[ { "slot":"진통", "why":"…", "options":["acetaminophen"], "otc":true },
            { "slot":"소염", "why":"…", "options":["ibuprofen","naproxen","dexibuprofen"], "pick":"ibuprofen", "otc":true },
            { "slot":"근이완", "why":"…", "options":["eperisone"], "otc":false, "alt":"…" },
            { "slot":"위보호", "why":"…", "options":["famotidine","antacid"], "otc":true } ],
   "how":["복용 순서/타이밍 문장…"],
   "selfcare":["온찜질…"],
   "avoid":["두 가지 소염제 동시 복용…"],
   "notWorking":{ "title":"…", "steps":["…"] },
   "redflags":["…"],
   "sources":["acp2017","moore2015"] }]
```

## drugs.json — 성분(ingredient) 단위. 제품은 products 안에.
```
[{ "id":"ibuprofen", "name":"이부프로펜", "en":"Ibuprofen", "class":"nsaid",
   "rx":"일반",            // 안전상비 | 일반 | 전문
   "for":["통증","발열","염증","생리통"],
   "dose":{ "adult":"1회 200~400mg, 4~6시간마다", "max":"1일 1,200mg(일반의약품 기준)", "child":"…" },
   "onset":"30~60분", "duration":"4~6시간",
   "risk":{ "gi":2, "cv":2, "renal":2, "liver":1 },      // 1(낮음)~5(높음), 근거는 sources
   "riskNote":{ "gi":"…" },
   "avoid":["위궤양·위장출혈 병력","임신 20주 이후","아스피린 천식"],
   "caution":["신장 기능 저하","항응고제·SSRI 복용"],
   "interactions":[{"with":"aspirin","level":"주의","note":"…"}],
   "pregnancy":"20주 이후 금기", "children":"생후 6개월 이상(체중 기준)",
   "products":[{"name":"부루펜정 400mg","maker":"삼일제약","amount":"이부프로펜 400mg","rx":"일반"}],
   "tips":["식후 복용…"],
   "sources":["castellsague2012","fda2020"] }]
```

## classes.json — 성분군 비교(예: NSAID)
```
[{ "id":"nsaid", "name":"소염진통제(NSAID)", "lead":"…",
   "members":["ibuprofen","naproxen","dexibuprofen","aspirin","diclofenac","celecoxib","meloxicam","aceclofenac","loxoprofen"],
   "axes":[{"key":"gi","label":"위장 부담"},{"key":"cv","label":"심혈관 부담"}],
   "table":[{"drug":"ibuprofen","gi":"…","cv":"…","duration":"…","otc":"…"}],
   "verdict":["위장이 약하면 → …","심장 질환 있으면 → …"],
   "sources":["…"] }]
```

## supplements.json — 영양제 성분
```
[{ "id":"vitd", "name":"비타민 D", "for":"…", "evidence":"강함|중간|약함", "evidenceNote":"…",
   "forms":[{"name":"D3(콜레칼시페롤)","bio":"높음","note":"…"}],
   "dose":{ "typical":"1,000~2,000 IU", "kr":"식약처 기능성 일일섭취량 …", "ul":"4,000 IU" },
   "label":["IU↔µg 환산…"], "timing":"…", "cautions":["…"], "stackWarn":["…"],
   "priceTip":"…", "sources":["…"] }]
```

## sources.json — 인용 사전
```
{ "cnt2013": { "label":"CNT Collaboration, Lancet 2013", "url":"https://doi.org/…", "type":"meta" } }
```

## profile 필터 키(앱 내 저장, 전송 없음)
`age`(성인/65세 이상/소아), `pregnant`, `ulcer`, `kidney`, `liver`, `heart`, `asthma`, `anticoag`, `alcohol`
→ drugs[].avoid/caution 에 위 키를 `flags:["ulcer","pregnant"]` 로 붙이면 화면에서 경고를 띄운다.
