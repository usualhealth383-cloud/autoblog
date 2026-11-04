// 소아 판정 모듈(11-03 소아 세션) — 푸시를 켠 기기(mn_push_subs app='kids')의 계정만 · 판정은 kids_logic.ts(순수 · 시험 _서버/시험_소아푸시판정_1103.mjs)
//   읽는 열쇠: kh.noti(앱 알림판 켬·시각) · kh.kids(아이 목록) · kh.vacdue@<아이>(앱이 계산한 다음 맞을 날들) · kh.rx@<아이>(처방약 칸)
import type { Module } from './types.ts';
import { decide, message, onceOf, 가기, type KidsData } from './kids_logic.ts';

const mod: Module = {
  app: 'kids',
  async run(ctx) {
    let n = 0;
    const subs = await ctx.sql`select distinct on (user_id) user_id, coalesce(tz, 'Asia/Seoul') as tz from public.mn_push_subs where app = 'kids' order by user_id, last_ok desc nulls last`;
    if (!subs.length) return 0;
    const ids = subs.map((s: { user_id: string }) => s.user_id);
    const recs = await ctx.sql`select user_id, key, value from public.records where app = 'kids' and user_id = any(${ids})
      and (key in ('kh.noti', 'kh.kids') or key like 'kh.vacdue@%' or key like 'kh.rx@%')`;
    const by: Record<string, KidsData> = {};
    for (const r of recs) {
      const d = (by[r.user_id] ||= { vacdue: {}, rx: {} });
      const v = ctx.parse(r.value);
      if (r.key === 'kh.noti') d.noti = v as never;
      else if (r.key === 'kh.kids') d.kids = v as never;
      else if (r.key.startsWith('kh.vacdue@')) d.vacdue![r.key.slice(10)] = v as never;
      else if (r.key.startsWith('kh.rx@')) d.rx![r.key.slice(6)] = v as never;
    }
    for (const s of subs) {
      const d = by[s.user_id]; if (!d) continue;
      for (const due of decide(ctx.now, s.tz, d)) {
        const ok = await ctx.push(s.user_id, (l) => ({ ...message(due.kind, l), go: 가기[due.kind], tag: 'kids-' + due.kind }), onceOf(due));
        if (ok) n++;
      }
    }
    return n;
  },
};
export default mod;
