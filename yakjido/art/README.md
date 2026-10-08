# 삽화 넣는 법 (약지도)

이 폴더에 아래 이름 그대로 PNG 를 넣고 `python3 yakjido/tools/build.py` 를 돌리면 끝이에요.
빌드가 알아서 배포본으로 복사하고, 앱은 **있는 그림만** 그립니다. 없는 그림은 자리도 안 생겨요.
파일을 지우면 배포본에서도 같이 지워집니다.

| 파일명 | 들어가는 화면 | 권장 비율 |
|---|---|---|
| `icon-1024.png` | 앱 아이콘 (192·512·180·마스커블까지 자동 생성) | 1:1 |
| `hero-home.png` | 홈 맨 위 | 16:10 (오른쪽은 비워 두기) |
| `guide-1-where.png` | 3단계 안내 1단계 | 1:1 |
| `guide-2-pharmacy.png` | 증상 › 약국에서 이렇게 말씀하세요 | 3:2 |
| `guide-3-take.png` | 3단계 안내 3단계 | 1:1 |
| `photo-guide.png` | 사진으로 약 알아보기 | 3:2 |
| `pill-search.png` | 이 약이 무슨 약일까 | 1:1 |
| `schedule.png` | 오늘 약, 잊지 않게 | 3:2 |
| `supp-label.png` | 영양제 라벨 사진 찍기 | 1:1 |
| `kids-dose.png` | 아이 해열제 용량 | 1:1 |
| `easy-mode.png` | 내 정보 › 어르신 모드 (88px 원형) | 1:1 |
| `me-safety.png` · `tips.png` · `empty-search.png` | (자리만 예약, 지금은 안 씀) | 1:1 |

`.webp` · `.jpg` 도 같은 이름이면 인식합니다.

## 화풍 (새로 만들 때 앞에 붙일 문장)

```
Style: soft watercolor-like flat illustration, gentle shading, rounded soft edges, a circular
vignette fading into pure white at the border, calm and warm like a good hospital brochure.
Not photorealistic, not cartoon. People: Korean, 60s-70s unless stated, kind natural faces,
gray hair, realistic proportions. Palette: teal #0B6E8F, deep teal #08526B, muted amber #B5711C,
cream #FAF8F3, soft mint #DCEFF5, plus natural skin and wood tones. Absolutely no text, letters,
numbers, logos, or brand packaging. Medicines only as plain white pills, plain paper pharmacy
pouches, a plain syrup bottle. Output PNG.
```

1:1 그림은 앱에서 **원형으로 잘라** 쓰기 때문에 네 모서리에는 중요한 것을 두지 마세요.
