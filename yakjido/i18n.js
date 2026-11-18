/* ▼▼ 위기번호 표 시작 ▼▼ */
/* ═══ 메디나눔 위기·응급 번호 표 — 나라 기준(말 기준 아님) · 2026-11-04 곁에에서 꺼냄(다섯 앱 공용 · 길동무 「말과 나라」가 재사용)
   나라: ISO 2자. 위기[0] = 한국 109(자살예방) 자리, 위기[1] = 한국 1577-0199(정신건강) 자리. 위기가 비면 응급 번호로.
   확인된 번호만 넣는다(멕시코는 응급 911 만 · 위기 전용 번호 확인 전). 표에 없는 나라는 XX — 번호 null: 누르는 단추 없이 「그 나라 응급 번호로 전화하세요」 글만.
   11-04b: XX 112 기본값 없앰 · 응급 번호 12나라(VN TH PH ID NP UZ KH MN LK BD IN GB) — 출처는 줄 옆.
   나라 고르는 순서: ① localStorage mn.place.country(사용자가 「말과 나라」에서 고른 값) ② 앱이 가진 값 ③ 시간대·기기 지역 짐작.
   ── 공용 부품 셋(위기번호 표 · 설정 부품 · 응급카드 부품) 공통 약속 · 주인: 길동무 세션 ──
   판: 이 파일 안 «판» 한 곳(코드의 판 값). 고치면 판을 올리고 다섯 앱에 다시 심는다. 지금 판 2026-11-05a.
   심는 순서(앱마다 같다): ① 위기번호 표 → ② 설정 부품 → ③ 응급카드 부품 — 표가 앞에 있어야 말과 나라 고르개·응급 번호가 표를 쓴다.
   심기·비교: python3 _도구/공용부품_심기.py 비교 · python3 _도구/공용부품_심기.py <소아|곁에|길동무|CS> · 다른 저장소(약지도): python3 _도구/공용부품_심기.py 파일 <경로>
   ⛔ 앱 사본을 직접 고치지 않는다 — 이 파일을 고치고 다시 심는다(심기 스크립트는 정본과 다른 사본을 보면 멈춘다).
*/
(function () {
  if (window.메디나눔위기번호) return;
  var 판 = '2026-11-19b';   /* 11-17a 영국 위기[1] NHS 111(2번) · 방글라데시 Kaan Pete Roi(시간 있음) · 나라 「안내」 한 줄(안내(나라, 말)) */   /* 11-05b 유럽연합 26나라(스페인 빼고) 112 · 11-04d 라오스 LA 구급 1195 · TH 1669·VN 115·KH 119 gov.uk 다시 확인 · 11-04c 머리 주석 정리 */
  var 표 = {
    KR: { 이름: { ko: '한국', en: 'Korea', es: 'Corea', ja: '韓国', zh: '韩国' }, 응급: '119', 경찰: '112', 위기: ['109', '1577-0199'] },
    US: { 이름: { ko: '미국', en: 'United States', es: 'Estados Unidos', ja: 'アメリカ', zh: '美国' }, 응급: '911', 경찰: '911', 위기: ['988'] },
    ES: { 이름: { ko: '스페인', en: 'Spain', es: 'España', ja: 'スペイン', zh: '西班牙' }, 응급: '112', 경찰: '112', 위기: ['024'] },
    JP: { 이름: { ko: '일본', en: 'Japan', es: 'Japón', ja: '日本', zh: '日本' }, 응급: '119', 경찰: '110', 위기: ['0570-783-556', '0570-064-556'] }   /* 109(자살예방) 자리 → いのちの電話, 1577-0199(정신건강) 자리 → こころの健康相談統一ダイヤル */,
    CN: { 이름: { ko: '중국', en: 'China', es: 'China', ja: '中国', zh: '中国' }, 응급: '120', 경찰: '110', 위기: ['12356'] },
    MX: { 이름: { ko: '멕시코', en: 'Mexico', es: 'México', ja: 'メキシコ', zh: '墨西哥' }, 응급: '911', 경찰: '911', 위기: ['800 911 2000'] },   /* 11-05 위기 Línea de la Vida 800 911 2000 24시간 — paho.org(25주년) · tabasco.gob.mx(주 보건부) · 11-03 Main — 확인된 응급 911 만(위기 전용 번호는 확인 전이라 넣지 않음 → 위기 자리도 911) */
    HK: { 이름: { ko: '홍콩', en: 'Hong Kong', es: 'Hong Kong', ja: '香港', zh: '香港' }, 응급: '999', 경찰: '999', 위기: ['2896 0000'] },   /* 10-27 Main 표 — The Samaritans(英文) */
    /* 11-04 Main — 한국에 많이 사는 나라부터 «응급(구급) 번호만». 공식 출처 두 곳이 맞는 것만. 위기 상담 번호는 아직 넣지 않음(위기 자리도 응급 번호).
       경찰은 한 번호로 모두 받는 나라만 같은 번호, 나머지는 null(→ 글로 「그 나라 경찰 번호」, 누르는 단추 없음).
       뺀 나라: 미얀마(영국 정부 192 · 미국 대사관은 192 를 고속도로 번호로·다른 번호와 엇갈림) → 그 밖. */
    VN: { 이름: { ko: '베트남', en: 'Vietnam', es: 'Vietnam', ja: 'ベトナム', zh: '越南' }, 응급: '115', 경찰: null, 위기: [] },   /* gov.uk/foreign-travel-advice/vietnam/getting-help · vietnam.travel(베트남 관광청) — 115 구급, 112 아님 */
    TH: { 이름: { ko: '태국', en: 'Thailand', es: 'Tailandia', ja: 'タイ', zh: '泰国' }, 응급: '1669', 경찰: null, 위기: ['1323'] },   /* 11-05 위기 정신건강국 1323 24시간 — thailand.go.th · nationthailand.com · gov.uk Thailand health(1669 보건부) · th.usembassy.gov */
    PH: { 이름: { ko: '필리핀', en: 'Philippines', es: 'Filipinas', ja: 'フィリピン', zh: '菲律宾' }, 응급: '911', 경찰: '911', 위기: ['1553'] },   /* 11-05 위기 NCMH Crisis Hotline 1553(보건부) 24시간 — lusog-isip.deped.gov.ph · DOH 발표(mb.com.ph 2026-01) · gov.uk Philippines getting-help(911 구급·소방·경찰) · ph.usembassy.gov */
    ID: { 이름: { ko: '인도네시아', en: 'Indonesia', es: 'Indonesia', ja: 'インドネシア', zh: '印度尼西亚' }, 응급: '118', 경찰: null, 위기: [] },   /* gov.uk Indonesia getting-help(118) · indonesia.travel(118·119) */
    NP: { 이름: { ko: '네팔', en: 'Nepal', es: 'Nepal', ja: 'ネパール', zh: '尼泊尔' }, 응급: '102', 경찰: null, 위기: [] },   /* gov.uk Nepal getting-help · np.usembassy.gov · heoc.mohp.gov.np */
    UZ: { 이름: { ko: '우즈베키스탄', en: 'Uzbekistan', es: 'Uzbekistán', ja: 'ウズベキスタン', zh: '乌兹别克斯坦' }, 응급: '103', 경찰: null, 위기: [] },   /* gov.uk Uzbekistan getting-help · uzbekistan.travel */
    KH: { 이름: { ko: '캄보디아', en: 'Cambodia', es: 'Camboya', ja: 'カンボジア', zh: '柬埔寨' }, 응급: '119', 경찰: null, 위기: [] },   /* gov.uk Cambodia getting-help · travel.state.gov Cambodia */
    LA: { 이름: { ko: '라오스', en: 'Laos', es: 'Laos', ja: 'ラオス', zh: '老挝' }, 응급: '1195', 경찰: null, 위기: [] },   /* 11-04d 구급 1195(경찰 1191·화재 1190 따로) — gov.uk/foreign-travel-advice/laos/getting-help · travel.gc.ca Laos 둘 다 1195. 일부 생활 안내의 195 는 공식 아님 */
    MN: { 이름: { ko: '몽골', en: 'Mongolia', es: 'Mongolia', ja: 'モンゴル', zh: '蒙古' }, 응급: '103', 경찰: null, 위기: [] },   /* gov.uk Mongolia getting-help · mn.usembassy.gov */
    LK: { 이름: { ko: '스리랑카', en: 'Sri Lanka', es: 'Sri Lanka', ja: 'スリランカ', zh: '斯里兰卡' }, 응급: '1990', 경찰: null, 위기: ['1926'] },   /* 11-05 위기 국립정신건강연구소 1926 24시간(보건부 소속) — NIMH 연차보고 2022 · sundaytimes.lk · gov.uk Sri Lanka health · lk.usembassy.gov(1990 Suwa Seriya) */
    BD: { 이름: { ko: '방글라데시', en: 'Bangladesh', es: 'Bangladés', ja: 'バングラデシュ', zh: '孟加拉国' }, 응급: '999', 경찰: '999', 위기: ['09612-119911'], 안내: { ko: '목숨이 위험하면 먼저 999 · Kaan Pete Roi(마음 상담) 09612-119911 은 매일 오후 3시~새벽 3시', en: 'If a life is at risk, call 999 first · Kaan Pete Roi (emotional support) 09612-119911 is open daily 3 pm–3 am', es: 'Si hay riesgo para la vida, llame primero al 999 · Kaan Pete Roi (apoyo emocional) 09612-119911 atiende cada día de 15:00 a 3:00', ja: '命に危険があるときはまず999 · Kaan Pete Roi(心の相談)09612-119911 は毎日 午後3時〜午前3時', zh: '有生命危险请先拨999 · Kaan Pete Roi(情绪支持)09612-119911 每天下午3点至凌晨3点' } },   /* 11-17 위기 Kaan Pete Roi — kaanpeteroi.org(공식 · 매일 15:00~03:00 · 휴일 없음) · LifeLine International 같은 값. 24시간이 아니라서 응급 999 먼저 */   /* gov.uk Bangladesh getting-help · 999.gov.bd */
    IN: { 이름: { ko: '인도', en: 'India', es: 'India', ja: 'インド', zh: '印度' }, 응급: '112', 경찰: '112', 위기: ['14416'] },   /* 11-05 위기 Tele-MANAS 14416(보건가족복지부) — pib.gov.in PRID 2022057 · PRID 1919200 · gov.uk India health(112) · India ERSS(112 · 내무부) */
    GB: { 이름: { ko: '영국', en: 'United Kingdom', es: 'Reino Unido', ja: 'イギリス', zh: '英国' }, 응급: '999', 경찰: '999', 위기: ['116 123', '111'], 안내: { ko: '111 은 걸고 2번 — 정신건강 위기(잉글랜드 · 24시간) · 목숨이 위험하면 999', en: 'For 111, press 2 — mental health crisis (England, 24 hours) · If a life is at risk, call 999', es: 'En el 111, pulse 2: crisis de salud mental (Inglaterra, 24 horas) · Si hay riesgo para la vida, llame al 999', ja: '111 はかけたら2番 — 心の危機(イングランド・24時間)· 命に危険があるときは999', zh: '拨打111后按2 — 心理危机(英格兰,24小时)· 有生命危险请拨999' } },   /* gov.uk · NHS 999 · 11-05 위기 Samaritans 116 123 24시간 — phw.nhs.wales · 111.wales.nhs.uk · cntw.nhs.uk */   /* 11-17 위기[1] NHS 111 「2번 — 정신건강」 잉글랜드 24시간 · 모든 나이 — england.nhs.uk/2024/08(NHS 111 offering crisis mental health support) · 지역 NHS 안내(111 → 2) */
    /* 11-05 현욱님 결정(소아 경유) — 유럽연합 27개국 공통 응급 번호 112(유럽 지침 2002/22/EC 제26조 · (EU) 2018/1972 제109조). 위기 상담은 나라마다 달라 빈칸(→ 응급 번호), 경찰도 빈칸. 스페인은 위에 024 와 함께 있다 */
    AT: { 이름: { ko: '오스트리아', en: 'Austria', es: 'Austria', ja: 'オーストリア', zh: '奥地利' }, 응급: '112', 경찰: null, 위기: [] },
    BE: { 이름: { ko: '벨기에', en: 'Belgium', es: 'Bélgica', ja: 'ベルギー', zh: '比利时' }, 응급: '112', 경찰: null, 위기: [] },
    BG: { 이름: { ko: '불가리아', en: 'Bulgaria', es: 'Bulgaria', ja: 'ブルガリア', zh: '保加利亚' }, 응급: '112', 경찰: null, 위기: [] },
    HR: { 이름: { ko: '크로아티아', en: 'Croatia', es: 'Croacia', ja: 'クロアチア', zh: '克罗地亚' }, 응급: '112', 경찰: null, 위기: [] },
    CY: { 이름: { ko: '키프로스', en: 'Cyprus', es: 'Chipre', ja: 'キプロス', zh: '塞浦路斯' }, 응급: '112', 경찰: null, 위기: [] },
    CZ: { 이름: { ko: '체코', en: 'Czechia', es: 'Chequia', ja: 'チェコ', zh: '捷克' }, 응급: '112', 경찰: null, 위기: [] },
    DK: { 이름: { ko: '덴마크', en: 'Denmark', es: 'Dinamarca', ja: 'デンマーク', zh: '丹麦' }, 응급: '112', 경찰: null, 위기: [] },
    EE: { 이름: { ko: '에스토니아', en: 'Estonia', es: 'Estonia', ja: 'エストニア', zh: '爱沙尼亚' }, 응급: '112', 경찰: null, 위기: [] },
    FI: { 이름: { ko: '핀란드', en: 'Finland', es: 'Finlandia', ja: 'フィンランド', zh: '芬兰' }, 응급: '112', 경찰: null, 위기: [] },
    FR: { 이름: { ko: '프랑스', en: 'France', es: 'Francia', ja: 'フランス', zh: '法国' }, 응급: '112', 경찰: null, 위기: [] },
    AU: { 이름: { ko: '호주', en: 'Australia', es: 'Australia', ja: 'オーストラリア', zh: '澳大利亚' }, 응급: '000', 경찰: '000', 위기: ['13 11 14'] },   /* 11-19 Lifeline · 원천: lifeline.org.au · healthdirect.gov.au(000) · findahelpline.com/countries/au */
    CA: { 이름: { ko: '캐나다', en: 'Canada', es: 'Canadá', ja: 'カナダ', zh: '加拿大' }, 응급: '911', 경찰: '911', 위기: ['988'] },   /* 11-19 9-8-8 전화·문자 · 원천: 988.ca · crtc.gc.ca(911) · findahelpline.com/countries/ca */
    NZ: { 이름: { ko: '뉴질랜드', en: 'New Zealand', es: 'Nueva Zelanda', ja: 'ニュージーランド', zh: '新西兰' }, 응급: '111', 경찰: '111', 위기: ['1737'] },   /* 11-19 1737 전화·문자 · 원천: 1737.org.nz · police.govt.nz(111) · findahelpline.com/countries/nz */
    DE: { 이름: { ko: '독일', en: 'Germany', es: 'Alemania', ja: 'ドイツ', zh: '德国' }, 응급: '112', 경찰: '110', 위기: ['0800 111 0 111', '0800 111 0 222', '116 123'], 안내: { ko: '텔레폰제엘조르게 — 독일어 상담 · 24시간 · 통화료 없음', en: 'TelefonSeelsorge — German-language counselling · 24 hours · free call', es: 'TelefonSeelsorge — atención en alemán · 24 horas · llamada gratuita', ja: 'テレフォンゼールゾルゲ — ドイツ語の相談 · 24時間 · 通話料なし', zh: 'TelefonSeelsorge — 德语咨询 · 24小时 · 免费电话' } },   /* 11-19 Main · 원천 둘: findahelpline.com/organizations/telefonseelsorge · telefonseelsorge.de(둘 다 0800 111 0 111 · 0800 111 0 222 · 116 123). 경찰 110 */
    GR: { 이름: { ko: '그리스', en: 'Greece', es: 'Grecia', ja: 'ギリシャ', zh: '希腊' }, 응급: '112', 경찰: null, 위기: [] },
    HU: { 이름: { ko: '헝가리', en: 'Hungary', es: 'Hungría', ja: 'ハンガリー', zh: '匈牙利' }, 응급: '112', 경찰: null, 위기: [] },
    IE: { 이름: { ko: '아일랜드', en: 'Ireland', es: 'Irlanda', ja: 'アイルランド', zh: '爱尔兰' }, 응급: '112', 경찰: null, 위기: [] },
    IT: { 이름: { ko: '이탈리아', en: 'Italy', es: 'Italia', ja: 'イタリア', zh: '意大利' }, 응급: '112', 경찰: null, 위기: [] },
    LV: { 이름: { ko: '라트비아', en: 'Latvia', es: 'Letonia', ja: 'ラトビア', zh: '拉脱维亚' }, 응급: '112', 경찰: null, 위기: [] },
    LT: { 이름: { ko: '리투아니아', en: 'Lithuania', es: 'Lituania', ja: 'リトアニア', zh: '立陶宛' }, 응급: '112', 경찰: null, 위기: [] },
    LU: { 이름: { ko: '룩셈부르크', en: 'Luxembourg', es: 'Luxemburgo', ja: 'ルクセンブルク', zh: '卢森堡' }, 응급: '112', 경찰: null, 위기: [] },
    MT: { 이름: { ko: '몰타', en: 'Malta', es: 'Malta', ja: 'マルタ', zh: '马耳他' }, 응급: '112', 경찰: null, 위기: [] },
    NL: { 이름: { ko: '네덜란드', en: 'Netherlands', es: 'Países Bajos', ja: 'オランダ', zh: '荷兰' }, 응급: '112', 경찰: null, 위기: [] },
    PL: { 이름: { ko: '폴란드', en: 'Poland', es: 'Polonia', ja: 'ポーランド', zh: '波兰' }, 응급: '112', 경찰: null, 위기: [] },
    PT: { 이름: { ko: '포르투갈', en: 'Portugal', es: 'Portugal', ja: 'ポルトガル', zh: '葡萄牙' }, 응급: '112', 경찰: null, 위기: [] },
    RO: { 이름: { ko: '루마니아', en: 'Romania', es: 'Rumanía', ja: 'ルーマニア', zh: '罗马尼亚' }, 응급: '112', 경찰: null, 위기: [] },
    SK: { 이름: { ko: '슬로바키아', en: 'Slovakia', es: 'Eslovaquia', ja: 'スロバキア', zh: '斯洛伐克' }, 응급: '112', 경찰: null, 위기: [] },
    SI: { 이름: { ko: '슬로베니아', en: 'Slovenia', es: 'Eslovenia', ja: 'スロベニア', zh: '斯洛文尼亚' }, 응급: '112', 경찰: null, 위기: [] },
    SE: { 이름: { ko: '스웨덴', en: 'Sweden', es: 'Suecia', ja: 'スウェーデン', zh: '瑞典' }, 응급: '112', 경찰: null, 위기: [] },
    XX: { 이름: { ko: '그 밖', en: 'Other', es: 'Otro', ja: 'その他', zh: '其他' }, 응급: null, 경찰: null, 위기: [] }   /* 11-04 Main — 모르는 나라는 누르는 번호 없음(112 기본값 없앰) */
  };
  /* 11-16 Main 결정(안전 쪽) — 나라 짐작은 이 한 곳에서. 시간대가 표에 있으면 그 나라 · 시간대는 읽히는데 표에 없으면 XX(「현지 응급 번호」 — 해외에서 119 가 안 통하는 나라가 많다) ·
     시간대를 «못 읽을 때만» 한국어 화면은 KR(119). 기기 언어의 지역(ko-KR·en-US)으로는 짐작하지 않는다(11-04h). 앱은 고른 나라(mn.place) → 이 짐작 순으로 쓴다 */
  var 시간대표 = { 'Pacific/Auckland': 'NZ', 'Pacific/Chatham': 'NZ', 'Asia/Seoul': 'KR', 'Asia/Tokyo': 'JP', 'Asia/Shanghai': 'CN', 'Asia/Chongqing': 'CN', 'Asia/Urumqi': 'CN', 'Asia/Hong_Kong': 'HK', 'Europe/Madrid': 'ES', 'Atlantic/Canary': 'ES', 'Africa/Ceuta': 'ES',
        'America/Mexico_City': 'MX', 'America/Monterrey': 'MX', 'America/Merida': 'MX', 'America/Cancun': 'MX', 'America/Chihuahua': 'MX', 'America/Mazatlan': 'MX', 'America/Hermosillo': 'MX', 'America/Tijuana': 'MX',
        'Europe/London': 'GB', 'Europe/Dublin': 'IE', 'Asia/Singapore': 'SG', 'Asia/Manila': 'PH', 'Asia/Kolkata': 'IN', 'Asia/Calcutta': 'IN', 'Pacific/Auckland': 'NZ',
        'Asia/Ho_Chi_Minh': 'VN', 'Asia/Saigon': 'VN', 'Asia/Bangkok': 'TH', 'Asia/Jakarta': 'ID', 'Asia/Makassar': 'ID', 'Asia/Jayapura': 'ID', 'Asia/Kathmandu': 'NP', 'Asia/Katmandu': 'NP', 'Asia/Tashkent': 'UZ', 'Asia/Samarkand': 'UZ',
        'Asia/Phnom_Penh': 'KH', 'Asia/Ulaanbaatar': 'MN', 'Asia/Ulan_Bator': 'MN', 'Asia/Colombo': 'LK', 'Asia/Dhaka': 'BD',
        'Europe/Berlin': 'DE', 'Europe/Busingen': 'DE', 'Europe/Paris': 'FR', 'Europe/Rome': 'IT', 'Europe/Amsterdam': 'NL', 'Europe/Brussels': 'BE', 'Europe/Vienna': 'AT', 'Europe/Warsaw': 'PL', 'Europe/Prague': 'CZ', 'Europe/Stockholm': 'SE', 'Europe/Copenhagen': 'DK', 'Europe/Helsinki': 'FI', 'Europe/Lisbon': 'PT', 'Atlantic/Madeira': 'PT', 'Atlantic/Azores': 'PT', 'Europe/Athens': 'GR', 'Europe/Budapest': 'HU', 'Europe/Bucharest': 'RO', 'Europe/Sofia': 'BG', 'Europe/Zagreb': 'HR', 'Europe/Ljubljana': 'SI', 'Europe/Bratislava': 'SK', 'Europe/Vilnius': 'LT', 'Europe/Riga': 'LV', 'Europe/Tallinn': 'EE', 'Europe/Luxembourg': 'LU', 'Europe/Malta': 'MT', 'Asia/Nicosia': 'CY', 'Asia/Famagusta': 'CY', 'Europe/Nicosia': 'CY', 'Europe/Mariehamn': 'FI' };
  function 나라짐작(말) {
    var tz = ''; try { tz = Intl.DateTimeFormat().resolvedOptions().timeZone || ''; } catch (e) { tz = ''; }
    if (!tz) return String(말 || '').slice(0, 2) === 'ko' ? 'KR' : 'XX';
    if (시간대표[tz]) return 시간대표[tz];
    if (/^America\/(New_York|Chicago|Denver|Los_Angeles|Phoenix|Anchorage|Detroit|Indiana|Kentucky|Boise|Juneau|Sitka|Nome|Adak|Menominee|North_Dakota)|^Pacific\/Honolulu$/.test(tz)) return 'US';
    if (/^America\/(Toronto|Vancouver|Edmonton|Winnipeg|Halifax|St_Johns|Regina|Montreal)/.test(tz)) return 'CA';
    if (/^Australia\//.test(tz)) return 'AU';
    return 'XX';
  }
  function 고른곳() { try { var v = JSON.parse(localStorage.getItem('mn.place') || 'null'); if (v && v.country) return 표[v.country] ? v.country : 'XX'; } catch (e) {} return null; }
  function 안내(나라, 말) { var n = 표[나라]; if (!n || !n.안내) return ''; var k = String(말 || 'ko').slice(0, 2); return n.안내[k] || n.안내.en || ''; }   /* 번호만으로 모자랄 때(누른 뒤 몇 번 · 여는 시간) 화면에 한 줄 */
  window.메디나눔위기번호 = { 판: 판, 표: 표, 고른곳: 고른곳, 나라짐작: 나라짐작, 시간대표: 시간대표, 안내: 안내 };   /* 표를 쓰는 앱은 읽기만 */
})();
/* ▲▲ 위기번호 표 끝 ▲▲ */
/* ═══ 약지도 다섯 언어(ko · en · es · ja · zh) — 10-27 현욱님 · 요청서 yozm-health docs/requests/20261027_메디나눔_전앱_다섯언어.md ═══
   한국어이고 한국에 있으면 이 파일을 받지 않는다(첫 화면 예산). 받으면 하는 일:
   ① 그 언어 사전(data/i18n/<lang>.json)을 받아 — 증상 응급·진료 신호, 처방약 길잡이 응급 칸(안전 먼저), 화면 글
   ② 그린 화면의 글을 사전으로 바꾼다(없는 글은 한국어 그대로 — 안전 칸을 숨기지 않는다)
   ③ 응급·마음 위기 번호를 «있는 나라» 표로 바꾼다(언어가 아니라 나라 — 표에 있는 숫자만)
   ④ 한국어가 아닌 화면 맨 아래에 「한국어 원문에서 번역」 한 줄 + 원문 보기(11-05 「검수 전」 꼬리 뗌) */
(function () {
  if (window.I18N) return;
  var L = window.LANG || 'ko', CC = window.CC || 'KR';
  /* 나라별 번호 — 요청서 표만(새 나라·번호는 Main 이 원문 확인 뒤 더함). m = 마음 위기 */
  var EMG = { KR: { e: '119', m: ['109', '1577-0199'] }, US: { e: '911', m: ['988'] }, ES: { e: '112', m: ['024'] },
              JP: { e: '119', m: ['0570-064-556', '0570-783-556'] }, CN: { e: '120', m: ['12356'] } };
  /* 11-04b 약지도 표(KR·US·ES·JP·CN) 먼저, 없으면 공용 위기번호 표(_도구/위기번호_표.js). 표에도 없으면 번호 없음(null) — 누르는 단추 없이 「그 나라 응급 번호」 글 */
  var 공표 = window.메디나눔위기번호 && window.메디나눔위기번호.표, 공 = 공표 && 공표[CC];
  var N = EMG[CC] || (공 && 공.응급 ? { e: 공.응급, m: 공.위기 || [] } : { e: null, m: [], unknown: true });
  var 현지 = { ko: '현지 응급 번호(한국에서는 119)', en: 'the local emergency number', es: 'el número de emergencias del país', ja: '現地の緊急番号', zh: '当地急救电话' }[L] || 'the local emergency number';
  var DICT = null, ui = {}, uiN = {}, UH = {}, UHN = {}, REV = {}, KO = new Map();   /* KO — 번역 글 → 바꾸기 전 한국어(그릴 때마다 다시 얹어도 남게 한 번만 만든다) */
  var NOTE = { en: 'Translated from the Korean original', es: 'Traducido del original en coreano', ja: '韓国語の原文からの翻訳です', zh: '译自韩文原文' };   /* 11-05 현욱님·Main 「검수 전」 꼬리 떼기 — 번역이라는 사실만 */
  var ORIG = { en: 'Show Korean original', es: 'Ver original en coreano', ja: '韓国語の原文を見る', zh: '查看韩文原文' };
  var KRNOTE = { en: 'Medicine doses follow Korean approval — check with a pharmacist or doctor where you live.', es: 'Las dosis siguen la aprobación de Corea: confírmelas con un farmacéutico o médico de su país.', ja: '薬の量は韓国の承認基準です。お住まいの国の薬剤師・医師に確認してください。', zh: '药物剂量依据韩国批准标准，请向您所在国家的药师或医生确认。' };
  var key = function (t) { return String(t).replace(/\s+/g, ' ').trim(); };
  var numKey = function (t) { return t.replace(/\d[\d,.]*/g, '#'); };

  /* 글꼴·줄바꿈 — ja·zh 는 낱말 단위가 아니라 글자 단위(keep-all 이면 한 줄이 통째로 넘침) */
  var root = document.documentElement;
  root.lang = L === 'zh' ? 'zh-Hans' : L; root.classList.add('lang-' + L);
  /* ja·zh 는 기기 글꼴(10-27 바깥 파일 0 — 중국은 구글 글꼴이 막히고 Noto CJK 는 너무 커서 싣지 않는다) */
  var st = document.createElement('style');
  st.textContent = '.lang-ja body,.lang-ja button,.lang-ja input,.lang-ja textarea{font-family:"Hiragino Sans","Hiragino Kaku Gothic ProN","Noto Sans CJK JP","Noto Sans JP","Yu Gothic UI","Meiryo","Pretendard Variable",system-ui,sans-serif}.lang-zh body,.lang-zh button,.lang-zh input,.lang-zh textarea{font-family:"PingFang SC","Hiragino Sans GB","Noto Sans CJK SC","Noto Sans SC","Microsoft YaHei","Pretendard Variable",system-ui,sans-serif}' +
    'html:not(.lang-ko) nav.tabbar button{white-space:normal;text-align:center;font-size:12.5px;line-height:1.15;padding-inline:2px;overflow-wrap:normal;hyphens:auto;letter-spacing:-.01em}@media (min-width:1024px){html:not(.lang-ko) nav.tabbar button{text-align:left;font-size:1rem}}' +
    '.lang-ja *,.lang-zh *{word-break:normal!important;line-break:strict;overflow-wrap:anywhere}.lang-en *,.lang-es *{word-break:normal!important;overflow-wrap:break-word}' +
    'html:not(.lang-ko) .review-stamp{white-space:normal;flex:0 1 auto;min-width:0;text-align:right;line-height:1.25}html:not(.lang-ko) .chip,html:not(.lang-ko) .hq-c{white-space:normal;max-width:100%;min-width:0;overflow-wrap:anywhere}' +
    '.i18n-kr{margin:0 0 8px;padding:8px 10px;border-radius:10px;background:var(--alert-tint);color:var(--alert);font-size:.875rem;font-weight:700;line-height:1.4}.i18n-note{display:flex;flex-wrap:wrap;gap:4px 10px;align-items:center;margin:24px 0 8px;padding-top:10px;border-top:1px solid var(--hairline);font-size:.8125rem;color:var(--muted)}.i18n-note button{color:var(--primary);font-weight:600;min-height:36px}';
  document.head.appendChild(st);

  function 받기() {
    if (L === 'ko') { DICT = {}; return Promise.resolve(); }
    var d = window.__I18N__ && window.__I18N__[L];   /* 아티팩트(파일 하나)는 사전을 안에 싣는다 */
    var p = d ? Promise.resolve(d) : fetch('data/i18n/' + L + '.json').then(function (r) { return r.ok ? r.json() : {}; }).catch(function () { return {}; });
    return p.then(function (j) {
      DICT = j || {}; ui = DICT.ui || {}; UH = DICT.uiH || {}; for (var h in UH) if (/\d/.test(h)) UHN[numKey(h)] = UH[h];
      /* 숫자만 다른 글 — 번역의 숫자도 틀(#)로 바꿔 둔다. 숫자 개수가 원문과 다르면(°F 병기 등) 틀로 쓰지 않는다(같은 글일 때만 씀) */
      for (var k in ui) if (/\d/.test(k)) { var a = k.match(/\d[\d,.]*/g) || [], b = String(ui[k]).match(/\d[\d,.]*/g) || []; if (a.length === b.length) uiN[numKey(k)] = numKey(String(ui[k])); }
    });
  }
  /* 본문 덮어쓰기 — 증상·처방약 길잡이의 안전 칸. 자료가 늦게 오므로 그릴 때마다 한 번씩 본다(이미 했으면 건너뜀) */
  function 본문() {
    if (!DICT || typeof D === 'undefined' || !D) return;   /* D·RXG 는 앱 스크립트의 전역 const — window 속성이 아니다 */
    var S = DICT.sym || {};
    (D.symptoms || []).forEach(function (s) {
      var t = S[s.id]; if (!t) return;   /* 본문(core.json)이 늦게 와 덮을 수 있어 그릴 때마다 다시 얹는다(값이 같으면 그대로) */
      if (t.name && s.name !== t.name) { REV[t.name] = s.name; s.name = t.name; } if (t.short) s.short = t.short;   /* REV — 약사에게 보일 한국어 칸(data-ko)에서 되돌리려고 */
      if (s.care) ['er', 'clinic', 'pharmacy'].forEach(function (k) { if (t[k] && s.care[k]) s.care[k] = s.care[k].map(function (x, i) { return t[k][i] || x; }); });
      if (s.triage && t.escalate) s.triage.escalate = t.escalate;
      if (t.find && !s._find) { s._find = 1; s.tags = (s.tags || []).concat(t.find); }   /* 안 보이는 찾는 말 — 검색에서만(화면엔 안 보임) */
    });
    /* 11-02 본문 — 많이 보는 증상부터 주마다(장부). 안전 칸과 따로 body 에 두고 칸마다 번호로 맞춘다. 빈 칸·모자란 칸은 한국어 그대로 */
    var B = DICT.body || {};
    /* 11-05 금기 거르기는 한국어 약 이름으로 문장을 찾는다 — 번역 글은 바꾸기 전 한국어를 KO 에 두고 그걸로 거른다(yKo·yBanP · app-shell banList·banProse·medTips) */
    var ko = function (n, o) { if (n !== o && o) KO.set(n, o); return n; };
    window.yKo = function (t) { return t && typeof t === 'object' ? t._ko : KO.get(t); };
    window.yBanP = function (t, b) { var k = KO.get(t); if (k == null) return null;
      var sp = function (x) { return String(x).replace(/([.!?](?:\*\*)?)\s+|([。！？](?:\*\*)?)\s*/g, function (m, a, c) { return (a || c) + '\u0001'; }).split('\u0001').filter(function (y) { return y.trim(); }); };
      var ks = sp(k), hs = ks.map(function (x) { return b.hit(x); }); if (!hs.some(Boolean)) return t;
      var ts = sp(t); return ts.length === ks.length ? ts.filter(function (x, i) { return !hs[i]; }).join(' ') : '';   /* 문장 수가 다르면 그 칸을 통째로 뺀다(안전 쪽) */ };
    (D.symptoms || []).forEach(function (s) {
      var b = B[s.id]; if (!b) return;
      ['lead', 'planTitle', 'planLabel'].forEach(function (k) { if (b[k] && s[k]) s[k] = ko(b[k], s[k]); });
      ['how', 'pharmacy', 'selfcare', 'avoid'].forEach(function (k) { if (b[k] && Array.isArray(s[k])) s[k] = s[k].map(function (x, i) { return b[k][i] ? ko(b[k][i], x) : x; }); });
      if (b.plan && Array.isArray(s.plan)) s.plan.forEach(function (o, i) { var x = b.plan[i]; if (x && !o._k) o._k = { slot: o.slot, title: o.title };   /* 11-05 칸 이름으로 맞추는 곳(withSlot·catName)은 한국어 _k 로 */ if (x) ['slot', 'title', 'why', 'either'].forEach(function (f) { if (x[f] && o[f] && o[f] !== x[f]) { if (f !== 'why') REV[x[f]] = o[f]; o[f] = ko(x[f], o[f]); } }); });
      if (b.notWorking && s.notWorking) { if (b.notWorking.title) s.notWorking.title = b.notWorking.title; if (b.notWorking.steps && s.notWorking.steps) s.notWorking.steps = s.notWorking.steps.map(function (x, i) { return b.notWorking.steps[i] ? ko(b.notWorking.steps[i], x) : x; }); }
      if (b.clinic && s.triage && s.triage.clinic) s.triage.clinic = ko(b.clinic, s.triage.clinic); if (b.pharm && s.triage && s.triage.pharmacy) s.triage.pharmacy = ko(b.pharm, s.triage.pharmacy);   /* 「약국에서는」 — banProse 가 KO 로 거름 */   /* 11-05 「병원에서는」 칸 */
      if (b.faq && Array.isArray(s.faq)) s.faq.forEach(function (o, i) { var x = b.faq[i]; if (x) { if (o._ko == null) o._ko = (o.q || '') + ' ' + (o.a || ''); if (x.q) o.q = x.q; if (x.a) o.a = x.a; } });
    });
    /* 11-05 약 설명(보이기만 하는 칸) — 용량·주의·금기·simple 은 아직 한국어(판정·약사 카드가 그 글을 읽는다). pAdj 는 yKo 로 한국어 원문에 규칙을 건다 */
    var DG = DICT.drug || {};
    (D.drugs || []).forEach(function (d) { var b = DG[d.id]; if (!b) return;
      ['tagline', 'lead', 'children', 'onset', 'duration'].forEach(function (k) { if (b[k] && d[k]) d[k] = ko(b[k], d[k]); });
      ['for', 'sideEffects', 'stop', 'tips'].forEach(function (k) { if (b[k] && Array.isArray(d[k])) d[k] = d[k].map(function (x, i) { return b[k][i] ? ko(b[k][i], x) : x; }); });
      if (b.faq && Array.isArray(d.faq)) d.faq.forEach(function (o, i) { var x = b.faq[i]; if (x) { if (o._ko == null) o._ko = (o.q || '') + ' ' + (o.a || ''); if (x.q) o.q = ko(x.q, o.q); if (x.a) o.a = ko(x.a, o.a); } });
    });
    var R = typeof RXG !== 'undefined' ? RXG : window.RXG, RX = DICT.rx || {};
    if (R && R.guides) {
      for (var g in RX) { var G = R.guides[g]; if (!G) continue; var x = RX[g];
        if (x.title) G.title = x.title; if (x.short) G.short = x.short; if (x.lead) G.lead = x.lead;
        ['er', 'do'].forEach(function (f) { if (x[f] && G[f]) G[f].forEach(function (o, i) { if (x[f][i]) o.t = x[f][i]; }); });
        if (x.miss && G.miss) G.miss.t = x.miss; }
    }
  }
  function 글(t) {
    var k = key(t); if (!k || !/[가-힣]/.test(k)) return null;
    if (ui[k] != null) return ui[k];
    if (/\d/.test(k)) { var nk = numKey(k), v = uiN[nk]; if (v != null) { var nums = k.match(/\d[\d,.]*/g) || [], i = 0; return v.replace(/#/g, function () { return nums[i++] || ''; }); } }
    return null;
  }
  /* 번호 — 한국 번호를 있는 나라 번호로. 마음 위기 번호가 그 나라 표에 없으면 응급 번호로 */
  function 번호(s) {
    if (CC === 'KR') return s;
    var E = N.e || 현지;
    return s.replace(/1577-0199/g, N.m[1] || N.m[0] || E).replace(/(^|[^\d-])109(?![\d-])/g, function (a, p) { return p + (N.m[0] || E); }).replace(/(^|[^\d-])119(?![\d-])/g, function (a, p, off, str) { return /한국에서는\s?$/.test(str.slice(Math.max(0, off - 7), off + p.length)) ? a : p + E; });   /* 11-17 「현지 응급 번호(한국에서는 119)」 안의 119 는 다시 바꾸지 않는다(다시 그릴 때마다 겹쳐 쌓이던 것) */
  }
  /* 11-12 홈 빨간 동그라미(56px) — 번호를 모르는 나라면 긴 「그 나라 응급 번호」 대신 짧은 말 */
  function 동그라미() { if (CC === 'KR' || N.e) return; document.querySelectorAll('.sos-dot').forEach(function (a) { a.textContent = { ko: '응급', en: 'SOS', es: 'SOS', ja: '緊急', zh: '急救' }[L] || 'SOS'; }); }
  /* 11-03 아래 탭은 칸이 좁아 긴 번역이 겹친다 — 탭에만 짧은 이름(화면 제목은 그대로) */
  var TABS = { en: { 'Medicine dictionary': 'Medicines', 'My information': 'My info' }, es: { 'Diccionario de medicamentos': 'Medicinas' } };
  function 탭() { var m = TABS[L], nav = document.querySelector('nav.tabbar'); if (!m || !nav || innerWidth >= 1024) return;
    var w = document.createTreeWalker(nav, NodeFilter.SHOW_TEXT, null), n; while ((n = w.nextNode())) { var k = n.nodeValue.trim(); if (m[k]) n.nodeValue = n.nodeValue.replace(k, m[k]); } }
  /* 11-04 약사에게 보여 줄 한국어 칸(data-ko) — 자료 단계에서 번역된 증상 이름·처방 칸 이름을 한국어로 되돌린다 */
  function 한국어칸(el) { if (!el || !el.querySelectorAll) return; var ks = Object.keys(REV).filter(function (k) { return k.length > 2; }).sort(function (a, b) { return b.length - a.length; });
    el.querySelectorAll('[data-ko]').forEach(function (c) { var w = document.createTreeWalker(c, NodeFilter.SHOW_TEXT, null), n;
      while ((n = w.nextNode())) { if (n.parentNode.closest && n.parentNode.closest('[data-noko]')) continue; var v = n.nodeValue, t = v.trim(); if (!t) continue;
        if (REV[t]) { n.nodeValue = v.replace(t, REV[t]); continue; }
        for (var i = 0; i < ks.length; i++) if (v.indexOf(ks[i]) >= 0) v = v.split(ks[i]).join(REV[ks[i]]);
        if (v !== n.nodeValue) n.nodeValue = v; } }); }
  /* 11-05 굵은 글씨가 낀 문단은 문단째(uiH: 「…**굵게**…」 → 번역) — 조각마다 옮기면 어순이 깨진다 */
  function 문단(el) { if (L === 'ko' || !el.querySelectorAll) return;
    el.querySelectorAll('p,li,span,small,div').forEach(function (e) { var c = e.childNodes, k = '', b = 0;
      if (c.length < 2 || (e.closest && e.closest('[data-ko]'))) return;
      for (var i = 0; i < c.length; i++) { var x = c[i]; if (x.nodeType === 3) k += x.nodeValue; else if (/^(B|STRONG)$/.test(x.nodeName) && !x.children.length) { k += '**' + x.textContent + '**'; b++; } else return; }
      k = key(k); if (!b || !/[가-힣]/.test(k)) return;
      var v = UH[k], nums = k.match(/\d[\d,.-]*/g) || [], j = 0; if (v == null && (v = UHN[numKey(k)]) != null) v = v.replace(/\d[\d,.-]*/g, function () { return nums[j++] || ''; });
      if (v != null) e.innerHTML = v.replace(/[&<>]/g, function (m) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;' }[m]; }).replace(/\*\*(.+?)\*\*/g, '<b>$1</b>'); }); }
  function 바꾸기(el) {
    if (!el) return;
    문단(el);
    var w = document.createTreeWalker(el, NodeFilter.SHOW_TEXT, null), n, todo = [];
    while ((n = w.nextNode())) todo.push(n);
    todo.forEach(function (n) {
      if (n.parentNode && (/^(SCRIPT|STYLE|TEXTAREA|NOSCRIPT|TEMPLATE)$/.test(n.parentNode.nodeName) || (n.parentNode.closest && n.parentNode.closest('script,style,textarea,noscript,template')))) return;   /* 11-18 Main(곁에 사고) — 붙은 script 안 글은 절대 바꾸지 않는다 */
      var 칸ko = n.parentNode && n.parentNode.closest ? n.parentNode.closest('[data-ko],[data-noko]') : null; if (칸ko && 칸ko.hasAttribute('data-ko')) return;   /* 11-04 약사에게 보여 줄 한국어 칸(한국에 사는 외국어 사용자) — 번역하지 않음 */
      var v = n.nodeValue, t = L !== 'ko' ? 글(v) : null;
      if (t != null) { var lead = v.match(/^\s*/)[0], tail = v.match(/\s*$/)[0]; if (/^[.,:;!?。，、．）)]/.test(t)) lead = ''; v = lead + t + tail; }   /* 굵은 글씨로 나뉜 문장 — 「labels .」 빈칸 없애기 */
      v = 번호(v); if (v !== n.nodeValue) n.nodeValue = v;
    });
    el.querySelectorAll('[placeholder],[aria-label],[title]').forEach(function (e) {
      ['placeholder', 'aria-label', 'title'].forEach(function (a) { var v = e.getAttribute(a); if (!v) return; var t = L !== 'ko' ? 글(v) : null; var nv = 번호(t != null ? t : v); if (nv !== v) e.setAttribute(a, nv); });
    });
    if (CC !== 'KR') el.querySelectorAll('a[href^="tel:"]').forEach(function (a) { var h = a.getAttribute('href'), nh = 'tel:' + 번호(h.slice(4));
      if (!N.e && /^tel:(119|109|1577-0199)$/.test(h)) { a.removeAttribute('href'); a.setAttribute('aria-disabled', 'true'); a.classList.add('tel-none'); return; }   /* 번호 모르는 나라 — 누르는 단추 없음 */
      if (nh !== h) a.setAttribute('href', nh); });
  }
  function 알림줄(view) {
    if (L === 'ko' || !view || view.querySelector('.i18n-note')) return;
    var d = document.createElement('div'); d.className = 'i18n-note';
    d.innerHTML = '<span>' + NOTE[L] + '</span><button type="button" onclick="try{localStorage.setItem(\'yakjido.lang.prev\',\'' + L + '\')}catch(e){};setLang(\'ko\')">' + ORIG[L] + '</button>';
    view.appendChild(d);   /* 11-03 Main — 첫 3초에 경고가 먼저 보이지 않게 화면 맨 아래 작은 한 줄로(첫 진입 경고 벽 금지) */
    /* 약 용량 칸 — 「한국 허가 기준 — 사는 나라 약사와 확인」 */
    view.querySelectorAll('.dose-card,.dose-hero,.sv-dose').forEach(function (c) { if (c.querySelector('.i18n-kr')) return; var p = document.createElement('p'); p.className = 'i18n-kr'; p.textContent = KRNOTE[L]; c.insertBefore(p, c.firstChild); });   /* 11-09 C3 — 용량 줄 위에 눈에 띄게 */
  }
  window.I18N = {
    lang: L, cc: CC, emg: N,
    tr: function (el) { if (DICT && el) 바꾸기(el); },   /* 11-03 늦게 채우는 칸(기내용 받아 두기 등) */
    t: function (s) { var r = L !== 'ko' ? 글(s) : null; return 번호(r != null ? r : s); },   /* 11-03 그린 뒤에 넣는 글(로그인 필수 안내 등) */
    apply: function (view) { if (!DICT) return; 본문(); 바꾸기(view); 바꾸기(document.querySelector('nav.tabbar')); 탭(); 한국어칸(view); 알림줄(view); 동그라미(); },
    ready: 받기().then(function () { 본문(); if (typeof route === 'function') route(); })
  };
})();
/* 11-12 사용자25 #21 — 영어 문장 검색 낱말 바꾸기(app-shell 의 enQ 가 부른다) */
var EN_Q = [[/blood\s*pressure|hypertension/g, '혈압약'], [/cold\s*(medicine|medication|remedy)|flu\s*medicine/g, '감기약'], [/pain\s*(killer|reliever|medicine)|analgesic/g, '진통제'], [/head\s*ache|migraine/g, '두통'], [/heart\s*burn|acid\s*reflux/g, '속쓰림'], [/indigestion|upset\s*stomach/g, '소화불량'], [/diarrh?o?ea/g, '설사'], [/constipation/g, '변비'], [/cough/g, '기침'], [/sore\s*throat/g, '목 아픔'], [/runny\s*nose|stuffy\s*nose|congestion/g, '코막힘'], [/fever/g, '열'], [/insomnia|can'?t\s*sleep|sleep/g, '잠이 안 올 때'], [/allerg\w*/g, '알레르기'], [/back\s*pain/g, '허리'], [/period\s*pain|cramps/g, '생리통'], [/hangover/g, '숙취'], [/diabetes|blood\s*sugar/g, '당뇨약'], [/\b(cold)\b/g, '감기'], [/\b(pills?|tablets?|medicines?|medication|drugs?|for|with|and|the|a|my)\b/g, ' ']];
window.enQS = q => /[가-힣]/.test(q) || !/[a-z]/i.test(q) ? q : EN_Q.reduce((s, [r, k]) => s.replace(r, ' ' + k + ' '), q.toLowerCase()).replace(/\s+/g, ' ').trim() || q;
