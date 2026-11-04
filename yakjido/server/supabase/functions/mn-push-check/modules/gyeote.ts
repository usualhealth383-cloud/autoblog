// 곁에 판정 모듈 — ① 11-03 곁에 세션(판정 gyeote_logic.ts · 시험 yakjido/tests/gyeote_push.mjs)
//   저녁 마음 체크(정한 시간 · 오늘 배터리·마음을 아직 안 남겼으면) · 이번 주 마음 카드(정한 요일·시간) · 다시 재 볼 날(낮에만 · 하루 한 번)
//   알림 설정(gyeote_pushset)이 서버에 없으면 ①은 보내지 않는다. 알림 글에는 마음 상태·검사 이름을 담지 않는다.
// ② 11-04 복약 시각(kg_logic.ts · 시험 yakjido/tests/push_kids_gyeote.mjs) — gy.remind = {on, times:['HH:MM'], tz, lang} → ±3분 「약 드실 시간이에요」(약 이름 없음)
import type { Module } from './types.ts';
import { due, text } from './gyeote_logic.ts';
import { gyeoteDue, gyeoteMessage, pickLang } from './kg_logic.ts';
const KEYS = ['gyeote_pushset', 'gyeote_battery', 'gyeote_moods', 'gyeote_retest'];
const mod: Module = {
  app: 'gyeote',
  async run(ctx) {
    let n = 0;
    const rows = await ctx.sql`
      select r.user_id, r.key, r.value from public.records r
       where r.app = 'gyeote' and r.key in ${ctx.sql(KEYS)}
         and r.user_id in (select distinct s.user_id from public.mn_push_subs s where s.app = 'gyeote')`;
    const by = new Map<string, Record<string, unknown>>();
    for (const x of rows) { const o = by.get(x.user_id) || {}; o[x.key] = ctx.parse(x.value); by.set(x.user_id, o); }
    for (const [uid, o] of by) {
      const d = due(o.gyeote_pushset as never, o.gyeote_battery as never, o.gyeote_moods as never, o.gyeote_retest as never, ctx.now);
      for (const it of d.list) {
        if (it.kind === 'retest' && await ctx.sentCount(uid, 'retest', d.day) >= 1) continue;
        if (await ctx.push(uid, (l) => ({ ...text(it.kind, l), kind: it.kind, day: d.day }), { kind: it.kind, day: d.day, slot: it.slot })) n++;
      }
    }
    // ② 복약 시각
    const rem = await ctx.sql`select user_id, value from public.records where app = 'gyeote' and key = 'gy.remind'`;
    for (const x of rem) {
      const v = ctx.parse(x.value);
      for (const dd of gyeoteDue(v, ctx.now)) {
        const ok = await ctx.push(x.user_id, (l) => ({ ...gyeoteMessage(v?.lang ? pickLang(v.lang) : l), kind: 'gyeote-dose', tag: 'gyeote-dose@' + dd.slot, go: '#/' }),
          { kind: 'gyeote-dose', day: dd.day, slot: dd.slot });
        if (ok) n++;
      }
    }
    return n;
  },
};
export default mod;
