// 길동무 판정 모듈(11-03 길동무 세션) — 푸시를 켠 기기(mn_push_subs app='gildongmu')의 계정만 · 판정은 gildongmu_logic.ts(순수 · 시험 _서버/시험_길동무푸시판정_1103.mjs)
import type { Module } from './types.ts';
import { decide, message, onceOf } from './gildongmu_logic.ts';

const mod: Module = {
  app: 'gildongmu',
  async run(ctx) {
    let n = 0;
    const subs = await ctx.sql`select distinct on (user_id) user_id, coalesce(tz, 'Asia/Seoul') as tz from public.mn_push_subs where app = 'gildongmu' order by user_id, last_ok desc nulls last`;
    if (!subs.length) return 0;
    const ids = subs.map((s: { user_id: string }) => s.user_id);
    const recs = await ctx.sql`select user_id, key, value from public.records where app = 'gildongmu' and user_id = any(${ids}) and key in ('gd.plans', 'gd.log', 'gd.temps')`;
    const by: Record<string, Record<string, unknown>> = {};
    for (const r of recs) (by[r.user_id] ||= {})[r.key] = ctx.parse(r.value);
    for (const s of subs) {
      const d = by[s.user_id] || {};
      for (const due of decide(ctx.now, s.tz, d['gd.plans'] as never, d['gd.log'] as never, d['gd.temps'] as never)) {
        const ok = await ctx.push(s.user_id, (l) => ({ ...message(due.kind, l), go: '#/', tag: 'gildongmu-' + due.kind }), onceOf(due));   /* slot ≤ 20자(체온은 시:분:초) */
        if (ok) n++;
      }
    }
    return n;
  },
};
export default mod;
