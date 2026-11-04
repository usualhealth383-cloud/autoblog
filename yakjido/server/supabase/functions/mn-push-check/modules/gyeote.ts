// 곁에 판정 — 11-04 Main 「앱을 닫아도 알림」. 복약 시각 ±3분에 「약 드실 시간이에요」(약 이름 없음).
// 기록: records(app='gyeote', key='gy.remind') = { on, times:['HH:MM',…], tz, lang } — 형식은 kg_logic.ts 머리. 끈 사람(on:false)은 안 감.
import type { Module } from './types.ts';
import { gyeoteDue, gyeoteMessage, pickLang } from './kg_logic.ts';

const mod: Module = {
  app: 'gyeote',
  async run(ctx) {
    let n = 0;
    const rows = await ctx.sql`select user_id, value from public.records where app = 'gyeote' and key = 'gy.remind'`;
    for (const x of rows) {
      const rem = ctx.parse(x.value);
      for (const d of gyeoteDue(rem, ctx.now)) {
        const ok = await ctx.push(x.user_id, (l) => ({ ...gyeoteMessage(rem?.lang ? pickLang(rem.lang) : l), kind: 'gyeote-dose', tag: 'gyeote-dose@' + d.slot, go: '#/' }),
          { kind: 'gyeote-dose', day: d.day, slot: d.slot });
        if (ok) n++;
      }
    }
    return n;
  },
};
export default mod;
