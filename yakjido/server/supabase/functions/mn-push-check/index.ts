// 메디나눔 공용 푸시 — 5분마다(pg_cron → 이 함수 · 11-04 15분에서 바꿈) 다섯 앱 판정 모듈을 차례로 돌려 웹 푸시를 보낸다 · 2026-11-03
// 표: yakjido/server/supabase/medinanum/메디나눔_공용푸시_1103.sql(mn_push_subs · mn_push_sent) · 앱 모듈: ./modules/<앱>.ts
// 배포: supabase functions deploy mn-push-check --no-verify-jwt (예약 작업이 부르므로 x-cron-secret 머리글로 막음)
// 비밀은 yak-family-check 와 같은 Vault 값을 공용으로 쓴다: yak_family_cron_secret · yak_vapid_public · yak_vapid_private(저장소엔 값 없음)
// 바꾸는 날: 예약 작업이 yak-family-check 대신 이 함수를 부르게(한 번에 하나만 — 둘이 같이 돌면 약지도 알림이 두 번 간다)
import postgres from 'https://deno.land/x/postgresjs@v3.4.5/mod.js';
import webpush from 'npm:web-push@3.6.7';
import type { Ctx, Module, Payload, Once } from './modules/types.ts';
import yakjido from './modules/yakjido.ts';
import kids from './modules/kids.ts';
import gildongmu from './modules/gildongmu.ts';
import clinicscore from './modules/clinicscore.ts';
import gyeote from './modules/gyeote.ts';
const MODULES: Module[] = [yakjido, kids, gildongmu, clinicscore, gyeote];

const sql = postgres(Deno.env.get('SUPABASE_DB_URL')!, { prepare: false, max: 1 });
async function vault(name: string): Promise<string | null> {
  const r = await sql`select decrypted_secret from vault.decrypted_secrets where name = ${name}`;
  return r.length ? String(r[0].decrypted_secret) : null;
}
let vapidReady = false;
async function vapid() {
  if (vapidReady) return;
  const pub = await vault('yak_vapid_public'), priv = await vault('yak_vapid_private');
  if (!pub || !priv) throw new Error('vapid missing');   // 열쇠는 yak-family-check 가 처음 돌 때 만들어 둔 것을 쓴다
  webpush.setVapidDetails('mailto:contact@medinanum.com', pub, priv); vapidReady = true;
}
const parse = (v: unknown) => { try { const x = (v as { v?: unknown })?.v; return typeof x === 'string' ? JSON.parse(x) : x; } catch { return null; } };

let sent = 0, dropped = 0;
function ctxFor(app: Module['app'], now: Date): Ctx {
  return {
    sql, now, parse,
    async sentCount(userId, kind, day) { const [{ n }] = await sql`select count(*)::int as n from public.mn_push_sent where user_id = ${userId} and app = ${app} and kind = ${kind} and day = ${day}`; return n; },
    async push(userId: string, make: (lang: string) => Payload, once: Once) {
      const subs = await sql`select endpoint, p256dh, auth, lang from public.mn_push_subs where user_id = ${userId} and app = ${app}`;
      if (!subs.length) return false;
      const ins = await sql`insert into public.mn_push_sent (user_id, app, kind, day, slot) values (${userId}, ${app}, ${once.kind}, ${once.day}, ${once.slot}) on conflict do nothing returning slot`;
      if (!ins.length) return false;   // 이미 보냄
      for (const s of subs) {
        try {
          await webpush.sendNotification({ endpoint: s.endpoint, keys: { p256dh: s.p256dh, auth: s.auth } }, JSON.stringify(make(s.lang || 'ko')), { TTL: 3600, urgency: 'high' });
          await sql`update public.mn_push_subs set last_ok = now() where endpoint = ${s.endpoint}`; sent++;
        } catch (e) {
          const code = (e as { statusCode?: number })?.statusCode;
          if (code === 404 || code === 410) { await sql`delete from public.mn_push_subs where endpoint = ${s.endpoint}`; dropped++; }
          else console.error('push', app, code || (e as Error)?.name);
        }
      }
      return true;
    },
  };
}

Deno.serve(async (req) => {
  let secret: string | null = null;
  try { secret = await vault('yak_family_cron_secret'); } catch { secret = null; }
  if (!secret || req.headers.get('x-cron-secret') !== secret) return new Response('forbidden', { status: 403 });
  try { await vapid(); } catch (e) { console.error('vapid', (e as Error)?.message); return Response.json({ ok: false, step: 'vapid' }, { status: 500 }); }
  const now = new Date(); sent = 0; dropped = 0;
  const per: Record<string, number | string> = {};
  for (const m of MODULES) {   // 한 앱이 실패해도 다른 앱은 돈다
    try { per[m.app] = await m.run(ctxFor(m.app, now)); } catch (e) { per[m.app] = 'error'; console.error('module', m.app, (e as { code?: string })?.code || (e as Error)?.name); }
  }
  return Response.json({ ok: true, per, sent, dropped });
});
