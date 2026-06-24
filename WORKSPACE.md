# 요즘OO 워크스페이스 — 어느 PC에서든 이어서 작업하기

> 이 파일 하나면 새 PC에서도 전체 작업을 바로 이어받을 수 있습니다.
> **핵심 원칙: 모든 작업물은 GitHub에 둔다. OneDrive·로컬 폴더에만 두지 않는다.**
> (OneDrive/로컬은 다른 PC나 Claude가 볼 수 없습니다. GitHub만이 PC 간 공통 진실입니다.)

---

## 1. 전체 프로젝트 지도 (GitHub repo 4개)

계정: **`usualhealth383-cloud`**

| repo | 공개여부 | 하는 일 | 기본 브랜치 |
|---|---|---|---|
| **`autoblog`** | 공개 | 트렌드 기반 **블로그 자동발행**(글·이미지 → 블로거/네이버/스레드) + 수익화(쿠팡·애드센스) | `main` |
| **`yozm-health`** | 비공개 | **요즘건강 유튜브 영상 자동제작 파이프라인** (영상 본체) | `master` |
| **`yozm-media`** | 공개 | 만든 영상 **호스팅**(인스타·스레드 공개 URL용) | `main` |
| **`auto-trader`** | 비공개 | 자동매매 봇(Python) — 별개 프로젝트 | `main` |

- **블로그 작업** → `autoblog`
- **영상(유튜브) 작업** → `yozm-health` (+ 결과 호스팅은 `yozm-media`)
- **자동매매** → `auto-trader`

---

## 2. 새 PC에서 처음 시작하기 (3단계)

```powershell
# 1) git / GitHub 로그인 (최초 1회 — 비공개 repo 받으려면 필요)
#    GitHub CLI 가 가장 쉬움:  https://cli.github.com  설치 후
gh auth login

# 2) 작업 폴더로 이동 (예: C:\work)
cd C:\work

# 3) autoblog 만 먼저 받고, 그 안의 동기화 스크립트로 나머지를 한 번에 받기
git clone https://github.com/usualhealth383-cloud/autoblog.git
autoblog\sync_all.bat
```

`sync_all.bat` 이 4개 repo를 모두 `C:\work\` 아래에 나란히 받아옵니다(이미 있으면 최신화).

---

## 2-1. 새 PC에서 "로컬 실행"까지 하려면 — git이 안 옮기는 것들 ⚠️

> 먼저: **매일 자동발행은 PC와 무관**합니다(GitHub Actions가 클라우드에서 GitHub Secrets로
> 실행). 두 PC가 다 꺼져 있어도 글은 나갑니다. 아래는 **이 PC에서도 로컬 대시보드(수동 승인)
> 나 개발**을 하려는 경우에만 필요합니다.

**git이 자동 동기화하는 것** = 코드 전부. (`sync_all.bat` 한 번이면 끝)

**git이 절대 안 옮기는 것**(`.gitignore`에 막아둠 — 비밀·환경이라 PC마다 따로 둬야 함):

| 파일/폴더 | 무엇 | 새 PC에서 어떻게 |
|---|---|---|
| `.env` | 모든 API 키·비밀 | 기존 PC의 `.env`를 **직접 복사**(USB·비밀번호관리자·본인 OneDrive). **git엔 금지** |
| `.venv/` | 파이썬 가상환경 | 복사 X. 새로 생성(`setup_pc.bat`가 해줌) |
| `config/client_secret.json` | 블로거 OAuth 클라이언트 | 기존 PC에서 복사 |
| `config/token.json` | 블로거 로그인 토큰 | 복사하거나, `블로거_인증.bat`로 이 PC에서 재발급 |
| `data/` | 생성된 글·이미지 결과물 | 복사 불필요(매번 새로 생성) |

**가장 쉬운 길 — 이 폴더에서 `setup_pc.bat` 더블클릭:**
가상환경 생성 → 패키지 설치 → `.env` 골격까지 자동. 그 뒤 `.env`에 키만 채우고
(블로거 로컬 발행 쓸 거면) `config/client_secret.json` 복사 + `블로거_인증.bat` 1회 실행.

> 💡 `.env`를 PC 간에 옮길 때 **절대 git commit 하지 마세요**(키 유출). 본인 USB나
> 비밀번호 관리자로 옮기는 게 안전합니다. GitHub Actions용 키는 이미 GitHub Secrets에
> 따로 있으니 자동발행과는 무관합니다.

---

## 3. 매번 작업할 때 규칙 (PC가 바뀌어도 안 꼬이게)

1. **시작 전:** `sync_all.bat` 더블클릭 → 모든 repo를 GitHub 최신으로 맞춤.
2. **작업 후:** 그 repo에서 **commit + push**. (push 안 하면 다른 PC에서 안 보임!)
3. 끝.

> Claude Code 웹/모바일 세션도 똑같이 GitHub를 기준으로 동작합니다. 그래서 push만
> 해두면 어느 기기·어느 세션에서든 그대로 이어집니다.

---

## 4. Claude Code 세션의 repo 범위 (중요)

각 Claude 세션은 **한 repo로만** GitHub 접근이 열립니다.
- 블로그를 손보려면 → `autoblog` 로 세션 시작
- 영상을 손보려면 → **`yozm-health` 로 세션 시작** (autoblog 세션에선 영상 repo를 못 봄)

세션을 만들 때(claude.ai/code) 대상 repo를 그 프로젝트로 골라주세요.

---

## 5. 한눈에 상태 보기

`sync_all.bat` 은 마지막에 각 repo의 브랜치·미커밋 변경 상태를 출력합니다.
어떤 repo에 push 안 한 변경이 남았는지 바로 확인할 수 있습니다.
