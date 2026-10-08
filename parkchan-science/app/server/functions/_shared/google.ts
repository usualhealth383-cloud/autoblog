// Google 서비스 계정으로 OAuth 접근 토큰 받기 — 라이브러리 없이 WebCrypto(RS256)만 쓴다.
// GOOGLE_OAUTH_URL 을 바꾸면 로컬 시험대의 가짜 Google 로 붙는다(운영에서는 비워 둔다).
type SA = { client_email: string; private_key: string; token_uri?: string };
const cache = new Map<string, { at: string; exp: number }>();

const b64u = (b: ArrayBuffer | Uint8Array | string) => {
  const bytes = typeof b === 'string' ? new TextEncoder().encode(b) : new Uint8Array(b as ArrayBuffer);
  let s = ''; bytes.forEach((x) => (s += String.fromCharCode(x)));
  return btoa(s).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
};

export async function googleToken(saJson: string, scope: string): Promise<string> {
  const hit = cache.get(scope);
  if (hit && hit.exp > Date.now() + 60_000) return hit.at;
  const sa: SA = JSON.parse(saJson);
  const url = Deno.env.get('GOOGLE_OAUTH_URL') || sa.token_uri || 'https://oauth2.googleapis.com/token';
  const now = Math.floor(Date.now() / 1000);
  const head = b64u(JSON.stringify({ alg: 'RS256', typ: 'JWT' }));
  const body = b64u(JSON.stringify({ iss: sa.client_email, scope, aud: url, iat: now, exp: now + 3600 }));
  const pem = sa.private_key.replace(/-----[^-]+-----/g, '').replace(/\s+/g, '');
  const der = Uint8Array.from(atob(pem), (c) => c.charCodeAt(0));
  const key = await crypto.subtle.importKey('pkcs8', der, { name: 'RSASSA-PKCS1-v1_5', hash: 'SHA-256' }, false, ['sign']);
  const sig = await crypto.subtle.sign('RSASSA-PKCS1-v1_5', key, new TextEncoder().encode(`${head}.${body}`));
  const r = await fetch(url, {
    method: 'POST', headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({ grant_type: 'urn:ietf:params:oauth:grant-type:jwt-bearer', assertion: `${head}.${body}.${b64u(sig)}` }),
  });
  const j = await r.json();
  if (!r.ok || !j.access_token) throw new Error('google oauth: ' + (j.error_description || j.error || r.status));
  cache.set(scope, { at: j.access_token, exp: Date.now() + (j.expires_in || 3600) * 1000 });
  return j.access_token;
}

// Supabase REST(서비스 키) — 함수 안에서 DB 함수를 부를 때
export async function rpc(fn: string, args: unknown) {
  const url = Deno.env.get('SUPABASE_URL')!, key = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!;
  const r = await fetch(`${url}/rest/v1/rpc/${fn}`, {
    method: 'POST', headers: { apikey: key, Authorization: `Bearer ${key}`, 'Content-Type': 'application/json' }, body: JSON.stringify(args),
  });
  const t = await r.text();
  if (!r.ok) throw new Error(`rpc ${fn}: ${r.status} ${t}`);
  return t ? JSON.parse(t) : null;
}
export async function rest(path: string, init: RequestInit = {}) {
  const url = Deno.env.get('SUPABASE_URL')!, key = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!;
  const r = await fetch(`${url}/rest/v1/${path}`, { ...init, headers: { apikey: key, Authorization: `Bearer ${key}`, 'Content-Type': 'application/json', ...(init.headers || {}) } });
  const t = await r.text();
  if (!r.ok) throw new Error(`rest ${path}: ${r.status} ${t}`);
  return t ? JSON.parse(t) : null;
}
export const CORS = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type, x-cron-secret, x-push-secret',
  'Access-Control-Allow-Methods': 'POST, OPTIONS',
};
export const json = (body: unknown, status = 200) => new Response(JSON.stringify(body), { status, headers: { ...CORS, 'Content-Type': 'application/json' } });
