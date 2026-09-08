# 서버 연동 (Supabase) — 원장님 계정이 생기면 30분

앱은 `app/server/config.json` 이 있으면 **서버 모드**, 없으면 **로컬 모드**(학생·출석·공지가 그 기기 안에만)로 빌드됩니다.
실제 운영(여러 학생 폰 ↔ 원장님 폰)은 서버 모드가 필요하고, 무료 구간(Supabase Free)으로 충분합니다.

## 비용
| 항목 | 비용 |
|---|---|
| Supabase Free | 0원 (DB 500 MB · 월 5 GB 전송 — 학원 규모에서 넉넉) |
| 문자 발송 | 앱이 원장님 폰의 문자 앱을 여는 방식이라 **별도 비용 없음** |

## 순서
1. https://supabase.com 에서 계정·프로젝트 생성(Region: Northeast Asia — Seoul).
2. **Authentication → Users → Add user** 로 원장님 이메일·비밀번호 계정을 하나 만듭니다(앱의 원장 로그인).
3. **SQL Editor** → `schema.sql` 내용을 통째로 붙여 넣고 Run.
   - 실행 전에 파일 안의 `OWNER_EMAIL_HERE` 를 2번의 이메일로 바꿉니다.
4. **Settings → Database → Custom Postgres config** 에 `app.attend_secret` 을 아무 긴 문자열로 설정합니다(출석 코드 씨앗 — 서버만 압니다).
5. **Project Settings → API** 의 `Project URL` 과 `anon public` 키를 `app/server/config.json` 에 넣습니다(`config.example.json` 참고).
6. `python3 app/build.py` → `cd app-native && npm run sync` → APK 자동 빌드(Actions → android-apk).

## v2 (2026-09-08) — 계정·보호자·이용권
- `profiles`(계정 1명 = 1행: 역할 student/parent/owner · 이름 · 연락처 · 연결한 학생 코드 · 자녀 코드 · 이용권 만료일), `passes`(이용권 코드) 표와
  RPC `redeem_pass`(이용권 등록) · `delete_my_account`(계정 삭제)가 추가됐다. `schema.sql` 을 다시 통째로 실행하면 된다(있는 표는 건너뛴다).
- 회원가입은 Supabase Auth(이메일·비밀번호). **Authentication → Providers → Email** 에서 "Confirm email" 을 끄면 가입 즉시 로그인된다(켜 두면 메일 확인 뒤 로그인).
- 원장 계정은 `is_owner()` 의 이메일 1개. 앱에서 '원장·선생님'으로 가입해도 그 이메일이 아니면 관리 화면이 열리지 않는다.
- 보호자는 자녀 코드로 자녀의 출석·진도·공지를 읽기만 한다(RLS `my_codes()`).

## 앱 쪽에서 바뀌는 것 (이미 구현됨)
`app-shell.html` 의 `DBX` 가 서버 어댑터로 바뀝니다. 함수 이름·반환 형태는 로컬 어댑터와 같으므로 화면 코드는 그대로입니다.
- **학생**: 요청 헤더 `x-student-code` 로 자기 코드 행만 보입니다(RLS). 코드 등록 → 반 공지 → 출석(`mark_attend`, 서버가 30초 창 검증) → 진도(`progress` — 오늘의 개념·문제 기록, 문제 은행 풀이 `bh`, 보관한 글귀 `qkeep`, 일정·시간표·D-day `sched` 를 한 JSON 으로 저장·병합)가 서버에 저장되어 **폰을 바꿔도 이어집니다**.
- **원장**: 내 정보 → '원장님이신가요?' → 이메일 로그인(Supabase Auth). 학생 등록·코드 발급·명단 삭제, 출석 코드 표시(`current_attend_code`)·수동 출석(`mark_attend_manual`), 공지 발송·읽음 집계.
- 시연용 비밀번호(2580)는 서버 모드에서 쓰이지 않습니다.

## 계정 없이 끝까지 시험하기 (개발용)
```
python3 app/server/mock_server.py 8766          # Supabase 흉내(메모리)
cd docs/parkchan && python3 -m http.server 8765  # 앱
python3 parkchan-science/tools/e2e_server.py     # 원장 → 학생 가입·출석·문제 → 새 폰 동기화 → 보호자 자녀 보기 → 이용권 → 계정 삭제 → 읽음·통계
python3 parkchan-science/tools/e2e_local.py      # 같은 흐름을 로컬 모드(서버 없음)에서
```
앱을 `?server=http://127.0.0.1:8766&key=anon` 으로 열면 그 기기에서 서버 주소를 기억합니다(`?server=` 빈값으로 열면 해제).

## 아직 안 정한 값 [확인 필요]
반 편성(월목/화금/수토) · 반별 수업 시작 시각(지각 기준, `classes` 표) · 무료 열람 기간(7일) · 기기 변경 허용(월 1회)

## 이야기(커뮤니티) 표

`schema.sql` 에 `posts`·`comments` 가 있습니다. 읽기는 로그인한 사람 전체, 쓰기·수정은 자기 글만,
삭제는 원장(또는 본인)만입니다. 좋아요·신고·채택은 남의 행을 고쳐야 하므로 RLS 로 열지 않고
`like_toggle` · `report_item` · `pick_comment` 세 함수로만 열었습니다(본문은 건드릴 수 없습니다).
신고가 3건 쌓이면 앱이 화면에서 가리고, 원장 화면 `원장 › 이야기` 에 모입니다.
`profiles.nick` 이 이야기에서 보이는 이름입니다(실명은 쓰지 않습니다).
