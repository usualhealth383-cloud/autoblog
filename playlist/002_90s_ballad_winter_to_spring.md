# 회차 002 — 「1990, 어느 겨울밤에서 봄까지」 (콘셉트 B · 90년대 감성 발라드)

> 컨셉: **"그 시절 라디오에서 흘러나왔을 것 같은, 발표되지 않은 노래들."**
> 한 사람이 겨울밤 이별을 겪고 봄에 놓아주기까지를 10곡에 담은 하나의 이야기입니다(한국어 7곡 + 팝송 3곡, 약 40분).
> 가사·멜로디는 모두 새로 만든 창작곡입니다. 기존 곡의 가사, 멜로디, 제목, 가수 이름은 쓰지 않습니다.

## 0. 공통 사운드 설계 (90년대 초 한국 발라드 문법)

| 요소 | 설계 |
|---|---|
| 인트로 | 그랜드 피아노 솔로 4~8마디 |
| 편곡 | 현악 섹션, 아날로그 신스 패드, 프렛리스 베이스, 브러시 스네어 |
| 간주 | 색소폰 또는 나일론 기타 솔로 |
| 클라이맥스 | 마지막 후렴 **반음~온음 전조(키 체인지)** |
| 음색 | 테이프 질감, 따뜻한 리버브. 요즘식 오토튠·트랩 비트는 배제 |
| 템포 | 66~78 BPM. 8번 곡만 시티팝 92 BPM으로 분위기 전환 |

### Suno 설정
- Custom 모드, 모델 v5.5, 가사 칸에 아래 가사를 그대로 붙여넣습니다. `[Verse]` 같은 대괄호 태그도 그대로 둡니다.
- **Exclude styles (모든 곡 공통):** `trap, EDM, autotune, rap, modern pop production, heavy 808, dubstep`
- **가수 고정 (Voices 기능):** 1번 곡에서 마음에 드는 남자 목소리가 나오면 **Voice/Persona로 저장**하고, 남자 곡(2·4·6·10)은 그 목소리로 만듭니다. 여자 곡(3·7·8)은 3번 곡의 목소리를 저장해서 씁니다. 이렇게 하면 채널 전체가 같은 두 가수로 이어집니다. 이 두 가상 가수가 채널의 정체성이 됩니다.
- **실존 가수 이름은 프롬프트에 넣지 않습니다.** Suno가 차단하고, 초상권 문제도 생깁니다.

### 공통 Style 기본값
```
1990s Korean ballad, K-ballad, nostalgic, emotional, grand piano intro, lush string section,
soft analog synth pads, fretless bass, gentle brushed drums, saxophone solo, key change in final chorus,
warm analog tape saturation, vintage reverb
```
곡마다 아래 **추가 Style**을 이 기본값 뒤에 붙입니다.

---

## 01. 가로등 아래서 · 남자 · 76 BPM
**추가 Style:** `warm male tenor vocal, 76 bpm, bittersweet, rainy city night`

```
[Intro: soft piano]

[Verse 1]
젖은 거리 위로 하나둘 불이 켜지면
습관처럼 나는 또 이 길을 걸어요
그대 웃음소리 머물던 모퉁이엔
낯선 사람들만 바삐 스쳐 가네요

[Pre-Chorus]
잊었다 말했던 내 마음이
이 밤엔 자꾸만 거짓말 같아

[Chorus]
가로등 아래서 그대를 기다려요
오지 않을 걸 알면서도
노랗게 번지는 불빛 속에 서면
그날의 우리가 보일 것 같아

[Verse 2]
주머니 속에는 건네지 못한 표 두 장
접힌 자국마다 그 겨울이 남았죠
빗방울 하나에 이름을 불러 보다
목이 메어 그만 고개를 숙여요

[Pre-Chorus]
시간이 지나면 괜찮다고
누군가 그랬죠 그 말을 믿었죠

[Chorus]
가로등 아래서 그대를 기다려요
오지 않을 걸 알면서도
노랗게 번지는 불빛 속에 서면
그날의 우리가 보일 것 같아

[Instrumental Break: saxophone solo]

[Bridge]
한 번만 단 한 번만
그대 날 돌아봐 준다면

[Final Chorus: key change up]
가로등 아래서 그대를 기다려요
이 밤이 끝나지 않도록
노랗게 번지는 불빛 속에 서면
그날의 우리가 거기 있어요

[Outro]
불빛이 꺼질 때까지 여기 있을게요
```

## 02. 마지막 버스 · 남자 · 70 BPM
**추가 Style:** `warm male tenor vocal, 70 bpm, tender, late night bus stop, melancholic`

```
[Intro: piano and strings]

[Verse 1]
그대 집 앞 정류장 낡은 벤치에 앉아
마지막 버스가 오길 기다렸었죠
조금만 더 늦게 와 주길 바랐던 밤
그대 손이 참 따뜻했었는데

[Pre-Chorus]
떠나는 버스 창에 기대어
작게 손 흔들던 그대

[Chorus]
마지막 버스는 오늘도 떠나가요
그대 없는 이 길 위로
창가에 비친 내 얼굴 너머로
아직도 그대가 손을 흔드네요

[Verse 2]
몇 번의 겨울이 지나고 또 지나도
나는 그 정류장을 지나치지 못해
불 꺼진 창문을 한참 올려다보다
혼자 웃어요 바보처럼

[Pre-Chorus]
떠나는 버스 창에 기대어
작게 손 흔들던 그대

[Chorus]
마지막 버스는 오늘도 떠나가요
그대 없는 이 길 위로
창가에 비친 내 얼굴 너머로
아직도 그대가 손을 흔드네요

[Bridge]
다음 정류장에 그대가 서 있다면
이번엔 내가 먼저 내릴게요

[Final Chorus: key change up]
마지막 버스는 오늘도 떠나가요
그대 없는 이 길 위로
멀어지는 불빛 끝자락에서
나도 이제 손을 흔들어요

[Outro]
잘 가요 내 사랑
잘 가요
```

## 03. 부치지 못한 편지 · 여자 · 68 BPM
**추가 Style:** `clear gentle female vocal, 68 bpm, delicate, nylon guitar and piano, heartfelt`

```
[Intro: nylon guitar]

[Verse 1]
책상 서랍 깊은 곳에 잠든 편지 한 장
그대 이름 적어 놓고 끝내 보내지 못했죠
잉크가 번진 자리엔 그날의 내가 있어
보고 싶다 그 한마디 몇 번을 지웠는지

[Pre-Chorus]
용기 없던 스무 살의 나를
그대는 알고 있었을까요

[Chorus]
부치지 못한 편지에 담긴 말
사랑했어요 정말 사랑했어요
계절이 바뀌어 빛이 바래도
그 마음만은 그대로예요

[Verse 2]
우체통 앞을 서성이던 하얀 겨울밤
손끝이 시려 와도 돌아서던 내 모습
이제는 주소조차 알 수 없는 그대에게
이 노래가 대신 닿을 수 있다면

[Pre-Chorus]
용기 없던 스무 살의 나를
그대는 알고 있었을까요

[Chorus]
부치지 못한 편지에 담긴 말
사랑했어요 정말 사랑했어요
계절이 바뀌어 빛이 바래도
그 마음만은 그대로예요

[Bridge]
언젠가 우연히 이 노래를 듣거든
그게 나였다고 알아줘요

[Final Chorus: key change up]
부치지 못한 편지에 담긴 말
사랑했어요 정말 사랑했어요
이제야 비로소 소리 내어 봐요
그대 그대 사랑했어요

[Outro]
안녕 나의 그대
```

## 04. 겨울 공중전화 · 남자 · 72 BPM
**추가 Style:** `husky warm male vocal, 72 bpm, wintry, lonely, soft electric piano`

```
[Intro: electric piano]

[Verse 1]
동전 몇 개를 손에 꼭 쥔 채로
얼어붙은 유리문을 열었죠
수화기 너머 들려오던 그 목소리
여보세요 그 한마디에 숨이 멎었죠

[Pre-Chorus]
아무 말도 하지 못하고
조용히 수화기를 내려놓았죠

[Chorus]
겨울 공중전화 그 작은 불빛 아래
하얀 입김으로 그댈 불러요
들리지 않아도 괜찮아요
내 마음은 아직 거기 있어요

[Verse 2]
이젠 모두가 손에 쥔 전화기로
언제든 서로를 찾을 수 있는데
왜 나는 지금도 그 길모퉁이에서
멈춰 선 시간을 서성이나요

[Pre-Chorus]
아무 말도 하지 못하고
조용히 수화기를 내려놓았죠

[Chorus]
겨울 공중전화 그 작은 불빛 아래
하얀 입김으로 그댈 불러요
들리지 않아도 괜찮아요
내 마음은 아직 거기 있어요

[Instrumental Break: saxophone solo]

[Bridge]
신호가 끊어지기 전에
한 번만 내 이름 불러 줘요

[Final Chorus: key change up]
겨울 공중전화 그 작은 불빛 아래
하얀 입김으로 그댈 불러요
이 겨울이 다 지나가도
내 마음은 거기 있을게요
```

## 05. 그대 창가에 · 남녀 듀엣 · 74 BPM
**추가 Style:** `male and female duet, 74 bpm, romantic, harmonies, sweeping strings`

```
[Intro: piano]

[Verse 1: Male]
그대 창가에 불이 꺼지면
나의 하루도 조용히 저물어요

[Verse 1: Female]
그대 발소리 멀어져 가면
나는 커튼 뒤에 한참을 서 있죠

[Pre-Chorus: Duet]
같은 하늘 아래 같은 별을 보며
우리 같은 꿈을 꾸고 있나요

[Chorus: Duet]
그대 창가에 머문 달빛처럼
조용히 곁에 있을게요
말하지 않아도 알 수 있도록
이 밤이 다 가도록

[Verse 2: Male]
내일은 꼭 말하겠다고
몇 번을 다짐하고 돌아섰죠

[Verse 2: Female]
내일은 먼저 웃어 보이자고
거울 앞에서 연습했었죠

[Pre-Chorus: Duet]
같은 하늘 아래 같은 별을 보며
우리 같은 꿈을 꾸고 있나요

[Chorus: Duet]
그대 창가에 머문 달빛처럼
조용히 곁에 있을게요
말하지 않아도 알 수 있도록
이 밤이 다 가도록

[Bridge: Female]
이젠 창문을 열어요
[Bridge: Male]
이젠 그대를 불러요
[Bridge: Duet]
사랑해요

[Final Chorus: Duet, key change up]
그대 창가에 머문 달빛처럼
언제나 곁에 있을게요
말하지 않아도 알 수 있도록
이 밤이 다 가도록
```

## 06. Midnight Avenue · 남자 · 팝송 · 78 BPM
**Style (기본값 대신 사용):** `late 1980s adult contemporary pop ballad, warm male tenor vocal, 78 bpm, DX7 electric piano, lush strings, gated reverb drums soft, saxophone solo, key change final chorus, nostalgic city night, analog warmth`

```
[Intro: electric piano]

[Verse 1]
Neon on the wet pavement, taxis rolling by
I still take the long way home beneath the city sky
Every corner keeps a secret, every window holds a light
And I swear I hear your laughter on the edge of the night

[Pre-Chorus]
I tell myself I'm over you
But the streets don't lie

[Chorus]
Down Midnight Avenue, I'm still looking for you
In every passing face, in every shade of blue
The radio is playing the song we used to know
Down Midnight Avenue, I can't let go

[Verse 2]
There's a coffee shop on Seventh where we used to sit and talk
You'd draw hearts on foggy windows, I would never watch the clock
Now the booth is full of strangers and the waitress doesn't know
That a part of me is waiting there from twenty years ago

[Pre-Chorus]
I tell myself I'm over you
But the streets don't lie

[Chorus]
Down Midnight Avenue, I'm still looking for you
In every passing face, in every shade of blue
The radio is playing the song we used to know
Down Midnight Avenue, I can't let go

[Instrumental Break: saxophone solo]

[Bridge]
If you're out there tonight, look up at the moon
I'll be singing this for you

[Final Chorus: key change up]
Down Midnight Avenue, I'm still looking for you
In every passing face, in every shade of blue
And if the night is long, I'll carry on and go
Down Midnight Avenue, I can't let go

[Outro]
Midnight Avenue
```

## 07. Letters in the Rain · 여자 · 팝송 · 70 BPM
**Style (기본값 대신 사용):** `late 1980s adult contemporary ballad, emotive female vocal, 70 bpm, piano and strings, soft rain mood, gentle drums, key change final chorus, analog warmth`

```
[Intro: piano]

[Verse 1]
I found your letters in a box beneath the stairs
Faded ink and paper roses, still the way you left them there
Wait for me, you wrote in winter, I'll be home before the spring
Now it's raining on the window and the phone won't ring

[Pre-Chorus]
Every word you left behind
Is a light I keep inside

[Chorus]
Letters in the rain, I read them once again
Every line a little heartbeat, every page a friend
And even if the ink runs down like tears upon my face
Your love is never washed away

[Verse 2]
I still wear the silver locket that you gave me on the train
I still set an extra coffee cup and whisper out your name
People say that time is gentle, people say a heart will mend
But I'm keeping every letter till the very end

[Pre-Chorus]
Every word you left behind
Is a light I keep inside

[Chorus]
Letters in the rain, I read them once again
Every line a little heartbeat, every page a friend
And even if the ink runs down like tears upon my face
Your love is never washed away

[Bridge]
If the stars could carry what I never said
I would send them all tonight to you

[Final Chorus: key change up]
Letters in the rain, I read them once again
Every line a little heartbeat, every page a friend
And even when the ink is gone and time has run its race
Your love is never washed away

[Outro]
Never washed away
```

## 08. 라디오를 켜면 · 여자 · 시티팝 · 92 BPM
**Style (기본값 대신 사용):** `early 1990s Korean city pop, bright female vocal, 92 bpm, funky bass, clean electric guitar cutting, Rhodes, brass hits, shimmering synths, night drive, romantic, analog warmth`

```
[Intro: Rhodes and bass groove]

[Verse 1]
늦은 밤 창문을 열고 라디오를 켜면
DJ의 낮은 목소리 내 맘을 두드려요
신청곡 엽서 위에 몰래 적은 그대 이름
오늘은 혹시 들릴까 볼륨을 높여요

[Pre-Chorus]
두근두근 내 마음은
주파수를 맞춰요

[Chorus]
라디오를 켜면 그대가 생각나요
반짝이는 이 밤 노래가 흐르면
별빛을 타고 그대에게 갈래요
오늘 밤 나의 노래가 되어 줘요

[Verse 2]
그대도 어디선가 같은 노래 듣고 있을까
같은 멜로디에 살며시 웃고 있을까
창밖엔 도시의 불빛 하나둘씩 춤을 추고
나는 그대 생각에 밤을 새워요

[Pre-Chorus]
두근두근 내 마음은
주파수를 맞춰요

[Chorus]
라디오를 켜면 그대가 생각나요
반짝이는 이 밤 노래가 흐르면
별빛을 타고 그대에게 갈래요
오늘 밤 나의 노래가 되어 줘요

[Instrumental Break: guitar solo]

[Bridge]
시그널 음악이 흐르면
우리만의 시간이 시작돼요

[Final Chorus: key change up]
라디오를 켜면 그대가 생각나요
반짝이는 이 밤 노래가 흐르면
별빛을 타고 그대에게 갈래요
영원히 나의 노래가 되어 줘요
```

## 09. Last Dance in December · 남녀 듀엣 · 팝송 · 72 BPM
**Style (기본값 대신 사용):** `late 1980s adult contemporary duet ballad, male and female vocals, 72 bpm, piano, strings, soft synth pads, slow dance, winter, romantic, key change final chorus, analog warmth`

```
[Intro: piano]

[Verse 1: Male]
Snow is falling on the dance floor lights
The band is playing one more song tonight
[Verse 1: Female]
You lean your head against my shoulder now
And the whole world slows down somehow

[Pre-Chorus: Duet]
Don't say goodbye
Not yet, not tonight

[Chorus: Duet]
Give me one last dance in December
One more turn before the music ends
Hold me close so I'll remember
How it felt to be more than friends

[Verse 2: Female]
Tomorrow you'll be on a plane to somewhere new
[Verse 2: Male]
And I'll be watching every star that's leading you
[Verse 2: Duet]
So let the clock stand still for just a while
I'll keep the memory of your smile

[Pre-Chorus: Duet]
Don't say goodbye
Not yet, not tonight

[Chorus: Duet]
Give me one last dance in December
One more turn before the music ends
Hold me close so I'll remember
How it felt to be more than friends

[Bridge: Male]
And if we never meet again
[Bridge: Female]
I'll hear this song and you'll be there

[Final Chorus: Duet, key change up]
Give me one last dance in December
One more turn before the music ends
Hold me close so I'll remember
Every night until we meet again

[Outro]
One last dance
```

## 10. 다시 그 길에서 · 남자 · 66 BPM · 피날레
**추가 Style:** `warm male tenor vocal, 66 bpm, hopeful, spring, cherry blossoms, big orchestral final chorus`

```
[Intro: piano]

[Verse 1]
참 오랜만에 이 길을 걸어요
그대와 걷던 벚꽃 길 위를
변한 건 없죠 바람도 하늘도
우리만 조금 달라졌을 뿐

[Pre-Chorus]
그때는 몰랐죠
그 모든 날이 선물이었단 걸

[Chorus]
다시 그 길에서 그대를 만난다면
웃으며 인사할 수 있을까요
고마웠다고 행복했다고
늦었지만 꼭 말하고 싶어요

[Verse 2]
그대도 어디선가 잘 지내고 있겠죠
누군가의 곁에서 웃고 있겠죠
아프지 말아요 울지도 말아요
그거면 돼요 난 그거면 돼요

[Pre-Chorus]
그때는 몰랐죠
그 모든 날이 선물이었단 걸

[Chorus]
다시 그 길에서 그대를 만난다면
웃으며 인사할 수 있을까요
고마웠다고 행복했다고
늦었지만 꼭 말하고 싶어요

[Bridge]
시간이 흘러 모든 게 희미해져도
그대와 나의 봄은 여기 남아 있어요

[Final Chorus: key change up, full orchestra]
다시 그 길에서 그대를 만난다면
환하게 웃으며 손 흔들게요
고마웠다고 행복했다고
이제는 웃으며 말할 수 있어요

[Outro: piano fades]
안녕 나의 봄날
```

---

## 곡 고르는 기준 (곡당 2버전 중 1개)

1. 한국어 발음이 뭉개지지 않는지 확인합니다. 특히 후렴 첫 줄이 중요합니다.
2. 마지막 후렴에서 전조가 실제로 나오는지 확인합니다.
3. 인트로가 피아노나 기타로 깔끔하게 시작하는지 확인합니다.
4. 셋 다 아니면 다시 생성합니다. 10곡 완성에 약 150~300크레딧이 들어, Pro 월 2,500크레딧의 10% 안팎입니다.

**현욱님 손길 1줄 권장:** 곡마다 가사 한 줄이라도 직접 고쳐 주시면, 정책상 "사람의 창작 기여"가 분명해지고 노래에도 진짜 감정이 실립니다.

## 커버 이미지 — Gemini 나노바나나, 16:9

```
A rainy Seoul street at night in the early 1990s, a glowing yellow public phone booth,
warm streetlights reflecting on wet asphalt, an old bus passing with blurred lights,
a cassette tape and a handwritten letter on a café window sill in the foreground,
nostalgic film photography look, Kodak Gold 400 grain, soft bokeh, teal and amber palette,
no people's faces, no text, 16:9, cinematic
```
**썸네일 문구 (2줄):** `그 시절 라디오에서` / `흘러나올 것 같은 노래`

## 업로드 정보

**제목:** [Playlist] 1990, 어느 겨울밤에서 봄까지 | 그 시절 라디오에서 흘러나올 것 같은 발라드 10곡 | 밤에 듣기 좋은 노래

**영어 제목:** [Playlist] Winter Night to Spring, 1990 | Retro Korean Ballads & 80s Pop | Songs for Late Nights

**설명란:**
```
그 시절 라디오에서 흘러나왔을 것 같은, 발표되지 않은 노래들.
한 사람의 겨울밤 이별부터 봄날의 작별 인사까지, 10곡으로 이어지는 하나의 이야기입니다.

▸ 곡 목록
[build_playlist.py가 만든 _chapters.txt 붙여넣기]

▸ 모든 가사는 창작곡이며, 음악은 AI 작곡 도구(Suno, 상업 라이선스)로 제작했습니다.
  기획·작사·곡 선택·배열은 사람이 했습니다.

#플레이리스트 #90년대발라드 #옛날노래 #감성발라드 #밤에듣기좋은노래 #시티팝 #playlist
```
> ⚠️ 제목, 태그, 설명에 **실존 가수 이름과 기존 곡 제목은 넣지 않습니다.** 검색 노출을 노린 오해 유발 메타데이터는 유튜브 스팸 정책 위반이고, 실존 가수를 연상시키면 퍼블리시티권 분쟁 소지도 있습니다.

## titles.txt (합성용, 파일명 순서대로)
```
가로등 아래서
마지막 버스
부치지 못한 편지
겨울 공중전화
그대 창가에
Midnight Avenue
Letters in the Rain
라디오를 켜면
Last Dance in December
다시 그 길에서
```

## 합성 명령 (제작 PC)
```
python playlist/build_playlist.py --tracks _playlist/002/tracks --image _playlist/002/cover.png ^
  --titles _playlist/002/titles.txt --out _playlist/002/playlist_002.mp4 --crossfade 2
```
보컬곡은 곡 사이 겹침을 2초로 짧게 줍니다. 길게 겹치면 가사가 섞입니다.
