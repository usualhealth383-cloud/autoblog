# 박찬 과학 · 하루 한 개념 — 작업 규칙

> **이어서 작업할 때 먼저 `docs/13-로드맵-인수인계.md` 를 읽는다** — 지금 상태·다음 작업·원장님 결정 대기 목록.

## 빌드·배포
- 앱 원본은 `app/app-shell.html` 한 파일. `cd app && python3 build.py` → `docs/parkchan/index.html`(GitHub Pages). 빌드는 `node --check` 문법 관문을 통과해야 쓴다.
- `docs/parkchan/sw.js` 의 `CACHE`·`DATA` 줄은 빌드가 앱 지문으로 고쳐 쓴다(손으로 올리지 않는다). sw.js 를 고친 커밋은 빌드를 한 번 더 돌려 확인.
- 문제 은행·자료 탐구·그림은 `more-지문.json` 으로 따로 나간다(첫 화면 뒤에 받음). 이 셋을 쓰는 화면·버튼은 `MORE.ok` 전이면 자리 표시·`afterMore()` 로 기다린다 — 새 화면을 만들면 `MORE_VIEWS`·클릭 관문에 넣고 `tools/e2e_lazy.py` 로 확인.
- 앱 안 파일 저장은 `saveFile()` 하나로(안드로이드 WebView 에는 다운로드·Web Share 가 없다 — Filesystem+Share 플러그인).
- 안드로이드: `app-native/`(Capacitor, targetSdk 36) · CI `.github/workflows/android-apk.yml`.
- 서버: `app/server/schema.sql`(Supabase·RLS) · `functions.sql` · `functions/*`(Edge Function, Deno).

## 본책(교재 PDF)
- 빌드: `bash book/build.sh` · `bash book2/build.sh` (둘을 **동시에 돌리지 않는다** — 합본 만들기가 메모리를 넘겨 죽는다). 소단원 하나: `bash tools/check_chapter.sh 08|i01|sample|2101`.
- 문제 짜임은 `docs/12-본책-보강-브리프.md`(소단원 24문항·바로알기·채점 기준표·간격 두고 다시 꺼내기). 합격본 `book/chapter-08`.
- 쪽을 더하거나 빼면 새 쪽 폴리오를 `?` 로 두고 `python3 tools/renumber_book.py book|book2` — 전권 폴리오·차례·'N쪽'('66·67쪽' 포함) 참조를 다시 매긴다. 손으로 고치지 않는다.
- 정답표·해설이 바뀌면 `python3 tools/make_answer_index.py book|book2` 로 부록 '정답 한눈에 보기'를 다시 만든다(앱 추출기와 같은지 검사 포함). 그다음 `python3 tools/extract_bank.py` → 앱 빌드.
- 글꼴은 **고정 굵기**(`~/.fonts/static/`, `tools/make_static_fonts.py`)를 쓴다. 2026-10-02: 가변 글꼴이 소단원 PDF 를 9 MB 로 키우고(고정 굵기 1 MB) 굵기·크기 조합이 많으면 인쇄가 'Printing failed' 로 멈췄다.
- 실행 중인 build.sh 를 고치지 않는다(bash 는 스크립트를 읽어 가며 돈다). `pkill -f` 에 스크립트 이름을 쓰면 내 셸도 죽는다.
- `qa_check.py` 는 하한선을 '완전히' 넘어간 요소를 못 잡는다 — 넘친 쪽은 PNG 로 직접 본다.

## 시험 — "완료"는 이것이 다 통과했을 때만
- 시험대: `bash tools/testbed_up.sh`(Postgres :54329 · PostgREST :3001 · 게이트웨이 :8767, 스키마 새로 깖) · 앱: `cd docs/parkchan && python3 -m http.server 8765 --bind 127.0.0.1`
- 서버: `tools/testbed_security.py` · `tools/testbed_functions.py`
- 화면: `tools/e2e_*.py`(talk·admin·family·note·care 는 `--server` 도) · `tools/a11y_audit.py` · `tools/contrast_audit.py`
- 확인 창은 `#ask` — 시험은 `_ui.auto_yes(pg)` 로 자동 승인, 사람처럼 누를 땐 `window.__askManual`.

## 하지 말 것
- 기출 원문 재현 금지 · 명언은 출처 페이지 대조를 통과한 것만(`tools/verify_quotes.py`)
- autoblog 자동발행(`.github/workflows/daily.yml` 의 `if: false`) 손대지 않기
- 유료 서비스·API는 비용 보고 후 승인 · Supabase 프로젝트 생성은 원장님 승인 대기 · `gildongmu` 프로젝트 건드리지 않기
- 모델 이름을 코드·문서·커밋 본문에 쓰지 않기

## 재발 방지(겪은 실수에서 나온 규칙)
- **외부 모듈(결제·인증·푸시)의 기본값은 원본 코드에서 확인한다.** 2026-10-01: `@capgo/native-purchases` 가 결제를 기본으로 자동 확정해, 서버가 반영하지 않은 결제도 환불되지 않을 뻔했다 → `autoAcknowledgePurchases:false`, 확정은 서버만.
- **개인정보를 새로 남기면(칸·로그·IP) 같은 커밋에서** 개인정보처리방침(`app/legal/privacy.html` 수집 항목·보유 기간)과 Play 데이터 보안 표(`docs/09`)를 고치고, 파기(`private.purge_old`)와 그 시험을 넣는다.
- 보호자 동의는 '동의 표시 + 학원 확인 문자'가 끝이다(시행령 제17조의2 ① 1호). 동의 표시만으로 열리게 바꾸지 않는다.
- **교재를 다시 추출하면** `tools/check_content.py`(빌드가 자동으로 부름)가 지수·첨자 보존을 확인한다. 2026-10-01: 추출기가 `<sup>`·`<sub>` 를 걷어 '10⁻¹⁰ m'가 '10−10 m', 'H₂O'가 'H2O'로 학생에게 보이고 있었다 — 원본 대비 개수와 흔적(10−10 m)을 함께 본다.
- **웹판과 앱(APK)은 같은 `data/` 를 싣는다.** CI 에서 데이터를 다시 만들지 않는다 — 2026-10-01: CI 가 옛 `make_quotes.py` 로 글귀를 덮어써 앱에만 옛 글귀 39개가 들어가 있었다(지금은 막아 둠).
- 스타일은 부모 범위(`.stu .mini` 같은)에만 두지 말고 새 자리에서 쓰는지 화면으로 확인한다 — 스크린샷을 직접 본다.
- **셸 조건에 `cmd | grep -q` 를 `set -o pipefail` 과 같이 쓰지 않는다.** 2026-10-02: build.sh 의 `fc-list | grep -q` 가 늘 실패로 보여 빌드마다 글꼴 34 MB 를 다시 받고 있었다 → 파일 존재(`[ -s 파일 ]`)로 판정.
- 문제를 쓰다 보면 개념 쪽 오류가 보인다 — 2026-10-02 보강에서 맨틀 대류 방향, 불의 고리 지도 좌우, 힘-시간 그래프 넓이, 용광로 O₂, 은 이온 전자 수 같은 그림 오류가 나왔다. 그림도 '수치·방향이 본문과 맞는가'로 검수한다.
- **서버 권한은 학생 계정으로도 시험한다.** 2026-10-02: 학생이 자기 글·댓글을 지우지 못하고 있었다(PostgREST 가 고칠 때 RETURNING 을 붙여, 지운 줄이 읽기 정책 `not deleted` 에 걸림). 시험이 원장(owner_all)으로만 지워서 몰랐다 → 쓰기 경로마다 학생·보호자·손님 계정 시험.
- **교재 빌드(book*/build.sh)와 e2e 를 동시에 돌리지 않는다** — 2026-10-02 메모리를 넘겨 작업 프로세스가 통째로 다시 시작됐다(앱 서버 :8765 도 죽는다 → 다시 띄울 것).
- 이름을 문자로 자를 때는 구분자를 띄어쓰기까지 본다 — 2026-10-02 추출기가 '에너지·물질 순환'의 `·` 에서 잘라 앱에 '물질 순환'으로 보였다(단원 구분은 ' · ').
- **학생이 무언가를 쓰거나 기록하는 화면은 기본을 '한 칸 + 완료'로.** 2026-10-07 원장님: "너무 자세하면 부담돼 — 적고 싶게 편안한 분위기". 공부 노트 쓰기에 틀 4개·칩·마음·이해도·교재와 견주기를 한 화면에 다 펼쳤더니 부담스러웠다 → 기본은 한 칸 + 오늘 기분, 나머지는 '+ 더 쓰기' 안에. 새 입력 화면을 만들 때 먼저 "꼭 처음부터 보여야 하는가"를 묻는다.
- **긴 회귀는 백그라운드(nohup)로 두고 턴을 끝내지 않는다.** 2026-10-07: 턴이 끝나 세션이 쉬면 컨테이너가 다시 시작돼 백그라운드 회귀가 세 번 중간에 죽었다(앱 서버 :8765·시험대도 같이 죽음). 회귀는 10분 안쪽 묶음으로 나눠 앞에서 차례로 돌린다(`runall.sh 태그 suite...`).
- **그림 글자는 그림 좌표(viewBox) 13 이상, 첨자 10 이상.** 2026-10-07: 강의용 그림 140장의 이름표가 7.5~11(폰 카드에서 4~6 px, 책에서도 5 pt)이라 원장님 시안 비교 뒤 'B 균형'으로 다 키웠다. 그림을 새로 그리거나 고치면 `python3 tools/extract_content.py` → `python3 tools/fig_label_audit.py`(끝 줄 FIG LABEL OK) → PNG 로 직접 본다. **본책(chapter·summary·exam) 그림은 인쇄 8 pt 이상(첨자 6 pt)** — `python3 tools/book_fig_audit.py <파일>`(끝 줄 BOOK FIG OK)·`overflow_check.py`·`qa_check.py`(괘선 간격 2.5 mm). 교재 CSS 글꼴은 file:// 경로라 http 로 열면 대체 글꼴이 된다(점검 도구는 바꿔 내준다). 이 작업 중 원래 그림의 과학 오류(기권 기온 곡선 좌우, 판·대류 방향, 충격량 넓이 등)가 여럿 나왔다 — 그림을 고칠 땐 내용도 같이 본다.
- **SQL 권한 검사는 `coalesce(…, false)` 로 감싼다.** 2026-10-07: `if not (is_owner() or my_student_code() = c or …)` 에서 학생이 아니면 `my_student_code()` 가 null → `not(null)` 도 null 이라 막지 못해, 확인 전 보호자·남의 보호자·손님이 선생님 한 마디를 읽을 수 있었다(보안 시험이 잡음). 새 함수마다 '못 봐야 할 계정' 시험을 같이 넣는다.
- **앱 스크립트에 정규식 뒤돌아보기 `(?<=` `(?<!` 를 쓰지 않는다.** 2026-10-08: 9곳이 있어 iOS 16.3 이하 사파리에서 '문법 오류'로 앱 전체가 흰 화면이 될 뻔했다(node --check 는 통과). 앞 글자 조건은 `(?:^|[^0-9])` 처럼 쓰고, 바꾸면 앞 글자를 잡은 묶음 번호가 밀리는지 본다. `build.py` 가 막는다. 입력 칸 글자는 폰에서 16px 이상(아이폰 자동 확대) — `@media (pointer:coarse)` 규칙이 맞춘다.
