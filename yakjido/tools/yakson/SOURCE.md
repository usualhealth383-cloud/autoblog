# 약손 데이터 원본

정본은 `usualhealth383-cloud/yozm-health` 저장소의 `med/약손_앱/데이터/*.json` 이다.
이 폴더는 그 사본이고, `tools/import_yakson.py` 가 약지도 데이터로 바꾼다.

| 여기 | 정본 |
|---|---|
| ING.json | 성분.json |
| BRAND.json | 상품.json |
| QADB.json | 물어보기.json |
| NUT.json | 영양제.json |
| COMBO.json | 조합.json |
| NSAID_CMP.json | 계열비교.json |

## 갱신하는 법
```
git clone --depth 1 https://github.com/usualhealth383-cloud/yozm-health /home/user/yozm-health
cp /home/user/yozm-health/med/약손_앱/데이터/{성분,상품,물어보기,영양제,조합,계열비교}.json  →  이 폴더(위 표대로)
python3 tools/import_yakson.py && python3 tools/import_combo.py && python3 tools/build.py
```
약손 쪽 인계 문서: `med/약손_앱/인계_0915.md` (그쪽 저장소).
원본 JSON 을 여기서 고치지 말 것 — 정본 저장소에서 고치고 다시 가져온다.
