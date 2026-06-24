# HANDOFF — autoblog 세션 인수인계

> 최종 갱신: 2026-06-24 / 목적: 다음 세션이 이 파일만 읽고 바로 이어받기.
> 핵심 토대(GitHub 쓰기 권한)는 이미 해결됨. 남은 건 비용 관리(선택)와 heygen 올리기.

---

## 0. 한 줄 요약

- ✅ **GitHub 쓰기 권한 해결됨** — Claude GitHub App 설치 완료. 새 세션에서 `git push` 정상 동작 확인(브랜치 `claude/dazzling-cori-3am7k4`로 푸시 성공).
- ✅ **OpenAI 비용 절감 수정 이미 적용됨** (커밋 `6b8d37a`): 이미지 품질 high→medium, 영어번역 off, 글 1000자 축소, concurrency(중복실행 자동취소) 추가.
- ✅ **결제 재진단 완료** — "폭주" 아님. 하루 1번 정상 실행 중. (아래 2 참조)
- ⏳ **남은 일**: (선택) OpenAI 사용 한도 설정 / (선택) 추가 비용 절감 / heygen 코드 GitHub에 올리기.

---

## 1. 배경 맥락

- 사용자는 별도의 **heygen 자동화** 작업을 다른 PC/OneDrive에 갖고 있음. 이 repo엔 없음. 이어가려면 그 PC에서 GitHub로 올려야 함(아래 4-③).
- PC 간 연속성 = GitHub로만 가능(OneDrive/로컬은 Claude가 접근 불가). 사용자 합의: **코드=GitHub, 영상 등 큰 파일=OneDrive**, git 폴더를 OneDrive 동기화 폴더 안에 두지 않기.
- 동기화 셋업 가이드는 사용자에게 파일(SYNC_SETUP.md)로 전달됨. 요지: GitHub Desktop으로 두 PC clone → 시작 시 Pull, 끝에 Push.

---

## 2. OpenAI 결제 — 재진단 (중요, 수정됨)

초기 추정(외부 cron 폭주)은 **부분적으로만 맞았음.** 실제 실행 이력 분석 결과:

```
06-17 ~ 06-23: 매일 정확히 21:54:03 UTC (06:54 KST) 1회씩만 실행
06-15 ~ 06-17: 다회 실행(초기 세팅/테스트, 수동 dispatch)
```

- 현재 트리거: `daily.yml`은 `on: workflow_dispatch` 만 있음(GitHub schedule 제거됨). 즉 **외부에서 매일 호출**됨.
- **매일 같은 초(21:54:03)에 칼같이** 실행 = 자동 스케줄러. 실행 주체 = 사용자 계정(`usualhealth383-cloud`). → **cron-job.org(또는 동등 서비스)가 사용자 토큰으로 매일 1회 호출 중.** (사용자는 "가입 안 했다"고 기억하나 실제로 뭔가 살아있음.)
- concurrency 설정으로 중복 트리거돼도 1개만 돎.
- **결론: 현재는 하루 1회 = 정상 범위.** 사용자가 본 $11.01은 6/15~6/17 초기(테스트 다회 + high 품질 이미지 + 영어번역)에서 누적됐을 가능성이 큼. 6/18 비용절감 적용 이후로는 하루치가 훨씬 낮아졌을 것.

### 비용 구조
- 비싼 쪽 = **AI 이미지 생성(`gpt-image-1`)**, 특히 과거 `high` 품질. (현재 medium)
- 글: `gpt-4o`. 영어번역 off로 절반 절감됨.
- 무료 스톡(Pexels/Unsplash) 우선 → AI는 폴백. 스톡 키가 설정돼 있으면 이미지 비용 거의 없음.

---

## 3. 남은 조치 (모두 선택 사항 / 사용자 영역)

1. **OpenAI 한도 설정** (platform.openai.com → Settings → Limits)
   - Soft limit 낮게(예 $15, 경고 이메일만) + Hard limit 높게(예 $30, 초과 시 차단).
   - "월 평소 사용액의 2배"를 hard로 → 정상 작업은 안 멈추고 폭주만 차단.
   - ※ 먼저 Usage에서 6/18 이후 하루 비용 확인 후 금액 결정.
2. **즉시 비용 0 원하면(kill 스위치)**: GitHub → Actions 탭 → daily-autoblog → `···` → Disable workflow.
3. **추가 비용 절감(새 세션에서 코드 수정 가능)**:
   - 이미지 4장→2장 / 품질 medium→low
   - 무료 스톡(Pexels/Unsplash) 우선 확실히 → AI 생성 최소화
   - 글 모델 gpt-4o→gpt-4o-mini (글 비용 ~1/10)
4. **cron-job.org 트리거 정체 확인**(원하면): 로그인해서 이 작업 등록돼 있는지 확인. (GitHub 밖이라 Claude 불가)

> 사용자 의향(2026-06-24): 자동 발행은 **계속 유지**. 한도 설정은 "작업 멈출까봐" 망설였으나, soft/hard 분리로 정상작업은 안 멈춘다고 설명함. 강제 안 함.

---

## 4. 시스템 구조 메모 (autoblog)

- 트렌드 기반 자동 블로그 발행(한국어 글 + 이미지 → Blogger 발행, 텔레그램 보고).
- 핵심 파일:
  - `.github/workflows/daily.yml` — 발행 파이프라인. 트리거 `workflow_dispatch`만. concurrency 있음. env로 모델/품질/번역 설정.
  - `src/auto_blog/images.py` — Pexels→Unsplash 무료 스톡 먼저, 미스 시 `gpt-image-1`(기본 max_images=4) 폴백.
  - `src/auto_blog/writer.py`, `translate.py`, `config.py` — 작성/번역/설정.
  - `scripts/daily_publish.py` — 엔트리포인트.
- 생성 이미지는 repo `public/`에 푸시해 공개 URL로 사용.

---

## 5. 다음 세션이 할 일

1. (요청 시) 위 3-③ 추가 비용 절감을 `daily.yml`/`images.py`에 적용 → 커밋·푸시. **이제 push 됨.**
2. **heygen 자동화 올리기**: 그 폴더가 있는 PC에서 GitHub repo로 올리도록 안내(영상은 `.gitignore`로 제외: `*.mp4 *.mov *.wav` 등). repo 생기면 세션에 추가해 이어 작업.
3. 두 PC 동기화 습관(GitHub Desktop: Pull→작업→Commit→Push) 정착 지원.

> 참고: 옛 읽기전용 세션(브랜치 `claude/happy-pasteur-pfnxjg`)에 로컬 커밋 `fdd09aa`가 있었으나 push 못 함. HANDOFF.md는 사용자가 웹에서 main에 직접 업로드함 + 새 세션이 갱신 푸시함. 이 파일이 그 최종 갱신본.
