// 소아(우리 집 소아과) 푸시 판정(순수 함수 · 11-03 소아 세션) — 서버에 동기화된 kh.* 만 본다
//   vac7  예방접종 일주일 전 — 아이 누구든 「다음 맞을 날」이 오늘+7 이면, 설정 시각(기본 09:00)부터 2시간 안에 한 번
//   vac1  예방접종 전날      — 「다음 맞을 날」이 내일이면, 설정 시각(기본 19:00)부터 2시간 안에 한 번
//   rx    처방약 먹일 시간   — 먹이는 중인 처방약(시작일 ≤ 오늘 < 시작일+일수)이 있고 오늘 칸을 다 채우지 않았으면, 설정 시각(기본 08:00 · 기본 꺼짐)부터 2시간 안에 한 번
//   「다음 맞을 날」은 앱이 계산해 올린 kh.vacdue@<아이>(앱 nextVac 과 같은 규칙: 맞은 칸·나이 지난 칸·해마다 칸·고른 백신에 없는 칸 뺌) — 서버가 접종표를 따로 들지 않는다(두 곳 규칙이 갈라지지 않게)
//   켬·시각은 앱 알림판 설정을 앱이 kh.noti 로 올린 것. 없으면 앱 기본값(vac7·vac1 켬, rx 끔)
//   잠금화면 글 — 아이 이름·백신 이름·약 이름을 넣지 않는다
export type NotiSet = Record<string, { on?: boolean; t?: string }>;
export type Kid = { id?: string };
export type VacDue = { n?: string; d?: string };
export type Rx = { name?: string; perDay?: number; days?: number; start?: string; done?: Record<string, unknown> };
export type KidsData = { noti?: NotiSet | null; kids?: Kid[] | null; vacdue?: Record<string, VacDue[] | null>; rx?: Record<string, Rx[] | null> };
export type Due = { kind: 'vac7' | 'vac1' | 'rx'; slot: string };
const 기본: Record<Due['kind'], { on: boolean; t: string }> = { vac7: { on: true, t: '09:00' }, vac1: { on: true, t: '19:00' }, rx: { on: false, t: '08:00' } };
const 날 = (s: unknown): s is string => typeof s === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(s);
export function localParts(d: Date, tz: string) {
  let z = tz; try { new Intl.DateTimeFormat('en-US', { timeZone: z }); } catch { z = 'Asia/Seoul'; }
  const p = Object.fromEntries(new Intl.DateTimeFormat('en-CA', { timeZone: z, year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', hourCycle: 'h23' })
    .formatToParts(d).map((x) => [x.type, x.value]));
  return { day: `${p.year}-${p.month}-${p.day}`, min: Number(p.hour) * 60 + Number(p.minute) };
}
export function addDays(day: string, n: number) { const d = new Date(day + 'T12:00:00Z'); d.setUTCDate(d.getUTCDate() + n); return d.toISOString().slice(0, 10); }
function 날차(a: string, b: string) { return Math.round((Date.parse(a + 'T12:00:00Z') - Date.parse(b + 'T12:00:00Z')) / 864e5); }
export function 설정값(noti: NotiSet | null | undefined, k: Due['kind']) {
  const o = (noti && typeof noti === 'object' && noti[k]) || {};
  return { on: 'on' in o ? !!o.on : 기본[k].on, t: typeof o.t === 'string' && /^\d{2}:\d{2}$/.test(o.t) ? o.t : 기본[k].t };
}
function 때됨(min: number, t: string) { const [h, m] = t.split(':').map(Number); const s = h * 60 + m; return min >= s && min < s + 120; }
/* 앱 rxAll · 처방상태 와 같은 거르기·셈 */
export function 먹이는중(x: Rx, 오늘: string) {
  if (!x || !x.name || !(x.perDay! >= 1 && x.perDay! <= 4) || !(x.days! >= 1 && x.days! <= 30) || !날(x.start)) return false;
  const 째 = 날차(오늘, x.start) + 1;
  if (째 < 1 || 째 > x.days!) return false;
  const done = x.done && typeof x.done === 'object' ? x.done : {};
  let 오늘번 = 0; for (let n = 1; n <= x.perDay!; n++) if (done[오늘 + '|' + n]) 오늘번++;
  return 오늘번 < x.perDay!;
}
export function decide(now: Date, tz: string, data: KidsData): Due[] {
  const t = localParts(now, tz), out: Due[] = [];
  const 아이들 = (Array.isArray(data.kids) ? data.kids : []).map((k) => k && k.id).filter((x): x is string => typeof x === 'string');
  const 날들 = (id: string) => (Array.isArray(data.vacdue?.[id]) ? data.vacdue![id]! : []).map((v) => v && v.d).filter(날);
  for (const [k, n] of [['vac7', 7], ['vac1', 1]] as const) {
    const s = 설정값(data.noti, k);
    if (!s.on || !때됨(t.min, s.t)) continue;
    const 그날 = addDays(t.day, n);
    if (아이들.some((id) => 날들(id).includes(그날))) out.push({ kind: k, slot: t.day });
  }
  const r = 설정값(data.noti, 'rx');
  if (r.on && 때됨(t.min, r.t) && 아이들.some((id) => (Array.isArray(data.rx?.[id]) ? data.rx![id]! : []).some((x) => 먹이는중(x, t.day)))) out.push({ kind: 'rx', slot: t.day });
  return out;
}
const 글: Record<string, Record<Due['kind'], [string, string]>> = {
  ko: { vac7: ['우리 집 소아과 · 예방접종', '일주일 뒤 예방접종 날이에요. 접종 탭에서 확인해 보세요.'], vac1: ['우리 집 소아과 · 예방접종', '내일 예방접종 날이에요. 접종 탭에서 확인해 보세요.'],
        rx: ['우리 집 소아과 · 처방약', '처방약 먹일 시간이에요. 먹인 뒤 앱에서 칸을 눌러 두세요.'] },
  en: { vac7: ['Our Family Pediatrician · Vaccines', 'A vaccine is due in one week. Check the Vaccines tab.'], vac1: ['Our Family Pediatrician · Vaccines', 'A vaccine is due tomorrow. Check the Vaccines tab.'],
        rx: ['Our Family Pediatrician · Medicine', 'Time for the prescribed medicine. Tap the box in the app after giving it.'] },
  es: { vac7: ['Pediatría en casa · Vacunas', 'Dentro de una semana toca una vacuna. Revise la pestaña Vacunas.'], vac1: ['Pediatría en casa · Vacunas', 'Mañana toca una vacuna. Revise la pestaña Vacunas.'],
        rx: ['Pediatría en casa · Medicamento', 'Es la hora del medicamento recetado. Marque la casilla en la app después de dárselo.'] },
  ja: { vac7: ['うちの小児科 · 予防接種', '1週間後に予防接種の日があります。予防接種タブで確認してください。'], vac1: ['うちの小児科 · 予防接種', '明日は予防接種の日です。予防接種タブで確認してください。'],
        rx: ['うちの小児科 · 処方薬', '処方薬を飲ませる時間です。飲ませたらアプリで欄を押してください。'] },
  zh: { vac7: ['我们家的儿科 · 接种', '一周后要接种疫苗。请在接种页面确认。'], vac1: ['我们家的儿科 · 接种', '明天要接种疫苗。请在接种页面确认。'],
        rx: ['我们家的儿科 · 处方药', '该吃处方药了。喂药后请在应用里点一下。'] },
};
export function onceOf(due: Due) { return { kind: due.kind, day: due.slot, slot: due.slot }; }   /* 하루 한 번 · slot 20자 안 */
export function message(kind: Due['kind'], lang = 'ko') { const [title, body] = (글[lang] || 글.ko)[kind]; return { title, body }; }
export const 가기: Record<Due['kind'], string> = { vac7: '#/note', vac1: '#/note', rx: '#/today' };
