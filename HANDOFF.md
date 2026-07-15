# HANDOFF — autoblog (글쓰기 자동화) 세션 인수인계

> 최종 갱신: **2026-07-14** / 브랜치: `main`
> 목적: 다른 세션·다른 PC가 **이 파일만 읽고 글쓰기 전체를 이어받게** 한다.
> ⚠️ 이 repo는 OneDrive(`C:\Users\parkh\OneDrive\capcut\auto_blog`) 안의 git clone — **동기화 규칙(§6) 먼저 읽을 것.**
> 🔒 **이 repo는 PUBLIC이다. 토큰·시크릿·앱시크릿을 절대 커밋하지 말 것**(키 "이름"만 기재. 실제 값은 `.env`=gitignored).

---

## 0. 한 줄 요약 (2026-07-14 대전환)
~~매일 06시 트렌드글 자동발행~~ → **중단**. 이제 **"프리미엄 글을 미리 만들어 두고, 현욱님이 요청하면 링크를 텔레그램으로 보내면 사람이 복붙 발행"** 하는 방식.
이유: 자동생성 트렌드글의 **품질이 낮다는 현욱님 피드백 반복** + Blogger API 쓰기가 막힘 + 애드센스가 "가치 없는 콘텐츠"로 거절.

---

## 0-1. ⭐ 2026-07-14 변경사항 (이번 세션 핵심 — 꼭 읽기)

### (1) 매일 아침 자동발송 **OFF**
- `gh workflow disable daily.yml` 실행함 → `daily-autoblog` = **disabled_manually**.
- 외부 cron-job.org가 계속 트리거해도 **워크플로가 비활성이라 안 돎**. 아침 텔레그램 발송 없음.
- 되살리려면: `gh workflow enable daily.yml`.

### (2) 프리미엄 글 파이프라인 신설 — `scripts/premium2_batch.py`
- 입력: `data/premium2/*.json` → 출력: `docs/{slug}.html` (복붙 페이지).
- **무료 스톡 사진만 사용**(`imgmod._fetch_stock` 직접 호출, **AI 폴백 없음 = 비용 0**). 글당 4장.
- 이미지는 `docs/img/{slug}/`에 커밋 → **`raw.githubusercontent.com/.../docs/img/...` URL로 참조**.
  → **GITHUB_TOKEN 불필요**(Contents API 대신 그냥 git push). 이 방식이 지금 표준.
- 실행: `python scripts/premium2_batch.py [--no-telegram]`
- 목록 홈: **`docs/index.html`** = 복붙 페이지 링크 모음 (+ OAuth `?code=` 캐처 겸용).

### (3) 프리미엄 10편 완성 (재고 ≈ 2주치)
비타민D / 마그네슘 / 오메가3 / 나트륨 / 계단 / 무릎 / 잇몸 / 코르티솔 / 낮잠 / 근감소증
- 평균 **4,500자, 출처 8.5개**, 각 사진 4장, 근거표+FAQ+고지문. 긴 문단(160자+) **0개**.
- 링크: `https://usualhealth383-cloud.github.io/autoblog/{slug}.html` (전체 목록은 `/autoblog/`)
- 텔레그램으로 링크 발송 완료.

### (4) 글 품질 기준 (이걸 안 지키면 현욱님이 바로 알아챔)
1. **두괄식** — 첫 섹션에서 결론부터. 배경·소개·이전 줄거리는 **뒤로**.
2. **네이버 홈판 스타일** — 한 문단 **1~2문장**(160자 넘기지 말 것). 모바일 스캔.
3. **딥리서치 필수** — 웹검색으로 **실제 조회**(질병관리청·학회·논문). 확인 못 한 수치는 **아예 쓰지 말 것**. 상충 연구는 **양쪽 병기**.
4. 존댓말·문장형(개조식 금지), 강한 훅, 3,500자+, 근거표+출처+FAQ.
5. **사진은 내가 직접 가져온다** — placeholder로 미루지 말 것. AI 생성 금지(비용·이질감).
   - 건강글: 무료 스톡(Pexels/Unsplash). **따뜻한 한국/아시아 정서**, 서구 모델컷 지양.
   - 드라마/영화: **공식 포스터·스틸을 직접 수급**(정당한 인용, 캡션에 `사진=SBS` 등 출처).
     언론기사에서 img 직접 URL 추출(예: `image.edaily.co.kr`, `image.starnewskorea.com`) → 다운로드 → `docs/img/`.

### (5) 서브에이전트 10개 병렬 집필이 잘 작동
- 각 에이전트에게 **JSON을 직접 Write** 시킬 것(결과를 최종 메시지로 넘기게 하면 output이 비는 문제 발생).
- 1편당 ~5분, 토큰 ~6만. 10편 동시 OK.

### (6) Threads 삭제 권한 확보 (`threads_delete`)
- **대시보드의 "사용자 토큰 생성기" 버튼은 스코프가 고정** → threads_delete 절대 안 붙음(2회 실패로 확인).
- **해결: OAuth 인증 URL에 scope 직접 지정**해서 발급해야 함.
  1. 이용사례→설정→**리디렉션 콜백 URL** 등록: `https://usualhealth383-cloud.github.io/autoblog/`
  2. `https://threads.net/oauth/authorize?client_id={APP_ID}&redirect_uri={REDIRECT}&scope=threads_basic,threads_content_publish,threads_manage_replies,threads_read_replies,threads_manage_insights,threads_delete&response_type=code`
  3. 승인 → `?code=` → `POST https://graph.threads.net/oauth/access_token`(authorization_code) → 단기토큰
  4. → `GET https://graph.threads.net/access_token?grant_type=th_exchange_token` → **60일 장기토큰**
  5. 검증: `GET /v1.0/debug_token?input_token={t}&access_token={t}` → scopes 확인
- `threads_upload.delete(media_id)` 추가됨. `DELETE /v1.0/{media_id}` → `{"success":true}`.
- ✅ `THREADS_TOKEN`(usual_sense) = delete 포함 완료. ⚠️ `THREADS_TOKEN_HEALTH`(usual.health) = **아직 delete 없음**(필요 시 위 절차 반복).
- `.env` 키(값 아님): `THREADS_APP_ID`, `THREADS_APP_SECRET`, `THREADS_REDIRECT_URI`, `THREADS_TOKEN`, `THREADS_USER_ID`, `THREADS_TOKEN_HEALTH`.

### (7) 환경 함정
- **이 PC는 SSL 가로채기 프록시** → 일부 호스트에서 `requests`가 self-signed 오류.
  → `requests.get(..., verify=False)` + `urllib3.disable_warnings()` 필요(스톡/텔레그램은 정상, 언론사 이미지 등은 필요).
- ffmpeg: `C:\Users\parkh\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_*\ffmpeg-*\bin\ffmpeg`
  (`drawtext`는 fontconfig 없어 segfault → 쓰지 말 것).
- Bash 도구에서 `cd` 후 cwd 리셋되는 경우 있음 → **절대경로** 사용.

---

## 1. 발행 채널별 상태

| 채널 | 방식 | 상태 | 비고 |
|---|---|---|---|
| 🇰🇷 **Blogger** | 공식 API | 🔴 **쓰기 차단(2026-06-25~, 07-14 재확인)** | 아래 참고 |
| 📗 **네이버** | 반자동(복붙 페이지) | ✅ **현재 주력** | 약관상 자동발행 안 함 |
| 🧵 **Threads** | 공식 API 자동 | ✅ 가동 | `usual_sense`. 삭제까지 가능해짐 |
| 📷 **Instagram** | 공식 API | ⏸ OFF | 현욱님이 "인스타는 일단 하지말고 스레드만" |
| 💬 **Telegram** | 보고/링크 전달 | ✅ 가동 | **아침 자동발송은 중단**, 요청 시 링크만 |

### 🔴 Blogger 쓰기 차단 (2026-07-14 재확인)
- **읽기는 정상**: `blogs.get` OK (블로그 `요즘 상식`, LIVE, 글 21개).
- **쓰기는 실패**: `posts.insert` → **403 "The caller does not have permission"**. `isDraft=True`(초안)조차 실패.
- 토큰·스코프·블로그 문제 **아님**(재인증해도 동일, 읽기·`revert`(숨김)는 됨).
- **추정 원인**: 과거 API로 글을 대량 게시 → **자동게시 남용(스팸) 가드**. 시기가 애드센스 "가치 없는 콘텐츠" 거절과 겹침.
- **확인 요청함(현욱님 미회신)**: blogger.com 대시보드에 경고/검토 배너 있는지 → 있으면 검토 요청(review).
- ⚠️ **자주 시도하지 말 것**(하루 1회 이하). 예약작업 `publish-pending-blog`가 매일 16시 재시도 중(풀리면 자동발행 후 스스로 중단).

### 애드센스
- **거절됨: "가치가 별로 없는 콘텐츠"** → 대응으로 **저품질 글 21개 숨김 처리** + 프리미엄 품질로 전환(현 전략).
- 승인되면 `ADSENSE_CLIENT`/`ADSENSE_SLOT` 시크릿만 넣으면 코드는 준비됨.

---

## 2. 파이프라인·핵심 파일
- **프리미엄(현행 주력)**: `scripts/premium2_batch.py` ← `data/premium2/*.json` → `docs/{slug}.html`.
  드라마/영화 단건: `scripts/premium_drama.py`(김부장 7화), `scripts/premium_movie.py`(한란).
  구 프리미엄 건강 10편: `scripts/premium_batch.py` ← `data/premium/*.json` → `docs/health-{slug}.html`.
- **구 자동발행(현재 비활성)**: `scripts/daily_publish.py` + `.github/workflows/daily.yml`.
- `src/auto_blog/`: `trends`·`strategist`·`research`·`writer`·`images`(스톡→AI폴백)·`formatter`·`affiliate`·`variants`·`translate`·`telegram_bot`.
- 발행: `publishers/{blogger,naver_draft,threads_upload,instagram}.py`.

### 글 JSON 스키마(premium2)
```json
{"slug":"...", "title":"이모지+후킹 제목(55자내)", "tags":["…13개"],
 "disclaimer":"…", "sources":["실제 조회 출처 4+"],
 "table":{"caption":"제목(출처명시)","headers":[],"rows":[[]]},
 "sections":[{"heading":"🔥 …","paragraphs":["1~2문장",…],"image_prompt":"english stock query"}]}
```

---

## 3. 현재 설정값
- **프리미엄 글**: 3,500자+ / 섹션 8~10 / 사진 4장(무료 스톡) / 표·출처·FAQ 필수.
- (구) `writer.MIN_CHARS,MAX_CHARS = 1500, 2100` — 자동발행용, 현재 비활성.
- **스레드**: 200자 내외 후킹 + 질문으로 마무리 + 해시태그. 포스터/사진 첨부 가능(`post(text, image_url=)`).
- **번역**: `TRANSLATE_TO_ENGLISH=false`(비용절감).
- 이미지 비용: **$0**(무료 스톡 전용).

---

## 4. 비용/스케줄
- `daily.yml` = **disabled**(§0-1). OpenAI 비용은 프리미엄 글 집필 시에만 발생.
- 예약작업(scheduled-tasks MCP): `publish-pending-blog`(매일16시, Blogger 재시도), `threads-auto-reply`(6시간마다 @usual_sense 댓글 자동답글), 주식 브리핑 4종. `publish-soccer-blog`는 비활성(스테일).

---

## 5. 다음 할 일 / 미결정
1. **Blogger 차단 해제** — 현욱님이 blogger.com 경고 배너 확인 필요. 안 풀리면 WordPress 병행 검토(`WORDPRESS_*` 키 이미 있음).
2. **현욱님이 "글 링크 줘" 하면** → `docs/index.html` 링크 또는 premium2 10편 링크를 텔레그램으로.
3. 재고 소진되면 프리미엄 10편 추가 집필(서브에이전트 병렬, §0-1(5) 방식).
4. `THREADS_TOKEN_HEALTH`에 delete 스코프 미적용(필요 시).
5. 요즘건강(영상) 이미지 무료 전환은 **`yozm-health` repo 세션**에서 진행할 것.

---

## 6. ⚠️ 동기화 규칙 (필독)
- 이 폴더는 **OneDrive 안의 git clone**. OneDrive가 `.git`까지 덮어써 이력 꼬임 발생 이력 있음.
- **여러 PC·여러 세션이 같은 `main`에 push** 중:
  - 시작 전: `git pull --ff-only origin main`
  - 끝: `git add … && git commit && git pull --rebase && git push`
  - 충돌 시 origin 기준. **force-push 금지**.
- 🔒 **push 전 토큰 스캔 필수**(PUBLIC repo!): `git diff --cached --text -U0 | grep -aE 'THAA|IGAA|sk-|AIza|ghp_|EAAB'`
- Python(이 PC): `.venv\Scripts\python.exe` (또는 `C:\Users\parkh\AppData\Local\Programs\Python\Python312\python.exe`. `python`은 MS Store 더미).
- git: `/c/Program Files/Git/cmd/git.exe`. 푸시가 2분 넘게 걸릴 때 있음 → `timeout 100 git push` 후 재시도.

---

## 7. 비밀/시크릿 (값은 절대 여기 쓰지 말 것)
- 로컬 `.env`(**gitignored 확인됨**): OpenAI·Telegram·Pexels·Unsplash·Blogger·`THREADS_*`·`IG_*`·`WORDPRESS_*`.
- Blogger OAuth: `config/client_secret.json`, `config/token.json`.
- 클라우드(GitHub Secrets): 위 + 제휴·애드센스 키.
- 등록 함정: PowerShell 파이프가 JSON에 BOM/따옴표 깨뜨림 → `gh secret set X --body $value` 또는 `cmd /c "gh secret set X < file"`.

---

## 8. 현욱님 작업 스타일 (중요)
- **자율 진행 선호** — 일일이 묻지 말고 알아서 끝까지. 단, 되돌리기 어려운 건 확인.
- **존댓말**, 호칭 "현욱님". 파일 링크 대신 **채팅에 내용 직접**.
- **딥리서치 최우선** — 단일 LLM 호출로 대충 쓰면 바로 알아챔("알맹이가 없다").
- 참고자료(영상 등)를 주면 **철저히 다 볼 것**(자막 전체 추출 등). 대충 훑으면 "실망스럽다".
- 피할 수 있는 실수·비용 낭비에 실망함. **비싼 AI 이미지 금지**.
