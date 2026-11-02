// 사본 — 정본은 mn-push-check/modules/yak_logic.ts (배포는 함수 폴더 안 파일만 실린다). 예약을 mn-push-check 로 바꾸면 이 함수는 은퇴. 고칠 땐 정본을 고치고 여기로 복사(tests/family_logic.mjs 가 둘이 같은지 본다).
// 약지도 알림 판정(순수 함수 · 시험: yakjido/tests/family_logic.mjs) — 11-03 사람마다 «자기 시간대»로
// 기록 꼴: yakjido.me.v1 = taking[] · sched{id:["HH:MM"]} · prn{id:true} · taken{"YYYY-MM-DD":["id@HH:MM"]} · skipped{…}
//          yakjido.fam.v1 = { tz:"Asia/Seoul", lang:"ko"|"en"|"es"|"ja"|"zh"(앱 언어 — 알림 글은 «받는 사람» 말로), wait:1|2|3, qs:"22:00", qe:"07:00", dose:true(앱을 닫아도 정시 알림), nm:{id:"이름"}(약 이름 보이기를 켠 경우만) }
export const PER_DAY = 2;              // 가족 한 분당 하루 2번까지
export const STALE_DAYS = 3;           // 본인 기록이 3일 넘게 안 올라오면 가족 알림을 보내지 않는다
export const NOSYNC_EXTRA = 30;        // 복용 시각 뒤로 기록이 한 번도 안 올라왔으면 30분 더 기다린다(오프라인 체크 오알림 줄이기)
export const DOSE_WIN = 7;             // 본인 정시 알림: 복용 시각 ±7분 안의 확인 때 한 번(15분마다 확인)
export const DEF = { tz: 'Asia/Seoul', lang: 'ko', wait: 2, qs: '22:00', qe: '07:00' };
export const LANGS = ['ko', 'en', 'es', 'ja', 'zh'];

const HM = /^([01]\d|2[0-3]):([0-5]\d)$/;
export const toMin = (t: string) => { const m = HM.exec(String(t)); return m ? Number(m[1]) * 60 + Number(m[2]) : -1; };
export function validTz(tz: unknown) { try { if (typeof tz !== 'string' || !tz) return false; new Intl.DateTimeFormat('en-US', { timeZone: tz }); return true; } catch { return false; } }
/** 설정 읽기 — 틀린 값은 기본값 */
export function prefs(f: any) {
  const o = f && typeof f === 'object' ? f : {};
  return { tz: validTz(o.tz) ? o.tz : DEF.tz, lang: LANGS.includes(o.lang) ? o.lang : DEF.lang, wait: [1, 2, 3].includes(Number(o.wait)) ? Number(o.wait) : DEF.wait,
    qs: HM.test(o.qs) ? o.qs : DEF.qs, qe: HM.test(o.qe) ? o.qe : DEF.qe, dose: o.dose === true,
    nm: o.nm && typeof o.nm === 'object' ? o.nm : null };
}
/** 그 시간대의 날짜·분 */
export function localNow(d: Date, tz: string) {
  const p = Object.fromEntries(new Intl.DateTimeFormat('en-CA', { timeZone: tz, year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', hourCycle: 'h23' })
    .formatToParts(d).map((x) => [x.type, x.value]));
  return { day: `${p.year}-${p.month}-${p.day}`, min: Number(p.hour) * 60 + Number(p.minute) };
}
export const seoulNow = (d: Date) => localNow(d, 'Asia/Seoul');
/** 쉬는 시간인가(자정을 넘는 구간 포함 · 시작=끝이면 쉬는 시간 없음) */
export function quiet(min: number, qs = DEF.qs, qe = DEF.qe) {
  const s = toMin(qs), e = toMin(qe); if (s < 0 || e < 0 || s === e) return false;
  return s < e ? (min >= s && min < e) : (min >= s || min < e);
}
export const stale = (updatedAt: Date | string | null, now: Date) => !updatedAt || now.getTime() - new Date(updatedAt).getTime() > STALE_DAYS * 864e5;

function slots(me: any, day: string) {
  if (!me || typeof me !== 'object') return [] as { id: string; t: string; m: number; done: boolean }[];
  const taking: string[] = Array.isArray(me.taking) ? me.taking.filter((x: unknown) => typeof x === 'string') : [];
  const sched = me.sched && typeof me.sched === 'object' ? me.sched : {};
  const prn = me.prn && typeof me.prn === 'object' ? me.prn : {};
  const took = new Set<string>(Array.isArray(me.taken?.[day]) ? me.taken[day] : []);
  const skip = new Set<string>(Array.isArray(me.skipped?.[day]) ? me.skipped[day] : []);
  const out: { id: string; t: string; m: number; done: boolean }[] = [];
  for (const id of taking) {
    if (prn[id]) continue;
    for (const t of (Array.isArray(sched[id]) ? sched[id] : [])) {
      const m = toMin(String(t)); if (m < 0) continue;
      const k = `${id}@${t}`; out.push({ id, t: String(t), m, done: took.has(k) || skip.has(k) });
    }
  }
  return out;
}
/** 가족 알림: 오늘 놓친 복용 시각들(이른 것부터). syncedAt = 본인 기록이 마지막으로 올라온 때(그 사람 시간대의 날짜·분) */
export function missedSlots(me: any, now: { day: string; min: number }, waitH = DEF.wait, syncedAt?: { day: string; min: number } | null): string[] {
  const out = new Set<string>();
  for (const s of slots(me, now.day)) {
    if (s.done) continue;
    const synced = !!syncedAt && (syncedAt.day > now.day || (syncedAt.day === now.day && syncedAt.min >= s.m));
    if (now.min < s.m + waitH * 60 + (synced ? 0 : NOSYNC_EXTRA)) continue;
    out.add(s.t);
  }
  return [...out].sort();
}
/** 본인 정시 알림: 지금(±7분) 드실 약 — 같은 시각은 한 장. key 는 앱 안 알림과 같은 꼴(id@HH:MM,…)이라 같은 tag 로 겹치지 않는다 */
export function dueNow(me: any, now: { day: string; min: number }) {
  const by: Record<string, string[]> = {};
  for (const s of slots(me, now.day)) { if (s.done || Math.abs(now.min - s.m) > DOSE_WIN) continue; (by[s.t] ||= []).push(s.id); }
  return Object.entries(by).sort().map(([t, ids]) => ({ t, ids, key: ids.map((id) => `${id}@${t}`).join(',') }));
}
/** 시각 글 — 그 말 꼴: ko 「오후 8:00」 · en "8:00 PM" · es "20:00" · ja 「午後8:00」 · zh 「下午8:00」 */
export function slotWord(t: string, lang = 'ko') {
  const m = toMin(t); const h = Math.floor(m / 60), mm = String(m % 60).padStart(2, '0'), h12 = h % 12 || 12, pm = h >= 12;
  if (lang === 'en') return `${h12}:${mm} ${pm ? 'PM' : 'AM'}`;
  if (lang === 'es') return `${String(h).padStart(2, '0')}:${mm}`;
  if (lang === 'ja') return `${pm ? '午後' : '午前'}${h12}:${mm}`;
  if (lang === 'zh') return `${pm ? '下午' : '上午'}${h12}:${mm}`;
  return `${pm ? '오후' : '오전'} ${h12}:${mm}`;
}
/** 가족 알림 글 — «가족(받는 사람)» 말로 · 약 이름 없이 · 단정하지 않게. 가족 시간대가 다르면 「(엄마 시간)」 */
export function message(label: string, slot: string, otherTz = false, lang = 'ko') {
  const t = slotWord(slot, lang);
  const B: Record<string, [string, string]> = {
    ko: ['약지도 가족 알림', `${label} · ${t}${otherTz ? ` (${label} 시간)` : ''} 약 체크 기록이 아직 없어요. 이미 드셨을 수도 있으니 한 번 연락해 보세요.`],
    en: ['Yakjido family alert', `${label} · no dose tick yet for ${t}${otherTz ? ` (${label}'s time)` : ''}. They may have taken it already — maybe check in with them.`],
    es: ['Aviso familiar de Yakjido', `${label} · todavía no hay registro de la toma de las ${t}${otherTz ? ` (hora de ${label})` : ''}. Puede que ya la haya tomado; quizá convenga llamar.`],
    ja: ['ヤクジド 家族の通知', `${label} · ${t}${otherTz ? `(${label}の時刻)` : ''}のお薬チェックの記録がまだありません。すでに飲んでいるかもしれないので、一度連絡してみてください。`],
    zh: ['药地图 家人提醒', `${label} · ${t}${otherTz ? `（${label}当地时间）` : ''}的服药打勾记录还没有。可能已经服用了，不妨联系一下。`],
  };
  const [title, body] = B[lang] || B.ko; return { title, body };
}
/** 본인 정시 알림 글 — 본인 말로 · 약 이름은 본인이 켰을 때만(nm) · 알림 단추 글도 같은 말 */
export function doseMessage(t: string, ids: string[], nm: Record<string, string> | null, lang = 'ko') {
  const names = nm ? ids.map((id) => typeof nm[id] === 'string' ? nm[id].slice(0, 30) : '').filter(Boolean) : [];
  const w = slotWord(t, lang), n = names.join(', ');
  const B: Record<string, [string, string, string, string]> = {
    ko: ['약지도 · 약 드실 시간', n ? `${w} · ${n} 드실 시간이에요` : `${w} · 약 드실 시간이에요`, '먹었어요', '10분 뒤 다시'],
    en: ['Yakjido · Time for your medicine', n ? `${w} · time to take ${n}` : `${w} · time to take your medicine`, 'Taken', 'In 10 min'],
    es: ['Yakjido · Hora de su medicamento', n ? `${w} · hora de tomar ${n}` : `${w} · hora de tomar su medicamento`, 'Tomado', 'En 10 min'],
    ja: ['ヤクジド · お薬の時間', n ? `${w} · ${n}を飲む時間です` : `${w} · お薬の時間です`, '飲みました', '10分後にもう一度'],
    zh: ['药地图 · 服药时间', n ? `${w} · 该服用${n}了` : `${w} · 该服药了`, '已服用', '10分钟后再提醒'],
  };
  const [title, body, took, later] = B[lang] || B.ko; return { title, body, acts: [took, later] };
}
