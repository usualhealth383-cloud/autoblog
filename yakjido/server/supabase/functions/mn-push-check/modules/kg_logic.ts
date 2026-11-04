// 소아·곁에 알림 판정(순수 함수 · 11-04) — 시험: yakjido/tests/push_kids_gyeote.mjs
// 소아 기록 records(app='kids', key='kh.remind@<아이>') = { on, next: { acet?: ISO, ibu?: ISO }, tz, lang }
//   next = 그 해열제를 «다시 먹일 수 있는 가장 이른 시각»(앱이 마지막 먹인 시각 + 간격으로 계산해 올림). 양·아이 이름은 알림에 넣지 않는다.
// 곁에 복약은 곁에 형식(gyeote_pushset.dose)이라 gyeote_logic.ts 에 있다(11-04 곁에 세션 요청).
import { localNow, validTz } from './yak_logic.ts';
export const WIN = 3;                 // ±3분(5분마다 확인 · 같은 일은 mn_push_sent 로 한 번)
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
    if (Math.abs(now.getTime() - t) > WIN * 60000) continue;
    const at = localNow(new Date(t), tz);   // 그 시각의 그 집 날짜·시각(자정 넘김도 그 시각 기준)
    out.push({ ing, day: at.day, slot: ing + '@' + hhmm(at.min) });
  }
  return out;
}
const ING: Record<string, Record<string, string>> = {
  acet: { ko: '아세트아미노펜', en: 'acetaminophen', es: 'paracetamol', ja: 'アセトアミノフェン', zh: '对乙酰氨基酚' },
  ibu: { ko: '이부프로펜', en: 'ibuprofen', es: 'ibuprofeno', ja: 'イブプロフェン', zh: '布洛芬' } };
export function kidsMessage(ing: 'acet' | 'ibu', l = 'ko') {
  l = lang(l); const n = ING[ing][l];
  const t: Record<string, [string, string]> = {
    ko: ['해열제 시간', `${n} 해열제를 먹일 수 있는 시간이에요. 열이 없거나 잘 놀면 꼭 먹이지 않아도 돼요.`],
    en: ['Fever medicine', `It's now OK to give ${n} again. If there's no fever and your child is playing well, you don't have to give it.`],
    es: ['Antitérmico', `Ya puede volver a dar ${n}. Si no tiene fiebre y juega bien, no hace falta dárselo.`],
    ja: ['解熱剤の時間', `${n}をまた飲ませてよい時間です。熱がなく元気に遊んでいれば、飲ませなくても大丈夫です。`],
    zh: ['退烧药时间', `现在可以再次给${n}了。如果没有发烧、玩得很好，不一定要给。`] };
  return { title: t[l][0], body: t[l][1] };
}
export { lang as pickLang };
