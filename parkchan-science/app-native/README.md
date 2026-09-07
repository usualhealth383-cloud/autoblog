# 박찬 과학 — 스토어 앱 (Capacitor)

`docs/parkchan/`(PWA 배포본)을 **한 줄도 고치지 않고** 그대로 감싼 안드로이드 앱입니다.
의료 앱들과 같은 방식입니다.

| 항목 | 값 |
|---|---|
| 앱 ID | `kr.parkchan.science` |
| 앱 이름 | 박찬 과학 |
| 웹 소스 | `www/` ← `docs/parkchan/` 복사본 (`npm run web`) |
| 아이콘·스플래시 | `tools/make_icons.py` 가 `app/icons/05_딥틸_흰심볼_크게.png` 에서 전부 생성 |

## 원장님 PC에서 APK 만들기 (처음 한 번)

1. **Android Studio** 설치 → 실행 → SDK 를 기본값으로 받습니다(처음 한 번, 10분).
2. 이 저장소를 받은 뒤 터미널에서
   ```
   cd parkchan-science/app-native
   npm install
   npm run android
   ```
   → Android Studio 가 `android/` 프로젝트를 엽니다.
3. Android Studio 메뉴 **Build → Build Bundle(s) / APK(s) → Build APK(s)**
   → `android/app/build/outputs/apk/debug/app-debug.apk` 가 생깁니다. 폰에 옮겨 설치하면 됩니다.
4. 스토어 제출용은 **Build → Generate Signed Bundle** 로 `.aab` 를 만듭니다(서명키는 처음 한 번 만들어 **잃어버리면 안 됩니다** — 업데이트마다 같은 키가 필요합니다).

## 앱 내용을 고쳤을 때

교재나 `app/app-shell.html` 을 고치면:
```
npm run sync      # 웹 다시 빌드 → www 갱신 → 안드로이드에 복사
```
그리고 Android Studio 에서 다시 Build 하면 됩니다.

## 아직 안 된 것
- iOS(`npx cap add ios`) — Mac 이 있어야 합니다.
- 서버 연동(학원 코드 인증·출석·공지 발송) — 지금은 전부 기기 안에만 저장됩니다.
- Google Play 등록비 $25 (1회) — 제출 시점에.
