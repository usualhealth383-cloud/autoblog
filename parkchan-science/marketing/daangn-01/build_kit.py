import html, sys, re
D = sys.argv[1]

import re as _re
_ALLOWED = set("~!@#$%^&*()<>-_+=\\₩:;,.?/\"' ")
def safe(t):
    # 당근 입력 칸은 ~!@#$%^&*()<>-_+=\₩:;,.?/"' 외 특수문자를 막는다
    t = t.replace('①', '1)').replace('②', '2)').replace('③', '3)').replace('④', '4)')
    t = t.replace(' — ', ' - ').replace('—', '-').replace('–', '-')
    t = _re.sub(r'(?m)^(\s*)· ', r'\1- ', t)          # 줄머리 가운뎃점 → 하이픈
    t = _re.sub(r'(\d)·(\d)', r'\1, \2', t)          # 1·2 → 1, 2
    t = t.replace(' · ', ', ').replace('·', ', ')
    t = t.replace('›', '>').replace('|', ',').replace('…', '...').replace('’', "'").replace('‘', "'").replace('“', '"').replace('”', '"')
    return t
def bad_chars(t):
    return sorted({c for c in t if not (c.isalnum() or c in _ALLOWED or c in '\n\t' or '\uac00' <= c <= '\ud7a3')})

FEE = "남교입 제2019-115호 · 고1 예비반 교습비 월 317,000원(주 2회 · 월 1,303분)"
PROFILE = [
 ("업체 이름", "박찬통합과학학원 (당근 등록 이름, 2026-10-11 심사 중)"),
 ("카테고리", "교육 › 학원 (앱 목록에서 '입시·보습학원' 또는 가장 가까운 항목)"),
 ("한 줄 소개", "통합과학 전문 · 원장 직강 · 월성 CGV 옆"),
 ("소개글", """대구 월성동 박찬 통합과학 학원입니다.
통합과학의 전신인 공통과학을 가르쳤던 경험과 오랜 입시 지도의 경험으로, 처음부터 끝까지 원장이 직접 가르치고 상담합니다.

· 개념과 원리 위주의 이해 중심 강의
· 기초가 부족한 학생을 위한 특별 보충 수업
· 사고력 · 응용력 향상을 돕는 문제 풀이
· 동영상으로 보강하는 수업 (결석한 날도 학원에서 보강)

반: 중등부 · 고1 예비 · 고1 내신 · 고3 수능
일주일 무료 수강 후 등록을 결정하실 수 있습니다.

남교입 제2019-115호"""),
 ("주소", "대구 달서구 조암로 25 그루빌딩 501호"),
 ("주소 상세 · 찾아오는 길", "월성 CGV 옆 그루빌딩 5층"),
 ("전화번호", "053-213-3577"),
 ("홈페이지 · 블로그", "https://blog.naver.com/parkchan3577"),
 ("영업시간 · 상담 시간", "매일(월~일) 오후 2시 ~ 오후 10시"),
]
PRICES = [
 ("중등부 주 1회 (월 총 1,042분)", "210,000원"),
 ("중등부 주 2회 (월 총 1,303분)", "267,000원"),
 ("고등부 주 1회 (월 총 912분)", "220,000원"),
 ("고등부 주 2회 · 고1 예비반 (월 총 1,303분)", "317,000원"),
]
COUPON = [
 ("쿠폰 이름", "고1 예비반 일주일 무료 수강"),
 ("쿠폰 내용", "현 중3 학생을 위한 고1 예비반 수업을 일주일 동안 무료로 들어 보실 수 있습니다. 상담 전화(053-213-3577) 또는 내원 후 수강 예약을 해 주십시오."),
 ("사용 기간", "2026년 10월 13일 ~ 11월 9일 (개강 첫 주까지)"),
 ("유의 사항", "고1 예비반(화금반 · 수토반) 대상 · 수강 예약 후 사용"),
]
NEWS = [
 ("10월 13일(화)", ["ad_B_cream.png", "02_period.png"], """내년 봄 처음 만나는 '통합과학', 차근차근 준비하실 수 있도록 안내드립니다.

대구 월성동 박찬 통합과학 학원입니다.
현 중3 학생을 위한 고1 예비반을 모집합니다.

· 화금반 11월 3일(화) · 수토반 11월 4일(수) 개강
· 주 2회
· 2027년 2월 28일까지

고등학교 통합과학은 통합과학 1과 2, 두 권입니다.
이 두 권을 3월 입학 전까지 확실히 지도하겠습니다.

먼저 일주일 들어 보시고 등록을 결정하셔도 됩니다.
상담 053-213-3577 (매일 오후 2시 ~ 10시) · 조암로 25 그루빌딩 501호 (월성 CGV 옆)"""),
 ("10월 16일(금)", ["03_twice.png"], """왜 예비반은 주 2회일까요? 원장이 직접 말씀드립니다.

평소 강의를 해 보면, 시간의 여유가 많을수록 더 상세히 설명하고 더 많은 문제를 함께 풀 수 있었습니다.

주 1회 수업에도 나름의 장점이 있을 것입니다.
다만 저는 주 2회 수업으로 조금 더 여유로운 시간 속에서 다양한 지식을 전하고 문제 풀이를 하며, 더 큰 학습 효과를 거두고자 합니다.

그래서 시간의 여유가 있는 고1 예비반 때만 일주일에 두 번 수업합니다.
고등학교에 올라가면 고1 내신반과 고3 수능반은 일주일에 한 번밖에 하지 못합니다.

상담 053-213-3577"""),
 ("10월 20일(화)", ["news_class.png"], """박찬 통합과학 학원은 이렇게 강의합니다.

① 개념과 원리 위주의 이해 중심 강의
중학교 때 과학 기초가 부족했거나 성적이 아쉬웠던 학생을 위해 특별 보충 수업을 준비해 두었습니다.

② 사고력 · 응용력 향상을 돕는 문제 풀이
자료를 해석하고, 처음 보는 상황에 개념을 적용하는 문제를 함께 풉니다.

③ 동영상으로 보강하는 수업
모든 수업은 수업 전에 동영상으로 제작되어 있습니다. 강의 후 부족하다고 느낀 부분이나 결석한 날의 수업도 학원에서 동영상으로 보강할 수 있습니다.

④ 원장 직강
통합과학의 전신인 공통과학을 가르쳤던 경험과 오랜 입시 지도의 경험으로, 처음부터 끝까지 직접 가르치고 상담합니다.

상담 053-213-3577"""),
 ("10월 23일(금)", ["04_change.png"], """지금 중3이 치를 수능, 과학탐구는 통합과학 한 과목입니다.

· 2022 개정 교육과정에 따라 고1 학생은 모두 통합과학을 배웁니다.
· 고교 내신은 2025년 고1부터 5등급제로 바뀌었습니다.
· 2028학년도 수능부터 과학탐구는 통합과학 한 과목이며, 지금 중3 학생들이 치를 수능도 현재 발표 기준으로 같은 체제입니다.

그래서 고1 첫 내신이 고등학교 3년의 출발점입니다.
고1 예비반에서 그 출발을 함께 준비하겠습니다.

상담 053-213-3577"""),
 ("10월 27일(화)", ["ad_C_free.png"], """먼저 일주일 들어 보십시오 — 고1 예비반 무료 수강 쿠폰을 열었습니다.

수업이 아이에게 맞는지 직접 확인해 보시고 등록을 결정하셔도 됩니다.

① 상담 전화 또는 내원
② 수강 예약
③ 일주일 무료 수강
④ 등록 결정

아래 쿠폰을 받아 두시고, 상담 전화 053-213-3577 로 편하게 연락 주십시오.
화금반 11월 3일(화) · 수토반 11월 4일(수) 개강"""),
 ("10월 30일(금)", ["ad_A_black.png", "05_roadmap.png"], """다음 주 개강합니다 — 화금반 11월 3일(화), 수토반 11월 4일(수).

박찬 통합과학 학원의 반은 하나의 흐름으로 이어집니다.

· 중등부반 — 고등학교 과학으로 이어지는 기초 (2027년 1월 개강)
· 고1 예비반 — 3월 입학 전, 통합과학 1·2를 확실히 (지금 모집)
· 고1 내신반 — 학교별 교과서(5개 출판사)에 맞춘 내신 대비 (2027년 3월 ~ 12월)
· 고3 수능반 — 첫 통합과학 수능(2028학년도) 대비 (2027년 1월 개강)

개강 첫 주도 일주일 무료 수강으로 들어 보실 수 있습니다.
상담 053-213-3577 · 월성 CGV 옆 그루빌딩 5층"""),
]
ADS = [
 ("ad_A_black.png", "현 중3 · 고1 예비반 모집", "3월 입학 전 통합과학 1·2를 확실히 · 일주일 무료 수강"),
 ("ad_B_cream.png", "처음 만나는 통합과학, 차근차근", "월성 CGV 옆 · 원장 직강 · 주 2회 고1 예비반"),
 ("ad_C_free.png", "먼저 일주일 들어 보십시오", "고1 예비반 무료 수강 · 11월 3일 · 4일 개강"),
]
def cp(label, text, big=False):
    text = safe(text)
    t = html.escape(text)
    return f'<div class="fld"><div class="lab">{html.escape(label)}<button class="cp" data-text="{html.escape(text, quote=True)}">복사</button></div><div class="val{" big" if big else ""}">{t}</div></div>'
h = []
h.append('<section class="box"><h2>① 비즈프로필 채우기</h2>' + ''.join(cp(k, v, k == "소개글") for k, v in PROFILE) +
         '<div class="fld"><div class="lab">가격(메뉴) — 네 줄 각각 등록</div>' + ''.join(f'<div class="price"><span>{html.escape(safe(a))}</span><b>{b}</b><button class="cp" data-text="{html.escape(safe(a))} {b}">복사</button></div>' for a, b in PRICES) + '</div>'
         '<div class="fld"><div class="lab">프로필 사진 · 매장 사진</div><div class="imgs"><figure><img src="images/00_profile.png" alt="프로필 사진 — 박찬 통합과학 글자 로고"><figcaption>프로필 사진(네이버 블로그와 같음)</figcaption></figure><figure><img src="images/photo_sign_front.jpg" alt="학원 간판과 고1 예비생 모집 현수막"><figcaption>매장 사진 · 간판 정면(첫 장으로)</figcaption></figure><figure><img src="images/photo_sign.png" alt="학원 외벽 간판"><figcaption>매장 사진 · 간판</figcaption></figure><figure><img src="images/photo_banner.png" alt="학원 입구 배너"><figcaption>매장 사진 · 입구</figcaption></figure></div>'
         '<p class="note">매장 사진은 5장 이상이 좋습니다 — 간판 정면을 첫 장으로 두고, 원장님 폰으로 <b>강의실 · 수업 영상 시청 공간 · 교재 책상</b> 3장을 더 찍어 넣어 주십시오(학생 얼굴은 나오지 않게).</p></div></section>')
h.append('<section class="box"><h2>② 쿠폰 만들기</h2>' + ''.join(cp(k, v) for k, v in COUPON) + '</section>')
nh = ''.join(f'<article class="news"><div class="when">소식 {i} · {d}</div><div class="imgs">' + ''.join(f'<figure><img src="images/{im}" alt="소식 {i} 사진 {k+1}"></figure>' for k, im in enumerate(ims)) +
             f'</div>{cp("글", body + chr(10) + chr(10) + FEE, True)}</article>' for i, (d, ims, body) in enumerate(NEWS, 1))
h.append('<section class="box"><h2>③ 소식 6편 — 화·금 주 2회</h2><p class="note">첫 줄이 피드에 보이는 문장입니다. 사진을 먼저 올리고 글을 붙여 넣으면 됩니다. 마지막 줄(등록번호·교습비)은 지우지 마십시오.</p>' + nh + '</section>')
ah = ''.join(f'<article class="news"><figure class="one"><img src="images/{im}" alt="광고 그림 — {html.escape(t)}"></figure>{cp("제목", t)}{cp("본문", b)}</article>' for im, t, b in ADS)
h.append('<section class="box"><h2>④ 광고 (유료 — 시작 전 승인)</h2><p class="note">처음엔 세 그림을 한꺼번에 걸고 2주 뒤 문의가 많이 온 그림만 남깁니다. 제안: 학원 반경 2km · 하루 1만 원 × 14일 ≈ 14만 원. 그림은 1080×1080(1:1)으로 만들었습니다 — 광고 화면이 다른 크기를 요구하면 알려 주십시오.</p>' + ah + '</section>')
order = """<ol class="how"><li>당근 앱 → 나의 당근 → <b>비즈프로필 만들기</b> → 사업자등록증으로 인증</li><li>①을 칸마다 복사해 넣고, 프로필 사진 · 매장 사진 올리기</li><li>②로 <b>쿠폰</b> 만들기</li><li>③ 소식을 날짜에 맞춰 올리기(화·금)</li><li>카운터에 <b>단골 QR</b>(비즈프로필 → 단골 → QR) 두고, 재원생 학부모님께 단골 맺기 부탁</li><li>④ 광고는 비용 확인 후 시작 — ads.daangn.com</li></ol>
<p class="note">개인 계정(월성동 · 화원읍 동네 인증)으로 동네생활 게시판에 학원 홍보 글을 올리면 운영정책에 걸릴 수 있습니다 — 홍보는 비즈프로필로만. 당근 광고도 학원 광고라 '선행' · '1등급' · 다른 학원 비교는 쓰지 않았습니다.</p>"""
T = open(sys.argv[2], encoding='utf-8').read()
T = T.replace('%ORDER%', order).replace('%BODY%', '\n'.join(h))
open(D + '/kit.html', 'w', encoding='utf-8').write(T)
allt = ' '.join(v for _, v in PROFILE + COUPON) + ' '.join(n[2] for n in NEWS) + ' '.join(a[1] + a[2] for a in ADS)
for w in ['선행', '1등급', '완성', '미리 끝', '다른 학원', '타 학원', '아이들은']:
    if w in allt: print('BANNED', w)
md = ['# 당근 올리기 묶음 (daangn-01)', '', '## 비즈프로필'] + [f'- **{k}**: {v}' for k, v in PROFILE] + ['', '## 가격'] + [f'- {a} — {b}' for a, b in PRICES] + ['', '## 쿠폰'] + [f'- **{k}**: {v}' for k, v in COUPON] + ['', '## 소식']
for i, (d, ims, body) in enumerate(NEWS, 1): md += ['', f'### 소식 {i} · {d} — 사진: {", ".join(ims)}', '', body, '', FEE]
md += ['', '## 광고'] + [f'- {im} — 제목: {t} / 본문: {b}' for im, t, b in ADS]
open(D + '/content.md', 'w', encoding='utf-8').write('\n'.join(md) + '\n')
print('ok')
_all = [safe(v) for _, v in PROFILE + COUPON] + [safe(a) for a, _ in PRICES] + [safe(n[2] + chr(10) + FEE) for n in NEWS] + [safe(x) for a in ADS for x in a[1:]]
_bad = sorted({c for t in _all for c in bad_chars(t)})
print('당근 금지 문자:', _bad if _bad else '없음')
