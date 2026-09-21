# 아이콘 원본 — 손대지 마세요

`icon-현욱님-구글드라이브-1254.png` 는 현욱님이 구글드라이브
「약 지도 Medicine Map」 폴더에 올려 주신 **원본 그대로**입니다.

`../icon-1024.png` 는 그 원본에서 **바깥 크림 여백만 잘라** 정사각형으로 맞춘 것입니다.
폰 홈 화면에서 다른 앱 아이콘과 크기가 맞아야 해서 잘랐습니다. 그림은 건드리지 않았습니다.

## 다시 만들 때
```python
from PIL import Image, ImageChops
im = Image.open('icon-현욱님-구글드라이브-1254.png').convert('RGB')
bgc = im.getpixel((4, 4))
box = ImageChops.difference(im, Image.new('RGB', im.size, bgc)).convert('L').point(lambda p: 255 if p > 18 else 0).getbbox()
cut = im.crop(box); s = max(cut.size)
sq = Image.new('RGB', (s, s), bgc); sq.paste(cut, ((s - cut.width) // 2, (s - cut.height) // 2))
sq.resize((1024, 1024), Image.LANCZOS).save('../icon-1024.png')
```

## 하지 말 것
- **빌드가 `art/` 안의 파일을 고치게 두지 마세요.** 2026-09-21 까지 `tools/build.py` 가
  `art/icon.svg` 로 `art/icon-1024.png` 를 덮어쓰고 있었습니다. 현욱님이 주신 원본이
  제가 옮겨 그린 벡터본으로 조용히 바뀌어 있었고, 형태가 눈에 띄게 달랐습니다
  (핀이 더 뾰족하고, 캡슐이 작고, 흰 캡슐에 없어야 할 테두리가 있었습니다).
  지금 build.py 는 `art/` 를 읽기만 하고, 끝에서 해시로 확인합니다.
- 옮겨 그린 벡터본(icon.svg·icon-maskable.svg)은 **지웠습니다.** 원본보다 나쁩니다.
