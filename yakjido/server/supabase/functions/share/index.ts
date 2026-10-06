// 약지도 «부모님께 약 보내기» — 하나의 함수로 세 동작(설계: yakjido/설계-가족연결.md)
//   POST {action:'create', items:[{id,name}], label?, note?, consent:true}  → {code, expires_at}
//   POST {action:'get', code}                                               → {items, label, note, expires_at, bought_at}
//   POST {action:'bought', code}                                            → {ok:true}
// 서버 키는 Supabase 가 함수 실행 환경에 자동으로 넣어 준다 — 저장소에 적지 않는다.
// 새 키 체계(publishable·secret) 프로젝트는 SUPABASE_SECRET_KEYS(JSON, 'default'), 옛 프로젝트는 SUPABASE_SERVICE_ROLE_KEY(2026-10-06 문서 확인)
import { createClient } from 'npm:@supabase/supabase-js@2';

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

function serverKey(): string {
  try { const k = JSON.parse(Deno.env.get('SUPABASE_SECRET_KEYS') || '{}')['default']; if (k) return k; } catch (_) { /* 옛 프로젝트 */ }
  return Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!;
}
const db = createClient(Deno.env.get('SUPABASE_URL')!, serverKey(), { auth: { persistSession: false } });

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
    const { data, error } = await db.from('shares').insert({
      code, items, label: clean(b.label, 20) || null, note: clean(b.note, 100) || null, consent_at: new Date().toISOString(),
    }).select('code, expires_at').single();
    if (error) return json({ error: 'save failed' }, 500, origin);
    return json(data, 200, origin);
  }

  if (b.action === 'get' || b.action === 'bought') {
    if (!okCode(b.code)) return json({ error: 'bad code' }, 400, origin);
    const { data, error } = await db.from('shares').select('items, label, note, expires_at, bought_at').eq('code', b.code).maybeSingle();
    if (error) return json({ error: 'read failed' }, 500, origin);
    if (!data || new Date(data.expires_at) < new Date()) return json({ error: 'expired' }, 410, origin);
    if (b.action === 'get') return json(data, 200, origin);
    await db.from('shares').update({ bought_at: new Date().toISOString() }).eq('code', b.code).is('bought_at', null);
    return json({ ok: true }, 200, origin);
  }
  return json({ error: 'unknown action' }, 400, origin);
});
