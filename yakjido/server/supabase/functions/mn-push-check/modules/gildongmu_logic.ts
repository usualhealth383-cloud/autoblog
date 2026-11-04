// 길동무 푸시 판정(순수 함수 · 11-03 길동무 세션) — 서버에 동기화된 gd.plans · gd.log · gd.temps 만 본다(기기 안 알림 설정·복약 칸은 서버에 없다 → 약은 기기 알림 몫)
//   eve   19:00~19:59(받는 사람 시간대) — 내일 날짜의 일정이 하나라도 있으면
//   rec   20:00~21:59 — 오늘 기록(증상·체온)이 없고, 최근 7일 안에 한 번이라도 기록한 사람(쉬는 분께 조르지 않음)
//   temp  37.5~37.9℃ 를 적고 60~120분 지났는데 그 뒤 체온이 없으면 「다시 재기」(앱 화면 「1시간 뒤 다시 재 보세요」와 같은 기준)
//   잠금화면에 보이는 글 — 병명·증상·숫자 기록은 넣지 않는다(체온 다시 재기의 38.0℃ 기준만)
export type Plan = { d?: string };
export type Log = { d?: string };
export type Temp = { d?: string; v?: number; at?: string };
export type Due = { kind: 'eve' | 'rec' | 'temp'; slot: string };
const 날 = (s: unknown) => typeof s === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(s);
export function localParts(d: Date, tz: string) {
  let z = tz; try { new Intl.DateTimeFormat('en-US', { timeZone: z }); } catch { z = 'Asia/Seoul'; }
  const p = Object.fromEntries(new Intl.DateTimeFormat('en-CA', { timeZone: z, year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', hourCycle: 'h23' })
    .formatToParts(d).map((x) => [x.type, x.value]));
  return { day: `${p.year}-${p.month}-${p.day}`, min: Number(p.hour) * 60 + Number(p.minute) };
}
export function addDays(day: string, n: number) { const d = new Date(day + 'T12:00:00Z'); d.setUTCDate(d.getUTCDate() + n); return d.toISOString().slice(0, 10); }
export function decide(now: Date, tz: string, plans: Plan[], log: Log[], temps: Temp[]): Due[] {
  const t = localParts(now, tz), out: Due[] = [];
  const P = Array.isArray(plans) ? plans : [], L = Array.isArray(log) ? log : [], T = Array.isArray(temps) ? temps : [];
  if (t.min >= 19 * 60 && t.min < 20 * 60) {
    const 내일 = addDays(t.day, 1);
    if (P.some((p) => p && 날(p.d) && p.d === 내일)) out.push({ kind: 'eve', slot: 내일 });
  }
  if (t.min >= 20 * 60 && t.min < 22 * 60) {
    const 오늘있음 = L.some((x) => x && x.d === t.day) || T.some((x) => x && x.d === t.day);
    const 일주 = addDays(t.day, -7);
    const 요즘씀 = L.some((x) => x && 날(x.d) && x.d! >= 일주 && x.d! < t.day) || T.some((x) => x && 날(x.d) && x.d! >= 일주 && x.d! < t.day);
    if (!오늘있음 && 요즘씀) out.push({ kind: 'rec', slot: t.day });
  }
  const 오늘체온 = T.filter((x) => x && x.d === t.day && typeof x.v === 'number' && typeof x.at === 'string' && !isNaN(Date.parse(x.at!)))
    .sort((a, b) => Date.parse(b.at!) - Date.parse(a.at!));
  const 마지막 = 오늘체온[0];
  if (마지막 && 마지막.v! >= 37.5 && 마지막.v! < 38.0) {
    const 지남 = (now.getTime() - Date.parse(마지막.at!)) / 60000;
    if (지남 >= 60 && 지남 < 120) out.push({ kind: 'temp', slot: 마지막.at! });
  }
  return out;
}
const 글: Record<string, Record<Due['kind'], [string, string]>> = {
  ko: { eve: ['길동무 · 내일 일정', '내일 적어 두신 일정이 있어요. 금식·챙길 것을 미리 확인해 보세요.'], rec: ['길동무 · 오늘 기록', '오늘 체온과 힘든 것을 아직 안 적으셨어요. 하나만 적어 두세요.'],
        temp: ['길동무 · 체온 다시 재기', '1시간이 지났어요. 체온을 다시 재 보세요. 38.0℃가 되면 병원에 바로 연락하세요.'] },
  en: { eve: ['Wayfellow · Tomorrow', 'You have something scheduled tomorrow. Check fasting and what to bring.'], rec: ['Wayfellow · Today', "You haven't logged your temperature or symptoms today. Just one is enough."],
        temp: ['Wayfellow · Recheck temperature', 'An hour has passed. Please take your temperature again. If it reaches 38.0℃, contact your hospital right away.'] },
  es: { eve: ['Wayfellow · Mañana', 'Mañana tiene algo programado. Revise el ayuno y lo que debe llevar.'], rec: ['Wayfellow · Hoy', 'Hoy aún no ha anotado la temperatura ni los síntomas. Con uno basta.'],
        temp: ['Wayfellow · Vuelva a tomarse la temperatura', 'Ha pasado una hora. Vuelva a tomarse la temperatura. Si llega a 38,0 ℃, llame enseguida a su hospital.'] },
  ja: { eve: ['Wayfellow · 明日の予定', '明日、記録した予定があります。絶食や持ち物を前もって確認しましょう。'], rec: ['Wayfellow · 今日の記録', '今日はまだ体温や症状を記録していません。ひとつだけでも記録しましょう。'],
        temp: ['Wayfellow · 体温をもう一度', '1時間たちました。もう一度体温をはかってください。38.0℃になったら、すぐに病院へ連絡してください。'] },
  zh: { eve: ['Wayfellow · 明天的日程', '明天有您记下的日程。请提前确认是否需要空腹、要带什么。'], rec: ['Wayfellow · 今天的记录', '今天还没有记录体温或不适。记一条就好。'],
        temp: ['Wayfellow · 再量体温', '已经过了1小时。请再量一次体温。到38.0℃请马上联系医院。'] },
};
// 11-03 Main — mn_push_sent.slot 은 20자 제한. 체온은 ISO 시각에서 시:분:초만(같은 날 같은 측정은 한 번)
export function onceOf(due: Due) {
  const slot = due.kind === 'temp' ? due.slot.slice(11, 19) : due.slot;
  return { kind: due.kind, day: due.slot.slice(0, 10), slot };
}
export function message(kind: Due['kind'], lang = 'ko') { const [title, body] = (글[lang] || 글.ko)[kind]; return { title, body }; }
