# 박찬 과학 콘텐츠 DB 스키마 v0.1

교재와 앱이 같은 데이터를 사용한다 (단일 원천). 저장 형식은 JSON(추후 Supabase/PostgreSQL 이관 전제).

## 계층 구조

```
course (통합과학1 / 통합과학2)
└─ unit          대단원 = 교육과정 영역 (예: 물질과 규칙성)
   └─ lesson     소단원 (예: 우주의 시작과 원소의 탄생)
      ├─ concept[]   개념 카드 = 앱의 "단락 선택 → 알짜 내용"의 단위
      └─ problem[]   문항 (1일 1문제·모의고사·교재 문제부가 공유)
```

## concept (개념 카드)

| 필드 | 타입 | 설명 |
|---|---|---|
| id | string | `TG1-2-1-C01` (통과1-단원-소단원-개념번호) |
| title | string | 개념 제목 |
| body | markdown | 본문 (교재 본문과 동일 원고) |
| gist | markdown | **알짜 요약** — 앱에서 단락 선택 시 보여주는 핵심 (3~5줄) |
| standards | string[] | 성취기준 코드 `["10통과1-02-01"]` |
| wing_notes | {term, desc}[] | 날개단 용어·보충 |
| teacher_tips | string[] | '박찬쌤 한마디' 첨삭 문구 |
| exam_points | string[] | '시험엔 이렇게' 출제 포인트 |
| figures | {id, caption}[] | 그림 참조 (SVG 파일명) |

## problem (문항)

| 필드 | 타입 | 설명 |
|---|---|---|
| id | string | `TG1-2-1-P01` |
| step | 1\|2\|3 | 1 개념 확인 / 2 내신 완성 / 3 수능 도전 |
| type | enum | `ox` `blank` `choice5` `bogi` (ㄱㄴㄷ 합답형) `essay` (서술형) |
| difficulty | 1~5 | 난이도 (앱 적응 추천용) |
| standards | string[] | 성취기준 코드 |
| concept_ids | string[] | 연관 개념 카드 (오답 시 앱이 해당 개념으로 연결) |
| stem | markdown | 발문 |
| data | markdown/figure | 제시 자료 (그림·표) |
| bogi | {ㄱ,ㄴ,ㄷ} | 합답형 보기 (type=bogi) |
| choices | string[5] | 선지 |
| answer | string | 정답 |
| explanation | markdown | 정답 해설 |
| wrong_notes | {choice, why}[] | **오답 선지별 해설** (마더텅급 상세도 기준) |
| points | 1.5\|2\|2.5 | 수능 배점 체계 (모의고사 조합용) |

## 활용 매핑

- **교재**: unit→lesson 순서대로 조판. concept.body+figures = 개념부, problem step1~3 = 문제부, explanation+wrong_notes = 해설편.
- **앱 1일 1문제**: problem에서 난이도·성취기준 균형 추출, concept_ids로 복습 연결.
- **모의고사**: 25문항/40분/배점 1.5·2·2.5 (2028 수능 규격)로 problem 조합.
- **앱 개념 열람**: concept.gist(알짜) 우선 노출 → 펼치면 body.

v0.1 비고: 샘플 챕터는 이 스키마로 데이터를 만들되 조판은 수동 HTML. 조판 자동화(데이터→HTML 렌더러)는 MVP 단계에서 구현.
