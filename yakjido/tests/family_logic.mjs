// 알림 판정 시험 — node --experimental-strip-types yakjido/tests/family_logic.mjs
import { missedSlots, dueNow, localNow, seoulNow, quiet, stale, message, doseMessage, slotWord, prefs } from '../server/supabase/functions/mn-push-check/modules/yak_logic.ts';
let bad = 0, n = 0; const ok = (c, m) => { n++; if (!c) { bad++; console.log('✗', m); } };
const day = '2026-11-02';
const me = { taking: ['ibu', 'met', 'prnx'], sched: { ibu: ['08:00', '20:00'], met: ['08:00'], prnx: ['09:00'] }, prn: { prnx: true },
  taken: { [day]: ['met@08:00'] }, skipped: {} };
const synced = { day, min: 23 * 60 };   // 기록이 오늘 밤까지 올라옴
const J = JSON.stringify;
ok(J(missedSlots(me, { day, min: 9 * 60 + 59 }, 2, synced)) === '[]', '2시간 전엔 놓침 아님');
ok(J(missedSlots(me, { day, min: 10 * 60 }, 2, synced)) === '["08:00"]', '08:00 ibu 놓침(같은 시각 met 은 먹음)');
ok(J(missedSlots(me, { day, min: 9 * 60 }, 1, synced)) === '["08:00"]', '기다리는 시간 1시간');
ok(J(missedSlots(me, { day, min: 10 * 60 + 59 }, 3, synced)) === '[]', '기다리는 시간 3시간');
ok(J(missedSlots({ ...me, skipped: { [day]: ['ibu@08:00'] } }, { day, min: 10 * 60 }, 2, synced)) === '[]', '건너뜀은 놓침 아님');
ok(J(missedSlots(me, { day, min: 22 * 60 + 1 }, 2, synced)) === '["08:00","20:00"]', '두 시각');
ok(missedSlots(me, { day, min: 12 * 60 }, 2, synced).indexOf('09:00') < 0, '필요할 때 약 제외');
ok(J(missedSlots({ taking: ['x'], sched: { y: ['08:00'] } }, { day, min: 900 }, 2, synced)) === '[]', '약통에 없는 약 제외');
ok(J(missedSlots(null, { day, min: 900 }, 2, synced)) === '[]', '빈 기록');
ok(J(missedSlots({ taking: ['a'], sched: { a: ['25:00', 'x'] } }, { day, min: 1400 }, 2, synced)) === '[]', '이상한 시각 무시');
// 오프라인: 복용 시각 뒤로 기록이 한 번도 안 올라왔으면 30분 더
const old = { day, min: 7 * 60 };
ok(J(missedSlots(me, { day, min: 10 * 60 + 29 }, 2, old)) === '[]' && J(missedSlots(me, { day, min: 10 * 60 + 30 }, 2, old)) === '["08:00"]', '동기화 없으면 30분 더');
ok(J(missedSlots(me, { day, min: 10 * 60 + 30 }, 2, null)) === '["08:00"]', '동기화 시각 모름 → 30분 더 뒤 보냄');
// 본인 정시 알림 ±3분(11-04 5분마다 확인)
ok(J(dueNow(me, { day, min: 8 * 60 - 3 }).map((x) => x.key)) === '["ibu@08:00"]', '정시 -3분(먹은 met 빼고 한 장)');
ok(dueNow(me, { day, min: 8 * 60 + 4 }).length === 0 && dueNow(me, { day, min: 8 * 60 - 4 }).length === 0, '±4분은 아님');
ok(J(dueNow({ ...me, taken: {} }, { day, min: 8 * 60 }).map((x) => x.key)) === '["ibu@08:00,met@08:00"]', '같은 시각 두 약 한 장 · 앱 알림과 같은 key');
// 시간대 세 곳 + 서머타임 경계
let s = localNow(new Date('2026-11-02T15:30:00Z'), 'Asia/Seoul'); ok(s.day === '2026-11-03' && s.min === 30, '서울 날짜 넘어감 ' + J(s));
s = localNow(new Date('2026-11-01T05:30:00Z'), 'America/New_York'); ok(s.day === '2026-11-01' && s.min === 90, '뉴욕 서머타임 끝나기 전(EDT 01:30) ' + J(s));
s = localNow(new Date('2026-11-01T06:30:00Z'), 'America/New_York'); ok(s.day === '2026-11-01' && s.min === 90, '뉴욕 서머타임 끝난 뒤(EST 01:30 다시) ' + J(s));
s = localNow(new Date('2026-03-08T07:30:00Z'), 'America/New_York'); ok(s.min === 3 * 60 + 30, '뉴욕 서머타임 시작(02시 건너뜀) ' + J(s));
s = localNow(new Date('2026-10-25T00:30:00Z'), 'Europe/Madrid'); ok(s.day === '2026-10-25' && s.min === 2 * 60 + 30, '마드리드 서머타임 끝나기 전(CEST) ' + J(s));
s = localNow(new Date('2026-10-25T01:30:00Z'), 'Europe/Madrid'); ok(s.min === 2 * 60 + 30, '마드리드 서머타임 끝난 뒤(CET) ' + J(s));
s = localNow(new Date('2026-11-02T12:00:00Z'), 'Europe/Madrid'); ok(s.min === 13 * 60, '마드리드 겨울 UTC+1 ' + J(s));
ok(seoulNow(new Date('2026-11-02T00:00:00Z')).min === 9 * 60, '서울 UTC+9');
// 설정
ok(J(prefs({ tz: 'Mars/Base', wait: 7, qs: '25:00' })) === J({ tz: 'Asia/Seoul', lang: 'ko', wait: 2, qs: '22:00', qe: '07:00', dose: false, nm: null }), '틀린 설정은 기본값');
ok(prefs({ tz: 'America/New_York', wait: 3, qs: '09:00', qe: '17:00', dose: true }).tz === 'America/New_York', '설정 읽기');
// 쉬는 시간
ok(quiet(22 * 60) && quiet(6 * 60 + 59) && !quiet(7 * 60) && !quiet(21 * 60 + 59), '기본 쉬는 시간 22~07');
ok(quiet(10 * 60, '09:00', '17:00') && !quiet(18 * 60, '09:00', '17:00'), '낮 쉬는 시간(야간 근무)');
ok(!quiet(3 * 60, '00:00', '00:00'), '시작=끝이면 쉬는 시간 없음');
ok(stale('2026-10-28T00:00:00Z', new Date('2026-11-02T00:00:00Z')) && !stale('2026-11-01T00:00:00Z', new Date('2026-11-02T00:00:00Z')), '3일 기록 없음');
ok(slotWord('20:00') === '오후 8:00' && slotWord('08:05') === '오전 8:05' && slotWord('00:00') === '오전 12:00' && slotWord('12:30') === '오후 12:30', '시각 글');
const m = message('엄마', '20:00'); ok(!/이부|ibu/.test(m.body) && /체크 기록이 아직 없어요/.test(m.body) && /이미 드셨을 수도/.test(m.body), '가족 글: 약 이름 없음·단정 않음 ' + m.body);
ok(/\(엄마 시간\)/.test(message('엄마', '20:00', true).body), '가족 시간대 다르면 (엄마 시간)');
ok(doseMessage('08:00', ['ibu'], null).body === '오전 8:00 · 약 드실 시간이에요', '본인 글 기본: 약 이름 없음');
ok(doseMessage('08:00', ['ibu', 'met'], { ibu: '이부프로펜', met: '메트포르민' }).body === '오전 8:00 · 이부프로펜, 메트포르민 드실 시간이에요', '본인 글: 이름 켬');
// 다섯 말 × 가족/본인(11-03 — 알림 글은 받는 사람 말로)
const SW = { ko: '오후 8:00', en: '8:00 PM', es: '20:00', ja: '午後8:00', zh: '下午8:00' };
for (const L of ['ko', 'en', 'es', 'ja', 'zh']) {
  ok(slotWord('20:00', L) === SW[L], `시각 꼴 ${L} ${slotWord('20:00', L)}`);
  const f = message('엄마', '20:00', false, L), fo = message('엄마', '20:00', true, L);
  ok(f.body.includes(SW[L]) && f.body.includes('엄마') && !/[가-힣]{3,}/.test(f.body.replace(/엄마/g, '')) === (L !== 'ko') || L === 'ko', `가족 글 ${L}: ${f.body}`);
  ok(fo.body.length > f.body.length && fo.body.split('엄마').length === 3, `가족 글 다른 시간대 표시 ${L}: ${fo.body}`);
  const d0 = doseMessage('08:00', ['ibu'], null, L), d1 = doseMessage('08:00', ['ibu'], { ibu: 'Ibuprofen' }, L);
  ok(d0.body.includes(slotWord('08:00', L)) && !d0.body.includes('Ibuprofen') && d1.body.includes('Ibuprofen') && d0.acts.length === 2, `본인 글 ${L}: ${d0.body} / ${d1.body} / ${d0.acts}`);
  ok(L === 'ko' || !/[가-힣]/.test(d0.title + d0.body + d0.acts.join('')), `본인 글에 한국어 없음 ${L}`);
}
ok(prefs({ lang: 'fr' }).lang === 'ko' && prefs({ lang: 'ja' }).lang === 'ja', '언어 설정 읽기');
console.log(bad ? `✗ ${bad}개 실패` : `✓ 알림 판정 ${n}가지(서울·뉴욕·마드리드·서머타임 경계·다섯 말)`);

// 사본 맞춤: yak-family-check/logic.ts 는 첫 줄 주석만 다르고 정본과 같아야 한다
{
  const fs = await import('node:fs');
  const d = new URL('../server/supabase/functions/', import.meta.url);
  const a = fs.readFileSync(new URL('mn-push-check/modules/yak_logic.ts', d), 'utf8');
  const b = fs.readFileSync(new URL('yak-family-check/logic.ts', d), 'utf8').split('\n').slice(1).join('\n');
  if (a !== b) { console.error('✘ yak-family-check/logic.ts 가 정본(mn-push-check/modules/yak_logic.ts)과 다름'); process.exit(1); }
  console.log('✓ 판정 사본 = 정본');
}
process.exit(bad ? 1 : 0);
