# 서버 연동 (Supabase) — 원장님 계정이 생기면 30분

지금 앱은 **로컬 모드**입니다: 학생·출석·공지가 그 기기 안에만 있습니다.
실제 운영(여러 학생 폰 ↔ 원장님 폰)은 서버가 있어야 하고, 무료 구간(Supabase Free)으로 충분합니다.

## 비용
| 항목 | 비용 |
|---|---|
| Supabase Free | 0원 (DB 500 MB · 월 5 GB 전송 — 학원 규모에서 넉넉) |
| 문자 발송 | 앱이 원장님 폰의 문자 앱을 여는 방식이라 **별도 비용 없음** |

## 순서
1. https://supabase.com 에서 계정·프로젝트 생성(Region: Northeast Asia — Seoul).
2. **SQL Editor** → `schema.sql` 내용을 통째로 붙여 넣고 Run.
   - 실행 전에 파일 안의 `OWNER_EMAIL_HERE` 를 원장님 로그인 이메일로 바꿉니다.
3. **Project Settings → API** 의 `Project URL` 과 `anon public` 키를
   `app/app-shell.html` 의 `CFG.supabaseUrl` / `CFG.supabaseKey` 에 넣습니다.
4. **Settings → Database → Custom Postgres config** 에 `app.attend_secret` 을 아무 긴 문자열로 설정합니다(출석 코드 씨앗).
5. `python3 app/build.py` → `cd app-native && npm run sync`.

## 앱 쪽에서 바뀌는 것
`app-shell.html` 의 `DB` 객체가 `CFG.supabaseUrl` 이 비어 있지 않으면 서버 어댑터로 바뀝니다.
함수 이름·반환 형태는 로컬 어댑터와 같으므로 화면 코드는 손대지 않습니다.
- 학생: 요청 헤더 `x-student-code` 로 자기 코드만 보입니다(RLS).
- 원장: Supabase Auth 이메일 로그인 → 전부 보입니다. 앱의 시연용 비밀번호(2580)는 서버 모드에서 쓰지 않습니다.
- 출석: 학생 앱이 `mark_attend(code, 입력값)` 함수를 부르고, 서버가 30초 창을 검증합니다.

## 아직 안 정한 값 [확인 필요]
반 편성(월목/화금/수토) · 반별 수업 시작 시각(지각 기준) · 무료 열람 기간(7일) · 기기 변경 허용(월 1회)
