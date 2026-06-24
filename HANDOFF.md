# HANDOFF — autoblog (글쓰기 자동화) 세션 인수인계

> 최종 갱신: 2026-06-25 / 브랜치: `main`
> 목적: 다른 세션·다른 PC가 **이 파일만 읽고 글쓰기 자동화 전체를 이어받게** 한다.
> ⚠️ 이 repo는 OneDrive(`C:\Users\parkh\OneDrive\capcut\auto_blog`) 안의 git clone이다 — **동기화 규칙(§6)을 먼저 읽을 것.**

---

## 0. 한 줄 요약
트렌드 분석 → GPT 글 + 3중검수 + 이미지 → **블로거 자동발행 / 네이버 복붙페이지 / 스레드·인스타 자동게시 / 텔레그램 보고**. 전부 **클라우드(GitHub Actions)에서 매일 ~06:00 KST 자동 실행**, PC 무관.

---

## 0-1. 사용자 GitHub repo 전체 지도

계정 `usualhealth383-cloud` — **repo 4개**(각 Claude 세션은 한 repo로만 스코프됨):

| repo | 공개 | 내용 |
|---|---|---|
| `autoblog` | 공개 | 본 블로그 자동발행(이 repo) |
| `yozm-health` | 비공개 | **요즘건강 유튜브 영상 자동제작 파이프라인**(heygen 등은 여기서 검토) |
| `yozm-media` | 공개 | 요즘OO 영상 호스팅(인스타·스레드 공개 URL용) |
| `auto-trader` | 비공개 | 자동매매 봇(별개, 06-17 이후 멈춤) |

> 영상 작업은 OneDrive가 아니라 **`yozm-health` 로 스코프된 새 세션**에서 이어갈 것(이미 GitHub에 있음).

---

## 1. 발행 채널별 상태

| 채널 | 방식 | 상태 | 비고 |
|---|---|---|---|
| 🇰🇷 **Blogger** | 공식 API 완전자동 발행 | ✅ 가동 | `commonsense383.blogspot.com` |
| 📗 **네이버** | 반자동(복붙) | ✅ 가동 | API 자동발행은 약관위반 → 아래 |
| 🧵 **Threads** | 공식 API 완전자동 게시 | ✅ 가동(토큰 시 작동) | 계정 `usual_sense`(요즘상식) |
| 📷 **Instagram** | 공식 API 자동 게시 | ⏸ 기본 OFF | `IG_ENABLED=true`일 때만 |
| 💬 **Telegram** | 발행 후 보고 | ✅ 가동 | 사진+요약+링크 |

### 네이버(복붙) 구조
- 자동발행 안 함(약관·저품질 위험). 대신 **사람이 복붙하기 쉬운 웹페이지**를 자동 갱신.
- `daily_publish._update_naver_page` → `latest_naver.json`을 repo에 push → GitHub Pages
  **복붙 페이지** `https://usualhealth383-cloud.github.io/autoblog/naver.html`에서 글+사진 전체 복사.
- `variants.make_naver`가 **새 제목+새 도입문단**을 만들어 블로거와 중복(저품질) 회피.
- 텔레그램 보고에도 사진을 묶음(sendMediaGroup)으로 보내 네이버에 바로 붙이기 쉽게 함.

### 스레드/인스타
- `variants.make_threads` → 첫 줄 후킹 강한 **200자 내외** 짧은 글 + 해시태그 + 블로그 링크.
- `publishers/threads_upload.py`(공식 Threads API: 컨테이너 생성→publish), `instagram` 동일 패턴.
- **토큰 있을 때만 게시**(없으면 조용히 스킵). 시크릿: `THREADS_TOKEN`/`THREADS_USER_ID`, `IG_TOKEN`/`IG_USER_ID`.

---

## 2. 파이프라인·핵심 파일
- 엔트리: `scripts/daily_publish.py`(run_auto→이미지 호스팅→publish→네이버페이지→스레드/인스타→텔레그램).
- `src/auto_blog/`: `trends`·`strategist`(주제선정)·`research`(딥리서치)·`writer`(본문, gpt-4o + Gemini/Claude 3중검수 + 엄격 안전게이트)·`images`(Pexels/Unsplash 스톡→gpt-image-1 폴백)·`formatter`·`affiliate`(쿠팡·증권 제휴)·`variants`(스레드/네이버/요약 변형)·`translate`·`telegram_bot`.
- 발행: `publishers/{blogger,naver_draft,threads_upload,instagram}.py`.
- 이미지 호스팅: 생성 이미지를 GitHub Contents API로 `public/`에 올려 raw 공개 URL 사용(race 불가).

---

## 3. 현재 설정값(중요)
- **글 길이**: `writer.MIN_CHARS,MAX_CHARS = 1500, 2100` (1500~2000자). ✅ **2026-06-25 사용자 확정**(블로거·네이버 모두 단일, 3500자 안 함).
- **스레드**: 본문 200자 이내(`variants.make_threads`).
- **텔레그램 요약**: 공백포함 900~1000자(`variants.make_summary`), 사진은 공개 URL 우선.
- **이미지**: 섹션마다 1장(기본 4장), `IMAGE_QUALITY=medium`.
- **번역**: `TRANSLATE_TO_ENGLISH=false`(비용절감, 영문판 OFF).
- **수익화**: 쿠팡 파트너스(`affiliate.py`, 구매의도 글) + 증권 제휴(금융 글) + **인-아티클 애드센스**(`formatter._adsense_block`, `ADSENSE_CLIENT`/`ADSENSE_SLOT` 둘 다 있을 때만, 블로거 발행본 한정/네이버 제외). 애드센스 계정은 **검토 중**(승인 시 시크릿만 넣으면 켜짐).

---

## 4. 비용/스케줄 (예전 폭주 → 해결됨)
- 트리거: `daily.yml`은 `workflow_dispatch`만. **외부 cron-job.org**가 매일 ~06:00 KST 호출.
  (Google Apps Script 트리거 방식도 과거 사용 — 현재는 cron-job.org. **하루 1회인지 사용자가 가끔 확인**.)
- ✅ **결제 폭주(6월 중순 $11+ 반복) 대응 적용됨**: `concurrency: cancel-in-progress`(중복 트리거 1개만),
  `IMAGE_QUALITY: high→medium`, `TRANSLATE_TO_ENGLISH: true→false`.
- 가끔 손댈 것: **OpenAI 크레딧 충전**(429 quota 소진 시 발행 멈춤 → platform.openai.com billing).
- 수동 실행: `gh workflow run daily.yml` (gh 없으면 GitHub 웹 Actions에서 Run).

---

## 5. 미결정 / 사용자 확인 대기
1. ~~블로그 본문 길이~~ → **결정됨(2026-06-25): 1500~2000자 단일.** 플랫폼별 분리 안 함.
2. **텔레그램 "📄 글 전문(~3800자)" 메시지** — 네이버 복붙 편의용으로 들어가 있으나, 보고가 길어짐.
   유지/제거 미정.
3. **애드센스** — 계정 검토 중. 승인되면 `ADSENSE_CLIENT`/`ADSENSE_SLOT` 시크릿만 등록(코드 준비됨).
   당장 수익은 **쿠팡 파트너스**(`COUPANG_ACCESS_KEY`/`COUPANG_SECRET_KEY` 등록 시 즉시 작동).

---

## 6. ⚠️ 동기화 규칙 (꼬임 방지 — 필독)
- 이 폴더는 **OneDrive 안의 git clone**. OneDrive가 PC 간 `.git`까지 덮어써서 git 이력이 꼬일 수 있다(실제 발생함).
- **여러 Claude 세션 + 여러 PC가 같은 `main`에 동시 push** 중. 따라서:
  - **작업 시작 전: `git pull --ff-only origin main`**
  - **작업 끝: `git add … && git commit && git pull --rebase && git push`**
  - 충돌 시 GitHub(origin)이 기준. 로컬 임의 force-push 금지.
- Python 실제 경로(이 PC): `C:\Users\parkh\AppData\Local\Programs\Python\Python312\python.exe`
  (`python`은 MS Store 더미라 작동 안 함).
- ✅ **권장: 새 PC는 OneDrive 밖(`C:\work\`)에 clone** 해서 OneDrive의 `.git` 꼬임을 원천 차단.
  도구: 루트의 **`WORKSPACE.md`**(전체 안내) / **`sync_all.bat`**(4개 repo 한 번에 pull) /
  **`setup_pc.bat`**(venv+패키지+.env 골격). 비개발자는 **GitHub Desktop**으로 Pull/Push만 해도 됨.

---

## 7. 비밀/시크릿
- 로컬: `.env`(OpenAI·텔레그램·Pexels·Blogger 등), `config/client_secret.json`·`config/token.json`(Blogger OAuth), `config/telegram_chats.json`.
- 클라우드(GitHub Secrets): 위 + `THREADS_*`·`IG_*`·`COUPANG_*`·`SECURITIES_*`·`UNSPLASH_ACCESS_KEY`·`ADSENSE_CLIENT`·`ADSENSE_SLOT`.
- 등록 함정: PowerShell 파이프가 JSON에 BOM/따옴표 깨뜨림 → `cmd /c "gh secret set X < file"`로 등록.
