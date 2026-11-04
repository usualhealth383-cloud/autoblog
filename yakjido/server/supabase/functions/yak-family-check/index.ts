// 약지도 알림 — 15분마다(pg_cron → 이 함수) ① 본인 정시 알림(켠 분만) ② 가족 놓침 알림 · 웹 푸시 · 2026-11-03
// 설계: yakjido/가족알림_설계.md · 표: 메디나눔_약지도_가족알림_1102.sql + _보완2_1103.sql
// 배포: supabase functions deploy yak-family-check --no-verify-jwt (예약 작업이 부르므로 로그인 토큰 대신 x-cron-secret 머리글로 막는다)
// 비밀은 Supabase Vault 에서 읽는다(11-02 Main — 값이 채팅·대시보드 입력을 거치지 않게): yak_family_cron_secret(서버 안 gen_random_bytes) ·
// yak_vapid_private · yak_vapid_public(처음 돌 때 web-push 로 만들어 Vault 에 넣음). 저장소엔 값이 없다.
// 사람마다 자기 시간대(yakjido.fam.v1 의 tz — 기기 설정 값)로 날짜·시각·쉬는 시간을 판단한다. 없으면 서울.
import postgres from 'https://deno.land/x/postgresjs@v3.4.5/mod.js';
import webpush from 'npm:web-push@3.6.7';
import { missedSlots, dueNow, localNow, quiet, stale, message, doseMessage, prefs, PER_DAY } from './logic.ts';

const sql = postgres(Deno.env.get('SUPABASE_DB_URL')!, { prepare: false, max: 1 });

async function vault(name: string): Promise<string | null> {
  const r = await sql`select decrypted_secret from vault.decrypted_secrets where name = ${name}`;
  return r.length ? String(r[0].decrypted_secret) : null;
}
let vapidReady = false;
async function vapid() {
  if (vapidReady) return;
  let pub = await vault('yak_vapid_public'), priv = await vault('yak_vapid_private');
  if (!pub || !priv) {   // 처음 한 번 — 만들어 Vault 에 넣고(이미 있으면 그대로) 다시 읽는다
    const k = webpush.generateVAPIDKeys();
    await sql`select vault.create_secret(${k.publicKey}, 'yak_vapid_public') where not exists (select 1 from vault.secrets where name = 'yak_vapid_public')`;
    await sql`select vault.create_secret(${k.privateKey}, 'yak_vapid_private') where not exists (select 1 from vault.secrets where name = 'yak_vapid_private')`;
    pub = await vault('yak_vapid_public'); priv = await vault('yak_vapid_private');
  }
  webpush.setVapidDetails('mailto:contact@medinanum.com', pub!, priv!);
  vapidReady = true;
}
const parse = (v: unknown) => { try { const x = (v as { v?: unknown })?.v; return typeof x === 'string' ? JSON.parse(x) : x; } catch { return null; } };

let sent = 0, dropped = 0;
async function push(userId: string, payload: string) {
  const subs = await sql`select endpoint, p256dh, auth from public.yak_push_subs where user_id = ${userId}`;
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

Deno.serve(async (req) => {
  let secret: string | null = null;
  try { secret = await vault('yak_family_cron_secret'); } catch { secret = null; }
  if (!secret || req.headers.get('x-cron-secret') !== secret) return new Response('forbidden', { status: 403 });
  try { await vapid(); } catch (e) { console.error('vapid', (e as Error)?.name); return Response.json({ ok: false, step: 'vapid' }, { status: 500 }); }
  const nowD = new Date(); sent = 0; dropped = 0;
  let selfChecked = 0, famChecked = 0;
  try {
    // ① 본인 정시 알림 — 설정(fam.v1)에서 dose:true 인 분만
    const self = await sql`
      select f.user_id, f.value as fam, m.value as me
        from public.records f join public.records m on m.user_id = f.user_id and m.app = 'yakjido' and m.key = 'yakjido.me.v1'
       where f.app = 'yakjido' and f.key = 'yakjido.fam.v1'`;
    for (const x of self) {
      const pf = prefs(parse(x.fam)); if (!pf.dose) continue;
      selfChecked++;
      const now = localNow(nowD, pf.tz);
      for (const d of dueNow(parse(x.me), now)) {
        const ins = await sql`insert into public.yak_dose_sent (user_id, day, slot) values (${x.user_id}, ${now.day}, ${d.t}) on conflict do nothing returning slot`;
        if (!ins.length) continue;
        const msg = doseMessage(d.t, d.ids, pf.nm, pf.lang);   // 본인 말로
        await push(x.user_id, JSON.stringify({ ...msg, kind: 'dose', key: d.key, day: now.day, tag: d.key }));
      }
    }
    // ② 가족 놓침 알림 — 본인이 허락한 연결만, 본인 시간대 기준
    const rows = await sql`
      select l.id, l.member_id, l.owner_label, l.muted_until, r.value, r.updated_at, f.value as fam, mf.value as mfam
        from public.yak_family_links l
        join public.records r on r.user_id = l.owner_id and r.app = 'yakjido' and r.key = 'yakjido.me.v1'
        left join public.records f on f.user_id = l.owner_id and f.app = 'yakjido' and f.key = 'yakjido.fam.v1'
        left join public.records mf on mf.user_id = l.member_id and mf.app = 'yakjido' and mf.key = 'yakjido.fam.v1'
       where l.member_id is not null and l.approved_at is not null and l.ended_at is null`;
    for (const x of rows) {
      famChecked++;
      if (x.muted_until && new Date(x.muted_until) > nowD) continue;
      if (stale(x.updated_at, nowD)) continue;
      const pf = prefs(parse(x.fam)), now = localNow(nowD, pf.tz);
      if (quiet(now.min, pf.qs, pf.qe)) continue;
      const slots = missedSlots(parse(x.value), now, pf.wait, x.updated_at ? localNow(new Date(x.updated_at), pf.tz) : null);
      if (!slots.length) continue;
      const [{ n }] = await sql`select count(*)::int as n from public.yak_family_sent where link_id = ${x.id} and day = ${now.day}`;
      if (n >= PER_DAY) continue;
      let slot: string | null = null;
      for (const s of slots) {
        const ins = await sql`insert into public.yak_family_sent (link_id, day, slot) values (${x.id}, ${now.day}, ${s}) on conflict do nothing returning slot`;
        if (ins.length) { slot = s; break; }
      }
      if (!slot) continue;
      const mp = prefs(parse(x.mfam)), other = !!x.mfam && mp.tz !== pf.tz;
      const msg = message(String(x.owner_label), slot, other, mp.lang);   // 가족(받는 사람) 말로
      await push(x.member_id, JSON.stringify({ ...msg, kind: 'family', go: '#/notify?fam=1', tag: 'yakjido-family-' + x.id }));
    }
  } catch (e) {
    console.error('check', (e as { code?: string })?.code || (e as Error)?.name);
    return Response.json({ ok: false }, { status: 500 });
  }
  return Response.json({ ok: true, selfChecked, famChecked, sent, dropped });
});
