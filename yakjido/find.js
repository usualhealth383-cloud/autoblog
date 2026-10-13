/* 약지도 찾기 보조(find.js) — 따로 받는 파일(첫 화면 예산 밖). 앱은 검색을 처음 쓸 때 받는다.
   ① 메디나눔 공용 찾기 부품(yozm-health _도구/찾기_부품.js, 판 2026-10-14)을 «고치지 않고» 그대로 싣는다 — 부품이 바뀌면 이 덩어리를 통째로 갈아 끼운다.
   ② 맨 아래 「약지도 쪽」: 약지도 검색이 못 알아들은 말(초성 ㅌㅇㄹㄴ · 오타 타이레롤·두퉁)만 고쳐 «약지도 검색에 다시» 넘긴다.
      순위·아이 거르기·기능 바로가기는 약지도 검색이 그대로 맡는다(부품은 위기 판정을 하지 않는다). 2026-10-14 Z8 */
/* ▼▼ 찾기 부품 시작 ▼▼ */
/* ═══ 찾기 — 네 앱(우리 집 소아과 · 길동무 · ClinicScore · 곁에) 공용 부품 (2026-10-14) ═══════════════
   하는 일: 앱이 넘겨준 항목(계산기·가이드·글·도구·질문)에서 사람이 친 말을 찾아 「점수 순」으로 돌려준다.
     · 띄어쓰기·대소문자·전각/반각·기호를 가리지 않는다(「소아해열제」=「소아 해열제」, 「ＣＵＲＢ－６５」=「curb65」).
     · 조사·말끝을 뗀다(해열제를 · 투석환자의 · 열성경련이요 → 해열제 · 투석환자 · 열성경련).
     · 낱말이 여럿이면 「모두 맞는 항목」이 먼저, 그다음 일부만 맞는 항목(점수 순).
     · 같은 말 사전(앱이 넘김)으로 펼친다 — 친 말 그대로 > 같은 말 > 관련 말 순으로 점수를 깎는다.
     · 초성(ㅎㅇㅈ) · 짧은 오타(친 말이 아무 데도 없을 때만) · 영어 약어(CPR·AKI·HD·Na·K 는 「낱말 통째로」만 맞춘다).
     · 점수: 제목 > 별칭 > 태그 > 요약 > 본문. 본문은 몇 번 나와도 요약을 넘지 못한다. 같은 점수면 앱이 정한 우선.
     · 결과마다 「왜 떴는지」(맞은 낱말 · 어디서 · 맞은 태그)와 강조 위치(제목·요약 · 본문 조각).
     · 관련 태그(해시태그처럼 이어 찾기) · 빈 결과일 때 「혹시 ○○?」 제안과 「낱말 하나씩 뺀 결과」.
   지키는 것
     · 바깥 요청 0 · 저장 0 · 화면 0 — 화면은 앱이 그린다(이 부품은 글자도 화면에 내놓지 않는다).
     · ES5(옛 안드로이드 웹뷰) — let/const/화살표/Set/Map/includes 를 쓰지 않는다.
     · 색인은 한 번 만들어 다시 쓴다(본문은 낱말 색인 + 두 글자 조각 색인).
   쓰는 법
     var 색인 = 찾기.만들기({
       항목: [{ id:'g_hyperk', 제목:'고칼륨혈증 응급처치', 별칭:['hyperkalemia'], 태그:['고칼륨','투석'],
               요약:'…', 본문:'…'(글 또는 글 배열 · HTML 이면 찾기.글만() 으로 먼저), 종류:'guide',
               우선:3,      // 같은 점수일 때 앞에(자주 쓰는 것)
               무게:1 }, …],  // (고를 수 있음) 점수에 곱한다 — 소식·설정 같은 곁가지는 0.7 쯤
       사전: { 혈액투석:['HD','hemodialysis'], … },                    // 같은 말(양쪽으로) — 0.7
       관련: { 투석:['혈액투석','복막투석'], 해열제:['아세트아미노펜','이부프로펜'], … },   // 넓은/좁은 말·상표(양쪽으로) — 0.45
       군말: ['소아','아이'],                                          // 앱 전체가 그 주제라 가려 주지 못하는 말(기본 군말에 더해짐)
       한글자: '열피약잠…',                                            // 한 글자로도 뜻이 되는 말(기본에 더해짐)
       나눠서: true, 다됨: function (색인) { … }                         // (고를 수 있음) 본문 색인을 조금씩 — 화면이 멈추지 않게.
     });                                                                //   그동안 색인.준비됨=false 이고 찾기는 제목·태그·요약(+이미 넣은 본문)으로 돈다
     var 결과 = 색인.찾기('투석 칼슘', { 최대:30, 종류:['calc','guide'] });   // 또는 거르기:function(항목){ return … }
       → [{ id, 점수, 모두:true|false, 맞은:['투석','칼슘'], 태그:['투석','칼슘글루콘산'],
            왜:[{낱말:'투석', 곳:'태그', 말:'투석', 종류:'그대로'}, …],
            강조:{ 제목:[[0,2]], 요약:[[…]] }, 조각:{ 글:'…', 강조:[[a,b]] } | null, 항목:{원래 항목} }, …]
       결과.낱말 = [{ 말, 뿌리, 상태:'맞음'|'약함'|'없음'|'군말', 펼침:[…] }]
       결과.제안 = [{ 말:'해열제', 질의:'해열제 용량' }]   (빈 결과이거나 못 찾은 낱말이 있을 때)
       결과.빼고 = [{ 뺀:'칼슘', 질의:'투석', 수:5, 첫:['id', …] }]   (모두 맞는 항목이 없을 때)
     색인.관련태그(결과, { 최대:8 }) → [{ 태그:'칼슘', 수:4, 질의:'#칼슘' }]   (누르면 색인.찾기('#칼슘'))
     색인.제안('해렬제') → [{ 말:'해열제', 질의:'해열제' }]
     찾기.강조HTML(글, 범위, 'mark') → 글자안전 처리된 HTML(범위 자리만 <mark>)
   ═══════════════════════════════════════════════════════════════════════════════════════════════ */
(function (바탕) {
  'use strict';
  var 판 = '2026-10-14';

  /* ── 1. 글자 다듬기 — 길이를 그대로 둔다(1:1). 그래서 다듬은 글의 자리가 곧 원래 글의 자리다. ── */
  var 위첨자 = { '¹': '1', '²': '2', '³': '3', '⁰': '0' };
  var 악센트 = 'aaaaaaeceeeeiiiidnooooo/ouuuuyty';   /* U+00E0 ~ U+00FF */
  function 한글자다듬기(c) {
    var n = c.charCodeAt(0);
    if (n >= 0xff01 && n <= 0xff5e) { c = String.fromCharCode(n - 0xfee0).toLowerCase(); n = c.charCodeAt(0); if (/[0-9a-z]/.test(c)) return c; return ' '; }
    if (n >= 0x2080 && n <= 0x2089) return String(n - 0x2080);
    if (n >= 0x2074 && n <= 0x2079) return String(n - 0x2070);
    if (위첨자[c]) return 위첨자[c];
    if (n === 0xb5) return 'μ';
    if (n >= 0x391 && n <= 0x3a9) return String.fromCharCode(n + 0x20);
    if (n >= 0xe0 && n <= 0xff) { var a = 악센트.charAt(n - 0xe0); return a === '/' ? ' ' : a; }
    return ' ';
  }
  var 남길글자 = /[^ 0-9a-z가-힣ㄱ-ㆎα-ω]/g;
  function 다듬기(s) {
    s = String(s == null ? '' : s);
    var 작게 = s.replace(/İ/g, 'i').toLowerCase();
    if (작게.length !== s.length) {   /* 드문 글자 때문에 길이가 달라지면 한 글자씩 */
      var 판들 = [];
      for (var i = 0; i < s.length; i++) { var x = s.charAt(i).toLowerCase(); 판들.push(x.length === 1 ? x : ' '); }
      작게 = 판들.join('');
    }
    return 작게.replace(남길글자, 한글자다듬기);
  }
  function 압축(s) { return s.replace(/ +/g, ''); }
  function 글만(html) {
    return String(html == null ? '' : html).replace(/<(script|style)[^>]*>[\s\S]*?<\/\1>/gi, ' ').replace(/<[^>]*>/g, ' ')
      .replace(/&nbsp;/g, ' ').replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&quot;/g, '"').replace(/&#39;/g, "'").replace(/&amp;/g, '&')
      .replace(/\s+/g, ' ').replace(/^ | $/g, '');
  }
  function 글자안전(s) { return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#39;'); }

  /* ── 2. 한글 조각 ── */
  var 초성표 = 'ㄱㄲㄴㄷㄸㄹㅁㅂㅃㅅㅆㅇㅈㅉㅊㅋㅌㅍㅎ';
  var 중성표 = 'ㅏㅐㅑㅒㅓㅔㅕㅖㅗㅘㅙㅚㅛㅜㅝㅞㅟㅠㅡㅢㅣ';
  var 종성표 = ['', 'ㄱ', 'ㄲ', 'ㄳ', 'ㄴ', 'ㄵ', 'ㄶ', 'ㄷ', 'ㄹ', 'ㄺ', 'ㄻ', 'ㄼ', 'ㄽ', 'ㄾ', 'ㄿ', 'ㅀ', 'ㅁ', 'ㅂ', 'ㅄ', 'ㅅ', 'ㅆ', 'ㅇ', 'ㅈ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ'];
  function 한글인가(c) { var n = c.charCodeAt(0); return n >= 0xac00 && n <= 0xd7a3; }
  function 한글뿐(s) { return /^[가-힣]+$/.test(s); }
  function 초성(s) {
    var o = '';
    for (var i = 0; i < s.length; i++) {
      var n = s.charCodeAt(i) - 0xac00;
      o += (n >= 0 && n < 11172) ? 초성표.charAt(Math.floor(n / 588)) : s.charAt(i);
    }
    return o;
  }
  function 자모(s) {
    var o = '';
    for (var i = 0; i < s.length; i++) {
      var n = s.charCodeAt(i) - 0xac00;
      if (n >= 0 && n < 11172) o += 초성표.charAt(Math.floor(n / 588)) + 중성표.charAt(Math.floor((n % 588) / 28)) + 종성표[n % 28];
      else o += s.charAt(i);
    }
    return o;
  }
  /* 편집 거리 — 한도를 넘으면 바로 그만둔다 */
  function 거리(a, b, 한도) {
    var m = a.length, n = b.length;
    if (Math.abs(m - n) > 한도) return 한도 + 1;
    var 앞 = [], 지금, i, j;
    for (j = 0; j <= n; j++) 앞.push(j);
    for (i = 1; i <= m; i++) {
      지금 = [i]; var 작은 = i;
      for (j = 1; j <= n; j++) {
        var v = Math.min(앞[j] + 1, 지금[j - 1] + 1, 앞[j - 1] + (a.charAt(i - 1) === b.charAt(j - 1) ? 0 : 1));
        지금.push(v); if (v < 작은) 작은 = v;
      }
      if (작은 > 한도) return 한도 + 1;
      앞 = 지금;
    }
    return 앞[n];
  }

  /* ── 3. 조사·말끝 ── 뗀 판은 「또 하나의 후보」일 뿐 원래 말을 지우지 않는다.
     어미(헐어요·낮음·부었어요)를 떼어 한 글자만 남으면 「그 글자로 시작하는 낱말」을 찾는다(헐 → 헐고·헐어 · 낮 → 낮아졌을). */
  var 어미들 = ['었어요', '았어요', '했어요', '겠어요', '었는데', '았는데', '어요', '아요', '여요', '워요', '어서', '아서', '었다', '았다', '네요', '음'];
  /* 두 글자 이상 남을 때만 떼는 말끝(말하기·말하다·말하나 → 말하) — 한 글자만 남으면(사고·바다·일기) 떼지 않는다 */
  var 어미둘 = ['는지', '는다', '도록', '기', '다', '나', '고', '지', '게', '니', '면', '며'];
  var 말끝들 = ['에서는', '에서도', '에게서', '으로는', '으로도', '이라고', '이라는', '이에요', '인가요', '있나요', '없나요', '되나요', '하나요',
    '할까요', '일까요', '인데요', '는데요', '했어요', '했는데', '합니다', '습니다', '이래요', '래요', '대요',
    '에서', '에게', '한테', '께서', '까지', '부터', '처럼', '보다', '이랑', '하고', '이나', '이며', '이고', '이요', '이야', '에는', '에도',
    '으로', '로는', '라고', '라는', '예요', '에요', '해요', '어요', '아요', '나요', '까요', '네요', '는데', '인데', '해서', '하면', '하는', '되는',
    '과', '와', '은', '는', '이', '가', '을', '를', '의', '에', '도', '만', '로', '랑', '요', '죠'];
  var 조사한글자 = '가이은는을를에의도만과와로랑요';
  var 조사뒤 = (function () { var o = {}; ['', '이', '가', '은', '는', '을', '를', '에', '의', '도', '만', '과', '와', '로', '으로', '이랑', '랑', '이요', '요', '이나', '에서', '에게', '까지', '부터', '처럼', '보다', '이야', '이라', '이에요', '예요'].forEach(function (x) { o[x] = 1; }); return o; })();
  var 모든말끝 = 어미들.concat(말끝들, 어미둘).sort(function (a, b) { return b.length - a.length; });
  function 뿌리들(w, 어미표시) {   /* w: 다듬고 압축한 낱말 · 어미표시 가 있으면 [{말, 어미}] */
    var 나옴 = [], 지금 = w;
    for (var 번 = 0; 번 < 3; 번++) {
      if (!한글인가(지금.charAt(지금.length - 1))) break;
      var 바뀜 = false;
      for (var i = 0; i < 모든말끝.length; i++) {
        var e = 모든말끝[i];
        if (지금.length > e.length && 지금.slice(-e.length) === e) {
          if (어미둘.indexOf(e) >= 0 && 말끝들.indexOf(e) < 0 && 지금.length - e.length < 2) continue;
          지금 = 지금.slice(0, -e.length);
          나옴.push(어미표시 ? { 말: 지금, 어미: 어미들.indexOf(e) >= 0, 몇번: 번 } : 지금); 바뀜 = true; break;
        }
      }
      if (!바뀜) break;
    }
    return 나옴;
  }

  var 기본군말 = ('좀 더 또 왜 뭐 뭘 무엇 무슨 어떻게 어떡해 어떡하죠 어쩌죠 어떤 언제 어디 얼마 얼마나 몇 것 거 수 때 그 저 제 저희 우리 내 나 ' +
    '너무 자꾸 계속 많이 조금 자주 갑자기 요즘 지금 오늘 어제 아까 방금 혹시 정말 진짜 그냥 ' +
    '알려줘 알려주세요 알려 주세요 궁금 궁금해요 궁금합니다 해요 하나요 인가요 있나요 되나요 괜찮나요 괜찮아요 같아요 같은데 ' +
    '해야 해도 하면 돼요 되요 되나 방법 정보 관련 대해 대해서 관해 관해서 설명 안 못 있어요 없어요 했어요 합니다 인데 는데 ' +
    '어떻게해요 어떻게하나요 알고 싶어요 싶어요 싶습니다 부탁 문의 질문 경우 정도 때문 때문에 가요 와요 봐요 줘요 했는데 하는데 ' +
    '안돼 안돼요 안되요 안되 안됨 안되나요 못해 못해요 못하겠어요 안와 안와요 안나요 안나와요 안해요').split(' ');
  var 기본한글자 = '열피약잠똥토변땀배목눈귀코손발입숨침살뼈폐간위장술밥키몸젖혀털점암맘돈성이';

  /* ── 4. 색인 만들기 ── */
  var 갈 = '\u0001', 사이 = '\u0002';
  var 곳이름 = ['제목', '별칭', '태그', '요약', '본문'];
  var 기본무게 = { 제목: 10, 별칭: 8, 태그: 7, 요약: 4, 본문: 2, 본문최대: 3.5 };   /* 본문: 한 번 2 · 여덟 번 넘게 3.5 — 요약(4)을 넘지 못한다 */

  function 배열로(x) { if (x == null || x === '') return []; return Object.prototype.toString.call(x) === '[object Array]' ? x : [x]; }
  function 어느항목(자리, p) {   /* 자리[i] <= p 인 가장 큰 i */
    var lo = 0, hi = 자리.length - 1;
    while (lo < hi) { var mid = (lo + hi + 1) >> 1; if (자리[mid] <= p) lo = mid; else hi = mid - 1; }
    return lo;
  }
  function 짧은영문(v) { return /^[0-9a-zα-ω]{1,3}$/.test(v); }
  function 한음절(v) { return v.length === 1 && 한글인가(v); }
  function 경계민감(v) { return 짧은영문(v) || 한음절(v); }
  function 시작표(띄) {   /* 붙인 글의 자리마다 「낱말 첫 글자인가」(1/0) */
    var o = '', 앞빈칸 = true;
    for (var i = 0; i < 띄.length; i++) { var c = 띄.charAt(i); if (c === ' ') { 앞빈칸 = true; continue; } o += 앞빈칸 ? '1' : '0'; 앞빈칸 = false; }
    return o;
  }

  function 만들기(설정) {
    var 시작 = Date.now();
    설정 = 설정 || {};
    var 항목 = 배열로(설정.항목);
    var N = 항목.length;
    var 무게 = {}; for (var k in 기본무게) 무게[k] = 기본무게[k];
    if (설정.무게) for (var k2 in 설정.무게) 무게[k2] = 설정.무게[k2];
    var 군말 = Object.create(null);
    기본군말.concat(배열로(설정.군말)).forEach(function (w) { var x = 압축(다듬기(w)); if (x) 군말[x] = 1; });
    var 한글자 = 기본한글자 + (설정.한글자 || '');

    /* 4-1. 짧은 칸(제목·별칭·태그·요약) — 칸마다 글 하나로 이어 붙여 indexOf 로 훑는다 */
    var 칸 = [];   /* 칸[f] = { 띄움, 붙임, 띄움자리[], 붙임자리[] } */
    var 원칸 = [];   /* 원칸[i] = [제목, 별칭배열, 태그배열, 요약] (원래 글) */
    var 다듬칸 = [];
    var 우선 = [], 항목무게 = [];
    var 짧은말 = Object.create(null);   /* 낱말 → 몇 항목 (분해·오타 후보) */
    var 통째 = Object.create(null);     /* 붙여 쓴 칸 통째(curb65 같은) — 띄어 친 말 붙이기 */
    var 초성글 = [갈], 초성자리 = [];
    var f, i, j;
    for (f = 0; f < 4; f++) 칸.push({ 띄움: [갈], 붙임: [갈], 시작: ['0'], 띄움자리: [], 붙임자리: [], 띄움길이: 1, 붙임길이: 1 });
    var 초성길이 = 1;
    for (i = 0; i < N; i++) {
      var it = 항목[i] || {};
      var 원 = [String(it.제목 == null ? '' : it.제목), 배열로(it.별칭).map(String), 배열로(it.태그).map(String), String(it.요약 == null ? '' : it.요약)];
      원칸.push(원);
      우선.push(+it.우선 || 0);
      항목무게.push(it.무게 == null || isNaN(+it.무게) ? 1 : Math.max(0, +it.무게));
      var 다듬 = [];
      var 본낱말 = Object.create(null);
      var 초 = [];
      for (f = 0; f < 4; f++) {
        var 조각들 = (f === 1 || f === 2) ? 원[f] : [원[f]];
        var 띄 = 조각들.map(다듬기);
        다듬.push(띄);
        var 붙 = 띄.map(압축);
        var c = 칸[f];
        c.띄움자리.push(c.띄움길이); c.붙임자리.push(c.붙임길이);
        var s1 = 띄.join(사이) + 갈, s2 = 붙.join(사이) + 갈;
        c.띄움.push(s1); c.붙임.push(s2); c.띄움길이 += s1.length; c.붙임길이 += s2.length;
        c.시작.push(띄.map(시작표).join('0') + '0');
        if (f < 3) {
          for (j = 0; j < 띄.length; j++) {
            if (붙[j] && 붙[j].length <= 24) 통째[붙[j]] = 1;
            var 낱 = 띄[j].match(/[가-힣ㄱ-ㆎ]+|[0-9a-zα-ω]+/g) || [];
            for (var q = 0; q < 낱.length; q++) {
              var w = 낱[q]; 본낱말[w] = 1;
              var 뿌 = 뿌리들(w); for (var r = 0; r < 뿌.length; r++) if (뿌[r].length >= 2) 본낱말[뿌[r]] = 1;
            }
            초.push(압축(초성(띄[j])));
          }
        }
      }
      for (var w2 in 본낱말) 짧은말[w2] = (짧은말[w2] || 0) + 1;
      다듬칸.push(다듬);
      초성자리.push(초성길이);
      var s3 = 초.join(사이) + 갈; 초성글.push(s3); 초성길이 += s3.length;
    }
    for (f = 0; f < 4; f++) { 칸[f].띄움 = 칸[f].띄움.join(''); 칸[f].붙임 = 칸[f].붙임.join(''); 칸[f].시작 = 칸[f].시작.join(''); }
    초성글 = 초성글.join('');

    /* 4-2. 본문 — 낱말 색인(낱말 → [항목, 횟수, …]) + 두 글자 조각 색인(조각 → [낱말 번호]) + 첫 글자 색인
       설정.나눠서 가 참이면 본문은 조금씩(setTimeout) 넣는다 — 그동안 찾기는 제목·태그·요약과 이미 넣은 본문으로 돈다. */
    var 낱말번호 = Object.create(null), 낱말 = [], 자리 = [];
    var 조각 = Object.create(null), 첫글자 = Object.create(null);
    var 본문원 = [];
    var 본문길이 = 0;
    var 낱말틀 = /[가-힣ㄱ-ㆎ]+|[0-9a-zα-ω]+/g;
    for (i = 0; i < N; i++) { var 본0 = 배열로((항목[i] || {}).본문).join(' '); 본문원.push(본0); 본문길이 += 본0.length; }
    function 새낱말(ww, i) {
      var id = 낱말.length; 낱말번호[ww] = id; 낱말.push(ww); 자리.push([i, 1]);
      var 첫 = ww.charAt(0); if (한글인가(첫)) (첫글자[첫] = 첫글자[첫] || []).push(id);
      for (var j = 0; j + 1 < ww.length; j++) {
        var 열쇠 = ww.substr(j, 2), L = 조각[열쇠];
        if (!L) { 조각[열쇠] = [id]; continue; }
        if (L[L.length - 1] !== id) L.push(id);
      }
    }
    function 본문넣기(i) {
      var 본 = 본문원[i]; if (!본) return;
      var 낱들 = 다듬기(본).match(낱말틀) || [];
      for (var j = 0; j < 낱들.length; j++) {
        var ww = 낱들[j], id = 낱말번호[ww], p;
        if (id === undefined) { 새낱말(ww, i); continue; }
        p = 자리[id];
        if (p[p.length - 2] === i) p[p.length - 1]++; else p.push(i, 1);
      }
    }
    var 본문다음 = 0;
    function 본문조금(몇) { var 끝 = Math.min(N, 본문다음 + 몇); for (; 본문다음 < 끝; 본문다음++) 본문넣기(본문다음); return 본문다음 >= N; }

    /* 4-3. 사전 — 낱말(붙임) → 묶음 번호들 */
    var 묶음 = [];   /* {말:[붙임…], 원:[…], 무게} */
    var 말묶음 = Object.create(null);
    function 사전넣기(표, 무게값) {
      if (!표) return;
      for (var 대표 in 표) {
        var 원들 = [대표].concat(배열로(표[대표]));
        var 붙들 = [], 원남김 = [], 본 = {};
        원들.forEach(function (x) { var d = 다듬기(x).replace(/^ +| +$/g, '').replace(/ +/g, ' '); var b = 압축(d); if (b && !본[b]) { 본[b] = 1; 붙들.push(d); 원남김.push(String(x)); } });
        var 번 = 묶음.length;
        묶음.push({ 말: 붙들, 원: 원남김, 무게: 무게값 });
        붙들.forEach(function (d) { var b = 압축(d); (말묶음[b] = 말묶음[b] || []).push(번); 짧은말[b] = 짧은말[b] || 0; if (d.indexOf(' ') >= 0) 통째[b] = 1; });
      }
    }
    사전넣기(설정.사전, 0.7);   /* 같은 말 — 친 말 그대로(1.0)가 다른 칸에서 맞아도 이기도록 0.7 */
    사전넣기(설정.관련, 0.45);
    var 사전한글 = Object.keys(말묶음).filter(function (b) { return 한글뿐(b) && b.length >= 2; });

    var 짧은말목록 = Object.keys(짧은말);
    var 첫소리묶음 = Object.create(null);   /* 오타 후보는 첫소리가 같은 말만 본다 */
    짧은말목록.forEach(function (t) { var k = 초성(t.charAt(0)); (첫소리묶음[k] = 첫소리묶음[k] || []).push(t); });
    var 색인 = {
      판: 판, 항목수: N, 낱말수: 0, 본문글자: 본문길이,
      만든시간: 0, 준비됨: false
    };
    /* 같은 말을 거듭 칠 때(한 글자씩 치는 동안) 다시 훑지 않게 — 판마다 맞춘 결과를 잠깐 둔다(본문 색인이 다 된 뒤에만) */
    var 판캐시 = Object.create(null), 판캐시수 = 0;

    /* ── 5. 낱말 하나를 칸마다 맞춰 본다 ── */
    /* 짧은 칸: 돌려주는 것 = { 항목번호: 자리값(1.1 통째 · 1.0 낱말 앞 · 0.85 안쪽) } (칸마다) */
    function 칸맞춤(v, f, 결과, 앞만) {
      var c = 칸[f], 경계 = 경계민감(v), 붙v = 압축(v);
      var p, it, 값;
      if (앞만) {   /* 낱말 앞에서만(뒤는 무엇이든) */
        p = c.띄움.indexOf(v);
        while (p >= 0) {
          if (!한글인가(c.띄움.charAt(p - 1) || ' ')) { it = 어느항목(c.띄움자리, p); if (!(결과[it] >= 1.0)) 결과[it] = 1.0; }
          p = c.띄움.indexOf(v, p + 1);
        }
        return;
      }
      if (!경계) {   /* 띄어쓰기를 뺀 글에서 한 번에 — 칸 통째 1.1 · 낱말 앞 1.0 · 안쪽 0.85 */
        p = c.붙임.indexOf(붙v);
        while (p >= 0) {
          it = 어느항목(c.붙임자리, p);
          var 앞 = c.붙임.charAt(p - 1), 뒤 = c.붙임.charAt(p + 붙v.length);
          값 = ((앞 === 갈 || 앞 === 사이) && (뒤 === 갈 || 뒤 === 사이)) ? 1.1 : c.시작.charAt(p) === '1' ? 1.0 : 0.85;
          if (!(결과[it] >= 값)) 결과[it] = 값;
          p = c.붙임.indexOf(붙v, p + 1);
        }
        return;
      }
      /* 경계가 중요한 말: 짧은 영어 약어(K·Na·HD·CPR) · 한 글자 한글(열·잠) */
      p = c.띄움.indexOf(v);
      while (p >= 0) {
        if (경계맞나(c.띄움, p, v)) {
          it = 어느항목(c.띄움자리, p);
          var 앞3 = c.띄움.charAt(p - 1), e = p + v.length, 뒤3 = c.띄움.charAt(e);
          값 = ((앞3 === 갈 || 앞3 === 사이) && (뒤3 === 갈 || 뒤3 === 사이)) ? 1.1 : 1.0;
          if (!(결과[it] >= 값)) 결과[it] = 값;
        }
        p = c.띄움.indexOf(v, p + 1);
      }
    }
    function 경계맞나(s, p, v) {
      var 앞 = s.charAt(p - 1), e = p + v.length, 뒤 = s.charAt(e);
      if (한음절(v)) {
        if (앞 && 한글인가(앞)) return false;
        if (!뒤 || !한글인가(뒤)) return true;
        var k = e; while (k < s.length && 한글인가(s.charAt(k))) k++;
        return !!조사뒤[s.slice(e, k)];
      }
      return !(/[0-9a-zα-ω]/.test(앞)) && !(/[0-9a-zα-ω]/.test(뒤));
    }
    /* 본문: 돌려주는 것 = { 항목번호: 횟수 } */
    function 본문맞춤(v, 앞만) {
      var 횟수 = {};
      if (앞만) { (첫글자[v] || []).forEach(function (wid) { 더하기(횟수, wid); }); return 횟수; }
      var 부분 = v.match(/[가-힣ㄱ-ㆎ]+|[0-9a-zα-ω]+/g) || [];
      if (!부분.length) return 횟수;
      if (부분.length > 1) {   /* 여러 낱말 말(fever reducer · 저Na) — 모두 든 항목만, 횟수는 가장 적은 것 */
        var 모음 = 부분.map(본문한낱말);
        for (var key in 모음[0]) {
          var 최소 = 모음[0][key];
          for (var z = 1; z < 모음.length; z++) { if (!모음[z][key]) { 최소 = 0; break; } if (모음[z][key] < 최소) 최소 = 모음[z][key]; }
          if (최소) 횟수[key] = 최소;
        }
        return 횟수;
      }
      return 본문한낱말(부분[0]);
    }
    function 더하기(횟수, wid) { var p = 자리[wid]; for (var t = 0; t < p.length; t += 2) 횟수[p[t]] = (횟수[p[t]] || 0) + p[t + 1]; }
    function 본문한낱말(v) {
      var 횟수 = {}, id;
      if (짧은영문(v)) { id = 낱말번호[v]; if (id !== undefined) 더하기(횟수, id); return 횟수; }
      if (한음절(v)) {
        for (var 뒤 in 조사뒤) { id = 낱말번호[v + 뒤]; if (id !== undefined) 더하기(횟수, id); }
        return 횟수;
      }
      var 고른 = null;
      for (var t = 0; t + 1 < v.length; t++) {
        var L = 조각[v.substr(t, 2)];
        if (!L) return 횟수;
        if (!고른 || L.length < 고른.length) 고른 = L;
      }
      if (!고른) return 횟수;
      for (var u = 0; u < 고른.length; u++) if (낱말[고른[u]].indexOf(v) >= 0) 더하기(횟수, 고른[u]);
      return 횟수;
    }
    function 초성맞춤(v) {
      var 결과 = {}, p = 초성글.indexOf(v);
      while (p >= 0) { var it = 어느항목(초성자리, p); 결과[it] = 1; p = 초성글.indexOf(v, p + 1); }
      return 결과;
    }

    /* ── 6. 친 말 풀기 ── */
    function 펼치기(w, 깊이) {   /* w: 압축한 낱말 → [{말(띄움 가능), 무게, 종류}] */
      var 판들 = [], 본 = Object.create(null);
      function 넣기(말, 무게값, 종류) {
        var b = 압축(말); if (!b) return;
        if (b.length === 1 && 한글인가(b) && 한글자.indexOf(b) < 0 && 종류 !== '그대로' && 종류 !== '말뿌리') return;
        if (본[b] !== undefined) { if (판들[본[b]].무게 < 무게값) { 판들[본[b]].무게 = 무게값; 판들[본[b]].종류 = 종류; } return; }
        본[b] = 판들.length; 판들.push({ 말: 말, 무게: 무게값, 종류: 종류 });
      }
      넣기(w, 1, '그대로');
      var 뿌정보 = 뿌리들(w, true), 뿌 = 뿌정보.map(function (x) { return x.말; });
      뿌정보.forEach(function (x) {
        var r = x.말;
        if (r.length >= 2 || (한글자.indexOf(r) >= 0 && x.몇번 === 0)) 넣기(r, 0.95, '그대로');   /* 한 글자는 한 번 뗀 것만(위로의 → 위로 ✓ → 위 ✗) */
        else if (x.어미 && x.몇번 === 0 && 한글뿐(r) && w.length <= 4) { 넣기(r, 0.6, '말뿌리'); if (판들[본[r]] && 판들[본[r]].종류 === '말뿌리') 판들[본[r]].앞 = true; }
      });
      var 바탕들 = [w].concat(뿌);
      var 사전맞음 = false;
      바탕들.forEach(function (b) {
        (말묶음[b] || []).forEach(function (번) {
          사전맞음 = true;
          var g = 묶음[번];
          g.말.forEach(function (x) { 넣기(x, g.무게, g.무게 >= 0.7 ? '같은 말' : '관련 말'); });
        });
      });
      if (!사전맞음 && 한글뿐(w) && w.length >= 3) {   /* 「투석환자」 안의 「투석」처럼 사전 말이 들어 있으면 */
        사전한글.forEach(function (t) {
          if (t.length < w.length && w.indexOf(t) >= 0) {
            넣기(t, 0.5, '같은 말');   /* 든 말은 친 말보다 한참 아래(발표불안 ⊃ 불안 이 「발표불안」 태그를 이기지 않게) */
            (말묶음[t] || []).forEach(function (번) { var g = 묶음[번]; g.말.forEach(function (x) { 넣기(x, g.무게 * 0.5, '같은 말'); }); });
          }
        });
      }
      return 판들;
    }
    /* 붙여 친 말 나누기 — 「소아해열제」 → 소아 + 해열제 */
    function 나누기(w) {
      if (!한글뿐(w) || w.length < 4) return null;
      var n = w.length, 최선 = [];
      최선[0] = [];
      for (var e = 1; e <= n; e++) {
        for (var s = Math.max(0, e - 8); s < e; s++) {
          if (!최선[s]) continue;
          var 조 = w.slice(s, e), 좋음 = false;
          if (조.length >= 2 && (짧은말[조] !== undefined || 낱말번호[조] !== undefined && 자리[낱말번호[조]].length >= 6)) 좋음 = true;
          else if (조.length === 1 && s > 0 && 조사한글자.indexOf(조) >= 0) 좋음 = true;   /* 사이에 낀 조사 */
          if (!좋음) continue;
          var 후보 = 최선[s].concat(조.length === 1 ? [] : [조]);
          if (!최선[e] || 후보.length < 최선[e].length) 최선[e] = 후보;
        }
      }
      var 끝 = 최선[n];
      return (끝 && 끝.length >= 2) ? 끝 : null;
    }
    function 풀기(q) {
      var 원문 = String(q == null ? '' : q);
      var 조각들 = 다듬기(원문.replace(/#/g, ' #')).split(/ +/).filter(Boolean);
      var 태그만 = /(^|\s)#\S/.test(원문);
      /* 띄어 친 말이 사전·칸에 붙은 말로 있으면 붙인다(「열 경련」→ 열경련 · 「curb 65」→ curb65) */
      var 낱 = [], 원조각 = [];
      for (var a = 0; a < 조각들.length; a++) {
        var 붙임 = null, 몇 = 0;
        for (var k = Math.min(3, 조각들.length - a); k >= 2; k--) {
          var 이음 = 조각들.slice(a, a + k).join('');
          if (말묶음[이음] || 통째[이음]) { 붙임 = 이음; 몇 = k; break; }
        }
        if (붙임) { 낱.push(붙임); 원조각.push(조각들.slice(a, a + 몇)); a += 몇 - 1; } else { 낱.push(조각들[a]); 원조각.push(null); }
      }
      var 낱말들 = [];
      낱.forEach(function (w, 순) {
        var b = 압축(w); if (!b) return;
        var 뿌 = 뿌리들(b);
        var 군 = !!군말[b] || 뿌.some(function (r) { return !!군말[r]; });
        var 판들 = 펼치기(b);
        var 군말아님 = function (x) { return !군말[x] && !뿌리들(x).some(function (r) { return !!군말[r]; }); };
        var 나눔 = 원조각[순] ? 원조각[순] : (말묶음[b] || 통째[b] || 짧은말[b] !== undefined) ? null : 나누기(뿌.length ? 뿌[뿌.length - 1] : b) || 나누기(b);
        if (나눔) {   /* 나눈 조각 가운데 군말(소아 앱의 「소아」)은 뺀다 — 「소아해열제」 = 「소아 해열제」 */
          var 남은조각 = 나눔.filter(군말아님);
          나눔 = (남은조각.length >= 2 || (남은조각.length === 1 && 남은조각.length < 나눔.length)) ? 남은조각 : null;
        }
        낱말들.push({ 말: b, 뿌리: 뿌.length ? 뿌[뿌.length - 1] : b, 군말: 군, 판들: 판들,
          나눔무게: 원조각[순] ? 0.6 : 0.95,   /* 띄어 친 것을 사전대로 붙였으면 붙인 뜻이 먼저(열 경련 → 열성경련), 붙여 친 것을 나눴으면 나눈 뜻이 먼저 */
          나눔: 나눔 ? 나눔.map(function (x) { return { 말: x, 판들: 펼치기(x) }; }) : null,
          초성: /^[ㄱ-ㅎ]{2,}$/.test(b) });
      });
      /* 모두 군말이면 군말도 쓴다 */
      if (낱말들.length && 낱말들.every(function (x) { return x.군말; })) 낱말들.forEach(function (x) { x.군말 = false; });
      return { 낱말: 낱말들, 태그만: 태그만, 붙임: 압축(조각들.join('')) };
    }

    /* ── 7. 점수 ── */
    function 판맞춤(판) {
      var 열쇠 = (판.앞 ? '^' : '') + 판.말, 있음 = 판캐시[열쇠];
      if (있음) return 있음;
      var 칸들 = [];
      for (var f = 0; f < 4; f++) { var m = {}; 칸맞춤(판.말, f, m, 판.앞); 칸들.push(m); }
      var r = { 칸: 칸들, 본: 본문맞춤(판.말, 판.앞) };
      if (색인.준비됨) { if (판캐시수 > 600) { 판캐시 = Object.create(null); 판캐시수 = 0; } 판캐시[열쇠] = r; 판캐시수++; }
      return r;
    }
    function 판점수(판, 결과, 곳들, 태그만) {   /* 결과[it] = {점, 곳, 판} 가장 좋은 것 · 곳들[it] = 칸 표시 */
      var f, it, 값, 맞음 = 판맞춤(판);
      for (f = 0; f < 4; f++) {
        var m = 맞음.칸[f];
        var W = 무게[곳이름[f]];
        if (태그만) W = f === 2 ? 12 : W * 0.6;
        for (it in m) {
          값 = W * 판.무게 * m[it];
          if (f === 0 && m[it] > 1) 값 *= 1.15;
          기록(결과, 곳들, +it, 값, f, 판);
        }
      }
      var 횟 = 맞음.본;
      for (it in 횟) {
        var n = 횟[it];
        값 = Math.min(무게.본문최대, 무게.본문 + 0.5 * Math.log(n) / Math.LN2) * 판.무게;
        if (태그만) 값 *= 0.6;
        기록(결과, 곳들, +it, 값, 4, 판);
      }
    }
    function 기록(결과, 곳들, it, 값, f, 판) {
      곳들[it] = (곳들[it] || 0) | (1 << f);
      var 지금 = 결과[it];
      if (!지금 || 지금.점 < 값) 결과[it] = { 점: 값, 곳: f, 판: 판 };
    }
    function 낱말점수(x, 태그만) {   /* 한 낱말 → { it: {점, 곳, 판, 나눔} } */
      var 결과 = {}, 곳들 = {};
      if (x.초성) {
        var m = 초성맞춤(x.말);
        for (var it0 in m) 기록(결과, 곳들, +it0, 무게.제목 * 0.7, 0, { 말: x.말, 무게: 0.7, 종류: '초성' });
      }
      x.판들.forEach(function (판) { 판점수(판, 결과, 곳들, 태그만); });
      for (var it in 결과) { var 몇곳 = 0, b = 곳들[it]; while (b) { 몇곳 += b & 1; b >>= 1; } 결과[it].점 += 0.1 * Math.min(3, 몇곳 - 1); }
      if (x.나눔) {   /* 나눈 조각이 모두 든 항목: 조각 평균 × 0.95 */
        var 조각결과 = x.나눔.map(function (y) { var r = {}, g = {}; y.판들.forEach(function (판) { 판점수(판, r, g, 태그만); }); return r; });
        for (var it2 in 조각결과[0]) {
          var 합 = 0, 다 = true;
          for (var z = 0; z < 조각결과.length; z++) { var e = 조각결과[z][it2]; if (!e) { 다 = false; break; } 합 += e.점; }
          if (!다) continue;
          var 나무 = x.나눔무게 || 0.95, 점 = 나무 * 합 / 조각결과.length;
          if (!결과[it2] || 결과[it2].점 < 점) 결과[it2] = { 점: 점, 곳: 조각결과[0][it2].곳, 판: { 말: x.나눔.map(function (y) { return y.말; }).join(' '), 무게: 나무, 종류: '나눔' }, 나눔: 조각결과.map(function (r) { return r[it2]; }) };
        }
      }
      return 결과;
    }
    var 자모캐시 = Object.create(null);
    function 자모로(t) { var x = 자모캐시[t]; if (x === undefined) { x = 자모(t); 자모캐시[t] = x; } return x; }
    function 오타판들(w) {   /* 친 말이 아무 데도 없을 때만 */
      var 나옴 = [];
      if (w.length < 2) return 나옴;
      var 한 = 한글뿐(w), 자w = 한 ? 자모(w) : null;
      var 후보 = 첫소리묶음[초성(w.charAt(0))] || [];   /* 첫소리까지 틀리는 일은 드물다 — 「헐어요」가 「없어요」로 가지 않게 */
      for (var i = 0; i < 후보.length; i++) {
        var t = 후보[i];
        if (t === w || Math.abs(t.length - w.length) > 1) continue;
        var d = 9;
        if (w.length >= 3) d = 거리(w, t, 1);
        if (d > 1 && 한 && 자w.length >= 5 && 한글뿐(t)) d = 거리(자w, 자모로(t), 1) <= 1 ? 1 : 9;
        if (d <= 1) 나옴.push({ 말: t, 수: 짧은말[t] || 0 });
      }
      나옴.sort(function (a, b) { return b.수 - a.수; });
      return 나옴.slice(0, 4);
    }

    /* 친 말을 풀고 낱말마다 항목 점수를 매긴다(한 번만) */
    function 분석(q, 옵션) {
      var 풀이 = 풀기(q);
      var 낱들 = 풀이.낱말;
      var 들어감 = 들어가나함수(옵션 || {});
      var 풀 = 0; for (var i0 = 0; i0 < N; i0++) if (들어감(i0)) 풀++;
      var 점들 = 낱들.map(function (x) { return 낱말점수(x, 풀이.태그만); });
      /* 아무 데도 없는 낱말은 오타 후보로 한 번 더 */
      낱들.forEach(function (x, k) {
        if (x.군말 || x.초성) return;
        var 있음 = false; for (var it in 점들[k]) if (들어감(+it)) { 있음 = true; break; }
        if (있음) return;
        var 오 = 오타판들(x.뿌리);
        if (!오.length && x.뿌리 !== x.말) 오 = 오타판들(x.말);
        if (!오.length) return;
        x.오타 = 오.map(function (o) { return o.말; });
        var y = { 말: x.말, 판들: [], 나눔: null };
        오.forEach(function (o) { 펼치기(o.말).forEach(function (p) { y.판들.push({ 말: p.말, 무게: p.무게 * 0.6, 종류: '비슷한 말', 앞: p.앞 }); }); });
        점들[k] = 낱말점수(y, 풀이.태그만);
      });
      var 수들 = 점들.map(function (r) { var df = 0; for (var it in r) if (들어감(+it)) df++; return df; });
      return { 풀이: 풀이, 낱들: 낱들, 들어감: 들어감, 풀: 풀, 점들: 점들, 수들: 수들 };
    }
    /* 점수를 모아 줄 세운다 — 뺄 낱말(뺌)이 있으면 그 낱말 없이 */
    function 순위(A, 뺌) {
      var 낱들 = A.낱들, 풀 = A.풀;
      var 상태 = 낱들.map(function (x, k) {
        if (k === 뺌) return '뺌';
        if (x.군말) return '군말';
        if (!A.수들[k]) return '없음';
        return (풀 >= 12 && A.수들[k] / 풀 > 0.35) ? '약함' : '맞음';
      });
      var 강한수 = 상태.filter(function (s) { return s === '맞음'; }).length;
      var 쓸 = 상태.map(function (s) { return s === '맞음' || (강한수 === 0 && s === '약함'); });
      if (강한수 === 0 && !쓸.some(Boolean)) 쓸 = 상태.map(function (s) { return s === '군말'; });
      var 기준수 = 쓸.filter(Boolean).length;
      var 무게들 = A.수들.map(function (df) {
        return Math.log(1 + (풀 - df + 0.5) / (df + 0.5));   /* 드문 낱말일수록 무겁게(BM25 꼴) — 「에피네프린 용량」에서 에피네프린이 용량을 이기게 */
      });
      var 모음 = {};
      낱들.forEach(function (x, k) {
        if (k === 뺌) return;
        if (상태[k] === '군말' && !쓸[k]) return;   /* 앱 전체가 그 주제인 말(소아 앱의 「소아」)은 점수에 넣지 않는다 */
        for (var it in A.점들[k]) {
          var n = +it; if (!A.들어감(n)) continue;
          var e = A.점들[k][it];
          var m = 모음[n] || (모음[n] = { 점: 0, 덮음: 0, 왜: [] });
          if (쓸[k]) { m.점 += e.점 * 무게들[k]; m.덮음++; }
          else m.점 += e.점 * 0.3;
          m.왜.push({ k: k, e: e });
        }
      });
      /* 띄어 친 말을 붙인 것이 제목·별칭·태그·요약에 통째로 있으면 덤(「컹컹 기침」) */
      if (뺌 < 0 && 낱들.length >= 2 && A.풀이.붙임.length >= 3) {
        [0, 1, 2, 3].forEach(function (f) {
          var m = {}; 칸맞춤(A.풀이.붙임, f, m);
          for (var it in m) if (모음[it]) 모음[it].점 += [6, 4, 4, 3][f];
        });
      }
      for (var it0 in 모음) if (항목무게[it0] !== 1) 모음[it0].점 *= 항목무게[it0];   /* 앱이 정한 항목 무게(소식·설정 같은 곁가지는 낮게) */
      var 목록 = [];
      for (var it in 모음) {
        var m = 모음[it];
        if (기준수 > 0 && m.덮음 === 0) continue;   /* 흔한 말·군말만 맞은 것은 뺀다 */
        목록.push({ i: +it, 점: Math.round(m.점 * 100) / 100, 덮음: m.덮음, 왜: m.왜 });
      }
      목록.sort(function (a, b) { return b.덮음 - a.덮음 || b.점 - a.점 || 우선[b.i] - 우선[a.i] || a.i - b.i; });
      return { 목록: 목록, 상태: 상태, 기준수: 기준수 };
    }
    function 찾기(q, 옵션) {
      옵션 = 옵션 || {};
      var 최대 = 옵션.최대 || 30;
      var 끝 = []; 끝.낱말 = []; 끝.제안 = []; 끝.빼고 = [];
      var A = 분석(q, 옵션);
      if (!A.낱들.length) return 끝;
      var R = 순위(A, -1), 낱들 = A.낱들;
      끝.낱말 = 낱들.map(function (x, k) {
        return { 말: x.말, 뿌리: x.뿌리, 상태: R.상태[k], 오타: x.오타 || null,
          펼침: x.판들.filter(function (p) { return p.종류 !== '그대로'; }).map(function (p) { return p.말; }),
          나눔: x.나눔 ? x.나눔.map(function (y) { return y.말; }) : null };
      });
      var 모두수 = 0;
      for (var r = 0; r < R.목록.length && 끝.length < 최대; r++) {
        var e2 = R.목록[r];
        var 모두 = e2.덮음 === R.기준수;
        if (모두) 모두수++;
        끝.push(결과만들기(e2, 낱들, 모두, 옵션));
      }
      if (!끝.length || 낱들.some(function (x, k) { return x.오타 || R.상태[k] === '없음'; })) 끝.제안 = 제안모으기(A, R);
      if (R.기준수 >= 2 && 모두수 === 0 && 옵션.빼고 !== false) 끝.빼고 = 빼고모으기(A, R);
      return 끝;
    }
    function 들어가나함수(옵션) {
      var 종류 = 옵션.종류 ? 배열로(옵션.종류) : null;
      var 거르기 = typeof 옵션.거르기 === 'function' ? 옵션.거르기 : null;
      if (!종류 && !거르기) return function () { return true; };
      var 표 = {}; if (종류) 종류.forEach(function (x) { 표[x] = 1; });
      var 메모 = {};
      return function (i) {
        if (메모[i] !== undefined) return 메모[i];
        var it = 항목[i] || {}, ok = true;
        if (종류 && !표[it.종류]) ok = false;
        if (ok && 거르기) { try { ok = !!거르기(it); } catch (e) { ok = false; } }
        메모[i] = ok; return ok;
      };
    }
    function 결과만들기(e, 낱들, 모두, 옵션) {
      var it = 항목[e.i] || {};
      var 원 = 원칸[e.i], 다듬 = 다듬칸[e.i];
      var 맞은 = [], 왜 = [], 판말 = [], 본문만 = true;
      e.왜.forEach(function (w) {
        var x = 낱들[w.k];
        if (맞은.indexOf(x.말) < 0) 맞은.push(x.말);
        var 판 = w.e.판;
        왜.push({ 낱말: x.말, 곳: 곳이름[w.e.곳], 말: 판.말, 종류: 판.종류 });
        if (w.e.곳 !== 4) 본문만 = false;
        var 판글 = function (p) { return (p.앞 ? '^' : '') + 압축(p.말); };   /* ^ = 낱말 앞에서만(헐 → 헐고) */
        if (w.e.나눔) w.e.나눔.forEach(function (y) { 판말.push(판글(y.판)); });
        else 판말.push(판글(판));
        /* 같은 낱말의 다른 판도 강조에 쓴다(사전으로 펼친 말 · 뿌리) */
        x.판들.forEach(function (p) { if (p.종류 !== '관련 말') 판말.push(판글(p)); });
      });
      판말 = 판말.filter(function (v, k) { return v && 판말.indexOf(v) === k; }).sort(function (a, b) { return b.length - a.length; });
      var 태그 = [];
      원[2].forEach(function (t, k) {
        var b = 압축(다듬[2][k]);
        for (var z = 0; z < 판말.length; z++) {
          var v = 판말[z];
          if (v.charAt(0) === '^' ? b.indexOf(v.slice(1)) === 0 : 경계민감(v) ? (b === v) : (b.indexOf(v) >= 0)) { if (태그.indexOf(t) < 0) 태그.push(t); break; }
        }
      });
      /* 칩 순서: 친 말과 똑같은 태그가 먼저(#투석 #칼슘), 그다음 짧은 것 */
      var 똑같음 = function (t) { var b = 압축(다듬기(t)); return 판말.some(function (v) { return v === b || v === '^' + b; }) ? 0 : 1; };
      태그.sort(function (a, b) { return 똑같음(a) - 똑같음(b) || a.length - b.length; });
      var 강조 = { 제목: 범위찾기(원[0], 다듬[0][0], 판말), 요약: 범위찾기(원[3], 다듬[3][0], 판말) };
      var 조각 = null;
      if (본문만 || 옵션.조각) 조각 = 조각만들기(e.i, 판말);
      return { id: it.id, 점수: e.점, 모두: 모두, 맞은: 맞은, 태그: 태그, 왜: 왜, 강조: 강조, 조각: 조각, 항목: it };
    }
    /* 원래 글에서 강조 자리 — 다듬은 글(1:1)을 붙여 찾고, 원래 자리로 되돌린다 */
    function 범위찾기(원글, 다듬글, 판말) {
      if (!원글 || !판말.length) return [];
      var 붙 = '', 지도 = [];
      for (var i = 0; i < 다듬글.length; i++) { var c = 다듬글.charAt(i); if (c !== ' ') { 붙 += c; 지도.push(i); } }
      var 칠 = [];
      판말.forEach(function (v0) {
        if (!v0) return;
        var 앞 = v0.charAt(0) === '^', v = 앞 ? v0.slice(1) : v0;
        var p = 붙.indexOf(v);
        while (p >= 0) {
          var a = 지도[p], b = 지도[p + v.length - 1] + 1;
          var ok = true;
          if (앞) ok = !한글인가(다듬글.charAt(a - 1) || ' ');
          else if (경계민감(v)) ok = 경계맞나(다듬글, a, 다듬글.slice(a, b));
          if (ok) 칠.push([a, b]);
          p = 붙.indexOf(v, p + 1);
        }
      });
      칠.sort(function (x, y) { return x[0] - y[0] || y[1] - x[1]; });
      var 합 = [];
      칠.forEach(function (r) { var 끝 = 합[합.length - 1]; if (끝 && r[0] <= 끝[1]) { if (r[1] > 끝[1]) 끝[1] = r[1]; } else 합.push([r[0], r[1]]); });
      return 합;
    }
    function 조각만들기(i, 판말) {
      var 원 = 본문원[i]; if (!원) return null;
      var 다듬 = 다듬기(원);
      var 처음 = -1, 길이 = 0;
      for (var z = 0; z < 판말.length; z++) {
        var 앞 = 판말[z].charAt(0) === '^', v = 앞 ? 판말[z].slice(1) : 판말[z], p = 다듬.indexOf(v);
        while (p >= 0 && (앞 ? 한글인가(다듬.charAt(p - 1) || ' ') : (경계민감(v) && !경계맞나(다듬, p, v)))) p = 다듬.indexOf(v, p + 1);
        if (p >= 0 && (처음 < 0 || p < 처음)) { 처음 = p; 길이 = v.length; }
      }
      if (처음 < 0) return null;
      var a = Math.max(0, 처음 - 30), b = Math.min(원.length, 처음 + 길이 + 60);
      while (a > 0 && a > 처음 - 45 && 원.charAt(a - 1) !== ' ') a--;
      while (b < 원.length && b < 처음 + 길이 + 80 && 원.charAt(b) !== ' ') b++;
      var 글 = 원.slice(a, b);
      var 범위 = 범위찾기(글, 다듬.slice(a, b), 판말);
      var 앞 = a > 0 ? '…' : '', 뒤 = b < 원.length ? '…' : '';
      return { 글: 앞 + 글 + 뒤, 강조: 범위.map(function (r) { return [r[0] + 앞.length, r[1] + 앞.length]; }) };
    }

    /* ── 8. 관련 태그 · 제안 · 하나씩 빼기 ── */
    function 관련태그(결과, 옵션) {
      옵션 = 옵션 || {};
      var 최대 = 옵션.최대 || 8, 셈 = {}, 원말 = {}, 본항목 = {};
      var 질의말 = {};
      (결과.낱말 || []).forEach(function (x) { 질의말[x.말] = 1; 질의말[x.뿌리] = 1; (x.펼침 || []).forEach(function (p) { 질의말[압축(p)] = 1; }); });
      var 몇 = Math.min(결과.length, 옵션.볼수 || 20);
      for (var r = 0; r < 몇; r++) {
        var it = 결과[r].항목 || {};
        var 본 = {};
        배열로(it.태그).forEach(function (t) {
          var b = 압축(다듬기(t)); if (!b || 본[b] || 질의말[b]) return; 본[b] = 1;
          셈[b] = (셈[b] || 0) + 1 / Math.sqrt(1 + r); 원말[b] = 원말[b] || String(t);
          본항목[b] = (본항목[b] || 0) + 1;
        });
      }
      var 목록 = Object.keys(셈).filter(function (b) { return 몇 < 4 || 본항목[b] >= 2; });
      목록.sort(function (a, b) { return 셈[b] - 셈[a]; });
      return 목록.slice(0, 최대).map(function (b) { return { 태그: 원말[b], 수: 본항목[b], 질의: '#' + 원말[b].replace(/\s+/g, '') }; });
    }
    function 제안모으기(A, R) {
      var 나옴 = [], 본 = {};
      A.낱들.forEach(function (x, k) {
        if (x.군말) return;
        var 후보 = [];
        if (x.오타) 후보 = x.오타.map(function (t) { return { 말: t }; });
        else if (R.상태[k] === '없음' && x.초성) {
          짧은말목록.forEach(function (t) { if (한글뿐(t) && 초성(t) === x.말) 후보.push({ 말: t, 수: 짧은말[t] || 0 }); });
          후보.sort(function (a, b) { return b.수 - a.수; });
        }
        후보.slice(0, 3).forEach(function (h) {
          var 새 = A.낱들.map(function (y, j) { return j === k ? h.말 : y.말; }).join(' ');
          if (!본[새]) { 본[새] = 1; 나옴.push({ 말: h.말, 질의: 새 }); }
        });
      });
      return 나옴.slice(0, 4);
    }
    function 빼고모으기(A, R) {
      var 나옴 = [];
      A.낱들.forEach(function (x, k) {
        if (R.상태[k] !== '맞음' && R.상태[k] !== '약함') return;
        var R2 = 순위(A, k);
        if (!R2.목록.length) return;
        var 남은 = A.낱들.filter(function (y, j) { return j !== k && !y.군말; }).map(function (y) { return y.말; }).join(' ');
        나옴.push({ 뺀: x.말, 질의: 남은, 수: R2.목록.length, 첫: R2.목록.slice(0, 3).map(function (z) { return (항목[z.i] || {}).id; }) });
      });
      return 나옴;
    }

    색인.찾기 = 찾기;
    색인.관련태그 = 관련태그;
    색인.제안 = function (q, 옵션) { var A = 분석(q, 옵션); return A.낱들.length ? 제안모으기(A, 순위(A, -1)) : []; };
    색인.빼고 = function (q, 옵션) { var A = 분석(q, 옵션); return A.낱들.length ? 빼고모으기(A, 순위(A, -1)) : []; };
    색인.풀이 = function (q) { var p = 풀기(q); return p.낱말.map(function (x) { return { 말: x.말, 뿌리: x.뿌리, 군말: x.군말, 초성: x.초성, 펼침: x.판들.map(function (y) { return y.말 + ':' + y.무게; }), 나눔: x.나눔 ? x.나눔.map(function (y) { return y.말; }) : null }; }); };
    색인.캐시비우기 = function () { 판캐시 = Object.create(null); 판캐시수 = 0; };
    색인.항목 = function (id) { for (var i = 0; i < N; i++) if (항목[i] && 항목[i].id === id) return 항목[i]; return null; };
    function 다됨() {
      색인.준비됨 = true; 색인.낱말수 = 낱말.length; 색인.만든시간 = Date.now() - 시작;
      if (typeof 설정.다됨 === 'function') { try { 설정.다됨(색인); } catch (e) {} }
    }
    if (설정.나눠서 && typeof setTimeout === 'function') {
      var 한번에 = 설정.한번에 || 30;
      var 돌기 = function () { if (본문조금(한번에)) 다됨(); else { 색인.낱말수 = 낱말.length; setTimeout(돌기, 0); } };
      setTimeout(돌기, 0);
    } else { 본문조금(N); 다됨(); }
    return 색인;
  }

  /* 강조 범위를 HTML 로 — 글은 늘 글자안전 처리한다 */
  function 강조HTML(글, 범위, 태그) {
    글 = String(글 == null ? '' : 글); 태그 = 태그 || 'mark';
    var o = '', 앞 = 0;
    (범위 || []).forEach(function (r) {
      if (r[0] < 앞) return;
      o += 글자안전(글.slice(앞, r[0])) + '<' + 태그 + '>' + 글자안전(글.slice(r[0], r[1])) + '</' + 태그 + '>';
      앞 = r[1];
    });
    return o + 글자안전(글.slice(앞));
  }

  /* 사전 여럿을 하나로(공통 + 앱) — 같은 대표어면 같은 말 목록을 잇는다 */
  function 합치기() {
    var 끝 = {};
    for (var a = 0; a < arguments.length; a++) {
      var 표 = arguments[a]; if (!표) continue;
      for (var k in 표) {
        var 더 = 배열로(표[k]);
        if (!끝[k]) 끝[k] = [];
        for (var j = 0; j < 더.length; j++) if (끝[k].indexOf(더[j]) < 0) 끝[k].push(더[j]);
      }
    }
    return 끝;
  }

  바탕.찾기 = { 판: 판, 만들기: 만들기, 합치기: 합치기, 다듬기: 다듬기, 초성: 초성, 글만: 글만, 강조HTML: 강조HTML, 글자안전: 글자안전 };
})(typeof window !== 'undefined' ? window : this);
/* ▲▲ 찾기 부품 끝 ▲▲ */

/* ▼▼ 약지도 쪽 ▼▼ — ES5(부품과 같은 꼴) */
(function (바탕) {
  'use strict';
  var 찾기 = 바탕.찾기;
  var 초표 = 'ㄱㄲㄴㄷㄸㄹㅁㅂㅃㅅㅆㅇㅈㅉㅊㅋㅌㅍㅎ', 중표 = 'ㅏㅐㅑㅒㅓㅔㅕㅖㅗㅘㅙㅚㅛㅜㅝㅞㅟㅠㅡㅢㅣ';
  function 붙임(s) { return 찾기.다듬기(s).replace(/ +/g, ''); }
  /* 자모로 풀기(받침은 번호 글자) — 「소하제」가 소염제보다 소화제에 가깝다는 것을 재려고 */
  function 자모(s) {
    var o = '';
    for (var i = 0; i < s.length; i++) {
      var n = s.charCodeAt(i) - 0xac00;
      o += (n >= 0 && n < 11172) ? 초표.charAt(Math.floor(n / 588)) + 중표.charAt(Math.floor((n % 588) / 28)) + (n % 28 ? String.fromCharCode(0x2460 + n % 28) : '') : s.charAt(i);
    }
    return o;
  }
  function 거리(a, b) {
    var 앞 = [], i, j;
    for (j = 0; j <= b.length; j++) 앞.push(j);
    for (i = 1; i <= a.length; i++) {
      var 지금 = [i];
      for (j = 1; j <= b.length; j++) 지금.push(Math.min(앞[j] + 1, 지금[j - 1] + 1, 앞[j - 1] + (a.charAt(i - 1) === b.charAt(j - 1) ? 0 : 1)));
      앞 = 지금;
    }
    return 앞[b.length];
  }
  function 목록(x) { return x == null ? [] : (Object.prototype.toString.call(x) === '[object Array]' ? x : [x]); }

  /* 색인 — 약지도 검색이 보는 이름들(증상 이름·태그, 성분·제품 이름, 영양제, 종류 묶음, 제품·성분 사전)과 구어 사전의 말.
     셈 = 낱말마다 무게(증상 이름 3 · 태그 2 · 나머지 1) — 초성 «ㄷㅌ» 처럼 후보가 여럿일 때 사람들이 많이 찾는 말(두통)을 먼저 */
  function 만들기(D, LEX, 말들) {
    var 항목 = [], 셈 = {};
    function 낱(t, w) {
      String(t == null ? '' : t).split(/[\s·,()\/\[\]+\-]+/).forEach(function (x) {
        x = 붙임(x); if (x.length >= 2 && /^[가-힣]+$/.test(x)) 셈[x] = (셈[x] || 0) + w;
      });
    }
    function 넣기(id, 제목, 별칭, 태그, 요약, 우선, w) {
      항목.push({ id: id, 제목: 제목, 별칭: 목록(별칭).filter(Boolean), 태그: 목록(태그).filter(Boolean), 요약: 요약 || '', 우선: 우선 });
      낱(제목, w); 목록(태그).forEach(function (t) { 낱(t, w > 1 ? w - 1 : 1); }); 목록(별칭).forEach(function (t) { 낱(t, 1); });
    }
    (D.symptoms || []).forEach(function (s) { 넣기('s:' + s.id, s.name, [], s.tags, s.short, 3, 3); });
    (D.drugs || []).forEach(function (d) { 넣기('d:' + d.id, d.name, [d.en].concat((d.products || []).map(function (p) { return p.name; })), d['for'], d.tagline, 2, 2); });
    (D.supplements || []).forEach(function (s) { 넣기('u:' + s.id, s.name, [s.en], s.tags, '', 1, 2); });
    ((D.ingredients || {}).quick || []).forEach(function (g) {
      넣기('k:' + g.id, g.n, (g.subs || []).reduce(function (a, x) { return a.concat([x.n], x.aka || []); }, []), [], '', 1, 1);
    });
    (LEX.brand || []).forEach(function (b) { 넣기('b:' + b.n, b.n, [], [], '', 2, 1); });
    (LEX.ing || []).forEach(function (x) { 넣기('i:' + x.id, x.n, [x.en], [], '', 1, 1); });
    (LEX.nut || []).forEach(function (x) { 넣기('n:' + x.id, x.n, [], [], '', 1, 1); });
    /* 약지도 구어 사전(SEARCH_SYN)·기능 바로가기 말 — 「머리아퍼」를 「머리아파」로 고치면 그다음은 약지도 사전이 두통으로 보낸다 */
    목록(말들).forEach(function (w, i) { 넣기('w:' + i, w, [], [], '', 0, 1); });
    var 색인 = 찾기.만들기({ 항목: 항목 });
    색인.셈 = 셈;
    return 색인;
  }
  function 초성후보(색인, w) {
    var 나옴 = [];
    for (var t in 색인.셈) if (t.length === w.length && 찾기.초성(t) === w) 나옴.push(t);
    나옴.sort(function (a, b) { return 색인.셈[b] - 색인.셈[a] || (a < b ? -1 : 1); });
    return 나옴.slice(0, 3);
  }
  /* 고치기(색인, 친 말, 약지도 결과 제목들) → { 질의, 다른:[…] } 또는 null(손대지 않음)
     · 초성만 친 낱말(ㅌㅇㄹㄴ) → 같은 초성의 낱말(타이레놀). 낱말 하나면 다음 후보 둘도 함께
     · 아무 데도 없는 낱말(타이레롤) → 부품의 비슷한 말 중 자모가 가장 가까운 것. 단, 약지도 결과 제목에 친 말이 그대로 있으면
       (식약처 제품 이름처럼 이 색인 밖에서 이미 찾은 것) 손대지 않는다 */
  function 고치기(색인, q, 제목들) {
    var 낱들 = String(q == null ? '' : q).replace(/^\s+|\s+$/g, '').split(/\s+/).filter(Boolean);
    if (!낱들.length) return null;
    var 초 = /^[ㄱ-ㅎ]{2,}$/;
    if (낱들.some(function (w) { return 초.test(w); })) {
      var 다른 = [], 못 = false;
      var 새 = 낱들.map(function (w) {
        if (!초.test(w)) return w;
        var c = 초성후보(색인, w); if (!c.length) { 못 = true; return w; }
        if (낱들.length === 1) 다른 = c.slice(1);
        return c[0];
      });
      return 못 ? null : { 질의: 새.join(' '), 다른: 다른 };
    }
    var 제목 = 목록(제목들).map(붙임), 통 = 붙임(q);
    if (통.length >= 2 && 제목.some(function (x) { return x.indexOf(통) >= 0; })) return null;   /* 친 말 그대로 찾은 결과가 있으면 볼 것도 없다 */
    var r = 색인.찾기(q, { 최대: 1 });
    var 틀린 = (r.낱말 || []).filter(function (x) { return x.오타 && x.오타.length; });
    if (!틀린.length || !(r.제안 || []).length) return null;
    if (틀린.some(function (x) { var b = 붙임(x.말); return 제목.some(function (t) { return t.indexOf(b) >= 0; }); })) return null;
    var 고른 = null, 점 = 1e9;
    r.제안.forEach(function (p, i) {
      var 원 = null;
      틀린.forEach(function (x) { if (x.오타.indexOf(p.말) >= 0) 원 = x.말; });
      var d = 원 ? 거리(자모(원), 자모(p.말)) : 9;
      if (d * 10 + i < 점) { 점 = d * 10 + i; 고른 = p; }
    });
    /* 약지도 검색이 무엇이든 찾았으면 «자모 하나만 다른» 진짜 오타일 때만 고친다 — 「비타민디를」을 「비타민」으로 넓히지 않게 */
    if (!고른 || (제목.length && 점 >= 20)) return null;
    return { 질의: 고른.질의, 다른: [] };
  }
  바탕.약지도찾기 = { 만들기: 만들기, 고치기: 고치기, 초성후보: 초성후보 };
})(typeof window !== 'undefined' ? window : this);
/* ▲▲ 약지도 쪽 끝 ▲▲ */
