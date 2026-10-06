# 회차 001 — 「잠 못 드는 첫날 밤」 (콘셉트 A · 수면)

## 설계 의도 (큐레이터 노트, 설명란과 영상 첫 화면에 사용)

1. 하루를 내려놓는 데 걸리는 시간에 맞춰 **45분 한 사이클**로 구성했습니다. Cochrane 리뷰에서 효과를 본 연구들의 청취 시간은 25~60분이었습니다.
2. 곡이 지날수록 **느려지고, 성기고, 낮아지도록** 배열했습니다. 피아노로 시작해 앰비언트로 끝납니다.
3. 갑작스러운 소리, 드럼, 높은 음역은 넣지 않았습니다. 마지막 곡은 박자 없이 사라지듯 끝납니다.

## 곡 구성 — 11곡, 약 45분 (영상에서는 4회 반복해 약 3시간)

Suno 설정: **Custom 모드 · Instrumental 켜기 · 모델 v5.5**. 아래 `Style` 칸을 그대로 붙여넣고, `Exclude styles`에는 공통으로 `drums, percussion, vocals, choir, bright synth, sudden crescendo, distortion`을 넣습니다.

### 1단계 · 내려놓기 (약 70 BPM, 피아노)

| # | 곡 제목 (파일명) | Style |
|---|---|---|
| 01 | Lights Down · 불을 끄고 | `solo felt piano, slow 70 bpm, soft and warm, close-mic intimate, gentle lullaby melody, D major, sparse, sleep music, tape warmth` |
| 02 | Warm Tea · 따뜻한 차 한 잔 | `felt piano with soft cello pad, 68 bpm, tender, nostalgic, F major, slow arpeggios, calm evening, minimal` |
| 03 | Window Light · 창가의 불빛 | `solo upright piano, muted hammers, 66 bpm, quiet reflective melody, A flat major, long sustain pedal, peaceful` |
| 04 | Slow Breath · 천천히 숨 | `felt piano and airy string pad, 64 bpm, very gentle, breathing rhythm, C major, soft dynamics, meditative` |

### 2단계 · 가라앉기 (약 60 BPM, 피아노와 패드)

| # | 곡 제목 | Style |
|---|---|---|
| 05 | Blanket · 이불 속 | `soft piano and warm analog pad, 60 bpm, sparse notes, lots of space, E flat major, cozy, dreamy, sleep` |
| 06 | Rain-free Night · 고요한 밤 | `ambient piano, reverb-rich, 58 bpm, slow drifting chords, B flat major, calm, no rhythm section` |
| 07 | Moon Ward · 달빛 병동 | `celesta and soft piano, 56 bpm, delicate music-box feel but low register, G major, tender, hushed` |
| 08 | Heavy Eyelids · 무거운 눈꺼풀 | `slow piano chords over warm drone, 54 bpm, very sparse, D flat major, fading phrases, deep calm` |

### 3단계 · 잠들기 (박자 없음, 앰비언트)

| # | 곡 제목 | Style |
|---|---|---|
| 09 | Deep Blue · 깊은 파랑 | `ambient drone, warm low pads, no beat, slowly evolving texture, deep relaxation, soft and dark, sleep` |
| 10 | Far Shore · 먼 물가 | `ambient soundscape, gentle sine pads, distant soft piano notes, no rhythm, very slow evolution, peaceful` |
| 11 | Goodnight · 잘 자요 | `minimal ambient, warm low drone fading slowly, no melody, no beat, deep sleep, ending into silence` |

**곡 고르는 기준:** 두 버전 중에서 ① 중간에 갑자기 커지는 구간이 없고 ② 처음과 끝이 부드러운 쪽을 고릅니다. 둘 다 아니면 다시 생성합니다. 곡당 약 10크레딧이 듭니다.

## 커버 이미지 — Gemini 나노바나나, 16:9

```
A quiet hospital-adjacent bedroom at night seen through a softly lit window, warm amber bedside lamp,
deep navy and indigo palette, gentle moonlight, a cup of tea on a wooden side table, linen bedding,
cinematic, painterly, calm, no people, no text, 16:9, high detail, soft film grain
```

텍스트를 넣지 않고 이미지만 씁니다. 썸네일 문구는 업로드 단계에서 따로 얹습니다.

**썸네일 문구 (2줄):** `잠 못 드는 밤` / `의사가 설계한 45분`

## 업로드 정보

**제목 (한국어):** 잠 못 드는 밤, 의사가 설계한 수면 음악 3시간 | 점점 느려지는 피아노 → 앰비언트 | Rest Rx 001

**제목 (영어 버전, 다국어 제목 기능에 입력):** Doctor-Designed Sleep Music 3 Hours | Slowing Piano to Ambient | Rest Rx 001

**설명란:**

```
잠이 오지 않는 밤을 위해, 의사가 직접 곡의 흐름을 설계했습니다.

▸ 오늘의 설계
1) 45분 한 사이클 × 4회 반복 — 연구에서 쓰인 음악 청취 시간(25~60분)에 맞춤
2) 피아노(약 70 BPM) → 패드(약 60 BPM) → 박자 없는 앰비언트 순으로 점점 느리고 낮게
3) 드럼·높은 음·갑작스러운 소리 없음

▸ 곡 목록
[build_playlist.py가 만든 _chapters.txt 붙여넣기]

▸ 근거: Cochrane Review 2022 — Listening to music for insomnia in adults (doi.org/10.1002/14651858.CD010459.pub3)

음악은 AI 작곡 도구(Suno, 상업 라이선스)로 만들고, 곡 선택·배열·설계는 사람이 했습니다.
이 영상은 수면 루틴을 돕는 음악이며 진료를 대신하지 않습니다. 불면이 3개월 이상 이어지면 전문의와 상담하세요.

#수면음악 #잠잘때듣는음악 #sleepmusic #피아노 #불면
```

## 합성 명령 (제작 PC)

```
python playlist/build_playlist.py --tracks _playlist/001/tracks --image _playlist/001/cover.png ^
  --out _playlist/001/rest_rx_001.mp4 --repeat 4
```
