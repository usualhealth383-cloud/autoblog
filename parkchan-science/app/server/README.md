# 서버 연동 (Supabase) — 원장님 계정이 생기면 30분

앱은 `app/server/config.json` 이 있으면 **서버 모드**, 없으면 **로컬 모드**(학생·출석·공지가 그 기기 안에만 — 시연용)로 빌드됩니다.
실제 운영(여러 학생 폰 ↔ 원장님 폰)은 서버 모드가 필요합니다.

## 비용
| 항목 | 비용 | 비고 |
|---|---|---|
| Supabase Free | 0원 | 한 사람당 **활성 무료 프로젝트 2개**(현욱님은 `gildongmu` 1개 사용 중 → 1개 더 가능) · 전송 월 10 GB(캐시 5 + 비캐시 5) · **7일간 활동이 적으면 일시 정지**(90일 안에 복구 가능) |
| Supabase Pro | 월 25달러 + 컴퓨트(Micro 1개는 포함 크레딧 10달러로 상쇄) ≈ 월 25달러 | 정지 없음 · 자동 백업. 조직 단위 요금 — 유료 판매를 시작하면 권장 |
| 문자 발송 | 0원 | 원장님 폰의 문자 앱을 여는 방식 |

출처: Supabase 문서 — Billing FAQ(무료 프로젝트 수·Pro 컴퓨트), Project Pausing, Bandwidth & Storage Egress (2026-09-29 확인)
| 푸시 알림(FCM) · 스토어 결제 확인 | 0원 | Firebase 무료 · Google Play API 무료 |

## 순서 (처음 한 번)
1. https://supabase.com → **New project** (Region: Northeast Asia — Seoul). 비밀번호는 안전한 곳에 적어 둡니다.
2. **SQL Editor** → `schema.sql` 을 통째로 붙여 넣고 **Run**.
3. 같은 파일 맨 아래 **[설정]** 두 줄의 `--` 를 지우고 원장님 이메일을 넣어 그 두 줄만 다시 Run.
4. **Authentication → Sign In / Providers → Email**: "Confirm email" **켜기**(원장 이메일 사칭 방지 · 메일 인증을 해야 원장 화면이 열립니다).
   **Authentication → URL Configuration → Site URL / Redirect URLs** 에 `https://usualhealth383-cloud.github.io/autoblog/parkchan/` 추가(가입 확인·비밀번호 재설정 메일이 돌아올 주소).
5. 앱에서 원장님 이메일로 **회원가입** → 메일의 링크 누르기 → 원장 화면이 열립니다.
6. **Project Settings → API** 의 `Project URL` 과 `anon public` 키를 `app/server/config.json` 에 넣습니다(`config.example.json` 참고).
7. `python3 app/build.py` → `cd app-native && npm run sync` → APK 자동 빌드(Actions → android-apk).

## 보안 설계 (v3 · 2026-09-29)
| 지키는 것 | 방법 |
|---|---|
| 이용권 만료일·역할·학원 코드를 학생이 직접 못 고침 | 프로필은 **이름·연락처·닉네임 칸만** 고칠 수 있게 칸 단위 권한. 나머지는 서버 함수로만 |
| 학원 코드 돌려쓰기 · 무차별 대입 | `link_code()` 한 곳에서만 연결 — 한 코드 = 학생 계정 하나, 틀린 코드 1시간 10번 제한 |
| 원격 출석(4자리 대입) | 자기 계정에 연결된 코드로만, 틀리면 6번에서 잠김 |
| 원장 사칭 | 설정한 이메일 **+ 메일 인증 완료** 계정만 원장 |
| 커뮤니티 사칭·도배·신고자 노출 | 글쓴이·닉네임은 서버가 채움 · 글 10분 5개/댓글 10분 20개 · 신고자 목록은 API로 안 나감(수만) · 신고 3건이면 서버에서 가림 |
| 저녁 수업 지각 판정 | DB 시간대를 **Asia/Seoul** 로 — 기본값(UTC)이면 18시 수업이 9시로 기록돼 지각이 안 잡힘 |
| 결제 위조 | 이용권 연장은 `grant_purchase()`(서비스 키 전용)만 — 앱은 영수증을 서버 함수에 넘길 뿐 |

## 로컬 시험대 — 진짜 Postgres·PostgREST 로 확인 (개발용)
```
bash tools/testbed_up.sh                 # Postgres 16(:54329) + PostgREST 12(:3001) + Auth 흉내 게이트웨이(:8767)
cd ../docs/parkchan && python3 -m http.server 8765 --bind 127.0.0.1 &
python3 tools/testbed_security.py        # 막혀야 할 일 56가지를 직접 두드림
python3 tools/e2e_server.py              # 원장 → 학생 가입·출석·문제 → 새 폰 동기화 → 보호자 → 이용권 → 계정 삭제 → 읽음·통계
python3 tools/e2e_talk.py --server       # 이야기(글·댓글·도움됨·채택·연결 끊김 안내)
python3 tools/e2e_authmail.py            # 가입 확인 메일 · 비밀번호 재설정 메일을 끝까지
```
`schema.sql` 을 그대로 깔고 RLS·칸 권한·트리거를 진짜로 돌립니다(예전 파이썬 흉내 서버는 이 규칙을 놓쳐서 없앴습니다 —
이 시험대로 옮기자마자 ‘학원 밖 이용자 진도 저장 실패’와 ‘30일인 달 보호자 화면 오류’ 두 버그가 바로 드러났습니다).
앱을 `?server=http://127.0.0.1:8767&key=<anon>` 으로 열면 그 기기에서 서버 주소를 기억합니다(`?server=` 빈값으로 열면 해제).

## 아직 안 정한 값 [확인 필요]
반 편성(월목/화금/수토) · 반별 수업 시작 시각(지각 기준, `classes` 표) · 무료 열람 기간(7일)
