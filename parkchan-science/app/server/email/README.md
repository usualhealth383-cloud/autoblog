# 인증 메일 문안 — Supabase Authentication → Email Templates 에 붙여 넣기

Supabase 기본 문안은 영어다. 아래를 각 템플릿의 **Subject** 와 **Message body (HTML)** 에 그대로 붙여 넣는다.
변수(`{{ .ConfirmationURL }}` 등)는 Supabase 가 채운다 — 고치지 않는다.

| 템플릿 | 파일 | 제목 |
|---|---|---|
| Confirm signup | `confirm.html` | [박찬 과학] 가입을 확인해 주세요 |
| Reset password | `reset.html` | [박찬 과학] 비밀번호를 새로 정해 주세요 |
| Change email address | `change.html` | [박찬 과학] 이메일 변경을 확인해 주세요 |

Magic Link·Invite 는 쓰지 않는다(앱에 그 흐름이 없음). URL Configuration → Site URL 은 `https://usualhealth383-cloud.github.io/autoblog/parkchan/`.
