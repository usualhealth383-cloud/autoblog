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
2. **Database → Extensions** 에서 **pg_cron** 켜기 → **SQL Editor** → `schema.sql` 을 통째로 붙여 넣고 **Run**.
   pg_cron 이 있어야 매일 새벽 정리(오류 기록 90일·코드 입력 IP 1일·의견 1년·지운 글 6개월·동의 없는 14세 미만 7일)가 돕니다 — 개인정보처리방침의 보관 기간 약속. 확인: `select jobname, schedule from cron.job;` 에 `pcs-purge-old` 가 보여야 합니다.
3. 같은 파일 맨 아래 **[설정]** 두 줄의 `--` 를 지우고 원장님 이메일을 넣어 그 두 줄만 다시 Run.
4. **Authentication → Sign In / Providers → Email**: "Confirm email" **켜기**(원장 이메일 사칭 방지 · 메일 인증을 해야 원장 화면이 열립니다).
   같은 화면에서 **비밀번호 규칙**: 최소 길이 **8**, "Lowercase, uppercase letters and digits" 가 아니라 **"Letters and digits"**, **Leaked password protection 켜기**(유출된 비밀번호 차단 · 앱도 8자+글자·숫자로 맞춰 둠).
   **Authentication → URL Configuration → Site URL / Redirect URLs** 에 `https://usualhealth383-cloud.github.io/autoblog/parkchan/` 추가(가입 확인·비밀번호 재설정 메일이 돌아올 주소).
5. 앱에서 원장님 이메일로 **회원가입** → 메일의 링크 누르기 → 원장 화면이 열립니다.
   **바로 이어서** `schema.sql` 맨 아래 ▼ 한 줄(`owner_uid`)의 `--` 를 지우고 실행 — 원장 계정을 id 로 못 박습니다. 이렇게 해 두면 누가 같은 이메일로 먼저 가입을 시도해도 원장이 될 수 없습니다(메일 인증을 실수로 꺼 둔 경우에도).
6. **Project Settings → API** 의 `Project URL` 과 `anon public` 키를 `app/server/config.json` 에 넣습니다(`config.example.json` 참고).
7. `python3 app/build.py` → `cd app-native && npm run sync` → APK 자동 빌드(Actions → android-apk).

## 결제 · 푸시 알림 (서버 연결 뒤, 한 번)
앱 쪽 코드와 서버 함수(`functions/verify-purchase`, `functions/push`)는 다 되어 있습니다. 원장님 계정으로 켜는 일만 남았습니다.

**A. 스토어 결제(Google Play · 일회성 이용권, 자동 결제 없음)**
1. Play Console → 앱 → **수익 창출 → 인앱 상품**: `pass_m1`(9,900원) · `pass_m6`(49,000원) · `pass_y1`(79,000원) 세 개를 만들고 활성화.
2. Google Cloud 에서 **서비스 계정** 하나 만들고 JSON 키 받기 → Play Console **사용자 및 권한**에서 그 이메일을 초대(권한: 재무 데이터 보기 · 주문 관리).
3. Supabase → **Edge Functions → Secrets**: `GOOGLE_SA_JSON`(키 JSON 전체) · `ANDROID_PACKAGE`=`kr.parkchan.science` · `CRON_SECRET`(아무 긴 문자열).
4. 배포: `npx supabase functions deploy verify-purchase --project-ref <REF>` (함수 폴더는 이 `functions/`).
5. `functions.sql` 의 ② 부분(환불 정리)을 값 바꿔 실행.
6. Play Console **라이선스 테스트**에 원장님 Gmail 을 넣으면 실제 돈 없이 결제 시험을 할 수 있습니다.

**B. 푸시 알림(공지 · 일정 · 보호자 등원 알림)**
1. https://console.firebase.google.com → 프로젝트 만들기 → Android 앱 추가(패키지 `kr.parkchan.science`) → `google-services.json` 받기.
2. GitHub 저장소 Secrets 에 `GOOGLE_SERVICES_JSON`(파일 내용), `SUPABASE_CONFIG_JSON`(`config.json` 내용) 등록 → APK 가 푸시를 켠 채로 빌드됩니다.
3. Firebase → 프로젝트 설정 → 서비스 계정 → **새 비공개 키** → Supabase Secrets `FIREBASE_SA_JSON` 에 넣고, `PUSH_SECRET`(아무 긴 문자열) · `ACADEMY`=`박찬 과학`.
4. 배포: `npx supabase functions deploy push --no-verify-jwt --project-ref <REF>` (DB 가 부르므로 로그인 토큰 검사를 끄고, 대신 `x-push-secret` 으로 막습니다).
5. `functions.sql` 의 ① 부분(푸시)을 값 바꿔 실행.

알림은 학원과 연결된 사람(학원 코드를 등록한 학생 · 자녀를 연결한 보호자 · 원장)에게만, 연결하는 순간 한 번 묻습니다. 로그아웃하면 그 폰의 알림 등록을 지웁니다.

## 운영 스위치 — 새 APK 없이 알리기 (SQL Editor 에서 한 줄)
| 하고 싶은 것 | 실행할 SQL |
|---|---|
| 점검·안내 한 줄 띄우기(앱을 켤 때 한 번) | `insert into private.config values ('notice', '10월 3일 새벽 2~4시 점검') on conflict (k) do update set v = excluded.v;` |
| 안내 내리기 | `delete from private.config where k = 'notice';` |
| 옛 버전 막기(업데이트해야 씀) | `insert into private.config values ('min_version', '1.1.0') on conflict (k) do update set v = excluded.v;` |
| 새 버전 권하기(가볍게 알림) | `insert into private.config values ('latest_version', '1.1.0') on conflict (k) do update set v = excluded.v;` |

## 보안 설계 (v3 · 2026-09-29)
| 지키는 것 | 방법 |
|---|---|
| 이용권 만료일·역할·학원 코드를 학생이 직접 못 고침 | 프로필은 **이름·연락처·닉네임 칸만** 고칠 수 있게 칸 단위 권한. 나머지는 서버 함수로만 |
| 학원 코드 돌려쓰기 · 무차별 대입 | `link_code()` 한 곳에서만 연결 — 한 코드 = 학생 계정 하나. 틀린 코드(끝난 코드·이미 쓴 코드 포함)는 1시간에 **계정당 10번 · 같은 IP 30번 · 학원 전체 300번**까지. 계정을 여러 개 만들어 돌려도 전체 한도에 걸린다(대신 공격이 들어오면 최대 1시간 동안 모두의 코드 등록이 멈출 수 있음 — 학생 수 수백 명 규모에서 정상 오타로는 닿지 않는 한도) |
| 원격 출석(4자리 대입) | 자기 계정에 연결된 코드로만, 틀리면 6번에서 잠김 |
| 원장 사칭 | 설정한 이메일 **+ 메일 인증 완료** 계정만 원장. 원장 계정을 만든 뒤 `owner_uid` 로 못 박으면(5단계 뒤) 그 계정 하나만 원장 — 이메일을 지웠다 다시 가입해도 원장이 못 됨 |
| 환불 뒤 다시 열기 · 동의 전 결제 | 환불·취소된 영수증은 지우지 않고 `revoked_at` 표시 → 같은 영수증을 다시 보내도 거절. 보호자 동의 전 14세 미만 결제는 반영·소비하지 않아 마켓이 3일 뒤 자동 환불 |
| 아이가 자기 번호를 보호자 번호로 | 보호자가 웹에서 동의해도 바로 열리지 않고, 원장님이 등록 서류의 번호와 대조해 **확인 문자**를 보낸 때 열림(시행령 제17조의2 ① 1호) |
| 커뮤니티 사칭·도배·신고자 노출 | 글쓴이·닉네임은 서버가 채움 · 글 10분 5개/댓글 10분 20개 · 신고자 목록은 API로 안 나감(수만) · 신고 3건이면 서버에서 가림 |
| 저녁 수업 지각 판정 | DB 시간대를 **Asia/Seoul** 로 — 기본값(UTC)이면 18시 수업이 9시로 기록돼 지각이 안 잡힘 |
| 공부 노트 엿보기 | `notes` 는 본인 것만 읽고 쓴다(원장·보호자 정책 없음). 남의 노트 id 로 덮어쓰기·고치기·지우기 불가, 주인 칸은 서버가 채움. 만 14세 미만은 보호자 동의 전 서버 저장 안 함. 계정 삭제 시 함께 삭제 |
| 결제 위조 · 남의 영수증 · 상품 바꿔치기 | 이용권 연장은 `grant_purchase()`(서비스 키 전용)만. 서버 함수가 Google 에 직접 물어 ‘결제 완료 · 이 계정(결제 때 넣은 계정 표시) · 이 상품’을 확인하고, 날수는 서버가 정함. 같은 영수증은 한 번만 |

## 로컬 시험대 — 진짜 Postgres·PostgREST 로 확인 (개발용)
```
bash tools/testbed_up.sh                 # Postgres 16(:54329) + PostgREST 12(:3001) + Auth 흉내 게이트웨이(:8767)
cd ../docs/parkchan && python3 -m http.server 8765 --bind 127.0.0.1 &
python3 tools/testbed_security.py        # 막혀야 할 일 96가지를 직접 두드림
python3 tools/e2e_note.py --server       # 공부 노트: 로그인 전 쓰기 → 가입 때 옮김 → 새 기기 동기화 → 남은 못 읽음 → 지우기
python3 tools/e2e_server.py              # 원장 → 학생 가입·출석·문제 → 새 폰 동기화 → 보호자 → 이용권 → 계정 삭제 → 읽음·통계
python3 tools/e2e_talk.py --server       # 이야기(글·댓글·도움됨·채택·연결 끊김 안내)
python3 tools/e2e_authmail.py            # 가입 확인 메일 · 비밀번호 재설정 메일을 끝까지
python3 tools/e2e_admin.py --server      # 원장 운영 도구(학생 수정·연장·연결 풀기·출석 취소·공지 삭제·출석부)
python3 tools/testbed_functions.py       # 결제 확인·푸시 함수를 진짜 Deno 로 + 가짜 Google(서명 검증·영수증·FCM) — 21가지
python3 tools/e2e_native.py              # 앱에서 결제 → 복원 → 코드 연결 때 푸시 등록 → 공지 푸시 → 오류 자동 기록 → 로그아웃 때 해제
```
`schema.sql` 을 그대로 깔고 RLS·칸 권한·트리거를 진짜로 돌립니다(예전 파이썬 흉내 서버는 이 규칙을 놓쳐서 없앴습니다 —
이 시험대로 옮기자마자 ‘학원 밖 이용자 진도 저장 실패’와 ‘30일인 달 보호자 화면 오류’ 두 버그가 바로 드러났습니다).
앱을 `?server=http://127.0.0.1:8767&key=<anon>` 으로 열면 그 기기에서 서버 주소를 기억합니다(`?server=` 빈값으로 열면 해제).

## 아직 안 정한 값 [확인 필요]
반 편성(월목/화금/수토) · 반별 수업 시작 시각(지각 기준, `classes` 표) · 무료 열람 기간(7일)
