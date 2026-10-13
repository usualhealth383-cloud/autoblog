# CLAUDE.md — autoblog 저장소 (약지도 앱 · 자동 블로그)

## 🧠 세션끼리 배우기 — 모든 세션 공통 (2026-10-13 현욱님 「각 세션이 서로 배우고 완전히 공유」)
- **시작할 때** yozm-health 저장소 `docs/memory/` 의 세 파일을 차례로 읽는다(붙어 있지 않으면 add_repo 로 붙이기 — 쓰기는 push):
  `medinanum-shared-hub.md`(메디나눔 지금 사실) → `medinanum-session-log.md`(최근 소식) → `shared-lessons.md`(모든 세션의 교훈·현욱님 공통 원칙).
  커밋은 `git pull --no-rebase` 뒤 push. yozm-health 는 커밋 전 현욱님 승인 규칙이 있다.
- **끝날 때**(또는 큰 실수·현욱님 지적 직후) `shared-lessons.md` 에 교훈 한 줄, 다른 앱에 영향이 가는 변경은 `medinanum-session-log.md` 에 한 줄. yozm-health 에 쓸 수 없으면 이 저장소 `yakjido/교훈-대기.md` 에 적고, 다음 세션이 옮긴다.
- **현욱님께 묻기 전에** 같은 결정이 이미 있었는지 찾는다 — `yakjido/의사-피드백.md`, 형제 앱(우리 집 소아과 등 yozm-health `med/`), 공통 교훈. 있으면 묻지 않고 따른다.

## 약지도 (`yakjido/` → 빌드 `docs/yakjido/`)
- 작업 가지 `claude/medicine-recommendation-app-na6x0m`. main 병합은 현욱님 승인이 있을 때만.
- **약 설명은 식약처 허가 문구가 기본.** 해외 지침·진료실 관행이 다르면 둘 다 보여 주고 「의사·약사와 상의」. 근거 없이 허가와 반대로 쓰지 않는다. 임상 판단은 `yakjido/의사-질문-*.md` 에 묶어서 짧게 묻는다.
- 모든 임상 숫자에 출처(`sources*.json`), PubMed 는 DOI 링크. 모르면 고치지 않는다.
- 글 규칙: 해요체 · 영어 약자 금지 · 숫자와 단위 띄어 쓰기 · 빈도는 「100명 중 N명」 · 「전문의」 대신 「의사」 · « » 『 』 금지 · 「무료」 금지(7일 체험만 예외).
- 검사: `python3 yakjido/tools/build.py` 뒤 `git checkout -- docs/yakjido/icon-maskable-512.png`, `python3 yakjido/tests/data.py`(자료·글 규칙·키 검사·용량 예산), `python3 yakjido/tests/run.py`(화면 315개, 25분 — 도는 동안 빌드 금지). 「완료」는 검사를 통과했을 때만.
- ⛔ 비밀 키(service_role·sb_secret·DB 비밀번호)는 어디에도 쓰지 않는다. publishable 키는 메디나눔 공용 키 하나만(data.py 가 막음).
- 메디나눔 공용 서버(gildongmu)는 네 앱과 같이 쓴다 — SQL 은 `yakjido/server/supabase/medinanum/`, 앱 목록 다섯 개 유지. 준비 안 된 서버 기능은 `meta` 스위치를 끈 채 넣는다.
- 기존 완성 아티팩트(https://claude.ai/artifact/9hsGKmBcZHpL16LtNoxCnn)는 `yakjido/tools/mkart.py` 로 다시 짓고 같은 주소에 올린다.

## 자동 블로그
- ⛔ 자동발행(daily.yml)은 정지 상태 — 현욱님 명시 지시 없이 절대 다시 켜지 않는다.
