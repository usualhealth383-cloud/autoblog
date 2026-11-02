// 곁에 푸시 판정 시험 — node --experimental-strip-types yakjido/tests/gyeote_push.mjs
import { due, text, local } from '../server/supabase/functions/mn-push-check/modules/gyeote_logic.ts';
let bad = 0, ok = 0; const 봄 = (c, m, x) => { if (c) ok++; else { bad++; console.log('❌ ' + m + ' — ' + JSON.stringify(x)); } };
const KST = (s) => new Date(s + '+09:00');
const set = { eve: { on: true, t: '21:00' }, week: { on: true, t: '20:00', dow: 0 }, tz: 'Asia/Seoul' };
const k = (s) => local(KST(s), 'Asia/Seoul').key;
// 2026-11-04 는 수요일, 11-08 은 일요일
봄(due(null, {}, {}, [], KST('2026-11-04T21:05')).list.length === 0, '설정 없으면 없음');
봄(due(set, {}, {}, [], KST('2026-11-04T20:59')).list.length === 0, '저녁 — 시간 전 없음');
봄(due(set, {}, {}, [], KST('2026-11-04T21:00')).list[0]?.kind === 'eve', '저녁 — 정시');
봄(due(set, {}, {}, [], KST('2026-11-04T22:59')).list[0]?.kind === 'eve', '저녁 — 두 시간 안');
봄(due(set, {}, {}, [], KST('2026-11-04T23:00')).list.length === 0, '저녁 — 두 시간 넘으면 없음');
봄(due(set, { [k('2026-11-04T12:00')]: 60 }, {}, [], KST('2026-11-04T21:10')).list.length === 0, '저녁 — 배터리 남겼으면 없음');
봄(due(set, { [k('2026-11-04T12:00')]: 0 }, {}, [], KST('2026-11-04T21:10')).list.length === 0, '저녁 — 배터리 0 도 남긴 것');
봄(due(set, {}, { [k('2026-11-04T12:00')]: { m: 1 } }, [], KST('2026-11-04T21:10')).list.length === 0, '저녁 — 마음 남겼으면 없음');
봄(due(set, { [k('2026-11-03T12:00')]: 60 }, {}, [], KST('2026-11-04T21:10')).list[0]?.kind === 'eve', '저녁 — 어제 기록은 오늘이 아님');
봄(due({ ...set, eve: { on: false, t: '21:00' } }, {}, {}, [], KST('2026-11-04T21:10')).list.length === 0, '저녁 — 꺼짐');
봄(due(set, { '2026-11-8': 50 }, {}, [], KST('2026-11-08T20:10')).list.map((x) => x.kind).join() === 'week', '일요일 20시 — 마음 카드(저녁은 21시)');
봄(due(set, {}, {}, [], KST('2026-11-07T20:10')).list.length === 0, '토요일 — 마음 카드 없음');
봄(due({ ...set, week: { on: false, t: '20:00', dow: 0 } }, {}, {}, [], KST('2026-11-08T20:10')).list.length === 0, '마음 카드 꺼짐');
const at = KST('2026-11-04T09:00').getTime();
봄(due(set, { [k('2026-11-04T12:00')]: 1 }, {}, [{ go: 'x', t: '우울', at }], KST('2026-11-04T09:30')).list.length === 0, '다시 재기 — 10시 전 없음');
봄(due(set, { [k('2026-11-04T12:00')]: 1 }, {}, [{ go: 'x', t: '우울', at }], KST('2026-11-04T10:00')).list[0]?.slot === String(at), '다시 재기 — 낮');
봄(due(set, { [k('2026-11-04T12:00')]: 1 }, {}, [{ go: 'x', at: at + 864e5 }], KST('2026-11-04T12:00')).list.length === 0, '다시 재기 — 아직 날 안 됨');
봄(due(set, {}, {}, [{ go: 'x', at: at - 4 * 864e5 }], KST('2026-11-04T12:00')).list.length === 0, '다시 재기 — 사흘 넘게 지난 것 없음');
봄(due(set, {}, {}, [{ go: 'x', at }], KST('2026-11-04T21:30')).list.map((x) => x.kind).join() === 'eve', '다시 재기 — 21시 뒤 없음');
봄(due({ ...set, tz: 'America/New_York' }, {}, {}, [], new Date('2026-11-04T21:05-05:00')).list[0]?.kind === 'eve', '시간대 — 뉴욕 21시');
봄(due({ ...set, tz: 'Not/AZone' }, {}, {}, [], KST('2026-11-04T21:05')).list[0]?.kind === 'eve', '이상한 시간대 → 서울');
for (const l of ['ko', 'en', 'es', 'ja', 'zh', 'xx']) for (const kd of ['eve', 'week', 'retest']) {
  const t = text(kd, l); 봄(t.title && t.body && t.go === '#/', '글 ' + l + kd, t);
  봄(!/우울|불안|검사|살펴|depress|anxi|PHQ|GAD/i.test(t.title + t.body), '글에 병명·검사 이름 없음 ' + l + kd, t);
  if (l !== 'ko' && l !== 'xx') 봄(!/[가-힣]/.test(t.title + t.body), '외국어 글에 한국어 없음 ' + l + kd, t);
}
봄(!JSON.stringify(text('retest', 'ko')).includes('우울'), '다시 재기 글에 검사 이름(t) 안 들어감');
console.log(`통과 ${ok} · 결함 ${bad}건`); process.exit(bad ? 1 : 0);
