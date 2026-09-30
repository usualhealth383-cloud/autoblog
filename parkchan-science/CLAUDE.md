# 박찬 과학 · 하루 한 개념 — 작업 규칙

## 빌드·배포
- 앱 원본은 `app/app-shell.html` 한 파일. `cd app && python3 build.py` → `docs/parkchan/index.html`(GitHub Pages). 빌드는 `node --check` 문법 관문을 통과해야 쓴다.
- 커밋마다 `docs/parkchan/sw.js` 의 `CACHE` 판을 올린다(옛 캐시가 새 앱을 가리지 않게).
- 안드로이드: `app-native/`(Capacitor, targetSdk 36) · CI `.github/workflows/android-apk.yml`.
- 서버: `app/server/schema.sql`(Supabase·RLS) · `functions.sql` · `functions/*`(Edge Function, Deno).

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
