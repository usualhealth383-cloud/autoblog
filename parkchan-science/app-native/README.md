# 박찬 과학 — 스토어 앱 (Capacitor)

`docs/parkchan/`(PWA 배포본)을 **한 줄도 고치지 않고** 그대로 감싼 안드로이드 앱입니다.
의료 앱들과 같은 방식입니다.

| 항목 | 값 |
|---|---|
| 앱 ID | `kr.parkchan.science` |
| 앱 이름 | 박찬 과학 |
| 웹 소스 | `www/` ← `docs/parkchan/` 복사본 (`npm run web`) |
| 아이콘·스플래시 | `tools/make_icons.py` 가 `app/icons/05_딥틸_흰심볼_크게.png` 에서 전부 생성 |
| 네이티브 기능 | 뒤로가기(화면 되돌아가기 → 홈 → 종료) · 상태바 색(테마 따라) · 스플래시 · **매일 알림**(설정의 '알림 받을 시각') |
| 앱 기능(v2) | 시작·로그인·회원가입(학생/보호자/원장) · 비밀번호 재설정 · 학원 코드 연결 · 보호자 자녀 화면(출석·진도·공지) · 이용권(코드 등록, 스토어 결제는 심사 후) · 학습 통계(연속 학습·달력·단원별 진도·정답률) · 검색·필터·북마크·공유·복습 문제 · 원장(학생 상세·반 관리·이용권 발급·통계) · 약관·개인정보·계정 삭제 |
| 앱 기능(v3, 2026-09-08) | **문제 탭** — 문제 은행 1,695문항(OX·선다·빈칸·자료·서술형)을 책·단원·소단원·유형·개수로 골라 풀기, 틀린 문제만 다시 풀기, 오답 노트 통합 · 자료 탐구·실험 27편 · 개념/문제/탐구 그림 **확대 보기**(핀치·드래그) · 통계에 소단원별 정답률 |

## APK 받는 법 ① — 자동 빌드 (PC 설치 없음, 권장)

저장소의 **Actions → `android-apk` → Run workflow** 를 누르면 3~6분 뒤
실행 화면 아래 **Artifacts → `parkchan-science-apk`** 에 `parkchan-science-debug.apk` 가 생깁니다.
폰에 옮겨 설치하면 됩니다(설정 → 출처를 알 수 없는 앱 허용). 앱 코드가 `main` 에 올라갈 때도 저절로 돕니다.

스토어 제출용(서명본)은 저장소 **Settings → Secrets** 에 아래 4개를 넣어 두면 같은 실행에서 `.apk`·`.aab` 가 함께 나옵니다.

| Secret | 값 |
|---|---|
| `ANDROID_KEYSTORE_B64` | 서명 키 파일을 base64 로: `base64 -w0 release.keystore` |
| `ANDROID_KEYSTORE_PASSWORD` | 키스토어 비밀번호 |
| `ANDROID_KEY_ALIAS` | 키 별칭 |
| `ANDROID_KEY_PASSWORD` | 키 비밀번호 |

서명 키는 처음 한 번 만들고 **잃어버리면 안 됩니다** — 업데이트마다 같은 키가 필요합니다.
```
keytool -genkeypair -v -keystore release.keystore -alias parkchan -keyalg RSA -keysize 2048 -validity 10000
```

## APK 받는 법 ② — 원장님 PC (Android Studio)

1. **Android Studio** 설치 → 실행 → SDK 를 기본값으로 받습니다(처음 한 번, 10분).
2. 이 저장소를 받은 뒤 터미널에서
   ```
   cd parkchan-science/app-native
   npm install
   npm run android
   ```
   → Android Studio 가 `android/` 프로젝트를 엽니다.
3. Android Studio 메뉴 **Build → Build Bundle(s) / APK(s) → Build APK(s)**
   → `android/app/build/outputs/apk/debug/app-debug.apk` 가 생깁니다.
4. 스토어 제출용은 **Build → Generate Signed Bundle** 로 `.aab` 를 만듭니다.

## 앱 내용을 고쳤을 때

교재나 `app/app-shell.html` 을 고치면:
```
npm run sync      # 웹 다시 빌드 → www 갱신 → 안드로이드에 복사
```
그 뒤 자동 빌드(Run workflow)를 한 번 더 돌리거나 Android Studio 에서 Build 합니다.

## 서버 모드로 만들기
`app/server/README.md` 대로 Supabase 프로젝트를 만든 뒤 `app/server/config.json` 에 URL·anon 키를 넣고
`npm run sync` 하면 앱이 서버 모드(학생 코드 인증·출석·공지·진도 동기화)로 빌드됩니다. 파일이 없으면 로컬 모드입니다.

## 아직 안 된 것
- iOS(`npx cap add ios`) — Mac 이 있어야 합니다.
- Google Play 등록비 $25 (1회) — 제출 시점에.
