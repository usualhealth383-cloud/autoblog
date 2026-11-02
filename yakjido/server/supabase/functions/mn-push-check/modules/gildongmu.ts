// 길동무 판정 모듈 — 자리만(11-03). 길동무 세션이 채운다(요청서 A: 각 앱이 심기).
// 쓰는 법: ctx.sql 로 records(app='gildongmu') 의 기록을 읽고, 보낼 때가 되면
//   await ctx.push(userId, (lang) => ({ title, body, tag, go: '#/…' }), { kind: '종류', day: 'YYYY-MM-DD(그 사람 시각)', slot: 'HH:MM 또는 구분자' })
// 시간대·말은 기기 구독(mn_push_subs.lang·tz) 또는 앱 설정 기록에서. 하루 상한은 ctx.sentCount. 판정은 순수 함수로 따로 두고 단위 시험(약지도 logic.ts·tests/family_logic.mjs 처럼).
import type { Module } from './types.ts';
const mod: Module = { app: 'gildongmu', async run() { return 0; } };
export default mod;
