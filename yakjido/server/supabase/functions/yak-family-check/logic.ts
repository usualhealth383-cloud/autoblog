// 약지도 가족 알림 — 놓침 판정(순수 함수 · 시험: yakjido/tests/family_logic.mjs)
// 기록 꼴은 앱의 yakjido.me.v1 그대로: taking[] · sched{id:["HH:MM"]} · prn{id:true} · taken{"YYYY-MM-DD":["id@HH:MM"]} · skipped{…}
export const GRACE_MIN = 120;          // 복용 시각 2시간 뒤
export const PER_DAY = 2;              // 한 가족에게 하루 2번까지
export const QUIET = [22 * 60, 7 * 60]; // 밤 10시 ~ 아침 7시에는 보내지 않는다
export const STALE_DAYS = 3;           // 본인 기록이 3일 넘게 안 올라오면(앱을 안 씀) 보내지 않는다

export function seoulNow(d: Date) {
  const p = Object.fromEntries(new Intl.DateTimeFormat('en-CA', { timeZone: 'Asia/Seoul', year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', hourCycle: 'h23' })
    .formatToParts(d).map((x) => [x.type, x.value]));
  return { day: `${p.year}-${p.month}-${p.day}`, min: Number(p.hour) * 60 + Number(p.minute) };
}
const toMin = (t: string) => { const m = /^([01]\d|2[0-3]):([0-5]\d)$/.exec(t); return m ? Number(m[1]) * 60 + Number(m[2]) : -1; };

/** 오늘 놓친 복용 시각들(이른 것부터, 같은 시각은 하나로). 약 이름은 돌려주지 않는다. */
export function missedSlots(me: any, now: { day: string; min: number }): string[] {
  if (!me || typeof me !== 'object') return [];
  const taking: string[] = Array.isArray(me.taking) ? me.taking.filter((x: unknown) => typeof x === 'string') : [];
  const sched = me.sched && typeof me.sched === 'object' ? me.sched : {};
  const prn = me.prn && typeof me.prn === 'object' ? me.prn : {};
  const took = new Set<string>(Array.isArray(me.taken?.[now.day]) ? me.taken[now.day] : []);
  const skip = new Set<string>(Array.isArray(me.skipped?.[now.day]) ? me.skipped[now.day] : []);
  const out = new Set<string>();
  for (const id of taking) {
    if (prn[id]) continue;
    const times = Array.isArray(sched[id]) ? sched[id] : [];
    for (const t of times) {
      const m = toMin(String(t)); if (m < 0) continue;
      if (now.min < m + GRACE_MIN) continue;
      const k = `${id}@${t}`;
      if (took.has(k) || skip.has(k)) continue;
      out.add(String(t));
    }
  }
  return [...out].sort();
}
export const quiet = (min: number) => min >= QUIET[0] || min < QUIET[1];
export const stale = (updatedAt: Date | string | null, now: Date) => !updatedAt || now.getTime() - new Date(updatedAt).getTime() > STALE_DAYS * 864e5;
/** 「오후 8:00」 */
export function slotWord(t: string) { const m = toMin(t); const h = Math.floor(m / 60), mm = String(m % 60).padStart(2, '0'); return `${h < 12 ? '오전' : '오후'} ${h % 12 || 12}:${mm}`; }
/** 알림 글 — 약 이름 없이, 단정하지 않게(「아직 체크가 없어요」) */
export function message(label: string, slot: string) {
  return { title: '약지도 가족 알림', body: `${label} · ${slotWord(slot)} 약 체크가 아직 없어요. 한 번 연락해 보세요.` };
}
