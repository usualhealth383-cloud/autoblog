import worker, { toGrid, wx } from '../server/worker.js';
// 1) 격자 변환 — 기상청 공개 좌표표와 대조
const K = { 서울:[37.5665,126.9780,60,127], 부산:[35.1796,129.0756,98,76], 제주:[33.4996,126.5312,53,38], 대구:[35.8714,128.6014,89,90], 인천:[37.4563,126.7052,55,124], 광주:[35.1595,126.8526,58,74], 대전:[36.3504,127.3845,67,100] };
let bad = 0; for (const [n,[la,lo,x,y]] of Object.entries(K)) { const g = toGrid(la,lo); if (g.nx!==x||g.ny!==y) { bad++; console.log('격자 불일치', n, g, x, y); } }
console.log('격자 검사', bad ? '실패 '+bad : '7/7 일치');
// 2) 모의 fetch 로 /wx 흐름
globalThis.fetch = async (url) => {
  const u = String(url);
  const ok = j => ({ ok: true, json: async () => j });
  if (u.includes('getUltraSrtNcst')) return ok({ response: { header: { resultCode: '00' }, body: { items: { item: [
    { category: 'T1H', obsrValue: '3.2' }, { category: 'REH', obsrValue: '28' }, { category: 'PTY', obsrValue: '0' }, { category: 'WSD', obsrValue: '4.1' } ] } } } });
  if (u.includes('getVilageFcst')) { const d = new Date(Date.now()+9*3600e3); const t = `${d.getUTCFullYear()}${String(d.getUTCMonth()+1).padStart(2,'0')}${String(d.getUTCDate()).padStart(2,'0')}`;
    return ok({ response: { body: { items: { item: [ { category: 'TMX', fcstDate: t, fcstTime: '1500', fcstValue: '15.0' }, { category: 'TMN', fcstDate: t, fcstTime: '0600', fcstValue: '-1.0' }, { category: 'SKY', fcstDate: t, fcstTime: '1200', fcstValue: '4' } ] } } } }); }
  if (u.includes('ArpltnInforInqireSvc')) return ok({ response: { body: { items: [ { pm10Value: '95', pm25Value: '48' }, { pm10Value: '-', pm25Value: '40' }, { pm10Value: '110', pm25Value: '52' } ] } } });
  return { ok: false };
};
const cors = { 'Content-Type': 'application/json' };
const r0 = await wx(new Request('https://x/wx?lat=37.57&lon=126.98'), {}, cors); console.log('키 없음 →', r0.status, await r0.text());
const r1 = await wx(new Request('https://x/wx?lat=37.57&lon=126.98'), { DATA_GO_KR_KEY: 'k' }, cors); console.log('응답 →', r1.status, await r1.text());
const r2 = await wx(new Request('https://x/wx?lat=1&lon=1'), { DATA_GO_KR_KEY: 'k' }, cors); console.log('범위 밖 →', r2.status);
const r3 = await worker.fetch(new Request('https://x/wx?lat=37.57&lon=126.98', { method: 'GET' }), { DATA_GO_KR_KEY: 'k' }); console.log('라우팅 →', r3.status, (await r3.text()).slice(0, 60));
