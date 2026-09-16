/**
 * 약지도 사진 지도 서버 — Cloudflare Worker (무료 플랜으로 충분)
 *
 * 하는 일: 앱이 보낸 약 사진(약봉투·약 상자·알약)을 Gemini 2.5 Flash 로 읽어
 *          제품명·성분·함량·용법 텍스트를 JSON 으로 돌려준다. 사진은 저장하지 않는다.
 *
 * 배포 (현욱님 PC, 5분):
 *   1) npm i -g wrangler && wrangler login
 *   2) cd yakjido/server && wrangler deploy            → https://yakjido-photo.<계정>.workers.dev
 *   3) wrangler secret put GEMINI_API_KEY             → Google AI Studio 에서 만든 키 붙여넣기
 *   4) (선택) wrangler secret put ALLOWED_ORIGIN      → https://usualhealth383-cloud.github.io
 *   5) yakjido/content/meta.json 의 "photoEndpoint" 에 워커 주소를 적고 build.py 실행
 *
 * 날씨 (선택): GET /wx?lat=&lon=  → 기상청 초단기실황·단기예보 + 에어코리아 미세먼지를 한 JSON 으로.
 *   wrangler secret put DATA_GO_KR_KEY   ← 공공데이터포털(data.go.kr) 일반 인증키(Decoding). 두 서비스 모두 활용신청 필요:
 *     · 기상청_단기예보 ((구)_동네예보) 조회서비스   · 한국환경공단_에어코리아_대기오염정보
 *   키가 없으면 /wx 는 404 를 주고 앱은 Open-Meteo 로 넘어간다. 30분 캐시(개발계정 일 1,000건 한도 보호).
 *
 * 비용: Gemini 2.5 Flash 입력 $0.30/1M 토큰 — 1,024px 사진 1장 ≈ 1,300 토큰 ≈ 0.5원 + 출력 소량.
 *       월 1만 장이어도 1만 원 미만. AI Studio 무료 한도(분당 10건·일 250건)로 시작 가능.
 */
export default {
  async fetch(req, env) {
    const origin = req.headers.get('Origin') || '';
    const allowed = env.ALLOWED_ORIGIN || '*';
    const cors = {
      'Access-Control-Allow-Origin': allowed === '*' ? '*' : (origin === allowed ? origin : allowed),
      'Access-Control-Allow-Methods': 'POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
      'Content-Type': 'application/json; charset=utf-8',
    };
    if (req.method === 'OPTIONS') return new Response(null, { headers: cors });
    if (req.method === 'GET' && new URL(req.url).pathname.endsWith('/wx')) return wx(req, env, { ...cors, 'Access-Control-Allow-Methods': 'GET, POST, OPTIONS' });
    if (req.method !== 'POST') return new Response(JSON.stringify({ error: 'POST only' }), { status: 405, headers: cors });
    if (!env.GEMINI_API_KEY) return new Response(JSON.stringify({ error: 'GEMINI_API_KEY 미설정' }), { status: 500, headers: cors });

    let body;
    try { body = await req.json(); } catch (e) { return new Response(JSON.stringify({ error: 'JSON 본문이 필요해요' }), { status: 400, headers: cors }); }
    const { image, mime = 'image/jpeg', hint = '' } = body || {};
    if (!image || image.length > 6_000_000) return new Response(JSON.stringify({ error: '사진이 없거나 너무 커요(4 MB 이하)' }), { status: 400, headers: cors });

    const prompt = `당신은 한국 약사입니다. 사진은 약 봉투(처방 조제), 약 상자, 알약, 시럽병 중 하나입니다.
사진에서 읽을 수 있는 것만 적고, 보이지 않는 것은 지어내지 마세요. 확신이 낮으면 confidence 를 낮게.
- items: 사진 속 약 하나마다 한 항목. name=제품명(상품명, 보이는 그대로), ingredients=성분명(한글, 예: 아세트아미노펜), strength=함량(예: 500mg), form=정/캡슐/시럽/파스/연고 등, count=봉투당 개수(보이면).
- directions: 약봉투·라벨에 인쇄된 용법 문구를 그대로(예: "1일 3회 식후 30분", "아침 저녁").
- patient: 봉투에 환자 이름·조제일이 있으면 name(가명 처리하지 말고 그대로), date.
- kind: bag(처방 약봉투) | box(약 상자) | pill(알약만) | bottle(시럽·액제) | supplement(영양제 라벨) | other.
- warnings: 사진에서 읽히는 경고 문구(있으면).
- pill: 알약 사진이면 각인 글자(앞 imprint_front, 뒤 imprint_back — 보이는 그대로, 없으면 빈 문자열), shape(원형/타원형/장방형/삼각형/사각형/오각형/육각형/팔각형/마름모형/기타), color(하양/노랑/분홍/주황/갈색/파랑/연두/초록/빨강/회색/보라/투명/검정/자주/청록/남색 중), score_line(분할선 있으면 true).
- supplement: 영양제·건강기능식품 라벨이면 성분표를 항목별로: name(성분명 한글), amount(숫자), unit(mg/µg/IU/CFU/g). 1일 섭취량 기준인지 1회 분량 기준인지 basis 에.
${hint ? '참고: ' + hint : ''}`;

    const schema = {
      type: 'OBJECT',
      properties: {
        kind: { type: 'STRING' },
        items: { type: 'ARRAY', items: { type: 'OBJECT', properties: {
          name: { type: 'STRING' }, ingredients: { type: 'ARRAY', items: { type: 'STRING' } }, strength: { type: 'STRING' },
          form: { type: 'STRING' }, count: { type: 'STRING' }, confidence: { type: 'NUMBER' } }, required: ['name', 'ingredients', 'confidence'] } },
        directions: { type: 'STRING' },
        patient: { type: 'OBJECT', properties: { name: { type: 'STRING' }, date: { type: 'STRING' } } },
        warnings: { type: 'ARRAY', items: { type: 'STRING' } },
        pill: { type: 'OBJECT', properties: { imprint_front: { type: 'STRING' }, imprint_back: { type: 'STRING' }, shape: { type: 'STRING' }, color: { type: 'STRING' }, score_line: { type: 'BOOLEAN' } } },
        supplement: { type: 'OBJECT', properties: { basis: { type: 'STRING' }, ingredients: { type: 'ARRAY', items: { type: 'OBJECT', properties: { name: { type: 'STRING' }, amount: { type: 'NUMBER' }, unit: { type: 'STRING' } } } } } },
      },
      required: ['kind', 'items'],
    };

    const model = env.GEMINI_MODEL || 'gemini-2.5-flash';
    const url = `https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent?key=${env.GEMINI_API_KEY}`;
    const payload = {
      contents: [{ role: 'user', parts: [{ text: prompt }, { inline_data: { mime_type: mime, data: image } }] }],
      generationConfig: { temperature: 0.1, response_mime_type: 'application/json', response_schema: schema },
    };
    const r = await fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
    if (!r.ok) {
      const t = await r.text();
      return new Response(JSON.stringify({ error: `Gemini ${r.status}`, detail: t.slice(0, 300) }), { status: 502, headers: cors });
    }
    const j = await r.json();
    const text = j?.candidates?.[0]?.content?.parts?.map(p => p.text).join('') || '{}';
    let out;
    try { out = JSON.parse(text); } catch (e) { out = { kind: 'other', items: [], raw: text.slice(0, 500) }; }
    out.model = model;
    return new Response(JSON.stringify(out), { headers: cors });
  },
};

/* ───────── 날씨: 기상청 + 에어코리아 ─────────
   앱이 보내는 것은 좌표뿐. 좌표 → 기상청 격자(nx,ny)와 가장 가까운 시도(에어코리아)로 바꿔 조회한다. */
const SIDO = [['서울',37.57,126.98],['부산',35.18,129.08],['대구',35.87,128.60],['인천',37.46,126.71],['광주',35.16,126.85],['대전',36.35,127.38],['울산',35.54,129.31],['세종',36.48,127.29],
  ['경기',37.26,127.03],['강원',37.88,127.73],['강원',37.75,128.88],['충북',36.64,127.49],['전북',35.82,127.15],['경남',35.23,128.68],['경북',36.02,129.36],['전남',34.81,126.39],['제주',33.50,126.53],['충남',36.80,127.15]];
function nearestSido(lat, lon){ let b = SIDO[0], bd = 1e9; for (const c of SIDO) { const d = (c[1] - lat) ** 2 + ((c[2] - lon) * Math.cos(lat * Math.PI / 180)) ** 2; if (d < bd) { bd = d; b = c; } } return b[0]; }
/* 기상청 LCC DFS 격자 변환 — 기상청 공개 산식 그대로 */
export function toGrid(lat, lon){
  const RE = 6371.00877, GRID = 5.0, SLAT1 = 30.0, SLAT2 = 60.0, OLON = 126.0, OLAT = 38.0, XO = 43, YO = 136, D = Math.PI / 180;
  const re = RE / GRID, slat1 = SLAT1 * D, slat2 = SLAT2 * D, olon = OLON * D, olat = OLAT * D;
  let sn = Math.tan(Math.PI * 0.25 + slat2 * 0.5) / Math.tan(Math.PI * 0.25 + slat1 * 0.5); sn = Math.log(Math.cos(slat1) / Math.cos(slat2)) / Math.log(sn);
  let sf = Math.tan(Math.PI * 0.25 + slat1 * 0.5); sf = Math.pow(sf, sn) * Math.cos(slat1) / sn;
  let ro = Math.tan(Math.PI * 0.25 + olat * 0.5); ro = re * sf / Math.pow(ro, sn);
  let ra = Math.tan(Math.PI * 0.25 + lat * D * 0.5); ra = re * sf / Math.pow(ra, sn);
  let theta = lon * D - olon; if (theta > Math.PI) theta -= 2 * Math.PI; if (theta < -Math.PI) theta += 2 * Math.PI; theta *= sn;
  return { nx: Math.floor(ra * Math.sin(theta) + XO + 0.5), ny: Math.floor(ro - ra * Math.cos(theta) + YO + 0.5) };  /* XO 43·YO 136 이면 +0.5 (+1.5 는 XO 42 판) */
}
const pad = n => String(n).padStart(2, '0');
function kst(){ return new Date(Date.now() + 9 * 3600 * 1000); }  /* UTC getter 로 읽으면 한국 시각 */
const ymd = d => `${d.getUTCFullYear()}${pad(d.getUTCMonth() + 1)}${pad(d.getUTCDate())}`;
/* PTY(강수형태)·SKY(하늘) → 앱이 쓰는 WMO 비슷한 코드 */
function wmo(pty, sky){ pty = +pty || 0; sky = +sky || 0; if ([3, 7].includes(pty)) return 71; if (pty === 4) return 80; if (pty) return 61; return sky >= 4 ? 3 : sky === 3 ? 2 : 0; }
const median = a => { a = a.map(Number).filter(v => Number.isFinite(v) && v >= 0).sort((x, y) => x - y); return a.length ? a[Math.floor(a.length / 2)] : null; };
export async function wx(req, env, cors){
  let key = env.DATA_GO_KR_KEY;
  if (!key) return new Response(JSON.stringify({ error: 'DATA_GO_KR_KEY 미설정' }), { status: 404, headers: cors });
  /* 포털은 Encoding 키(%2F·%3D 가 든 것)와 Decoding 키를 둘 다 준다. 어느 쪽을 넣어도 되게 — 아래에서 다시 encodeURIComponent 하므로 여기서는 풀어 둔다 */
  try { if (/%[0-9A-Fa-f]{2}/.test(key)) key = decodeURIComponent(key); } catch (e) {}
  const u = new URL(req.url); const lat = +u.searchParams.get('lat'), lon = +u.searchParams.get('lon');
  if (!(lat > 32 && lat < 40 && lon > 124 && lon < 132)) return new Response(JSON.stringify({ error: '한국 안 좌표만' }), { status: 400, headers: cors });
  const { nx, ny } = toGrid(lat, lon); const sido = nearestSido(lat, lon);
  /* 30분 캐시 — 같은 격자·시도는 다시 묻지 않는다 */
  const ck = new Request(`https://wx.cache/${nx}/${ny}/${encodeURIComponent(sido)}/${Math.floor(Date.now() / (30 * 60 * 1000))}`);
  const cache = typeof caches !== 'undefined' ? caches.default : null;
  const hit = cache && await cache.match(ck); if (hit) return new Response(await hit.text(), { headers: cors });
  const now = kst(); const hh = now.getUTCHours(), mm = now.getUTCMinutes();
  /* 초단기실황은 매시 40분 뒤에 나온다 */
  const nc = new Date(now); if (mm < 40) nc.setUTCHours(nc.getUTCHours() - 1);
  const ncst = `https://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getUltraSrtNcst?serviceKey=${encodeURIComponent(key)}&dataType=JSON&numOfRows=100&pageNo=1&base_date=${ymd(nc)}&base_time=${pad(nc.getUTCHours())}00&nx=${nx}&ny=${ny}`;
  /* 오늘 최고·최저는 02시 발표 단기예보(TMX·TMN) — 02:10 전이면 어제 23시 발표 */
  const fd = new Date(now); let fb = '0200'; if (hh < 2 || (hh === 2 && mm < 10)) { fd.setUTCDate(fd.getUTCDate() - 1); fb = '2300'; }
  const fcst = `https://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getVilageFcst?serviceKey=${encodeURIComponent(key)}&dataType=JSON&numOfRows=400&pageNo=1&base_date=${ymd(fd)}&base_time=${fb}&nx=${nx}&ny=${ny}`;
  const air = `https://apis.data.go.kr/B552584/ArpltnInforInqireSvc/getCtprvnRltmMesureDnsty?serviceKey=${encodeURIComponent(key)}&returnType=json&numOfRows=100&pageNo=1&sidoName=${encodeURIComponent(sido)}&ver=1.0`;
  const get = async url => { try { const r = await fetch(url, { headers: { Accept: 'application/json' } }); if (!r.ok) return null; return await r.json(); } catch (e) { return null; } };
  const [n, f, a] = await Promise.all([get(ncst), get(fcst), get(air)]);
  const nItems = n?.response?.body?.items?.item || []; const fItems = f?.response?.body?.items?.item || []; const aItems = a?.response?.body?.items || [];
  const nv = c => { const x = nItems.find(i => i.category === c); return x ? +x.obsrValue : null; };
  const today = ymd(now);
  const fv = c => { const x = fItems.find(i => i.category === c && i.fcstDate === today); return x ? +x.fcstValue : null; };
  const skyNow = (() => { const t = `${pad(hh)}00`; const x = fItems.filter(i => i.category === 'SKY' && i.fcstDate === today).sort((p, q) => Math.abs(+p.fcstTime - +t) - Math.abs(+q.fcstTime - +t))[0]; return x ? +x.fcstValue : null; })();
  const out = { src: 'kma', sido, nx, ny, now: nv('T1H'), feel: null, rh: nv('REH'), wind: nv('WSD'), code: wmo(nv('PTY'), skyNow), max: fv('TMX'), min: fv('TMN'),
    pm10: median(aItems.map(i => i.pm10Value)), pm25: median(aItems.map(i => i.pm25Value)), stations: aItems.length, at: Date.now() };
  if (out.now == null && out.max == null) return new Response(JSON.stringify({ error: '기상청 응답 없음', detail: (n?.response?.header?.resultMsg || '') }), { status: 502, headers: cors });
  /* 체감온도: 기상청 산식(겨울 풍속냉각)은 10℃ 이하·바람 1.3 m/s 이상일 때만 뜻이 있다 */
  if (out.now != null && out.wind != null && out.now <= 10 && out.wind >= 1.3) { const v = Math.pow(out.wind * 3.6, 0.16); out.feel = Math.round((13.12 + 0.6215 * out.now - 11.37 * v + 0.3965 * out.now * v) * 10) / 10; } else out.feel = out.now;
  const body = JSON.stringify(out);
  if (cache) try { await cache.put(ck, new Response(body, { headers: { 'Cache-Control': 'max-age=1800' } })); } catch (e) {}
  return new Response(body, { headers: cors });
}
