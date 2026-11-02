// 공용 푸시 약지도 모듈 시험 — node --experimental-strip-types yakjido/tests/push_module.mjs
import mod from '../server/supabase/functions/mn-push-check/modules/yakjido.ts';
let bad = 0, n = 0; const ok = (c, m) => { n++; if (!c) { bad++; console.log('✗', m); } };
const day = '2026-11-03';
const me = (taken) => ({ v: JSON.stringify({ taking: ['ibu'], sched: { ibu: ['08:00', '20:00'] }, taken: { [day]: taken } }) });
const fam = (o) => ({ v: JSON.stringify(o) });
function run(rowsSelf, rowsFam, nowISO, sentBefore = 0) {
  const sql = (strings) => { const q = strings.join('?'); return Promise.resolve(q.includes('yak_family_links') ? rowsFam : rowsSelf); };
  const pushed = [], once = new Set();
  const ctx = { sql, now: new Date(nowISO), parse: (v) => { try { return JSON.parse(v.v); } catch { return null; } },
    sentCount: async () => sentBefore,
    push: async (u, make, o) => { const k = u + o.kind + o.day + o.slot; if (once.has(k)) return false; once.add(k); pushed.push({ u, p: make('ko'), o }); return true; } };
  return mod.run(ctx).then((c) => ({ c, pushed }));
}
// 본인 정시: 서울 08:03 (UTC 23:03 전날)
let r = await run([{ user_id: 'A', fam: fam({ tz: 'Asia/Seoul', dose: true, lang: 'en' }), me: me([]) }], [], '2026-11-02T23:03:00Z');
ok(r.c === 1 && r.pushed[0].p.body === '8:00 AM · time to take your medicine' && r.pushed[0].p.key === 'ibu@08:00' && r.pushed[0].p.acts[0] === 'Taken', '본인 정시 영어 ' + JSON.stringify(r.pushed[0]?.p));
r = await run([{ user_id: 'A', fam: fam({ tz: 'Asia/Seoul', dose: false }), me: me([]) }], [], '2026-11-02T23:03:00Z');
ok(r.c === 0, '정시 알림 끈 분은 안 보냄');
r = await run([{ user_id: 'A', fam: fam({ tz: 'America/New_York', dose: true }), me: me([]) }], [], '2026-11-02T23:03:00Z');
ok(r.c === 0, '뉴욕 사람은 뉴욕 08:00 에(서울 08:03 엔 안 보냄)');
// 가족: 서울 10:15 (UTC 01:15), 08:00 놓침, 기록은 10:00 에 올라옴
const link = (extra = {}) => ({ id: 'L1', member_id: 'B', owner_label: '엄마', muted_until: null, value: me([]), updated_at: '2026-11-03T01:00:00Z', fam: fam({ tz: 'Asia/Seoul', wait: 2 }), mfam: fam({ tz: 'Asia/Seoul', lang: 'ja' }), ...extra });
r = await run([], [link()], '2026-11-03T01:15:00Z');
ok(r.c === 1 && r.pushed[0].u === 'B' && /午前8:00/.test(r.pushed[0].p.body) && r.pushed[0].o.kind === 'family:L1', '가족 일본어 ' + r.pushed[0]?.p.body);
r = await run([], [link({ muted_until: '2026-11-03T15:00:00Z' })], '2026-11-03T01:15:00Z');
ok(r.c === 0, '오늘만 끄기');
r = await run([], [link()], '2026-11-03T01:15:00Z', 2);
ok(r.c === 0, '하루 2번 상한');
r = await run([], [link({ fam: fam({ tz: 'Asia/Seoul', qs: '09:00', qe: '18:00' }) })], '2026-11-03T01:15:00Z');
ok(r.c === 0, '쉬는 시간');
r = await run([], [link({ updated_at: '2026-10-28T00:00:00Z' })], '2026-11-03T01:15:00Z');
ok(r.c === 0, '3일 넘게 기록 없음');
r = await run([], [link({ mfam: fam({ tz: 'America/New_York', lang: 'en' }) })], '2026-11-03T01:15:00Z');
ok(r.c === 1 && /Mom|엄마/.test(r.pushed[0].p.body) && /'s time/.test(r.pushed[0].p.body), '가족 다른 시간대 표시 ' + r.pushed[0]?.p.body);
console.log(bad ? `✗ ${bad}개 실패` : `✓ 공용 푸시 약지도 모듈 ${n}가지`);
process.exit(bad ? 1 : 0);
