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
