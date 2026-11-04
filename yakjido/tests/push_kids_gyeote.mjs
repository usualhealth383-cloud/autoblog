// 소아·곁에 알림 판정 시험 — node --experimental-strip-types yakjido/tests/push_kids_gyeote.mjs
import { kidsDue, kidsMessage, WIN } from '../server/supabase/functions/mn-push-check/modules/kg_logic.ts';
import { due, text } from '../server/supabase/functions/mn-push-check/modules/gyeote_logic.ts';
let bad = 0, n = 0; const ok = (c, m) => { n++; if (!c) { bad++; console.log('✗', m); } };
const T = s => new Date(s);
// 소아
const rem = { on: true, next: { acet: '2026-11-04T11:00:00Z', ibu: '2026-11-04T13:00:00Z' }, tz: 'Asia/Seoul', lang: 'ko' };
ok(kidsDue(rem, T('2026-11-04T11:00:00Z')).length === 1, '정각 한 건');
ok(kidsDue(rem, T('2026-11-04T11:09:00Z')).length === 1, '+9분 안(한 번 놓쳐도)');
ok(kidsDue(rem, T('2026-11-04T10:57:00Z')).length === 0, '그때 전에는 안 감(앞당기지 않음)');
ok(kidsDue(rem, T('2026-11-04T11:11:00Z')).length === 0, '+11분 밖');
ok(kidsDue(rem, T('2026-11-04T10:30:00Z')).length === 0, '30분 전 안 감');
ok(kidsDue({ ...rem, on: false }, T('2026-11-04T11:00:00Z')).length === 0, '끈 사람 안 감');
ok(kidsDue(null, T('2026-11-04T11:00:00Z')).length === 0, '기록 없음');
ok(kidsDue({ on: true, next: { acet: 'nope' } }, T('2026-11-04T11:00:00Z')).length === 0, '이상한 시각');
const k = kidsDue(rem, T('2026-11-04T11:00:00Z'))[0]; ok(k.ing === 'acet' && k.day === '2026-11-04' && k.slot === 'acet@20:00', '서울 시각 슬롯 ' + JSON.stringify(k));
// 자정 넘김 — 서울 00:01 은 그 날짜
const mid = kidsDue({ on: true, next: { ibu: '2026-11-04T15:01:00Z' }, tz: 'Asia/Seoul' }, T('2026-11-04T15:03:00Z'))[0];
ok(mid && mid.day === '2026-11-05' && mid.slot === 'ibu@00:01', '자정 넘김 ' + JSON.stringify(mid));
// 다른 시간대(뉴욕)
const ny = kidsDue({ on: true, next: { acet: '2026-11-04T23:00:00Z' }, tz: 'America/New_York' }, T('2026-11-04T23:02:00Z'))[0];
ok(ny && ny.day === '2026-11-04' && ny.slot === 'acet@18:00', '뉴욕 ' + JSON.stringify(ny));
ok(kidsDue({ on: true, next: { acet: '2026-11-04T23:00:00Z' }, tz: 'Bad/Zone' }, T('2026-11-04T23:00:00Z'))[0].slot === 'acet@08:00', '잘못된 시간대 → 서울');
// 글: 성분 이름만, 숫자(양) 없음
for (const l of ['ko', 'en', 'es', 'ja', 'zh', 'xx']) { const m = kidsMessage('ibu', l); ok(m.title && m.body && !/\d/.test(m.body), '소아 글 ' + l); }
ok(/이부프로펜을 다시 먹일 수 있는 때예요/.test(kidsMessage('ibu', 'ko').body), '성분 이름 · 소아 앱 글');
ok(kidsDue({ on: true, next: { acet: null, ibu: null } }, T('2026-11-04T11:00:00Z')).length === 0, 'next null 안 감');
// 곁에 — 곁에 형식(gyeote_pushset.dose · 11-04) · 정한 시각부터 WINDOW 안 첫 확인에 한 번
const set = { v: 1, tz: 'Asia/Seoul', dose: { on: true, times: ['08:30', '21:00', '08:30'] } };
const D = (iso) => due(set, {}, {}, null, T(iso)).list.filter((x) => x.kind === 'dose');
ok(D('2026-11-03T23:30:00Z').length === 1 && D('2026-11-03T23:30:00Z')[0].slot === '08:30', '08:30 서울 한 건(같은 시각 겹침 하나)');
ok(D('2026-11-03T23:34:00Z').length === 1, '+4분(5분 확인)');
ok(D('2026-11-03T23:29:00Z').length === 0, '1분 전 안 감');
ok(due({ ...set, dose: undefined }, {}, {}, null, T('2026-11-03T23:30:00Z')).list.length === 0, '끈 사람(칸 빠짐) 안 감');
ok(due({ ...set, dose: { on: false, times: ['08:30'] } }, {}, {}, null, T('2026-11-03T23:30:00Z')).list.length === 0, 'on:false 안 감');
ok(due({ ...set, dose: { on: true, times: ['8:30', 'x'] } }, {}, {}, null, T('2026-11-03T23:30:00Z')).list.length === 0, '이상한 시각 무시');
const d1 = D('2026-11-03T23:31:00Z')[0], d2 = D('2026-11-03T23:36:00Z')[0];
ok(d1 && d2 && d1.slot === d2.slot && due(set, {}, {}, null, T('2026-11-03T23:31:00Z')).day === due(set, {}, {}, null, T('2026-11-03T23:36:00Z')).day, '두 번 확인해도 같은 열쇠(중복 막힘)');
ok(due({ ...set, tz: 'America/New_York' }, {}, {}, null, T('2026-11-04T13:30:00Z')).list.some((x) => x.kind === 'dose' && x.slot === '08:30'), '뉴욕 08:30');
for (const l of ['ko', 'en', 'es', 'ja', 'zh']) { const m = text('dose', l); ok(m.body && m.title && m.tag === 'gyeote-dose' && !/\d/.test(m.body), '곁에 복약 글 ' + l); }
const k1 = kidsDue(rem, T('2026-11-04T11:01:00Z'))[0], k2 = kidsDue(rem, T('2026-11-04T11:06:00Z'))[0];
ok(k1 && k2 && k1.slot === k2.slot && k1.day === k2.day, '소아 두 번 확인 같은 열쇠');
ok(WIN === 3, '창 ±3분');
console.log(bad ? `✗ ${bad}개 실패` : `✓ 소아·곁에 알림 판정 ${n}가지(시간대·자정 넘김·중복·끈 사람)`);
process.exit(bad ? 1 : 0);
