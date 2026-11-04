// 소아·곁에 알림 판정(순수 함수 · 11-04) — 시험: yakjido/tests/push_kids_gyeote.mjs
// 소아 기록 records(app='kids', key='kh.remind@<아이>') = { on, next: { acet?: ISO, ibu?: ISO }, tz, lang }
//   next = 그 해열제를 «다시 먹일 수 있는 때»(앱 먹임판정 — 간격·24시간 양·하루 횟수) · 지났거나 24시간 안에 먹인 적 없으면 null(11-04 소아 세션 형식). 양·아이 이름은 알림에 넣지 않는다.
// 곁에 복약은 곁에 형식(gyeote_pushset.dose)이라 gyeote_logic.ts 에 있다(11-04 곁에 세션 요청).
import { localNow, validTz } from './yak_logic.ts';
export const WIN = 3;                 // ±3분(5분마다 확인 · 같은 일은 mn_push_sent 로 한 번)
export const LATE_MAX = 10;          // 소아 해열제: 그때부터 10분 안의 확인에서만(5분마다 확인 — 한 번 놓쳐도 다음에)
export const KIDS_PER_DAY = 12;       // 받는 사람 한 명당 하루 상한(아세트아미노펜 5 + 이부프로펜 4 보다 넉넉히)
const LANGS = ['ko', 'en', 'es', 'ja', 'zh'];
const lang = (l: unknown) => (typeof l === 'string' && LANGS.includes(l) ? l : 'ko');
const tzOf = (t: unknown) => (validTz(t) ? String(t) : 'Asia/Seoul');
const hhmm = (m: number) => `${String(Math.floor(m / 60)).padStart(2, '0')}:${String(m % 60).padStart(2, '0')}`;

/** 지금 ±WIN 분 안에 «다시 먹일 수 있게 되는» 해열제 */
export function kidsDue(rem: any, now: Date) {
  if (!rem || rem.on !== true || typeof rem.next !== 'object' || !rem.next) return [];
  const tz = tzOf(rem.tz), out: { ing: 'acet' | 'ibu'; day: string; slot: string }[] = [];
  for (const ing of ['acet', 'ibu'] as const) {
    const t = Date.parse(String(rem.next[ing] || '')); if (!isFinite(t)) continue;
    const late = now.getTime() - t; if (late < 0 || late > LATE_MAX * 60000) continue;   // 11-04 소아: 그때가 «지난 뒤» 첫 확인에(앞당겨 보내지 않음) · 10분 넘게 늦으면 보내지 않음
    const at = localNow(new Date(t), tz);   // 그 시각의 그 집 날짜·시각(자정 넘김도 그 시각 기준)
    out.push({ ing, day: at.day, slot: ing + '@' + hhmm(at.min) });
  }
  return out;
}
const ING: Record<string, Record<string, string>> = {
  acet: { ko: '아세트아미노펜', en: 'Acetaminophen', es: 'Paracetamol', ja: 'アセトアミノフェン', zh: '对乙酰氨基酚' },
  ibu: { ko: '이부프로펜', en: 'Ibuprofen', es: 'Ibuprofeno', ja: 'イブプロフェン', zh: '布洛芬' } };
export function kidsMessage(ing: 'acet' | 'ibu', l = 'ko') {   // 11-04 소아 세션 — 앱 안 알림과 같은 글
  l = lang(l); const n = ING[ing][l];
  const t: Record<string, [string, string]> = {
    ko: ['해열제', `${n}을 다시 먹일 수 있는 때예요. 꼭 먹여야 한다는 뜻은 아니에요.`],
    en: ['Fever medicine', `You can give ${n} again now. This doesn't mean you have to.`],
    es: ['Antitérmico', `Ya puede volver a dar ${n}. No significa que tenga que dárselo.`],
    ja: ['解熱剤', `${n}をまた飲ませてよい時間です。必ず飲ませなければならないという意味ではありません。`],
    zh: ['退烧药', `现在可以再次给${n}了。这并不表示一定要给。`] };
  return { title: t[l][0], body: t[l][1] };
}
export { lang as pickLang };
