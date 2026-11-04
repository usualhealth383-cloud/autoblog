// 소아(우리 집 소아과) 판정 — 11-04 Main 「앱을 닫아도 알림」. 해열제를 «다시 먹일 수 있는 시각»에 한 번(성분 이름만 · 양·아이 이름 없음).
// 기록: records(app='kids', key='kh.remind@<아이>') = { on, next:{acet?,ibu?}(ISO), tz, lang } — 형식은 kg_logic.ts 머리.
// 받는 사람: 기록 주인 + 공동 보호자(care_links app='kids' role='coparent' 수락·안 끊음). 끈 사람(on:false)은 안 감.
import type { Module } from './types.ts';
import { kidsDue, kidsMessage, KIDS_PER_DAY, pickLang } from './kg_logic.ts';

const mod: Module = {
  app: 'kids',
  async run(ctx) {
    let n = 0;
    const rows = await ctx.sql`
      select r.user_id, r.key, r.value,
             coalesce((select array_agg(l.guardian_id) from public.care_links l
                        where l.app = 'kids' and l.role = 'coparent' and l.patient_id = r.user_id
                          and l.accepted_at is not null and l.revoked_at is null and l.guardian_id is not null), '{}') as co
        from public.records r
       where r.app = 'kids' and r.key like 'kh.remind@%'`;
    for (const x of rows) {
      const rem = ctx.parse(x.value);
      for (const d of kidsDue(rem, ctx.now)) {
        const kind = ('kids-fever:' + String(x.key).slice(10)).slice(0, 80);   // mn_push_sent.kind 80자
        for (const to of [x.user_id, ...((x.co as string[]) || [])]) {
          if (await ctx.sentCount(to, kind, d.day) >= KIDS_PER_DAY) continue;   // 아이 한 명 · 받는 사람 한 명당 하루 상한
          const ok = await ctx.push(to, (l) => ({ ...kidsMessage(d.ing, rem?.lang ? pickLang(rem.lang) : l), kind: 'kids-fever', tag: kind + ':' + d.ing, go: '#/' }),
            { kind, day: d.day, slot: d.slot });
          if (ok) n++;
        }
      }
    }
    return n;
  },
};
export default mod;
