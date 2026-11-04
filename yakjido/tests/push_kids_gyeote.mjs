// 소아·곁에 알림 판정 시험 — node --experimental-strip-types yakjido/tests/push_kids_gyeote.mjs
import { kidsDue, kidsMessage, gyeoteDue, gyeoteMessage, WIN } from '../server/supabase/functions/mn-push-check/modules/kg_logic.ts';
let bad = 0, n = 0; const ok = (c, m) => { n++; if (!c) { bad++; console.log('✗', m); } };
const T = s => new Date(s);
// 소아
const rem = { on: true, next: { acet: '2026-11-04T11:00:00Z', ibu: '2026-11-04T13:00:00Z' }, tz: 'Asia/Seoul', lang: 'ko' };
ok(kidsDue(rem, T('2026-11-04T11:00:00Z')).length === 1, '정각 한 건');
ok(kidsDue(rem, T('2026-11-04T11:03:00Z')).length === 1, '+3분 안');
ok(kidsDue(rem, T('2026-11-04T10:57:00Z')).length === 1, '-3분 안');
ok(kidsDue(rem, T('2026-11-04T11:04:00Z')).length === 0, '+4분 밖');
ok(kidsDue(rem, T('2026-11-04T10:30:00Z')).length === 0, '30분 전 안 감');
ok(kidsDue({ ...rem, on: false }, T('2026-11-04T11:00:00Z')).length === 0, '끈 사람 안 감');
ok(kidsDue(null, T('2026-11-04T11:00:00Z')).length === 0, '기록 없음');
ok(kidsDue({ on: true, next: { acet: 'nope' } }, T('2026-11-04T11:00:00Z')).length === 0, '이상한 시각');
const k = kidsDue(rem, T('2026-11-04T11:00:00Z'))[0]; ok(k.ing === 'acet' && k.day === '2026-11-04' && k.slot === 'acet@20:00', '서울 시각 슬롯 ' + JSON.stringify(k));
// 자정 넘김 — 서울 00:01 은 그 날짜
const mid = kidsDue({ on: true, next: { ibu: '2026-11-04T15:01:00Z' }, tz: 'Asia/Seoul' }, T('2026-11-04T14:59:00Z'))[0];
ok(mid && mid.day === '2026-11-05' && mid.slot === 'ibu@00:01', '자정 넘김 ' + JSON.stringify(mid));
// 다른 시간대(뉴욕)
const ny = kidsDue({ on: true, next: { acet: '2026-11-04T23:00:00Z' }, tz: 'America/New_York' }, T('2026-11-04T23:02:00Z'))[0];
ok(ny && ny.day === '2026-11-04' && ny.slot === 'acet@18:00', '뉴욕 ' + JSON.stringify(ny));
ok(kidsDue({ on: true, next: { acet: '2026-11-04T23:00:00Z' }, tz: 'Bad/Zone' }, T('2026-11-04T23:00:00Z'))[0].slot === 'acet@08:00', '잘못된 시간대 → 서울');
// 글: 성분 이름만, 숫자(양) 없음
for (const l of ['ko', 'en', 'es', 'ja', 'zh', 'xx']) { const m = kidsMessage('ibu', l); ok(m.title && m.body && !/\d/.test(m.body), '소아 글 ' + l); }
ok(/이부프로펜/.test(kidsMessage('ibu', 'ko').body), '성분 이름');
// 곁에
const g = { on: true, times: ['08:00', '21:00', '08:00'], tz: 'Asia/Seoul', lang: 'ko' };
ok(gyeoteDue(g, T('2026-11-03T23:00:00Z')).length === 1, '08:00 서울 = 23:00Z 한 건(같은 시각 겹침 하나)');
ok(gyeoteDue(g, T('2026-11-03T23:02:00Z')).length === 1, '+2분');
ok(gyeoteDue(g, T('2026-11-03T23:05:00Z')).length === 0, '+5분 밖');
ok(gyeoteDue({ ...g, on: false }, T('2026-11-03T23:00:00Z')).length === 0, '곁에 끈 사람 안 감');
ok(gyeoteDue({ on: true, times: ['25:00', 'x'] }, T('2026-11-03T23:00:00Z')).length === 0, '이상한 시각 무시');
const a = gyeoteDue({ on: true, times: ['23:59'], tz: 'Asia/Seoul' }, T('2026-11-04T15:01:00Z'))[0];   // 서울 00:01 에 본 23:59
ok(a && a.day === '2026-11-04' && a.slot === '23:59', '00:01 에 본 23:59 → 어제 몫 ' + JSON.stringify(a));
const b = gyeoteDue({ on: true, times: ['00:01'], tz: 'Asia/Seoul' }, T('2026-11-04T14:59:00Z'))[0];   // 서울 23:59 에 본 00:01
ok(b && b.day === '2026-11-05' && b.slot === '00:01', '23:59 에 본 00:01 → 내일 몫 ' + JSON.stringify(b));
// 중복: 5분마다 확인 — 같은 시각은 같은 (day, slot) 이라 mn_push_sent 가 한 번만 받는다
const s1 = gyeoteDue(g, T('2026-11-03T22:58:00Z'))[0], s2 = gyeoteDue(g, T('2026-11-03T23:03:00Z'))[0];
ok(s1 && s2 && s1.day === s2.day && s1.slot === s2.slot, '두 번 확인해도 같은 열쇠(중복 막힘)');
const k1 = kidsDue(rem, T('2026-11-04T10:58:00Z'))[0], k2 = kidsDue(rem, T('2026-11-04T11:03:00Z'))[0];
ok(k1 && k2 && k1.slot === k2.slot && k1.day === k2.day, '소아 두 번 확인 같은 열쇠');
for (const l of ['ko', 'en', 'es', 'ja', 'zh']) ok(gyeoteMessage(l).body && !/\d/.test(gyeoteMessage(l).body), '곁에 글 ' + l);
ok(WIN === 3, '창 ±3분');
console.log(bad ? `✗ ${bad}개 실패` : `✓ 소아·곁에 알림 판정 ${n}가지(시간대·자정 넘김·중복·끈 사람)`);
process.exit(bad ? 1 : 0);
