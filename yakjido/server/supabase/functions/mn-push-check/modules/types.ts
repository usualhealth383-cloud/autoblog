// 메디나눔 공용 푸시 — 앱 판정 모듈이 받는 것(11-03)
// 모듈 하나 = 앱 하나. run() 은 5분마다 한 번 불린다(11-04 — 15분에서 바꿈). 보낼 것을 찾으면 ctx.push 로 보낸다(같은 일은 once 로 한 번만).
export type Payload = { title: string; body: string; kind?: string; key?: string; day?: string; tag?: string; go?: string; acts?: string[] };
export type Once = { kind: string; day: string; slot: string };
export interface Ctx {
  sql: any;            // postgres.js — records 표(user_id, app, key, value{v:"JSON 글"}, updated_at) 와 앱 표를 읽는다
  now: Date;
  /** userId 의 이 앱 기기들로 보낸다. make(기기 말) → 글. once 가 이미 보낸 것이면 보내지 않고 false */
  push: (userId: string, make: (lang: string) => Payload, once: Once) => Promise<boolean>;
  /** 이 앱·이 사람이 오늘 같은 kind 로 몇 번 보냈나(하루 상한) */
  sentCount: (userId: string, kind: string, day: string) => Promise<number>;
  parse: (v: unknown) => any;   // records.value → 앱 기록(JSON)
}
export interface Module { app: 'kids' | 'gildongmu' | 'clinicscore' | 'gyeote' | 'yakjido'; run: (ctx: Ctx) => Promise<number> }
