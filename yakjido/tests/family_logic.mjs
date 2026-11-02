// 가족 알림 놓침 판정 시험 — node --experimental-strip-types yakjido/tests/family_logic.mjs
import { missedSlots, seoulNow, quiet, stale, message, slotWord } from '../server/supabase/functions/yak-family-check/logic.ts';
let bad = 0; const ok = (c, m) => { if (!c) { bad++; console.log('✗', m); } };
const day = '2026-11-02';
const me = { taking: ['ibu', 'met', 'prnx'], sched: { ibu: ['08:00', '20:00'], met: ['08:00'], prnx: ['09:00'] }, prn: { prnx: true },
  taken: { [day]: ['met@08:00'] }, skipped: {} };
ok(JSON.stringify(missedSlots(me, { day, min: 9 * 60 + 59 })) === '[]', '2시간 전엔 놓침 아님');
ok(JSON.stringify(missedSlots(me, { day, min: 10 * 60 })) === '["08:00"]', '08:00 ibu 놓침(같은 시각 met 은 먹음)');
ok(JSON.stringify(missedSlots({ ...me, skipped: { [day]: ['ibu@08:00'] } }, { day, min: 10 * 60 })) === '[]', '건너뜀은 놓침 아님');
ok(JSON.stringify(missedSlots(me, { day, min: 22 * 60 + 1 })) === '["08:00","20:00"]', '두 시각');
ok(missedSlots(me, { day, min: 12 * 60 }).indexOf('09:00') < 0, '필요할 때 약 제외');
ok(JSON.stringify(missedSlots({ taking: ['x'], sched: { y: ['08:00'] } }, { day, min: 900 })) === '[]', '약통에 없는 약 제외');
ok(JSON.stringify(missedSlots(null, { day, min: 900 })) === '[]', '빈 기록');
ok(JSON.stringify(missedSlots({ taking: ['a'], sched: { a: ['25:00', 'x'] } }, { day, min: 1400 })) === '[]', '이상한 시각 무시');
const s = seoulNow(new Date('2026-11-02T15:30:00Z')); ok(s.day === '2026-11-03' && s.min === 30, '서울 날짜 넘어감 ' + JSON.stringify(s));
ok(quiet(22 * 60) && quiet(6 * 60 + 59) && !quiet(7 * 60) && !quiet(21 * 60 + 59), '조용한 시간');
ok(stale('2026-10-28T00:00:00Z', new Date('2026-11-02T00:00:00Z')) && !stale('2026-11-01T00:00:00Z', new Date('2026-11-02T00:00:00Z')), '3일 기록 없음');
ok(slotWord('20:00') === '오후 8:00' && slotWord('08:05') === '오전 8:05' && slotWord('00:00') === '오전 12:00' && slotWord('12:30') === '오후 12:30', '시각 글');
const m = message('엄마', '20:00'); ok(!/이부|ibu/.test(m.body) && /체크가 아직 없어요/.test(m.body), '약 이름 없음·단정 않음 ' + m.body);
console.log(bad ? `✗ ${bad}개 실패` : '✓ 가족 알림 판정 13가지');
process.exit(bad ? 1 : 0);
