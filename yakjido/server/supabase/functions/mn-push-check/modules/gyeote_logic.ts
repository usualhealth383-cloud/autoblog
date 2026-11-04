// 곁에 판정(순수 함수 · Deno 와 node --experimental-strip-types 둘 다) — 11-03 곁에 세션
// 읽는 기록(앱이 서버 저장 동의 + 로그인일 때만 records 에 있다):
//   gyeote_pushset { v:1, eve:{on,t}, week:{on,t,dow}, tz }  — 알림 설정 화면의 거울(앱이 열릴 때·바꿀 때 씀). 없으면 아무것도 보내지 않는다
//   gyeote_battery { 'YYYY-M-D': 0~100 } · gyeote_moods { 'YYYY-M-D': … } — 오늘 남겼으면 저녁 알림을 보내지 않는다
//   gyeote_retest [{ go, t, at(ms) }] — 「다음 주에 다시 재 보기」. 검사 이름(t)은 알림에 넣지 않는다
// 알림 글에는 마음 상태·검사 이름·병명을 담지 않는다(잠금 화면은 옆 사람도 본다).
export type Set = { eve?: { on?: boolean; t?: string }; week?: { on?: boolean; t?: string; dow?: number }; tz?: string; dose?: { on?: boolean; times?: string[] } };   // dose — 11-04 곁에(첫 6주 길잡이 + 복약 알림 켠 분만, 끄면 칸이 빠짐)
export type Retest = { go?: string; t?: string; at?: number };
export type Due = { kind: 'eve' | 'week' | 'retest' | 'dose'; slot: string };

export const WINDOW = 120;               // 정한 시간부터 이만큼(분) 안에서만 — 서버가 늦게 돌아도 밤늦게 뒤늦은 알림이 가지 않게
export const RETEST_FROM = 10 * 60, RETEST_TO = 21 * 60;   // 다시 재 볼 날 알림은 낮에만
export const RETEST_STALE_DAYS = 3;       // 사흘 넘게 지난 다시 재기는 보내지 않는다(홈 카드로만)

const toMin = (t?: string) => (/^\d{2}:\d{2}$/.test(t || '') ? Number(t!.slice(0, 2)) * 60 + Number(t!.slice(3)) : -1);
export function local(d: Date, tz: string) {
  let z = tz; try { new Intl.DateTimeFormat('en-CA', { timeZone: z }); } catch { z = 'Asia/Seoul'; }
  const p = Object.fromEntries(new Intl.DateTimeFormat('en-CA', { timeZone: z, year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', weekday: 'short', hourCycle: 'h23' })
    .formatToParts(d).map((x) => [x.type, x.value]));
  const dow = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].indexOf(String(p.weekday));
  return { day: `${p.year}-${p.month}-${p.day}`, key: `${Number(p.year)}-${Number(p.month)}-${Number(p.day)}`, min: Number(p.hour) * 60 + Number(p.minute), dow };
}
const inWin = (min: number, t?: string) => { const s = toMin(t); return s >= 0 && min >= s && min < s + WINDOW; };

export function due(set: Set | null, battery: Record<string, unknown> | null, moods: Record<string, unknown> | null, retest: Retest[] | null, now: Date): { day: string; list: Due[] } {
  if (!set || typeof set !== 'object') return { day: '', list: [] };
  const L = local(now, set.tz || 'Asia/Seoul'), list: Due[] = [];
  const b = battery && typeof battery === 'object' ? battery : {}, m = moods && typeof moods === 'object' ? moods : {};
  if (set.eve?.on && inWin(L.min, set.eve.t) && b[L.key] == null && !m[L.key]) list.push({ kind: 'eve', slot: set.eve.t! });
  if (set.week?.on && L.dow === (Number.isInteger(set.week.dow) ? set.week.dow : 0) && inWin(L.min, set.week.t)) list.push({ kind: 'week', slot: set.week.t! });
  if (set.dose?.on && Array.isArray(set.dose.times)) {   // 11-04 복약 — 정한 시각부터 WINDOW 안 첫 확인에 한 번(slot = 시각 · mn_push_sent 로 한 번만) · 최대 4개
    const seen = new Set<string>();
    for (const t of set.dose.times.slice(0, 4)) { if (typeof t === 'string' && !seen.has(t) && inWin(L.min, t)) { seen.add(t); list.push({ kind: 'dose', slot: t }); } }
  }
  if (Array.isArray(retest) && L.min >= RETEST_FROM && L.min < RETEST_TO) {
    const t = now.getTime();
    const r = retest.filter((x) => x && typeof x.at === 'number' && x.at <= t && t - x.at < RETEST_STALE_DAYS * 864e5).sort((a, c) => a.at! - c.at!)[0];
    if (r) list.push({ kind: 'retest', slot: String(r.at) });
  }
  return { day: L.day, list };
}

const APP: Record<string, string> = { ko: '곁에', en: 'Gyeote', es: 'Gyeote', ja: 'そばに', zh: '身边' };
const T: Record<Due['kind'], Record<string, [string, string]>> = {
  eve: { ko: ['', '오늘 하루 어땠나요? 10초면 돼요.'], en: ['', 'How was your day? It only takes 10 seconds.'], es: ['', '¿Qué tal su día? Solo le llevará 10 segundos.'],
         ja: ['', '今日はどんな一日でしたか？10秒でできます。'], zh: ['', '今天过得怎么样？只要10秒。'] },
  week: { ko: ['', '이번 주 마음 카드가 나왔어요.'], en: ['', 'This week’s mind card is ready.'], es: ['', 'Ya está la tarjeta de ánimo de esta semana.'],
          ja: ['', '今週のこころカードができました。'], zh: ['', '本周心情卡出来了。'] },
  dose: { ko: ['', '약 드실 시간이에요'], en: ['', 'Time for your medicine'], es: ['', 'Es hora de su medicación'], ja: ['', 'お薬の時間です'], zh: ['', '该吃药了'] },
  retest: { ko: ['다시 재 볼 날이에요', '일주일 전과 견줘 봐요'], en: ['Time to check again', 'Compare with a week ago'], es: ['Hoy toca volver a medir', 'Compare con hace una semana'],
            ja: ['もう一度はかる日です', '1週間前と比べてみましょう'], zh: ['今天该再测一次了', '和一周前比一比'] },
};
export function text(kind: Due['kind'], lang: string) {
  const l = APP[lang] ? lang : 'ko', [h, body] = T[kind][l];
  return { title: h || APP[l], body, tag: 'gyeote-' + kind, go: '#/' };
}
