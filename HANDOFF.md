# HANDOFF — autoblog 세션 인수인계

> 작성: 2026-06-23 / 브랜치: `claude/happy-pasteur-pfnxjg`
> 목적: 다음 **review 세션**이 이 파일만 읽고 바로 이어받을 수 있도록 이번 세션 전체 맥락을 정리.

---

## 0. 한 줄 요약

OpenAI에서 반복 결제($11.01 등)가 발생 중. 원인은 **`autoblog` GitHub Action이 외부 cron(cron-job.org)에 의해 하루 여러 번 트리거**되어, 매 실행마다 `gpt-4o`(본문, 영어번역 포함 2배) + `gpt-image-1`(`high` 품질) 을 호출하기 때문.

> **업데이트 (2026-06-24):** 아래 3번 비용 절감 수정은 **적용 완료**(커밋 `6b8d37a`). `IMAGE_QUALITY: medium`, `TRANSLATE_TO_ENGLISH: "false"`, `concurrency`(cancel-in-progress) 모두 `daily.yml`에 반영됨. 남은 건 **GitHub 밖 사용자 작업**(cron-job.org 빈도 확인, OpenAI Usage 상한 설정).

---

## 1. 세션에서 오간 맥락 (시간순)

1. 사용자가 "다른 PC에서 하던 **heygen 자동화 세션**" 을 기억하냐고 물음.
   - → 세션 간 메모리 없음(격리된 임시 컨테이너). 코드가 GitHub에 있어야만 확인 가능하다고 안내.
2. "OneDrive에도 있을 것" / "다른 PC에서 바로 쓸 수 있게 해준다고 했다" 고 함.
   - → OneDrive·로컬은 접근 불가. PC 간 연속성은 **GitHub push** 로만 가능하다고 설명.
3. "다른 PC에 **HANDOFF.md** 해놨다, 잘됐는지 확인 가능하냐" 고 함.
   - → 확인 결과 **GitHub에 HANDOFF.md 없음**:
     - 로컬 작업트리 없음 / `main` 브랜치만 존재 / 계정 전체 `filename:HANDOFF.md` 검색 0건.
     - 결론: 그 HANDOFF.md는 **그 PC 로컬/OneDrive에만 있고 push 안 됨.**
   - ⚠️ **2026-06-24 정정:** 이 진술은 틀렸음. 실제로는 계정에 repo가 **4개**이고 영상 작업도 GitHub에 있음(아래 0-1 참고).
4. 사용자가 "19:46에 OpenAI에서 또 $11.01 결제됐다, 이게 뭐냐" 고 물음 → 아래 **2. 결제 조사** 가 이번 세션의 핵심 산출물.

> **heygen/영상 관련 정정**: 영상 자동화는 OneDrive에만 있는 게 아니라 **GitHub에 이미 있음**.
> `yozm-health`(유튜브 자동제작 파이프라인) + `yozm-media`(영상 호스팅)가 그것. heygen 은 그
> 파이프라인 안에서 쓰는 도구로 추정. (이 autoblog repo 와는 별개)

---

## 0-1. 사용자 GitHub repo 전체 지도 (2026-06-24 확인)

계정 `usualhealth383-cloud` (2026-06-15 생성) — **repo 4개**:

| repo | 공개 | 내용 | 비고 |
|---|---|---|---|
| `yozm-health` | 비공개 | **요즘건강 유튜브 자동제작 파이프라인** (영상 본체) | 활발히 푸시 중(~06-24) |
| `yozm-media` | 공개 | 요즘OO 영상 호스팅(인스타·스레드 공개 URL용) | 영상 결과물 호스팅 |
| `autoblog` | 공개 | 본 블로그 자동발행 시스템 | 이 세션 |
| `auto-trader` | 비공개 | 자동매매 봇(Python) | 06-17 이후 멈춤 |

> ⚠️ **세션 범위 주의:** 각 세션은 GitHub MCP 가 **한 repo 로만** 스코프됨(이 세션=autoblog).
> 영상 파이프라인(`yozm-health`)을 작업하려면 **그 repo 로 스코프된 새 세션**을 열어야 함
> (autoblog 세션에서는 `yozm-health` 읽기/쓰기 불가).

---

## 2. OpenAI 결제 조사 (핵심)

### 증상
- OpenAI에서 반복 결제. 사용자가 본 건 **19:46경 $11.01** (사용자 표현 "또" = 반복됨).

### 원인 진단
이 repo의 GitHub Action(`.github/workflows/daily.yml`)이 OpenAI를 호출함:
- `OPENAI_MODEL: gpt-4o` — 본문 작성.
- `TRANSLATE_TO_ENGLISH: "true"` — **영어 번역분까지 생성 → 글 작성 비용 사실상 2배.**
- `IMAGE_MODEL: gpt-image-1`, `IMAGE_QUALITY: high` — 스톡(Pexels/Unsplash) 미스 섹션을 **high 품질**로 생성(가장 비쌈). `src/auto_blog/images.py` 기본 `max_images=4`.

### 결정적 증거 — 워크플로우 실행 이력
`daily.yml` 실행 12건이 **전부 `workflow_dispatch`** (schedule 아님 → 외부 cron-job.org가 dispatch로 때림). 6/17 저녁 1시간 내 군집 실행:

| 실행(UTC) | KST | 결과 |
|---|---|---|
| 06-17 09:03 | 18:03 | success |
| 06-17 09:12 | 18:12 | cancelled |
| 06-17 09:42 | 18:42 | success |
| 06-17 09:47 | 18:47 | success |
| 06-17 21:54 | 06:54(6/18) | success |

→ 사용자가 본 **19:46 결제**가 이 6/17 저녁 군집 실행(18:03~18:47, 3~4회 연속)과 시간대 일치. **$11.01은 단발 비용이 아니라 반복 실행으로 누적된 사용량/자동충전일 가능성** 높음.

### 진짜 근본 원인
**외부 cron-job.org가 워크플로우를 하루 1회가 아니라 여러 번 트리거.** 커밋 `e3e0946`("schedule: GitHub 자체예약 제거(외부 cron-job.org가 트리거)")에서 GitHub 자체 cron을 떼고 외부로 넘긴 뒤 과다 호출됨. **이 cron 설정은 GitHub 밖이라 Claude가 직접 못 봄 → 사용자 확인 필요.**

---

## 3. 권장 조치 (우선순위)

1. **[사용자] cron-job.org 스케줄 확인** — 트리거가 하루 1회만 도는지. (가장 중요, GitHub 밖)
2. **[사용자] OpenAI 대시보드 Usage 확인** — gpt-4o vs gpt-image-1 중 어디서 돈이 나가는지 확정. + 월 usage limit(상한) 설정해 폭주 방지.
3. **[적용 완료 — 커밋 `6b8d37a`]** `daily.yml` 비용 절감:
   - `IMAGE_QUALITY: high` → `medium` ✅
   - `TRANSLATE_TO_ENGLISH: "true"` → `"false"` ✅
   - **concurrency 추가** — 중복 트리거 시 1개만 돌고 나머지 자동 취소 ✅:
     ```yaml
     concurrency:
       group: daily-autoblog
       cancel-in-progress: true
     ```

> **상태: 코드 수정 적용·푸시 완료.** 남은 건 사용자 측 cron-job.org 빈도 점검 + OpenAI Usage 상한 설정.

---

## 4. 시스템 구조 메모 (autoblog)

- 트렌드 기반 자동 블로그 발행 (한국어 글 + 이미지 자동 생성 → Blogger 발행, 텔레그램 보고).
- 핵심 파일:
  - `.github/workflows/daily.yml` — 발행 파이프라인(예약 cron `13 21 * * *`는 있으나 실제론 외부 dispatch가 구동), env로 모델/품질/번역 설정.
  - `src/auto_blog/images.py` — 5단계 이미지 수급. **Pexels→Unsplash 무료 스톡 먼저, 미스 시 `gpt-image-1` 폴백.**
  - `src/auto_blog/writer.py`, `translate.py`, `config.py` — 본문 작성/번역/설정.
  - `scripts/daily_publish.py` — 엔트리포인트.
- 이미지 호스팅: 생성 이미지를 repo `public/`에 푸시해 공개 URL로 사용(커밋 다수가 `image: public/...`).

---

## 5. 다음 세션이 할 일

1. 사용자에게 **cron-job.org 트리거 빈도**와 **OpenAI Usage 내역** 확인 결과를 물어 근본 원인 확정.
2. ~~승인 시 **3번 비용 절감 수정**을 `daily.yml`에 적용~~ → **완료**(커밋 `6b8d37a`).
3. (별건) **영상 자동화는 `yozm-health` repo 로 스코프된 새 세션에서** 이어갈 것
   (OneDrive 안 거쳐도 됨 — 이미 GitHub 에 있음). heygen 도 거기서 검토.
