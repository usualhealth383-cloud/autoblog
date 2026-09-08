# 약지도 일러스트 의뢰서 (ChatGPT 이미지 생성용)

모든 그림에 아래 **공통 스타일 블록**을 그대로 붙여 넣고, 그 아래 개별 프롬프트를 이어 붙이세요.
결과물은 이 폴더(`yakjido/art/`)에 파일명대로 저장하면 앱에 연결합니다.

## 공통 스타일 블록 (매번 앞에 붙이기)

```
Style: warm premium flat vector illustration, soft rounded shapes, gentle two-tone shading, no outlines,
calm and trustworthy (like a good hospital brochure, not a cartoon). No text, no letters, no logos, no
real brand packaging. Clean transparent background (PNG). Palette only: teal #0B6E8F, deep teal #08526B,
amber #B5711C, cream #FAF8F3, sand #EFEBE3, soft mint #DCEFF5, charcoal #1E2A30.
Characters: Korean adults in their 60s–70s, kind faces, natural gray hair, comfortable home clothes,
realistic proportions (no big heads, no childish exaggeration). Medicines shown as plain white/pale pills,
small paper pharmacy pouches, and a simple syrup bottle — never identifiable products.
```

## 개별 프롬프트

| # | 파일명 | 크기 | 프롬프트 (공통 블록 뒤에 붙임) |
|---|---|---|---|
| 1 | `icon-1024.png` | 1024×1024, 배경 있음 | App icon for “약지도” (medicine map). A single simple symbol: a map-pin shape whose inner circle is a capsule/pill, teal #0B6E8F on cream #FAF8F3 background, centered, 20% padding on all sides so it survives rounded/circle masks, no text. Give 2 variants: (a) pin+capsule, (b) pin+two-tone round tablet. |
| 2 | `hero-home.png` | 1600×1000 | An elderly Korean couple at a sunlit kitchen table; the wife holds a smartphone taking a photo of a small paper pharmacy pouch, the husband holds a glass of water. Mood: relaxed, morning, warm. Wide composition with empty space on the right third for UI text. |
| 3 | `guide-1-where.png` | 800×800 | A senior man gently touching his lower back with one hand, slight discomfort but calm expression, standing in a living room. Centered, lots of margin. |
| 4 | `guide-2-pharmacy.png` | 800×800 | A friendly pharmacist (40s, white coat, no logo) handing a small paper bag across a counter to a senior woman; both smiling softly. |
| 5 | `guide-3-take.png` | 800×800 | Close-up of hands of an elderly person: one hand holding one white tablet, the other a glass of water; a simple analog clock and an empty rice bowl in the background to suggest “after a meal”. |
| 6 | `photo-guide.png` | 1200×800 | Top-down view: a smartphone held above a table photographing a pharmacy pouch and two pills laid flat under bright daylight; a soft glow indicates good lighting. No screen text. |
| 7 | `easy-mode.png` | 800×800 | A smiling senior woman wearing reading glasses, holding a phone at arm’s length with large simple buttons implied only as blank rounded rectangles (no text). Feeling: “this is easy”. |
| 8 | `kids-dose.png` | 800×800 | A mother measuring pink-tinted syrup in a small oral syringe for a toddler sitting on her lap; a kitchen scale nearby suggests “by weight”. Gentle, reassuring. |
| 9 | `empty-search.png` | 600×600 | A minimal magnifying glass over three plain pills of different shapes (round, oval, capsule) in teal/amber tones; calm, not sad. |
| 10 | `supp-label.png` | 800×800 | An elderly man reading the back label of a plain supplement bottle (label is a blank rectangle), squinting slightly, holding it toward the light. |

## 체크리스트 (받은 그림 확인)
- 글자·로고·실제 제품이 보이지 않는가
- 얼굴이 유치하지 않고 따뜻한가(60~70대, 자연스러운 비율)
- 배경이 투명한가(아이콘 제외)
- 팔레트를 벗어난 강한 원색이 없는가

## 연결 위치(제작 후 제가 연결)
1 → `manifest`·홈 화면 아이콘 / 2 → 홈 히어로 / 3·4·5 → 3단계 안내 각 단계 상단 / 6 → 사진으로 약 알아보기 첫 화면 / 7 → 어르신 모드 켜기 설명 / 8 → 소아 용량 계산기 / 9 → 검색 결과 없음 / 10 → 영양제 라벨 사진 버튼
