// 약지도 «부모님께 약 보내기» — 하나의 함수로 세 동작(설계: yakjido/설계-가족연결.md)
//   POST {action:'create', items:[{id,name}], label?, note?, consent:true}  → {code, expires_at}
//   POST {action:'get', code}                                               → {items, label, note, expires_at, bought_at}
//   POST {action:'bought', code}                                            → {ok:true}
// 데이터베이스는 Supabase 가 함수 실행 환경에 넣어 주는 SUPABASE_DB_URL 로 «바로» 붙는다 — 키를 쓰지 않는다.
// 2026-10-06: 처음엔 supabase-js + 새 secret 키였는데, 새 키는 JWT 가 아니어서 Authorization 머리글에 실리면
// 거절된다(Supabase 문서 「Migrating to publishable and secret API keys」). 배포 후 「read failed」 → 직접 연결로 바꿈.
import postgres from 'https://deno.land/x/postgresjs@v3.4.5/mod.js';

const ORIGINS = [
  'https://usualhealth383-cloud.github.io',   // 약지도 PWA (GitHub Pages)
  'capacitor://localhost', 'https://localhost', // 안드로이드 앱(Capacitor)
  'http://localhost:8765',                    // 개발·검사
];
const cors = (origin: string | null) => ({
  'Access-Control-Allow-Origin': origin && ORIGINS.includes(origin) ? origin : ORIGINS[0],
  'Access-Control-Allow-Headers': 'authorization, apikey, content-type',
  'Access-Control-Allow-Methods': 'POST, OPTIONS',
  'Vary': 'Origin',
});
const json = (body: unknown, status: number, origin: string | null) =>
  new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json; charset=utf-8', ...cors(origin) } });

const sql = postgres(Deno.env.get('SUPABASE_DB_URL')!, { prepare: false, max: 1 });
// 실패 이유는 개인정보가 없는 오류 번호만 돌려준다(진단용) — 자세한 내용은 함수 로그에
const fail = (what: string, e: unknown, origin: string | null) => {
  console.error(what, e);
  return json({ error: what, why: String((e as { code?: string })?.code || (e as Error)?.name || 'unknown') }, 500, origin);
};

// 추측 불가능한 코드(128비트, 주소에 쓰기 좋은 글자)
const newCode = () => {
  const b = crypto.getRandomValues(new Uint8Array(16));
  return btoa(String.fromCharCode(...b)).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
};
const clean = (s: unknown, n: number) => typeof s === 'string' ? s.replace(/[\u0000-\u001f<>]/g, '').trim().slice(0, n) : null;
const okCode = (c: unknown) => typeof c === 'string' && /^[A-Za-z0-9_-]{20,40}$/.test(c);

Deno.serve(async (req) => {
  const origin = req.headers.get('Origin');
  if (req.method === 'OPTIONS') return new Response('ok', { headers: cors(origin) });
  if (req.method !== 'POST') return json({ error: 'POST only' }, 405, origin);
  const raw = await req.text();
  if (raw.length > 4000) return json({ error: 'too large' }, 413, origin);
  let b: Record<string, unknown>;
  try { b = JSON.parse(raw); } catch { return json({ error: 'bad json' }, 400, origin); }

  if (b.action === 'create') {
    if (b.consent !== true) return json({ error: 'consent required' }, 400, origin);
    const items = Array.isArray(b.items) ? b.items.slice(0, 10).map((x: any) => ({
      id: clean(x?.id, 60), name: clean(x?.name, 80), product: clean(x?.product, 80),
    })).filter((x) => x.id && x.name) : [];
    if (!items.length) return json({ error: 'no items' }, 400, origin);
    const code = newCode();
    try {
      const [row] = await sql`insert into public.shares (code, items, label, note, consent_at)
        values (${code}, ${sql.json(items)}, ${clean(b.label, 20) || null}, ${clean(b.note, 100) || null}, now())
        returning code, expires_at`;
      return json(row, 200, origin);
    } catch (e) { return fail('save failed', e, origin); }
  }

  if (b.action === 'get' || b.action === 'bought') {
    if (!okCode(b.code)) return json({ error: 'bad code' }, 400, origin);
    let data;
    try {
      [data] = await sql`select items, label, note, expires_at, bought_at from public.shares where code = ${b.code} limit 1`;
    } catch (e) { return fail('read failed', e, origin); }
    if (!data || new Date(data.expires_at) < new Date()) return json({ error: 'expired' }, 410, origin);
    if (b.action === 'get') return json(data, 200, origin);
    try { await sql`update public.shares set bought_at = now() where code = ${b.code} and bought_at is null`; }
    catch (e) { return fail('save failed', e, origin); }
    return json({ ok: true }, 200, origin);
  }
  return json({ error: 'unknown action' }, 400, origin);
});
