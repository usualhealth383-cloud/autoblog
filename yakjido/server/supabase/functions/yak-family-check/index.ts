// 약지도 가족 알림 — 15분마다(pg_cron → 이 함수) 연결된 가족에게 «아직 체크가 없어요» 웹 푸시 · 2026-11-02
// 설계: yakjido/가족알림_설계.md · 표: yakjido/server/supabase/medinanum/메디나눔_약지도_가족알림_1102.sql
// 배포: supabase functions deploy yak-family-check --no-verify-jwt (예약 작업이 부르므로 로그인 토큰 대신 x-cron-secret 머리글로 막는다)
// 비밀(이름만 — 값은 저장소에 두지 않는다): FAMILY_CRON_SECRET · VAPID_PUBLIC_KEY · VAPID_PRIVATE_KEY · VAPID_SUBJECT(mailto:contact@medinanum.com)
// DB 는 Supabase 가 넣어 주는 SUPABASE_DB_URL 로 바로 붙는다(yak-share 와 같은 방식).
import postgres from 'https://deno.land/x/postgresjs@v3.4.5/mod.js';
import webpush from 'npm:web-push@3.6.7';
import { missedSlots, seoulNow, quiet, stale, message, PER_DAY } from './logic.ts';

const sql = postgres(Deno.env.get('SUPABASE_DB_URL')!, { prepare: false, max: 1 });
webpush.setVapidDetails(Deno.env.get('VAPID_SUBJECT') || 'mailto:contact@medinanum.com', Deno.env.get('VAPID_PUBLIC_KEY')!, Deno.env.get('VAPID_PRIVATE_KEY')!);

Deno.serve(async (req) => {
  const secret = Deno.env.get('FAMILY_CRON_SECRET');
  if (!secret || req.headers.get('x-cron-secret') !== secret) return new Response('forbidden', { status: 403 });
  const nowD = new Date(), now = seoulNow(nowD);
  if (quiet(now.min)) return Response.json({ ok: true, quiet: true });
  let checked = 0, sent = 0, dropped = 0;
  try {
    const rows = await sql`
      select l.id, l.member_id, l.owner_label, l.muted_day, r.value, r.updated_at
        from public.yak_family_links l
        join public.records r on r.user_id = l.owner_id and r.app = 'yakjido' and r.key = 'yakjido.me.v1'
       where l.member_id is not null and l.ended_at is null`;
    for (const x of rows) {
      checked++;
      if (x.muted_day && String(x.muted_day).slice(0, 10) === now.day) continue;
      if (stale(x.updated_at, nowD)) continue;
      let me: unknown = null;
      try { const v = (x.value as { v?: unknown })?.v; me = typeof v === 'string' ? JSON.parse(v) : v; } catch { continue; }
      const slots = missedSlots(me, now); if (!slots.length) continue;
      const [{ n }] = await sql`select count(*)::int as n from public.yak_family_sent where link_id = ${x.id} and day = ${now.day}`;
      if (n >= PER_DAY) continue;
      let slot: string | null = null;
      for (const s of slots) {
        const ins = await sql`insert into public.yak_family_sent (link_id, day, slot) values (${x.id}, ${now.day}, ${s}) on conflict do nothing returning slot`;
        if (ins.length) { slot = s; break; }
      }
      if (!slot) continue;
      const msg = message(String(x.owner_label), slot);
      const payload = JSON.stringify({ ...msg, go: '#/notify?fam=1', tag: 'yakjido-family-' + x.id });
      const subs = await sql`select endpoint, p256dh, auth from public.yak_push_subs where user_id = ${x.member_id}`;
      for (const s of subs) {
        try {
          await webpush.sendNotification({ endpoint: s.endpoint, keys: { p256dh: s.p256dh, auth: s.auth } }, payload, { TTL: 3600, urgency: 'high' });
          await sql`update public.yak_push_subs set last_ok = now() where endpoint = ${s.endpoint}`; sent++;
        } catch (e) {
          const code = (e as { statusCode?: number })?.statusCode;
          if (code === 404 || code === 410) { await sql`delete from public.yak_push_subs where endpoint = ${s.endpoint}`; dropped++; }   // 기기가 구독을 거뒀다
          else console.error('push', code || (e as Error)?.name);
        }
      }
    }
  } catch (e) {
    console.error('check', (e as { code?: string })?.code || (e as Error)?.name);
    return Response.json({ ok: false }, { status: 500 });
  }
  return Response.json({ ok: true, checked, sent, dropped });
});
