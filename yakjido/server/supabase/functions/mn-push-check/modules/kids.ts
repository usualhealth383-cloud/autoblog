// 소아 판정 모듈 — ① 11-03 소아 세션(푸시를 켠 기기의 계정 · 판정 kids_logic.ts · 시험 _서버/시험_소아푸시판정_1103.mjs)
//   읽는 열쇠: kh.noti(앱 알림판 켬·시각) · kh.kids(아이 목록) · kh.vacdue@<아이>(앱이 계산한 다음 맞을 날들) · kh.rx@<아이>(처방약 칸)
// ② 11-04 해열제 「다시 먹일 수 있는 시각」(kg_logic.ts · 시험 yakjido/tests/push_kids_gyeote.mjs) — kh.remind@<아이> = {on, next:{acet,ibu}(ISO), tz, lang}
//   받는 사람 = 기록 주인 + 공동 보호자(care_links app='kids' role='coparent' 수락·안 끊음). 성분 이름만(양·아이 이름 없음).
//   같은 사람에게 이번 확인에 해열제 알림이 갔으면 처방약(rx) 알림은 다음 확인(5분 뒤)으로 미룬다 — 같은 때 두 장 가지 않게.
import type { Module } from './types.ts';
import { decide, message, onceOf, 가기, type KidsData } from './kids_logic.ts';
import { kidsDue, kidsMessage, KIDS_PER_DAY, pickLang } from './kg_logic.ts';

const mod: Module = {
  app: 'kids',
  async run(ctx) {
    let n = 0;
    const 보냄 = new Set<string>();   // 이번 확인에 해열제 알림을 받은 사람
    // ② 해열제
    const rem = await ctx.sql`
      select r.user_id, r.key, r.value,
             coalesce((select array_agg(l.guardian_id) from public.care_links l
                        where l.app = 'kids' and l.role = 'coparent' and l.patient_id = r.user_id
                          and l.accepted_at is not null and l.revoked_at is null and l.guardian_id is not null), '{}') as co
        from public.records r
       where r.app = 'kids' and r.key like 'kh.remind@%'`;
    for (const x of rem) {
      const v = ctx.parse(x.value);
      for (const d of kidsDue(v, ctx.now)) {
        const kind = ('kids-fever:' + String(x.key).slice(10)).slice(0, 80);   // mn_push_sent.kind 80자
        for (const to of [x.user_id, ...((x.co as string[]) || [])]) {
          if (await ctx.sentCount(to, kind, d.day) >= KIDS_PER_DAY) continue;   // 아이 한 명 · 받는 사람 한 명당 하루 상한
          const ok = await ctx.push(to, (l) => ({ ...kidsMessage(d.ing, v?.lang ? pickLang(v.lang) : l), kind: 'kids-fever', tag: kind + ':' + d.ing, go: '#/' }),
            { kind, day: d.day, slot: d.slot });
          if (ok) { n++; 보냄.add(to); }
        }
      }
    }
    // ① 예방접종·처방약(11-03 그대로)
    const subs = await ctx.sql`select distinct on (user_id) user_id, coalesce(tz, 'Asia/Seoul') as tz from public.mn_push_subs where app = 'kids' order by user_id, last_ok desc nulls last`;
    if (!subs.length) return n;
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
        if (due.kind === 'rx' && 보냄.has(s.user_id)) continue;   // 해열제 알림과 같은 때 두 장 가지 않게(rx 는 2시간 창이라 다음 확인에 감)
        const ok = await ctx.push(s.user_id, (l) => ({ ...message(due.kind, l), go: 가기[due.kind], tag: 'kids-' + due.kind }), onceOf(due));
        if (ok) n++;
      }
    }
    return n;
  },
};
export default mod;
