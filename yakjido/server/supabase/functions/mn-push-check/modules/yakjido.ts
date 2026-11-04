// 약지도 판정 — ① 본인 정시 알림(fam.v1 dose:true) ② 가족 놓침 알림(허락된 연결만). 판정은 yak-family-check/logic.ts 와 같은 것(시험 60가지)
import type { Module } from './types.ts';
import { missedSlots, dueNow, localNow, quiet, stale, message, doseMessage, prefs, PER_DAY } from './yak_logic.ts';

const mod: Module = {
  app: 'yakjido',
  async run(ctx) {
    let n = 0;
    const self = await ctx.sql`
      select f.user_id, f.value as fam, m.value as me
        from public.records f join public.records m on m.user_id = f.user_id and m.app = 'yakjido' and m.key = 'yakjido.me.v1'
       where f.app = 'yakjido' and f.key = 'yakjido.fam.v1'`;
    for (const x of self) {
      const raw = ctx.parse(x.fam), pf = prefs(raw); if (!pf.dose) continue;
      const now = localNow(ctx.now, pf.tz);
      for (const d of dueNow(ctx.parse(x.me), now)) {
        const ok = await ctx.push(x.user_id, (l) => ({ ...doseMessage(d.t, d.ids, pf.nm, raw?.lang ? pf.lang : l), kind: 'dose', key: d.key, day: now.day, tag: d.key }),
          { kind: 'dose', day: now.day, slot: d.t });
        if (ok) n++;
      }
    }
    const rows = await ctx.sql`
      select l.id, l.member_id, l.owner_label, l.muted_until, r.value, r.updated_at, f.value as fam, mf.value as mfam
        from public.yak_family_links l
        join public.records r on r.user_id = l.owner_id and r.app = 'yakjido' and r.key = 'yakjido.me.v1'
        left join public.records f on f.user_id = l.owner_id and f.app = 'yakjido' and f.key = 'yakjido.fam.v1'
        left join public.records mf on mf.user_id = l.member_id and mf.app = 'yakjido' and mf.key = 'yakjido.fam.v1'
       where l.member_id is not null and l.approved_at is not null and l.ended_at is null`;
    for (const x of rows) {
      if (x.muted_until && new Date(x.muted_until) > ctx.now) continue;
      if (stale(x.updated_at, ctx.now)) continue;
      const pf = prefs(ctx.parse(x.fam)), now = localNow(ctx.now, pf.tz);
      if (quiet(now.min, pf.qs, pf.qe)) continue;
      const slots = missedSlots(ctx.parse(x.value), now, pf.wait, x.updated_at ? localNow(new Date(x.updated_at), pf.tz) : null);
      if (!slots.length) continue;
      const kind = 'family:' + x.id;
      if (await ctx.sentCount(x.member_id, kind, now.day) >= PER_DAY) continue;
      const mraw = ctx.parse(x.mfam), mp = prefs(mraw), other = !!mraw && mp.tz !== pf.tz;
      for (const s of slots) {
        const ok = await ctx.push(x.member_id, (l) => ({ ...message(String(x.owner_label), s, other, mraw?.lang ? mp.lang : l), kind: 'family', go: '#/notify?fam=1', tag: 'yakjido-family-' + x.id }),
          { kind, day: now.day, slot: s });
        if (ok) { n++; break; }
      }
    }
    return n;
  },
};
export default mod;
